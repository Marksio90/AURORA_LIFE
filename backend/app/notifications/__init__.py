"""
Notifications Module

Real-time notification system with WebSocket support.
"""
from app.notifications.service import NotificationService
from app.notifications.websocket import websocket_manager, WebSocketConnectionManager
from app.notifications.email import EmailService
from app.notifications.schemas import (
    # Enums
    NotificationType,
    NotificationPriority,
    NotificationChannel,

    # Notification Schemas
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationList,

    # Preferences
    NotificationPreferencesUpdate,
    NotificationPreferencesResponse,
    ChannelPreferences,

    # Bulk Operations
    BulkNotificationAction,
    BulkActionResponse,

    # Real-time
    WebSocketMessage,
    NotificationEvent,

    # Statistics
    NotificationStats,
)

__all__ = [
    # Services
    "NotificationService",
    "EmailService",

    # WebSocket
    "websocket_manager",
    "WebSocketConnectionManager",

    # Enums
    "NotificationType",
    "NotificationPriority",
    "NotificationChannel",

    # Notification Schemas
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "NotificationList",

    # Preferences
    "NotificationPreferencesUpdate",
    "NotificationPreferencesResponse",
    "ChannelPreferences",

    # Bulk Operations
    "BulkNotificationAction",
    "BulkActionResponse",

    # Real-time
    "WebSocketMessage",
    "NotificationEvent",

    # Statistics
    "NotificationStats",
]
