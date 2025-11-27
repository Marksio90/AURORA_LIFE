"""
Kafka Event Consumer

Consumes and processes events from Kafka topics.
"""
import json
import logging
import asyncio
from typing import Dict, Callable, Optional, Any
from datetime import datetime

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from app.core.config import settings
from app.events.schemas import BaseEvent, EventType, get_event_schema


logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Async Kafka event consumer.

    Subscribes to topics and processes events with registered handlers.
    """

    def __init__(
        self,
        consumer_group: str,
        bootstrap_servers: str = None,
        topic_pattern: str = "aurora.*"
    ):
        self.consumer_group = consumer_group
        self.bootstrap_servers = bootstrap_servers or getattr(
            settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
        )
        self.topic_pattern = topic_pattern
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: Dict[EventType, list[Callable]] = {}
        self._is_running = False

    async def start(self):
        """Start the Kafka consumer"""
        if self._is_running:
            return

        try:
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',  # Start from beginning
                enable_auto_commit=False,  # Manual commit for reliability
                max_poll_records=100,
                session_timeout_ms=30000
            )

            # Subscribe to topic pattern
            self.consumer.subscribe(pattern=self.topic_pattern)

            await self.consumer.start()
            self._is_running = True

            logger.info(
                f"✅ Kafka consumer '{self.consumer_group}' started. "
                f"Subscribed to pattern: {self.topic_pattern}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka consumer"""
        if self.consumer and self._is_running:
            await self.consumer.stop()
            self._is_running = False
            logger.info(f"Kafka consumer '{self.consumer_group}' stopped")

    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[BaseEvent], Any]
    ):
        """
        Register event handler for specific event type.

        Args:
            event_type: Type of event to handle
            handler: Async function to handle event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.info(f"✅ Registered handler for {event_type.value}")

    async def _process_event(self, event_data: dict):
        """
        Process single event.

        Args:
            event_data: Raw event data from Kafka
        """
        try:
            # Extract event type
            event_type_str = event_data.get('event_type')
            if not event_type_str:
                logger.warning("Event missing event_type field")
                return

            event_type = EventType(event_type_str)

            # Get schema and validate
            event_schema = get_event_schema(event_type)
            event = event_schema(**event_data)

            # Get handlers for this event type
            handlers = self._handlers.get(event_type, [])

            if not handlers:
                logger.debug(f"No handlers for {event_type.value}")
                return

            # Execute all handlers
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)

                    logger.debug(f"✅ Handler executed for {event_type.value}")

                except Exception as e:
                    logger.error(
                        f"❌ Error in handler for {event_type.value}: {e}",
                        exc_info=True
                    )

        except Exception as e:
            logger.error(f"❌ Error processing event: {e}", exc_info=True)

    async def consume(self):
        """
        Start consuming messages.

        This is a blocking call that runs until stopped.
        """
        if not self._is_running:
            await self.start()

        logger.info(f"🔄 Consumer '{self.consumer_group}' started consuming...")

        try:
            async for msg in self.consumer:
                try:
                    logger.debug(
                        f"📥 Received: {msg.topic} [partition {msg.partition}] "
                        f"@ offset {msg.offset}"
                    )

                    # Process event
                    await self._process_event(msg.value)

                    # Commit offset (manual commit for reliability)
                    await self.consumer.commit()

                except Exception as e:
                    logger.error(f"❌ Error consuming message: {e}")
                    # Continue processing other messages

        except asyncio.CancelledError:
            logger.info("Consumer task cancelled")
            raise

        except Exception as e:
            logger.error(f"❌ Fatal error in consumer: {e}")
            raise

        finally:
            await self.stop()


# ==================== CONSUMER INSTANCES ====================

_consumers: Dict[str, EventConsumer] = {}


def get_consumer(
    consumer_group: str,
    topic_pattern: str = "aurora.*"
) -> EventConsumer:
    """Get or create consumer instance"""
    key = f"{consumer_group}:{topic_pattern}"

    if key not in _consumers:
        _consumers[key] = EventConsumer(
            consumer_group=consumer_group,
            topic_pattern=topic_pattern
        )

    return _consumers[key]


async def shutdown_consumers():
    """Shutdown all consumers"""
    for consumer in _consumers.values():
        await consumer.stop()

    _consumers.clear()


# ==================== EXAMPLE HANDLERS ====================

async def handle_xp_earned(event):
    """Example handler for XP earned events"""
    from app.events.schemas import XPEarnedEvent

    logger.info(
        f"🎯 XP Earned: User {event.user_id} earned {event.amount} XP "
        f"from {event.source} (total: {event.total_xp})"
    )

    # Here you could:
    # - Update analytics
    # - Trigger notifications
    # - Update leaderboards
    # - Check for achievements


async def handle_achievement_unlocked(event):
    """Example handler for achievement unlocked events"""
    from app.events.schemas import AchievementUnlockedEvent

    logger.info(
        f"🏆 Achievement Unlocked: User {event.user_id} unlocked "
        f"'{event.achievement_name}' ({event.rarity})"
    )

    # Here you could:
    # - Send push notification
    # - Update user profile
    # - Post to social feed
    # - Award bonus XP


async def handle_integration_synced(event):
    """Example handler for integration sync events"""
    from app.events.schemas import IntegrationSyncedEvent

    logger.info(
        f"🔄 Integration Synced: {event.provider} synced "
        f"{event.records_synced} records in {event.sync_duration_seconds:.2f}s"
    )

    # Here you could:
    # - Update metrics dashboard
    # - Trigger ML predictions
    # - Process new data
    # - Send summary notification


async def handle_error_occurred(event):
    """Example handler for error events"""
    from app.events.schemas import ErrorOccurredEvent

    logger.error(
        f"⚠️ Error in {event.component}: {event.error_type} - "
        f"{event.error_message}"
    )

    # Here you could:
    # - Send to Sentry
    # - Alert on-call engineer
    # - Update error dashboard
    # - Trigger auto-recovery


# ==================== CONSUMER SETUP ====================

def setup_analytics_consumer():
    """Setup consumer for analytics pipeline"""
    consumer = get_consumer(
        consumer_group="aurora-analytics",
        topic_pattern="aurora.*"
    )

    # Register handlers
    consumer.register_handler(EventType.XP_EARNED, handle_xp_earned)
    consumer.register_handler(
        EventType.ACHIEVEMENT_UNLOCKED,
        handle_achievement_unlocked
    )
    consumer.register_handler(
        EventType.INTEGRATION_SYNCED,
        handle_integration_synced
    )

    return consumer


def setup_notification_consumer():
    """Setup consumer for notifications"""
    consumer = get_consumer(
        consumer_group="aurora-notifications",
        topic_pattern="aurora.gamification.*|aurora.social.*"
    )

    # Register handlers for events that trigger notifications
    consumer.register_handler(EventType.LEVEL_UP, lambda e: logger.info(f"🎉 Level up notification"))
    consumer.register_handler(EventType.ACHIEVEMENT_UNLOCKED, handle_achievement_unlocked)
    consumer.register_handler(EventType.FRIEND_REQUEST_SENT, lambda e: logger.info(f"👋 Friend request notification"))

    return consumer


def setup_monitoring_consumer():
    """Setup consumer for monitoring and alerts"""
    consumer = get_consumer(
        consumer_group="aurora-monitoring",
        topic_pattern="aurora.system.*"
    )

    # Register handlers for system events
    consumer.register_handler(EventType.ERROR_OCCURRED, handle_error_occurred)
    consumer.register_handler(EventType.HEALTH_CHECK, lambda e: logger.debug(f"💚 Health check"))

    return consumer


# ==================== STARTUP ====================

async def start_all_consumers():
    """Start all consumer groups"""
    consumers = [
        setup_analytics_consumer(),
        setup_notification_consumer(),
        setup_monitoring_consumer(),
    ]

    # Start all consumers concurrently
    tasks = [consumer.consume() for consumer in consumers]
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    # Run consumers
    asyncio.run(start_all_consumers())
