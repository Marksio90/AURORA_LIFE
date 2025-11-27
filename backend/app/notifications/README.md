## Notifications Module 🔔

Real-time notification system with WebSocket support, email delivery, and comprehensive preference management.

## 📋 Overview

The Notifications module provides:
- **In-app Notifications** - Persistent notifications in database
- **Real-time Updates** - WebSocket for instant delivery
- **Email Notifications** - SMTP-based email delivery
- **Push Notifications** - Web Push support (future)
- **Preference Management** - Granular user controls
- **Bulk Operations** - Efficient batch processing
- **Statistics** - Notification analytics

## 🏗️ Architecture

```
notifications/
├── schemas.py         # Pydantic models
├── service.py         # Notification CRUD service
├── websocket.py       # WebSocket connection manager
├── email.py           # Email delivery service
├── helpers.py         # Utility functions
└── __init__.py        # Module exports

models/
└── notification.py    # SQLAlchemy models
```

## 🚀 Quick Start

### Send a Notification

```python
from app.notifications.helpers import send_notification, NotificationType, NotificationPriority

# Send notification
await send_notification(
    db=db,
    user_id="user-123",
    notification_type=NotificationType.ACHIEVEMENT,
    title="Achievement Unlocked!",
    message="You've completed 100 activities",
    priority=NotificationPriority.HIGH,
    icon="🏆",
    action_url="/achievements",
    action_text="View Achievements",
)
```

### Use Helper Functions

```python
from app.notifications.helpers import (
    send_achievement_notification,
    send_level_up_notification,
    send_insight_notification,
)

# Send achievement notification
await send_achievement_notification(
    db=db,
    user_id="user-123",
    achievement_name="Century Club",
    achievement_description="Completed 100 activities",
    xp_earned=500,
)

# Send level up notification
await send_level_up_notification(
    db=db,
    user_id="user-123",
    new_level=25,
    rewards=["Custom Avatar", "Premium Badge"],
)

# Send insight notification
await send_insight_notification(
    db=db,
    user_id="user-123",
    insight_title="Sleep Pattern Detected",
    insight_message="You have a consistent bedtime around 11 PM",
    action_items=["Keep maintaining this schedule"],
)
```

### WebSocket Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/api/v1/notifications/ws?token=${authToken}`);

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'notification') {
        // New notification received
        console.log('New notification:', data.data);
        showNotification(data.data);
    } else if (data.type === 'ping') {
        // Send pong back
        ws.send(JSON.stringify({ type: 'pong' }));
    }
};

// Connection opened
ws.onopen = () => {
    console.log('WebSocket connected');
};

// Handle errors
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

## 📊 Notification Types

### Available Types

```python
class NotificationType(str, Enum):
    INSIGHT = "insight"               # Data-driven insights
    RECOMMENDATION = "recommendation" # Personalized suggestions
    ACHIEVEMENT = "achievement"       # Achievement unlocked
    LEVEL_UP = "level_up"            # Level increase
    STREAK = "streak"                # Streak milestone
    REMINDER = "reminder"            # Task reminders
    SOCIAL = "social"                # Social interactions
    SYSTEM = "system"                # System messages
    ALERT = "alert"                  # Important alerts
```

### Priority Levels

```python
class NotificationPriority(str, Enum):
    LOW = "low"         # Informational
    MEDIUM = "medium"   # Standard
    HIGH = "high"       # Important
    URGENT = "urgent"   # Critical
```

## 🌐 API Endpoints

### Notification Management

**Get Notifications**
```http
GET /api/v1/notifications?page=1&page_size=20&unread_only=false
```

Query Parameters:
- `page` - Page number (1-indexed)
- `page_size` - Items per page (max 100)
- `unread_only` - Return only unread
- `notification_type` - Filter by type
- `include_dismissed` - Include dismissed notifications

Response:
```json
{
    "notifications": [...],
    "total": 150,
    "unread_count": 12,
    "page": 1,
    "page_size": 20,
    "has_more": true
}
```

---

**Get Single Notification**
```http
GET /api/v1/notifications/{notification_id}
```

---

**Mark as Read**
```http
POST /api/v1/notifications/{notification_id}/read
```

---

**Mark All as Read**
```http
POST /api/v1/notifications/read-all
```

Response:
```json
{
    "success": true,
    "affected_count": 12,
    "message": "Marked 12 notifications as read"
}
```

---

**Dismiss Notification**
```http
POST /api/v1/notifications/{notification_id}/dismiss
```

