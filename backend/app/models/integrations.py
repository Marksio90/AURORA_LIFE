"""
Integration Models - External service connections

Supported integrations:
- Calendar (Google Calendar, Outlook)
- Health (Apple Health, Google Fit, Fitbit, Oura, Whoop)
- Productivity (Todoist, Notion, Trello)
- Music (Spotify)
- Weather (OpenWeather)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from app.models.base import Base


class IntegrationType(str, Enum):
    """Types of integrations"""
    CALENDAR = "calendar"
    HEALTH = "health"
    PRODUCTIVITY = "productivity"
    MUSIC = "music"
    WEATHER = "weather"
    SOCIAL = "social"
    FITNESS = "fitness"


class IntegrationProvider(str, Enum):
    """Supported integration providers"""
    # Calendars
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    APPLE_CALENDAR = "apple_calendar"

    # Health & Fitness
    APPLE_HEALTH = "apple_health"
    GOOGLE_FIT = "google_fit"
    FITBIT = "fitbit"
    OURA = "oura"
    WHOOP = "whoop"
    EIGHT_SLEEP = "eight_sleep"

    # Productivity
    TODOIST = "todoist"
    NOTION = "notion"
    TRELLO = "trello"
    ASANA = "asana"

    # Music
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"

    # Weather
    OPENWEATHER = "openweather"

    # Social
    STRAVA = "strava"
    MYFITNESSPAL = "myfitnesspal"


class SyncStatus(str, Enum):
    """Sync status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class UserIntegration(Base):
    """
    User's connected integrations.
    """
    __tablename__ = "user_integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Integration details
    provider = Column(SQLEnum(IntegrationProvider), nullable=False)
    integration_type = Column(SQLEnum(IntegrationType), nullable=False)

    # Connection status
    is_active = Column(Boolean, default=True)
    is_authorized = Column(Boolean, default=False)

    # OAuth tokens (encrypted in production!)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Provider-specific data
    provider_user_id = Column(String, nullable=True)
    provider_data = Column(JSON, nullable=True)

    # Sync settings
    auto_sync = Column(Boolean, default=True)
    sync_frequency_minutes = Column(Integer, default=60)  # How often to sync
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)

    # Data mapping preferences
    data_mapping = Column(JSON, nullable=True)
    # Example: {"steps": "activity", "heart_rate": "health_metric"}

    # Error handling
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)

    # Timestamps
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="integrations")
    sync_logs = relationship("IntegrationSyncLog", back_populates="integration", cascade="all, delete-orphan")


class IntegrationSyncLog(Base):
    """
    Log of integration sync operations.
    """
    __tablename__ = "integration_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("user_integrations.id"), nullable=False)

    # Sync details
    sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Results
    records_synced = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)

    # Error info
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Sync metadata
    sync_type = Column(String, nullable=True)  # "full", "incremental", "manual"
    data_range_start = Column(DateTime, nullable=True)
    data_range_end = Column(DateTime, nullable=True)

    # Relationships
    integration = relationship("UserIntegration", back_populates="sync_logs")


class SyncedData(Base):
    """
    Data synced from external integrations.

    Stores raw data from integrations before processing into life events.
    """
    __tablename__ = "synced_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("user_integrations.id"), nullable=False)

    # Data details
    data_type = Column(String, nullable=False)  # e.g., "calendar_event", "sleep_session", "workout"
    external_id = Column(String, nullable=True)  # ID from external system

    # Raw data
    raw_data = Column(JSON, nullable=False)

    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)

    # Link to created life event (if processed)
    life_event_id = Column(Integer, ForeignKey("life_events.id"), nullable=True)

    # Timestamps
    data_timestamp = Column(DateTime, nullable=False)  # When data occurred
    synced_at = Column(DateTime, default=datetime.utcnow)  # When we synced it

    # Relationships
    user = relationship("User", back_populates="synced_data")
    integration = relationship("UserIntegration")
    life_event = relationship("LifeEvent")


class WebhookSubscription(Base):
    """
    Webhook subscriptions for real-time updates.

    For services that support webhooks (Fitbit, Oura, etc.)
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("user_integrations.id"), nullable=False)

    # Webhook details
    webhook_url = Column(String, nullable=False)
    subscription_id = Column(String, nullable=True)  # ID from provider
    verification_token = Column(String, nullable=True)

    # Event types subscribed to
    event_types = Column(JSON, nullable=False)  # ["sleep", "activity", "body"]

    # Status
    is_active = Column(Boolean, default=True)
    last_ping_at = Column(DateTime, nullable=True)

    # Timestamps
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    integration = relationship("UserIntegration")


# Update User model
"""
Add to User class in app/models/user.py:

    # Integrations
    integrations = relationship("UserIntegration", back_populates="user")
    synced_data = relationship("SyncedData", back_populates="user")
"""
