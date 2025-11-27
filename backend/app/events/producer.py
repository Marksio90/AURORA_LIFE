"""
Kafka Event Producer

Publishes events to Kafka topics for real-time processing.
"""
import json
import logging
from typing import Optional
from datetime import datetime
import uuid

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.core.config import settings
from app.events.schemas import BaseEvent, EventType


logger = logging.getLogger(__name__)


class EventProducer:
    """
    Async Kafka event producer.

    Publishes events to Kafka topics for downstream processing.
    """

    def __init__(
        self,
        bootstrap_servers: str = None,
        topic_prefix: str = "aurora"
    ):
        self.bootstrap_servers = bootstrap_servers or getattr(
            settings, 'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
        )
        self.topic_prefix = topic_prefix
        self.producer: Optional[AIOKafkaProducer] = None
        self._is_connected = False

    async def start(self):
        """Start the Kafka producer"""
        if self._is_connected:
            return

        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                compression_type='gzip',
                acks='all',  # Wait for all replicas
                max_in_flight_requests_per_connection=5,
                retries=3
            )

            await self.producer.start()
            self._is_connected = True
            logger.info(f"✅ Kafka producer connected to {self.bootstrap_servers}")

        except Exception as e:
            logger.error(f"❌ Failed to connect Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer and self._is_connected:
            await self.producer.stop()
            self._is_connected = False
            logger.info("Kafka producer stopped")

    def _get_topic_name(self, event_type: EventType) -> str:
        """
        Get Kafka topic name for event type.

        Format: {prefix}.{category}.{subcategory}
        Example: aurora.gamification.xp_earned
        """
        parts = event_type.value.split('.')
        if len(parts) == 2:
            category, subcategory = parts
            return f"{self.topic_prefix}.{category}.{subcategory}"
        else:
            return f"{self.topic_prefix}.{event_type.value}"

    def _get_partition_key(self, event: BaseEvent) -> Optional[str]:
        """
        Get partition key for event.

        Events for same user go to same partition for ordering.
        """
        if event.user_id:
            return str(event.user_id)
        return None

    async def publish(self, event: BaseEvent) -> bool:
        """
        Publish event to Kafka.

        Args:
            event: Event to publish

        Returns:
            True if successful, False otherwise
        """
        if not self._is_connected:
            await self.start()

        try:
            topic = self._get_topic_name(event.event_type)
            partition_key = self._get_partition_key(event)

            # Convert event to dict
            event_data = event.model_dump(mode='json')

            # Add metadata
            event_data['_published_at'] = datetime.utcnow().isoformat()
            event_data['_producer_id'] = 'aurora-backend'

            # Send to Kafka
            future = await self.producer.send(
                topic=topic,
                value=event_data,
                key=partition_key
            )

            # Wait for confirmation
            record_metadata = await future

            logger.info(
                f"📤 Event published: {event.event_type.value} "
                f"→ {topic} (partition {record_metadata.partition}, "
                f"offset {record_metadata.offset})"
            )

            return True

        except KafkaError as e:
            logger.error(f"❌ Kafka error publishing event: {e}")
            return False

        except Exception as e:
            logger.error(f"❌ Error publishing event: {e}")
            return False

    async def publish_batch(self, events: list[BaseEvent]) -> int:
        """
        Publish multiple events in batch.

        Args:
            events: List of events to publish

        Returns:
            Number of successfully published events
        """
        if not self._is_connected:
            await self.start()

        success_count = 0

        for event in events:
            if await self.publish(event):
                success_count += 1

        logger.info(f"📤 Batch published: {success_count}/{len(events)} events")

        return success_count


# ==================== GLOBAL PRODUCER INSTANCE ====================

_event_producer: Optional[EventProducer] = None


async def get_event_producer() -> EventProducer:
    """Get global event producer instance"""
    global _event_producer

    if _event_producer is None:
        _event_producer = EventProducer()
        await _event_producer.start()

    return _event_producer


async def publish_event(event: BaseEvent) -> bool:
    """
    Convenience function to publish event.

    Usage:
        await publish_event(XPEarnedEvent(
            event_id=str(uuid.uuid4()),
            user_id=user.id,
            amount=50,
            source="life_event",
            total_xp=500
        ))
    """
    producer = await get_event_producer()
    return await producer.publish(event)


async def shutdown_producer():
    """Shutdown global producer"""
    global _event_producer

    if _event_producer:
        await _event_producer.stop()
        _event_producer = None


# ==================== HELPER FUNCTIONS ====================

def create_event_id() -> str:
    """Generate unique event ID"""
    return str(uuid.uuid4())


async def publish_life_event_created(
    user_id: str,
    life_event_id: str,
    event_category: str,
    event_time: datetime,
    **kwargs
):
    """Helper to publish life event created"""
    from app.events.schemas import LifeEventCreatedEvent

    event = LifeEventCreatedEvent(
        event_id=create_event_id(),
        user_id=user_id,
        life_event_id=life_event_id,
        event_category=event_category,
        event_time=event_time,
        **kwargs
    )

    return await publish_event(event)


async def publish_xp_earned(
    user_id: str,
    amount: int,
    source: str,
    total_xp: int,
    **kwargs
):
    """Helper to publish XP earned event"""
    from app.events.schemas import XPEarnedEvent

    event = XPEarnedEvent(
        event_id=create_event_id(),
        user_id=user_id,
        amount=amount,
        source=source,
        total_xp=total_xp,
        **kwargs
    )

    return await publish_event(event)


async def publish_achievement_unlocked(
    user_id: str,
    achievement_id: int,
    achievement_name: str,
    **kwargs
):
    """Helper to publish achievement unlocked"""
    from app.events.schemas import AchievementUnlockedEvent

    event = AchievementUnlockedEvent(
        event_id=create_event_id(),
        user_id=user_id,
        achievement_id=achievement_id,
        achievement_name=achievement_name,
        **kwargs
    )

    return await publish_event(event)