---

**Delete Notification**
```http
DELETE /api/v1/notifications/{notification_id}
```

---

**Bulk Actions**
```http
POST /api/v1/notifications/bulk
```

Request Body:
```json
{
    "notification_ids": ["id1", "id2", "id3"],
    "action": "mark_read"
}
```

Actions: `mark_read`, `mark_unread`, `dismiss`, `delete`

---

**Get Statistics**
```http
GET /api/v1/notifications/stats/summary
```

Response:
```json
{
    "total": 150,
    "unread": 12,
    "by_type": {
        "insight": 45,
        "achievement": 30,
        "recommendation": 25
    },
    "by_priority": {
        "high": 15,
        "medium": 100,
        "low": 35
    },
    "recent_count_7d": 28,
    "recent_count_30d": 95
}
```

### Preferences

**Get Preferences**
```http
GET /api/v1/notifications/preferences/me
```

---

**Update Preferences**
```http
PUT /api/v1/notifications/preferences/me
```

Request Body:
```json
{
    "email_enabled": true,
    "push_enabled": true,
    "in_app_enabled": true,
    "type_preferences": {
        "insight": {
            "email": true,
            "push": true,
            "in_app": true
        },
        "achievement": {
            "email": true,
            "push": true,
            "in_app": true
        }
    },
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "daily_digest_enabled": true,
    "daily_digest_time": "08:00",
    "weekly_summary_enabled": true,
    "weekly_summary_day": "monday",
    "weekly_summary_time": "09:00"
}
```

### WebSocket

**Connect**
```
ws://localhost:8000/api/v1/notifications/ws?token=YOUR_AUTH_TOKEN
```

**Message Types:**

Incoming:
```json
{
    "type": "notification",
    "event": "new_notification",
    "data": { /* notification object */ },
    "timestamp": "2025-01-27T12:00:00Z"
}
```

```json
{
    "type": "ping",
    "timestamp": "2025-01-27T12:00:00Z"
}
```

Outgoing:
```json
{
    "type": "pong",
    "timestamp": "2025-01-27T12:00:00Z"
}
```

## 🔧 Notification Service

### Create Notification

```python
from app.notifications.service import NotificationService
from app.notifications.schemas import NotificationCreate, NotificationType

service = NotificationService(db)

notification = service.create_notification(
    notification_data=NotificationCreate(
        user_id="user-123",
        type=NotificationType.ACHIEVEMENT,
        priority=NotificationPriority.HIGH,
        title="Achievement Unlocked",
        message="You've reached level 10!",
    )
)
```

### Get User Notifications

```python
notifications_list = service.get_user_notifications(
    user_id="user-123",
    page=1,
    page_size=20,
    unread_only=True,
)

print(f"Unread: {notifications_list.unread_count}")
for notif in notifications_list.notifications:
    print(f"{notif.title}: {notif.message}")
```

### Bulk Operations

```python
from app.notifications.schemas import BulkNotificationAction

action = BulkNotificationAction(
    notification_ids=["id1", "id2", "id3"],
    action="mark_read",
)

affected = service.bulk_action(action, user_id="user-123")
print(f"Affected {affected} notifications")
```

### Preferences

```python
# Get or create preferences
prefs = service.get_or_create_preferences(user_id="user-123")

# Update preferences
prefs = service.update_preferences(
    user_id="user-123",
    preferences_data={
        "email_enabled": True,
        "quiet_hours_enabled": True,
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
    }
)

# Check if notification should be sent
should_send = prefs.should_send(
    notification_type="insight",
    channel="email",
)
```

## 📧 Email Service

### Send Email Notification

```python
from app.notifications.email import EmailService

email_service = EmailService(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your-email@gmail.com",
    smtp_password="your-app-password",
    from_name="Aurora Life",
)

# Send notification email
email_service.send_notification_email(
    to_email="user@example.com",
    notification_type="achievement",
    title="Achievement Unlocked",
    message="You've completed 100 activities!",
    action_url="https://aurora-life.com/achievements",
    action_text="View Achievements",
)
```

### Send Daily Digest

```python
from datetime import datetime

email_service.send_daily_digest(
    to_email="user@example.com",
    notifications=[
        {
            "title": "New Insight",
            "message": "Your sleep pattern is consistent",
            "created_at": "2025-01-27 08:00:00",
        },
        # ... more notifications
    ],
    date=datetime.now(),
)
```

### Send Weekly Summary

