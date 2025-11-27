"""
Event Streaming Module

Kafka-based event streaming for real-time data processing.
"""
from app.events.schemas import (
    EventType,
    BaseEvent,
    UserRegisteredEvent,
    XPEarnedEvent,
    LevelUpEvent,
    AchievementUnlockedEvent,
    StreakUpdatedEvent,
    IntegrationSyncedEvent,
    PredictionGeneratedEvent,
)
from app.events.producer import (
    EventProducer,
    get_event_producer,
    publish_event,
    create_event_id,
    publish_xp_earned,
    publish_achievement_unlocked,
)
from app.events.consumer import (
    EventConsumer,
    get_consumer,
    setup_analytics_consumer,
    setup_notification_consumer,
    setup_monitoring_consumer,
)

__all__ = [
    # Schemas
    'EventType',
    'BaseEvent',
    'UserRegisteredEvent',
    'XPEarnedEvent',
    'LevelUpEvent',
    'AchievementUnlockedEvent',
    'StreakUpdatedEvent',
    'IntegrationSyncedEvent',
    'PredictionGeneratedEvent',

    # Producer
    'EventProducer',
    'get_event_producer',
    'publish_event',
    'create_event_id',
    'publish_xp_earned',
    'publish_achievement_unlocked',

    # Consumer
    'EventConsumer',
    'get_consumer',
    'setup_analytics_consumer',
    'setup_notification_consumer',
    'setup_monitoring_consumer',
]
