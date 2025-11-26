"""
Redis Streams consumer workers for event processing.

Processes events asynchronously using Redis Streams:
- Event notifications
- Real-time analytics
- Webhook delivery
- Email notifications
"""

import asyncio
import json
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import redis.asyncio as redis
import logging

from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class StreamConsumer:
    """Base class for Redis Streams consumers."""

    def __init__(
        self,
        stream_name: str,
        consumer_group: str,
        consumer_name: str,
        batch_size: int = 10,
        block_ms: int = 5000
    ):
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.batch_size = batch_size
        self.block_ms = block_ms
        self.redis_client: Optional[redis.Redis] = None
        self.running = False

    async def connect(self):
        """Connect to Redis."""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

        # Create consumer group if it doesn't exist
        try:
            await self.redis_client.xgroup_create(
                self.stream_name,
                self.consumer_group,
                id="0",
                mkstream=True
            )
            logger.info(
                f"Created consumer group '{self.consumer_group}' "
                f"for stream '{self.stream_name}'"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Failed to create consumer group: {e}")
                raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def consume(self):
        """Start consuming messages from the stream."""
        self.running = True
        logger.info(
            f"Starting consumer '{self.consumer_name}' "
            f"for stream '{self.stream_name}'"
        )

        while self.running:
            try:
                # Read messages from stream
                messages = await self.redis_client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.stream_name: ">"},
                    count=self.batch_size,
                    block=self.block_ms
                )

                if not messages:
                    continue

                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        try:
                            await self.process_message(message_id, message_data)

                            # Acknowledge message
                            await self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )

                        except Exception as e:
                            logger.error(
                                f"Error processing message {message_id}: {e}",
                                exc_info=True
                            )
                            # Message will be retried later via pending entries

            except asyncio.CancelledError:
                logger.info("Consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error

        logger.info(f"Consumer '{self.consumer_name}' stopped")

    async def process_message(self, message_id: str, data: Dict[str, Any]):
        """Process a single message. Override in subclass."""
        raise NotImplementedError

    def stop(self):
        """Stop the consumer."""
        self.running = False


class EventNotificationConsumer(StreamConsumer):
    """Consumer for event notifications."""

    def __init__(self):
        super().__init__(
            stream_name="events:notifications",
            consumer_group="notification-workers",
            consumer_name=f"worker-{datetime.now().timestamp()}"
        )

    async def process_message(self, message_id: str, data: Dict[str, Any]):
        """Process event notification."""
        event_type = data.get("event_type")
        user_id = data.get("user_id")
        event_id = data.get("event_id")

        logger.info(
            f"Processing event notification: {event_type} "
            f"for user {user_id}"
        )

        # Send WebSocket notification
        from app.core.websocket import connection_manager
        await connection_manager.broadcast_to_user(
            user_id=user_id,
            message={
                "type": "event_created",
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class AnalyticsConsumer(StreamConsumer):
    """Consumer for real-time analytics processing."""

    def __init__(self):
        super().__init__(
            stream_name="events:analytics",
            consumer_group="analytics-workers",
            consumer_name=f"worker-{datetime.now().timestamp()}"
        )

    async def process_message(self, message_id: str, data: Dict[str, Any]):
        """Process analytics event."""
        event_type = data.get("event_type")
        user_id = data.get("user_id")
        event_data = json.loads(data.get("event_data", "{}"))

        logger.info(f"Processing analytics for user {user_id}")

        # Update user's daily statistics
        async with AsyncSessionLocal() as db:
            from app.services.timeline import TimelineService
            timeline_service = TimelineService(db)

            await timeline_service.update_daily_aggregation(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data
            )


class WebhookDeliveryConsumer(StreamConsumer):
    """Consumer for webhook delivery."""

    def __init__(self):
        super().__init__(
            stream_name="webhooks:delivery",
            consumer_group="webhook-workers",
            consumer_name=f"worker-{datetime.now().timestamp()}",
            batch_size=5  # Lower batch size for webhooks
        )

    async def process_message(self, message_id: str, data: Dict[str, Any]):
        """Deliver webhook."""
        webhook_id = data.get("webhook_id")
        event_type = data.get("event_type")
        payload = json.loads(data.get("payload", "{}"))

        logger.info(f"Delivering webhook {webhook_id} for event {event_type}")

        from app.core.webhooks import WebhookService
        async with AsyncSessionLocal() as db:
            webhook_service = WebhookService(db)
            await webhook_service.deliver_webhook(
                webhook_id=webhook_id,
                event_type=event_type,
                payload=payload
            )


class EmailNotificationConsumer(StreamConsumer):
    """Consumer for email notifications."""

    def __init__(self):
        super().__init__(
            stream_name="notifications:email",
            consumer_group="email-workers",
            consumer_name=f"worker-{datetime.now().timestamp()}"
        )

    async def process_message(self, message_id: str, data: Dict[str, Any]):
        """Send email notification."""
        email_type = data.get("email_type")
        recipient = data.get("recipient")
        subject = data.get("subject")
        body = data.get("body")

        logger.info(f"Sending {email_type} email to {recipient}")

        from app.services.email_service import EmailService
        email_service = EmailService()

        await email_service.send_email(
            to=recipient,
            subject=subject,
            body=body
        )


# Worker manager
class StreamWorkerManager:
    """Manages multiple stream consumer workers."""

    def __init__(self):
        self.consumers: list[StreamConsumer] = []
        self.tasks: list[asyncio.Task] = []

    def register_consumer(self, consumer: StreamConsumer):
        """Register a consumer worker."""
        self.consumers.append(consumer)

    async def start_all(self):
        """Start all registered consumers."""
        logger.info(f"Starting {len(self.consumers)} stream consumers")

        for consumer in self.consumers:
            await consumer.connect()
            task = asyncio.create_task(consumer.consume())
            self.tasks.append(task)

        logger.info("All stream consumers started")

    async def stop_all(self):
        """Stop all consumers."""
        logger.info("Stopping all stream consumers")

        for consumer in self.consumers:
            consumer.stop()

        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        for consumer in self.consumers:
            await consumer.disconnect()

        logger.info("All stream consumers stopped")

    async def run_forever(self):
        """Run consumers until interrupted."""
        try:
            await self.start_all()
            # Keep running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop_all()


# Main entry point for running workers
async def main():
    """Run all stream consumer workers."""
    manager = StreamWorkerManager()

    # Register consumers
    manager.register_consumer(EventNotificationConsumer())
    manager.register_consumer(AnalyticsConsumer())
    manager.register_consumer(WebhookDeliveryConsumer())
    manager.register_consumer(EmailNotificationConsumer())

    # Run forever
    await manager.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
