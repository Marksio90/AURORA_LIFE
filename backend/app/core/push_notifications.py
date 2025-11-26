"""
Push notification system for web and mobile.

Supports:
- Web Push (browser notifications)
- Firebase Cloud Messaging (FCM) for mobile
- Notification templates
- Scheduling
- User preferences
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
import httpx
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class NotificationType:
    """Notification types."""
    INSIGHT_GENERATED = "insight_generated"
    PREDICTION_READY = "prediction_ready"
    STREAK_MILESTONE = "streak_milestone"
    BADGE_UNLOCKED = "badge_unlocked"
    FRIEND_FOLLOWED = "friend_followed"
    GOAL_COMPLETED = "goal_completed"
    DAILY_REMINDER = "daily_reminder"


NOTIFICATION_TEMPLATES = {
    NotificationType.INSIGHT_GENERATED: {
        "title": "🎯 New Insight Available!",
        "body": "We've generated a new insight based on your recent activities.",
        "icon": "/icons/insight.png"
    },
    NotificationType.PREDICTION_READY: {
        "title": "🔮 Your Predictions are Ready",
        "body": "Check out your energy and mood predictions for today.",
        "icon": "/icons/prediction.png"
    },
    NotificationType.STREAK_MILESTONE: {
        "title": "🔥 Streak Milestone!",
        "body": "You've reached a {days}-day streak! Keep it up!",
        "icon": "/icons/streak.png"
    },
    NotificationType.BADGE_UNLOCKED: {
        "title": "🏆 Badge Unlocked!",
        "body": "You've earned the '{badge_name}' badge!",
        "icon": "/icons/badge.png"
    },
}


class PushNotificationService:
    """Service for sending push notifications."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_notification(
        self,
        user_id: UUID,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None,
        custom_title: Optional[str] = None,
        custom_body: Optional[str] = None
    ):
        """
        Send a push notification to a user.

        Args:
            user_id: User UUID
            notification_type: Type of notification
            data: Additional data to include
            custom_title: Override template title
            custom_body: Override template body
        """
        # Check user's notification preferences
        if not await self._can_send_notification(user_id, notification_type):
            logger.info(f"User {user_id} has disabled {notification_type} notifications")
            return

        # Get user's push tokens
        tokens = await self._get_user_push_tokens(user_id)

        if not tokens:
            logger.info(f"No push tokens for user {user_id}")
            return

        # Get notification template
        template = NOTIFICATION_TEMPLATES.get(notification_type, {})

        # Format message
        title = custom_title or template.get("title", "AURORA_LIFE")
        body = custom_body or template.get("body", "You have a new notification")

        # Replace placeholders
        if data:
            body = body.format(**data)

        # Send to each token
        for token in tokens:
            if token["platform"] == "web":
                await self._send_web_push(token["token"], title, body, data)
            elif token["platform"] == "fcm":
                await self._send_fcm_notification(token["token"], title, body, data)

        # Log notification
        await self._log_notification(user_id, notification_type, title, body)

    async def _send_web_push(
        self,
        subscription: Dict[str, Any],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send web push notification."""
        from pywebpush import webpush, WebPushException

        try:
            payload = json.dumps({
                "title": title,
                "body": body,
                "icon": "/icon.png",
                "data": data or {}
            })

            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{settings.CONTACT_EMAIL}"
                }
            )

            logger.info("Web push notification sent successfully")

        except WebPushException as e:
            logger.error(f"Web push failed: {e}")
            if e.response and e.response.status_code == 410:
                # Subscription expired, remove it
                await self._remove_push_token(subscription)

    async def _send_fcm_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Send FCM notification to mobile device."""
        fcm_url = "https://fcm.googleapis.com/fcm/send"

        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "to": fcm_token,
            "notification": {
                "title": title,
                "body": body,
                "icon": "/icon.png",
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            },
            "data": data or {}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(fcm_url, json=payload, headers=headers)

                if response.status_code == 200:
                    logger.info("FCM notification sent successfully")
                else:
                    logger.error(f"FCM notification failed: {response.text}")

        except Exception as e:
            logger.error(f"FCM notification error: {e}")

    async def register_push_token(
        self,
        user_id: UUID,
        token: str,
        platform: str  # 'web' or 'fcm'
    ):
        """Register a push notification token."""
        from app.models.user import PushToken

        # Check if token already exists
        result = await self.db.execute(
            select(PushToken).where(
                PushToken.user_id == user_id,
                PushToken.token == token
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            push_token = PushToken(
                id=uuid4(),
                user_id=user_id,
                token=token,
                platform=platform,
                created_at=datetime.utcnow()
            )
            self.db.add(push_token)
            await self.db.commit()

            logger.info(f"Registered push token for user {user_id}")

    async def _get_user_push_tokens(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all push tokens for a user."""
        from app.models.user import PushToken

        result = await self.db.execute(
            select(PushToken).where(PushToken.user_id == user_id)
        )
        tokens = result.scalars().all()

        return [
            {
                "token": token.token,
                "platform": token.platform
            }
            for token in tokens
        ]

    async def _can_send_notification(
        self,
        user_id: UUID,
        notification_type: str
    ) -> bool:
        """Check if user allows this notification type."""
        from app.models.user import UserPreferences

        result = await self.db.execute(
            select(UserPreferences).where(UserPreferences.user_id == user_id)
        )
        prefs = result.scalar_one_or_none()

        if not prefs:
            return True  # Default: allow all

        notification_prefs = prefs.notification_preferences or {}
        return notification_prefs.get(notification_type, True)

    async def _log_notification(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str
    ):
        """Log sent notification."""
        from app.models.user import NotificationLog

        log = NotificationLog(
            id=uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            sent_at=datetime.utcnow()
        )

        self.db.add(log)
        await self.db.commit()

    async def _remove_push_token(self, token: str):
        """Remove an expired/invalid push token."""
        from app.models.user import PushToken
        from sqlalchemy import delete

        await self.db.execute(
            delete(PushToken).where(PushToken.token == token)
        )
        await self.db.commit()


# Convenience functions
async def send_streak_notification(db: AsyncSession, user_id: UUID, streak_days: int):
    """Send streak milestone notification."""
    service = PushNotificationService(db)
    await service.send_notification(
        user_id=user_id,
        notification_type=NotificationType.STREAK_MILESTONE,
        data={"days": streak_days}
    )


async def send_badge_notification(db: AsyncSession, user_id: UUID, badge_name: str):
    """Send badge unlocked notification."""
    service = PushNotificationService(db)
    await service.send_notification(
        user_id=user_id,
        notification_type=NotificationType.BADGE_UNLOCKED,
        data={"badge_name": badge_name}
    )
