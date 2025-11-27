"""
Notification Schemas

Pydantic models for notifications and preferences.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, UUID4
from enum import Enum


# ==================== ENUMS ====================

class NotificationType(str, Enum):
    """Notification types"""
    INSIGHT = "insight"
    RECOMMENDATION = "recommendation"
    ACHIEVEMENT = "achievement"
    LEVEL_UP = "level_up"
    STREAK = "streak"
    REMINDER = "reminder"
    SOCIAL = "social"
    SYSTEM = "system"
    ALERT = "alert"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"
    WEBSOCKET = "websocket"


# ==================== NOTIFICATION SCHEMAS ====================

class NotificationBase(BaseModel):
    """Base notification schema"""
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = Field(None, max_length=512)
    action_text: Optional[str] = Field(None, max_length=100)
    icon: Optional[str] = Field(None, max_length=100)
    image_url: Optional[str] = Field(None, max_length=512)
    expires_at: Optional[datetime] = None


class NotificationCreate(NotificationBase):
    """Schema for creating notification"""
    user_id: UUID4


class NotificationUpdate(BaseModel):
    """Schema for updating notification"""
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class NotificationResponse(NotificationBase):
    """Schema for notification response"""
    id: UUID4
    user_id: UUID4
    is_read: bool
    read_at: Optional[datetime] = None
    is_dismissed: bool
    dismissed_at: Optional[datetime] = None
    sent_push: bool
    sent_email: bool
    sent_in_app: bool
    created_at: datetime
    is_expired: bool = False

    class Config:
        from_attributes = True


class NotificationList(BaseModel):
    """List of notifications with pagination"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool


# ==================== NOTIFICATION PREFERENCES ====================

class ChannelPreferences(BaseModel):
    """Channel preferences for a notification type"""
    email: bool = True
    push: bool = True
    in_app: bool = True


class NotificationPreferencesBase(BaseModel):
    """Base notification preferences"""
    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True

    type_preferences: Dict[str, ChannelPreferences] = Field(
        default_factory=lambda: {
            "insight": ChannelPreferences(),
            "recommendation": ChannelPreferences(),
            "achievement": ChannelPreferences(),
            "level_up": ChannelPreferences(),
            "streak": ChannelPreferences(),
            "reminder": ChannelPreferences(push=False),
            "social": ChannelPreferences(),
            "system": ChannelPreferences(push=False),
            "alert": ChannelPreferences(),
        }
    )

    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

    daily_digest_enabled: bool = False
    daily_digest_time: str = Field(default="08:00", pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

    weekly_summary_enabled: bool = True
    weekly_summary_day: str = Field(default="monday")
    weekly_summary_time: str = Field(default="09:00", pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")


class NotificationPreferencesUpdate(NotificationPreferencesBase):
    """Schema for updating notification preferences"""
    pass


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Schema for notification preferences response"""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== BULK OPERATIONS ====================

class BulkNotificationAction(BaseModel):
    """Bulk action on notifications"""
    notification_ids: List[UUID4]
    action: str = Field(..., pattern="^(mark_read|mark_unread|dismiss|delete)$")


class BulkActionResponse(BaseModel):
    """Response for bulk action"""
    success: bool
    affected_count: int
    message: str


# ==================== REAL-TIME ====================

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # notification, ping, pong, etc.
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NotificationEvent(BaseModel):
    """Real-time notification event"""
    event_type: str = "new_notification"
    notification: NotificationResponse


# ==================== STATISTICS ====================

class NotificationStats(BaseModel):
    """Notification statistics"""
    total: int
    unread: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    recent_count_7d: int
    recent_count_30d: int
