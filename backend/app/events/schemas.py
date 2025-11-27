"""
Event schemas for Kafka streaming

Defines all event types that flow through the Kafka pipeline.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, UUID4


class EventType(str, Enum):
    """Types of events in the system"""
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    # Life events
    LIFE_EVENT_CREATED = "life_event.created"
    LIFE_EVENT_UPDATED = "life_event.updated"
    LIFE_EVENT_DELETED = "life_event.deleted"

    # Gamification events
    XP_EARNED = "gamification.xp_earned"
    LEVEL_UP = "gamification.level_up"
    ACHIEVEMENT_UNLOCKED = "gamification.achievement_unlocked"
    BADGE_EARNED = "gamification.badge_earned"
    STREAK_UPDATED = "gamification.streak_updated"

    # Social events
    FRIEND_REQUEST_SENT = "social.friend_request_sent"
    FRIEND_REQUEST_ACCEPTED = "social.friend_request_accepted"
    POST_CREATED = "social.post_created"
    COMMENT_ADDED = "social.comment_added"
    POST_LIKED = "social.post_liked"

    # Integration events
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_SYNCED = "integration.synced"
    INTEGRATION_FAILED = "integration.failed"

    # ML/AI events
    PREDICTION_GENERATED = "ml.prediction_generated"
    INSIGHT_CREATED = "ml.insight_created"
    RECOMMENDATION_MADE = "ml.recommendation_made"

    # System events
    ERROR_OCCURRED = "system.error_occurred"
    HEALTH_CHECK = "system.health_check"


class BaseEvent(BaseModel):
    """Base event schema"""
    event_id: str = Field(description="Unique event ID")
    event_type: EventType = Field(description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[UUID4] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID4: lambda v: str(v)
        }


# ==================== USER EVENTS ====================

class UserRegisteredEvent(BaseEvent):
    """User registration event"""
    event_type: EventType = EventType.USER_REGISTERED
    email: str
    username: str
    registration_source: str = "web"


class UserLoginEvent(BaseEvent):
    """User login event"""
    event_type: EventType = EventType.USER_LOGIN
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_method: str = "email"  # email, google, github


# ==================== LIFE EVENT EVENTS ====================

class LifeEventCreatedEvent(BaseEvent):
    """Life event created"""
    event_type: EventType = EventType.LIFE_EVENT_CREATED
    life_event_id: UUID4
    event_category: str  # sleep, exercise, work, etc.
    event_time: datetime
    duration_minutes: Optional[float] = None
    tags: List[str] = Field(default_factory=list)


class LifeEventUpdatedEvent(BaseEvent):
    """Life event updated"""
    event_type: EventType = EventType.LIFE_EVENT_UPDATED
    life_event_id: UUID4
    changes: Dict[str, Any]


# ==================== GAMIFICATION EVENTS ====================

class XPEarnedEvent(BaseEvent):
    """XP earned event"""
    event_type: EventType = EventType.XP_EARNED
    amount: int
    source: str  # "life_event", "achievement", "daily_challenge"
    multiplier: float = 1.0
    total_xp: int


class LevelUpEvent(BaseEvent):
    """Level up event"""
    event_type: EventType = EventType.LEVEL_UP
    previous_level: int
    new_level: int
    total_xp: int
    rewards: Dict[str, Any] = Field(default_factory=dict)


class AchievementUnlockedEvent(BaseEvent):
    """Achievement unlocked"""
    event_type: EventType = EventType.ACHIEVEMENT_UNLOCKED
    achievement_id: int
    achievement_name: str
    category: str
    rarity: str
    xp_reward: int
    points_reward: int


class StreakUpdatedEvent(BaseEvent):
    """Streak updated"""
    event_type: EventType = EventType.STREAK_UPDATED
    streak_type: str
    current_streak: int
    longest_streak: int
    milestone_reached: bool = False
    milestone_days: Optional[int] = None
    xp_reward: int = 0


# ==================== SOCIAL EVENTS ====================

class FriendRequestSentEvent(BaseEvent):
    """Friend request sent"""
    event_type: EventType = EventType.FRIEND_REQUEST_SENT
    friend_id: UUID4
    message: Optional[str] = None


class PostCreatedEvent(BaseEvent):
    """Social post created"""
    event_type: EventType = EventType.POST_CREATED
    post_id: int
    group_id: Optional[int] = None
    content_preview: str  # First 100 chars
    tags: List[str] = Field(default_factory=list)


# ==================== INTEGRATION EVENTS ====================

class IntegrationSyncedEvent(BaseEvent):
    """Integration synced successfully"""
    event_type: EventType = EventType.INTEGRATION_SYNCED
    integration_id: int
    provider: str  # fitbit, oura, spotify, google_calendar
    records_synced: int
    sync_duration_seconds: float
    data_types: List[str] = Field(default_factory=list)


class IntegrationFailedEvent(BaseEvent):
    """Integration sync failed"""
    event_type: EventType = EventType.INTEGRATION_FAILED
    integration_id: int
    provider: str
    error_type: str
    error_message: str
    retry_count: int = 0


# ==================== ML/AI EVENTS ====================

class PredictionGeneratedEvent(BaseEvent):
    """ML prediction generated"""
    event_type: EventType = EventType.PREDICTION_GENERATED
    model_type: str  # energy, mood, sleep_quality
    prediction_value: float
    confidence: float
    features_used: List[str] = Field(default_factory=list)
    model_version: str


class InsightCreatedEvent(BaseEvent):
    """Insight created"""
    event_type: EventType = EventType.INSIGHT_CREATED
    insight_id: UUID4
    insight_type: str  # correlation, pattern, recommendation
    title: str
    significance_score: float


class RecommendationMadeEvent(BaseEvent):
    """Recommendation made"""
    event_type: EventType = EventType.RECOMMENDATION_MADE
    recommendation_id: str
    recommendation_type: str  # activity, sleep_time, exercise
    priority: str  # high, medium, low
    confidence: float


# ==================== SYSTEM EVENTS ====================

class ErrorOccurredEvent(BaseEvent):
    """Error occurred in system"""
    event_type: EventType = EventType.ERROR_OCCURRED
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    severity: str = "error"  # info, warning, error, critical
    component: str  # backend, celery, integration


class HealthCheckEvent(BaseEvent):
    """Health check event"""
    event_type: EventType = EventType.HEALTH_CHECK
    component: str
    status: str  # healthy, degraded, unhealthy
    response_time_ms: float
    checks: Dict[str, bool] = Field(default_factory=dict)


# ==================== EVENT TYPE MAPPING ====================

EVENT_TYPE_MAP = {
    EventType.USER_REGISTERED: UserRegisteredEvent,
    EventType.USER_LOGIN: UserLoginEvent,
    EventType.LIFE_EVENT_CREATED: LifeEventCreatedEvent,
    EventType.LIFE_EVENT_UPDATED: LifeEventUpdatedEvent,
    EventType.XP_EARNED: XPEarnedEvent,
    EventType.LEVEL_UP: LevelUpEvent,
    EventType.ACHIEVEMENT_UNLOCKED: AchievementUnlockedEvent,
    EventType.STREAK_UPDATED: StreakUpdatedEvent,
    EventType.FRIEND_REQUEST_SENT: FriendRequestSentEvent,
    EventType.POST_CREATED: PostCreatedEvent,
    EventType.INTEGRATION_SYNCED: IntegrationSyncedEvent,
    EventType.INTEGRATION_FAILED: IntegrationFailedEvent,
    EventType.PREDICTION_GENERATED: PredictionGeneratedEvent,
    EventType.INSIGHT_CREATED: InsightCreatedEvent,
    EventType.RECOMMENDATION_MADE: RecommendationMadeEvent,
    EventType.ERROR_OCCURRED: ErrorOccurredEvent,
    EventType.HEALTH_CHECK: HealthCheckEvent,
}


def get_event_schema(event_type: EventType) -> type[BaseEvent]:
    """Get event schema class for event type"""
    return EVENT_TYPE_MAP.get(event_type, BaseEvent)