```python
email_service.send_weekly_summary(
    to_email="user@example.com",
    summary_data={
        "wellness_score": 85,
        "activities_count": 42,
        "achievements": 3,
    },
    week_start=datetime(2025, 1, 20),
    week_end=datetime(2025, 1, 27),
)
```

## 🔌 WebSocket Manager

### Send to Specific User

```python
from app.notifications.websocket import websocket_manager

# Send notification to user
await websocket_manager.send_notification(
    user_id="user-123",
    notification={
        "id": "notif-id",
        "title": "New Message",
        "message": "You have a new comment",
    }
)

# Send custom message
await websocket_manager.send_to_user(
    message={
        "type": "custom_event",
        "data": {"foo": "bar"},
    },
    user_id="user-123",
)
```

### Broadcast to All Users

```python
await websocket_manager.broadcast_to_all(
    message={
        "type": "system_announcement",
        "message": "Scheduled maintenance in 1 hour",
    }
)
```

### Check Connection Status

```python
# Check if user is connected
is_connected = websocket_manager.is_user_connected("user-123")

# Get stats
total_users = websocket_manager.get_active_users_count()
total_connections = websocket_manager.get_total_connections_count()
```

## 🎯 Helper Functions

All available in `app.notifications.helpers`:

```python
# Achievement
await send_achievement_notification(db, user_id, "Century Club", "100 activities", xp_earned=500)

# Level Up
await send_level_up_notification(db, user_id, new_level=25, rewards=["Badge"])

# Streak
await send_streak_notification(db, user_id, streak_days=30, milestone=True)

# Insight
await send_insight_notification(db, user_id, "Sleep Pattern", "Consistent bedtime")

# Recommendation
await send_recommendation_notification(db, user_id, "Exercise More", "Try 3x/week")

# Reminder
await send_reminder_notification(db, user_id, "Daily Check-in", "Log today's activities")

# Social
await send_social_notification(db, user_id, "friend_request", actor_name="John")

# System
await send_system_notification(db, user_id, "Update Available", "New features added")

# Alert
await send_alert_notification(db, user_id, "Account Security", "Login from new device")
```

## 🔐 Security

- WebSocket connections require authentication token
- Users can only access their own notifications
- Email delivery respects user preferences
- Rate limiting on notification creation (TODO)
- XSS protection in email templates

## 📊 Database Models

### Notification

```python
class Notification(Base):
    id: UUID
    user_id: UUID
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    data: JSONB              # Additional data
    action_url: str          # Optional action link
    action_text: str         # Optional action button text
    icon: str                # Emoji or icon name
    image_url: str           # Optional image
    is_read: bool
    read_at: datetime
    is_dismissed: bool
    dismissed_at: datetime
    sent_push: bool
    sent_email: bool
    sent_in_app: bool
    created_at: datetime
    expires_at: datetime
```

### NotificationPreference

```python
class NotificationPreference(Base):
    id: UUID
    user_id: UUID
    email_enabled: bool
    push_enabled: bool
    in_app_enabled: bool
    type_preferences: JSONB  # Per-type channel preferences
    quiet_hours_enabled: bool
    quiet_hours_start: str   # HH:MM
    quiet_hours_end: str     # HH:MM
    daily_digest_enabled: bool
    daily_digest_time: str   # HH:MM
    weekly_summary_enabled: bool
    weekly_summary_day: str
    weekly_summary_time: str
    created_at: datetime
    updated_at: datetime
```

## 🧪 Testing

```bash
# Test notification creation
curl -X POST "http://localhost:8000/api/v1/notifications/test/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "type": "achievement",
    "priority": "high",
    "title": "Test Notification",
    "message": "This is a test notification"
  }'

# Test WebSocket
wscat -c "ws://localhost:8000/api/v1/notifications/ws?token=$TOKEN"
```

## 📈 Performance

- Notifications are indexed by user_id and created_at
- WebSocket manager handles multiple connections per user
- Bulk operations use efficient batch updates
- Old notifications can be archived/deleted (90+ days)

## 🔮 Future Enhancements

- [ ] Web Push notifications (browser push)
- [ ] Mobile push notifications (FCM/APNS)
- [ ] SMS notifications (Twilio)
- [ ] Notification templates system
- [ ] A/B testing for notifications
- [ ] Delivery rate tracking
- [ ] Read rate analytics
- [ ] Smart notification batching
- [ ] ML-based send time optimization

---

**Last Updated:** 2025-01-27
**Version:** 1.0
**Maintained by:** Aurora Notifications Team
