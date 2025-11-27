"""
Notification Model

Database model for user notifications.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
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


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Notification details
    type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.SYSTEM)
    priority = Column(SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Additional data (flexible JSONB)
    data = Column(JSONB, nullable=True)

    # Action link (optional)
    action_url = Column(String(512), nullable=True)
    action_text = Column(String(100), nullable=True)

    # Icon/image
    icon = Column(String(100), nullable=True)  # emoji or icon name
    image_url = Column(String(512), nullable=True)

    # Read status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    # Dismissal
    is_dismissed = Column(Boolean, default=False, nullable=False)
    dismissed_at = Column(DateTime, nullable=True)

    # Delivery channels
    sent_push = Column(Boolean, default=False, nullable=False)
    sent_email = Column(Boolean, default=False, nullable=False)
    sent_in_app = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, title={self.title})>"

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def dismiss(self):
        """Dismiss notification"""
        self.is_dismissed = True
        self.dismissed_at = datetime.utcnow()

    @property
    def is_expired(self) -> bool:
        """Check if notification is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Channel preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)

    # Type preferences (JSONB for flexibility)
    type_preferences = Column(JSONB, nullable=False, default={
        "insight": {"email": True, "push": True, "in_app": True},
        "recommendation": {"email": True, "push": True, "in_app": True},
        "achievement": {"email": True, "push": True, "in_app": True},
        "level_up": {"email": True, "push": True, "in_app": True},
        "streak": {"email": True, "push": True, "in_app": True},
        "reminder": {"email": True, "push": False, "in_app": True},
        "social": {"email": True, "push": True, "in_app": True},
        "system": {"email": True, "push": False, "in_app": True},
        "alert": {"email": True, "push": True, "in_app": True},
    })

    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format

    # Daily digest
    daily_digest_enabled = Column(Boolean, default=False, nullable=False)
    daily_digest_time = Column(String(5), nullable=True, default="08:00")  # HH:MM

    # Weekly summary
    weekly_summary_enabled = Column(Boolean, default=True, nullable=False)
    weekly_summary_day = Column(String(10), nullable=True, default="monday")
    weekly_summary_time = Column(String(5), nullable=True, default="09:00")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id}, email={self.email_enabled}, push={self.push_enabled})>"

    def should_send(self, notification_type: str, channel: str) -> bool:
        """
        Check if notification should be sent based on preferences.

        Args:
            notification_type: Type of notification
            channel: Delivery channel (email, push, in_app)

        Returns:
            bool: True if should send
        """
        # Check global channel setting
        if channel == "email" and not self.email_enabled:
            return False
        elif channel == "push" and not self.push_enabled:
            return False
        elif channel == "in_app" and not self.in_app_enabled:
            return False

        # Check type-specific preferences
        type_prefs = self.type_preferences.get(notification_type, {})
        return type_prefs.get(channel, True)
