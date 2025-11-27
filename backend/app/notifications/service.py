"""
Notification Service

Core service for managing notifications.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import logging

from app.models.notification import Notification, NotificationPreference, NotificationType, NotificationPriority
from app.notifications.schemas import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationList, BulkNotificationAction, NotificationStats,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CREATE ====================

    def create_notification(
        self,
        notification_data: NotificationCreate,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            notification_data: Notification data

        Returns:
            Created Notification object
        """
        logger.info(f"Creating notification for user {notification_data.user_id}")

        notification = Notification(
            user_id=notification_data.user_id,
            type=notification_data.type,
            priority=notification_data.priority,
            title=notification_data.title,
            message=notification_data.message,
            data=notification_data.data,
            action_url=notification_data.action_url,
            action_text=notification_data.action_text,
            icon=notification_data.icon,
            image_url=notification_data.image_url,
            expires_at=notification_data.expires_at,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        logger.info(f"Notification created: {notification.id}")

        return notification

    def create_bulk_notifications(
        self,
        user_ids: List[str],
        notification_template: NotificationCreate,
    ) -> List[Notification]:
        """
        Create notifications for multiple users.

        Args:
            user_ids: List of user IDs
            notification_template: Notification template

        Returns:
            List of created Notification objects
        """
        logger.info(f"Creating bulk notifications for {len(user_ids)} users")

        notifications = []

        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                type=notification_template.type,
                priority=notification_template.priority,
                title=notification_template.title,
                message=notification_template.message,
                data=notification_template.data,
                action_url=notification_template.action_url,
                action_text=notification_template.action_text,
                icon=notification_template.icon,
                image_url=notification_template.image_url,
                expires_at=notification_template.expires_at,
            )
            notifications.append(notification)

        self.db.bulk_save_objects(notifications)
        self.db.commit()

        logger.info(f"Created {len(notifications)} notifications")

        return notifications

    # ==================== READ ====================

    def get_notification(
        self,
        notification_id: str,
        user_id: str,
    ) -> Optional[Notification]:
        """Get single notification"""
        return self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        ).first()

    def get_user_notifications(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        include_dismissed: bool = False,
    ) -> NotificationList:
        """
        Get user notifications with pagination.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Items per page
            unread_only: Return only unread notifications
            notification_type: Filter by notification type
            include_dismissed: Include dismissed notifications

        Returns:
            NotificationList with notifications and metadata
        """
        logger.info(f"Getting notifications for user {user_id}")

        # Base query
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id
        )

        # Filters
        if unread_only:
            query = query.filter(Notification.is_read == False)

        if not include_dismissed:
            query = query.filter(Notification.is_dismissed == False)

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        # Exclude expired
        query = query.filter(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )

        # Total count
        total = query.count()

        # Unread count
        unread_count = self.db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_dismissed == False,
            )
        ).scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        notifications = query.order_by(desc(Notification.created_at)).offset(offset).limit(page_size).all()

        # Check if there are more pages
        has_more = total > (page * page_size)

        return NotificationList(
            notifications=[NotificationResponse.model_validate(n) for n in notifications],
            total=total,
            unread_count=unread_count,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    # ==================== UPDATE ====================

    def mark_as_read(
        self,
        notification_id: str,
        user_id: str,
    ) -> Optional[Notification]:
        """Mark notification as read"""
        notification = self.get_notification(notification_id, user_id)

        if not notification:
            return None

        notification.mark_as_read()
        self.db.commit()
        self.db.refresh(notification)

        logger.info(f"Notification {notification_id} marked as read")

        return notification

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all unread notifications as read"""
        updated = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
        ).update({
            "is_read": True,
            "read_at": datetime.utcnow(),
        })

        self.db.commit()

        logger.info(f"Marked {updated} notifications as read for user {user_id}")

        return updated

    def dismiss_notification(
        self,
        notification_id: str,
        user_id: str,
    ) -> Optional[Notification]:
        """Dismiss notification"""
        notification = self.get_notification(notification_id, user_id)

        if not notification:
            return None

        notification.dismiss()
        self.db.commit()
        self.db.refresh(notification)

        logger.info(f"Notification {notification_id} dismissed")

        return notification

    # ==================== DELETE ====================

    def delete_notification(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """Delete notification"""
        notification = self.get_notification(notification_id, user_id)

        if not notification:
            return False

        self.db.delete(notification)
        self.db.commit()

        logger.info(f"Notification {notification_id} deleted")

        return True

    def delete_old_notifications(
        self,
        days: int = 90,
    ) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = self.db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).delete()

        self.db.commit()

        logger.info(f"Deleted {deleted} old notifications (older than {days} days)")

        return deleted

    # ==================== BULK OPERATIONS ====================

    def bulk_action(
        self,
        action: BulkNotificationAction,
        user_id: str,
    ) -> int:
        """
        Perform bulk action on notifications.

        Args:
            action: Bulk action data
            user_id: User ID (for security)

        Returns:
            Number of affected notifications
        """
        logger.info(f"Performing bulk action: {action.action} on {len(action.notification_ids)} notifications")

        query = self.db.query(Notification).filter(
            and_(
                Notification.id.in_(action.notification_ids),
                Notification.user_id == user_id,
            )
        )

        if action.action == "mark_read":
            affected = query.update({
                "is_read": True,
                "read_at": datetime.utcnow(),
            })
        elif action.action == "mark_unread":
            affected = query.update({
                "is_read": False,
                "read_at": None,
            })
        elif action.action == "dismiss":
            affected = query.update({
                "is_dismissed": True,
                "dismissed_at": datetime.utcnow(),
            })
        elif action.action == "delete":
            affected = query.delete()
        else:
            affected = 0

        self.db.commit()

        logger.info(f"Bulk action affected {affected} notifications")

        return affected

    # ==================== STATISTICS ====================

    def get_statistics(self, user_id: str) -> NotificationStats:
        """Get notification statistics for user"""

        total = self.db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        ).scalar() or 0

        unread = self.db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_dismissed == False,
            )
        ).scalar() or 0

        # By type
        by_type_query = self.db.query(
            Notification.type,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.type).all()

        by_type = {row.type: row.count for row in by_type_query}

        # By priority
        by_priority_query = self.db.query(
            Notification.priority,
            func.count(Notification.id).label('count')
        ).filter(
            Notification.user_id == user_id
        ).group_by(Notification.priority).all()

        by_priority = {row.priority: row.count for row in by_priority_query}

        # Recent counts
        recent_7d = self.db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= datetime.utcnow() - timedelta(days=7),
            )
        ).scalar() or 0

        recent_30d = self.db.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.created_at >= datetime.utcnow() - timedelta(days=30),
            )
        ).scalar() or 0

        return NotificationStats(
            total=total,
            unread=unread,
            by_type=by_type,
            by_priority=by_priority,
            recent_count_7d=recent_7d,
            recent_count_30d=recent_30d,
        )

    # ==================== PREFERENCES ====================

    def get_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get user notification preferences"""
        return self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

    def get_or_create_preferences(self, user_id: str) -> NotificationPreference:
        """Get or create user notification preferences"""
        preferences = self.get_preferences(user_id)

        if not preferences:
            preferences = NotificationPreference(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            logger.info(f"Created default preferences for user {user_id}")

        return preferences

    def update_preferences(
        self,
        user_id: str,
        preferences_data: Dict[str, Any],
    ) -> NotificationPreference:
        """Update user notification preferences"""
        preferences = self.get_or_create_preferences(user_id)

        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)

        preferences.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(preferences)

        logger.info(f"Updated preferences for user {user_id}")

        return preferences
