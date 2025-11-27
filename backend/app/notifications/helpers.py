"""
Notification Helpers

Utility functions for creating common notifications.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.notifications.service import NotificationService
from app.notifications.websocket import websocket_manager
from app.notifications.schemas import (
    NotificationCreate, NotificationType, NotificationPriority,
    NotificationResponse,
)

logger = logging.getLogger(__name__)


async def send_notification(
    db: Session,
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    action_url: Optional[str] = None,
    action_text: Optional[str] = None,
    icon: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    expires_at: Optional[datetime] = None,
    send_websocket: bool = True,
) -> NotificationResponse:
    """
    Send notification to user.

    Args:
        db: Database session
        user_id: User ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        priority: Priority level
        action_url: Optional action URL
        action_text: Optional action text
        icon: Optional icon/emoji
        data: Optional additional data
        expires_at: Optional expiration time
        send_websocket: Whether to send via WebSocket

    Returns:
        NotificationResponse
    """
    service = NotificationService(db)

    # Create notification
    notification_data = NotificationCreate(
        user_id=user_id,
        type=notification_type,
        priority=priority,
        title=title,
        message=message,
        action_url=action_url,
        action_text=action_text,
        icon=icon,
        data=data,
        expires_at=expires_at,
    )

    notif = service.create_notification(notification_data)
    notif_response = NotificationResponse.model_validate(notif)

    # Send via WebSocket if user is connected
    if send_websocket:
        await websocket_manager.send_notification(
            user_id=user_id,
            notification=notif_response.model_dump(),
        )

    logger.info(f"Notification sent to user {user_id}: {title}")

    return notif_response


# ==================== ACHIEVEMENT NOTIFICATIONS ====================

async def send_achievement_notification(
    db: Session,
    user_id: str,
    achievement_name: str,
    achievement_description: str,
    achievement_icon: Optional[str] = "🏆",
    xp_earned: Optional[int] = None,
) -> NotificationResponse:
    """Send achievement unlocked notification"""

    message = achievement_description

    if xp_earned:
        message += f" You earned {xp_earned} XP!"

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.ACHIEVEMENT,
        title=f"Achievement Unlocked: {achievement_name}",
        message=message,
        priority=NotificationPriority.MEDIUM,
        icon=achievement_icon,
        action_url="/achievements",
        action_text="View Achievements",
        data={
            "achievement_name": achievement_name,
            "xp_earned": xp_earned,
        },
    )


# ==================== LEVEL UP NOTIFICATIONS ====================

async def send_level_up_notification(
    db: Session,
    user_id: str,
    new_level: int,
    rewards: Optional[list] = None,
) -> NotificationResponse:
    """Send level up notification"""

    message = f"Congratulations! You've reached level {new_level}!"

    if rewards:
        message += f" Rewards unlocked: {', '.join(rewards)}"

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.LEVEL_UP,
        title=f"Level {new_level} Reached! ⬆️",
        message=message,
        priority=NotificationPriority.HIGH,
        icon="⬆️",
        action_url="/profile",
        action_text="View Profile",
        data={
            "new_level": new_level,
            "rewards": rewards or [],
        },
    )


# ==================== STREAK NOTIFICATIONS ====================

async def send_streak_notification(
    db: Session,
    user_id: str,
    streak_days: int,
    milestone: bool = False,
) -> NotificationResponse:
    """Send streak notification"""

    if milestone:
        title = f"🔥 {streak_days}-Day Streak Milestone!"
        message = f"Amazing! You've maintained your streak for {streak_days} consecutive days!"
        priority = NotificationPriority.HIGH
    else:
        title = f"🔥 {streak_days}-Day Streak!"
        message = f"Keep it up! You're on a {streak_days}-day streak!"
        priority = NotificationPriority.LOW

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.STREAK,
        title=title,
        message=message,
        priority=priority,
        icon="🔥",
        data={
            "streak_days": streak_days,
            "milestone": milestone,
        },
    )


# ==================== INSIGHT NOTIFICATIONS ====================

async def send_insight_notification(
    db: Session,
    user_id: str,
    insight_title: str,
    insight_message: str,
    insight_priority: NotificationPriority = NotificationPriority.MEDIUM,
    action_items: Optional[list] = None,
) -> NotificationResponse:
    """Send insight notification"""

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.INSIGHT,
        title=f"💡 {insight_title}",
        message=insight_message,
        priority=insight_priority,
        icon="💡",
        action_url="/insights",
        action_text="View Insights",
        data={
            "action_items": action_items or [],
        },
        expires_at=datetime.utcnow() + timedelta(days=7),
    )


# ==================== RECOMMENDATION NOTIFICATIONS ====================

async def send_recommendation_notification(
    db: Session,
    user_id: str,
    recommendation_title: str,
    recommendation_message: str,
    expected_impact: Optional[str] = None,
) -> NotificationResponse:
    """Send recommendation notification"""

    message = recommendation_message

    if expected_impact:
        message += f" Expected impact: {expected_impact}"

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.RECOMMENDATION,
        title=f"🎯 {recommendation_title}",
        message=message,
        priority=NotificationPriority.MEDIUM,
        icon="🎯",
        action_url="/recommendations",
        action_text="View Recommendations",
        expires_at=datetime.utcnow() + timedelta(days=7),
    )


# ==================== REMINDER NOTIFICATIONS ====================

async def send_reminder_notification(
    db: Session,
    user_id: str,
    reminder_title: str,
    reminder_message: str,
    action_url: Optional[str] = None,
) -> NotificationResponse:
    """Send reminder notification"""

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.REMINDER,
        title=f"⏰ {reminder_title}",
        message=reminder_message,
        priority=NotificationPriority.MEDIUM,
        icon="⏰",
        action_url=action_url,
        action_text="Take Action",
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )


# ==================== SOCIAL NOTIFICATIONS ====================

async def send_social_notification(
    db: Session,
    user_id: str,
    social_event: str,
    actor_name: str,
    action_url: Optional[str] = None,
) -> NotificationResponse:
    """Send social notification"""

    event_messages = {
        "friend_request": f"{actor_name} sent you a friend request",
        "friend_accepted": f"{actor_name} accepted your friend request",
        "post_like": f"{actor_name} liked your post",
        "post_comment": f"{actor_name} commented on your post",
        "mention": f"{actor_name} mentioned you",
    }

    message = event_messages.get(social_event, f"{actor_name} interacted with you")

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.SOCIAL,
        title="👥 Social Update",
        message=message,
        priority=NotificationPriority.LOW,
        icon="👥",
        action_url=action_url,
        action_text="View",
        data={
            "social_event": social_event,
            "actor_name": actor_name,
        },
    )


# ==================== SYSTEM NOTIFICATIONS ====================

async def send_system_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.LOW,
) -> NotificationResponse:
    """Send system notification"""

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.SYSTEM,
        title=title,
        message=message,
        priority=priority,
        icon="🔔",
    )


# ==================== ALERT NOTIFICATIONS ====================

async def send_alert_notification(
    db: Session,
    user_id: str,
    alert_title: str,
    alert_message: str,
    action_url: Optional[str] = None,
) -> NotificationResponse:
    """Send alert notification (high priority)"""

    return await send_notification(
        db=db,
        user_id=user_id,
        notification_type=NotificationType.ALERT,
        title=f"⚠️ {alert_title}",
        message=alert_message,
        priority=NotificationPriority.HIGH,
        icon="⚠️",
        action_url=action_url,
        action_text="View Details",
    )
