"""
Unit tests for Notification Service

Tests for:
- Notification CRUD operations
- Preference management
- Bulk operations
- Statistics
- Filtering and pagination
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.service import NotificationService
from app.notifications.schemas import (
    NotificationCreate, NotificationUpdate, NotificationType,
    NotificationPriority, BulkNotificationAction
)
from app.models.user import User
from app.models.notification import Notification, NotificationPreference


pytestmark = [pytest.mark.unit, pytest.mark.db]


@pytest.fixture
async def notification_service(db_session: AsyncSession) -> NotificationService:
    """Create a NotificationService instance."""
    return NotificationService(db_session)


@pytest.fixture
async def test_notification_data(test_user: User) -> NotificationCreate:
    """Create test notification data."""
    return NotificationCreate(
        user_id=str(test_user.id),
        type=NotificationType.ACHIEVEMENT,
        priority=NotificationPriority.MEDIUM,
        title="Test Achievement",
        message="You've unlocked a test achievement!",
        icon="🏆",
        action_url="/achievements",
        action_text="View",
        data={"achievement_id": "test-123"},
    )


@pytest.fixture
async def user_with_notifications(
    db_session: AsyncSession,
    test_user: User
) -> tuple[User, list[Notification]]:
    """Create user with multiple notifications."""
    notifications = []

    # Create 10 notifications of various types
    for i in range(10):
        notif = Notification(
            id=uuid4(),
            user_id=test_user.id,
            type=[NotificationType.ACHIEVEMENT, NotificationType.LEVEL_UP, NotificationType.INSIGHT][i % 3],
            priority=[NotificationPriority.LOW, NotificationPriority.MEDIUM, NotificationPriority.HIGH][i % 3],
            title=f"Test Notification {i}",
            message=f"This is test notification number {i}",
            is_read=(i < 5),  # First 5 are read
            is_dismissed=(i < 2),  # First 2 are dismissed
            created_at=datetime.utcnow() - timedelta(hours=i),
        )
        notifications.append(notif)
        db_session.add(notif)

    await db_session.commit()
    return test_user, notifications


class TestNotificationService:
    """Test NotificationService class"""

    async def test_service_initialization(self, notification_service):
        """Test notification service initialization"""
        assert notification_service is not None
        assert notification_service.db is not None

    async def test_create_notification(
        self,
        notification_service: NotificationService,
        test_notification_data: NotificationCreate
    ):
        """Test creating a notification"""
        notification = notification_service.create_notification(test_notification_data)

        assert notification is not None
        assert notification.id is not None
        assert notification.user_id == test_notification_data.user_id
        assert notification.type == test_notification_data.type
        assert notification.priority == test_notification_data.priority
        assert notification.title == test_notification_data.title
        assert notification.message == test_notification_data.message
        assert notification.is_read is False
        assert notification.is_dismissed is False

    async def test_get_notification(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test retrieving a single notification"""
        user, notifications = user_with_notifications
        first_notif = notifications[0]

        retrieved = notification_service.get_notification(
            notification_id=str(first_notif.id),
            user_id=str(user.id)
        )

        assert retrieved is not None
        assert retrieved.id == first_notif.id
        assert retrieved.title == first_notif.title

    async def test_get_notification_wrong_user(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]],
        test_user_2: User
    ):
        """Test that users can't access other users' notifications"""
        user, notifications = user_with_notifications
        first_notif = notifications[0]

        retrieved = notification_service.get_notification(
            notification_id=str(first_notif.id),
            user_id=str(test_user_2.id)  # Different user
        )

        assert retrieved is None

    async def test_get_user_notifications_pagination(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test paginated notification retrieval"""
        user, notifications = user_with_notifications

        result = notification_service.get_user_notifications(
            user_id=str(user.id),
            page=1,
            page_size=5
        )

        assert result is not None
        assert result.total >= 10
        assert len(result.items) <= 5
        assert result.page == 1
        assert result.page_size == 5
        assert result.total_pages >= 2

    async def test_get_user_notifications_unread_only(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test filtering for unread notifications"""
        user, notifications = user_with_notifications

        result = notification_service.get_user_notifications(
            user_id=str(user.id),
            unread_only=True,
            page=1,
            page_size=20
        )

        assert result is not None
        # Should have 5 unread notifications (last 5)
        assert result.total == 5

        # All should be unread
        for item in result.items:
            assert item.is_read is False

    async def test_get_user_notifications_by_type(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test filtering notifications by type"""
        user, notifications = user_with_notifications

        result = notification_service.get_user_notifications(
            user_id=str(user.id),
            notification_type=NotificationType.ACHIEVEMENT,
            page=1,
            page_size=20
        )

        assert result is not None

        # All should be ACHIEVEMENT type
        for item in result.items:
            assert item.type == NotificationType.ACHIEVEMENT

    async def test_mark_as_read(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test marking notification as read"""
        user, notifications = user_with_notifications
        unread_notif = notifications[5]  # Should be unread

        assert unread_notif.is_read is False

        updated = notification_service.mark_as_read(
            notification_id=str(unread_notif.id),
            user_id=str(user.id)
        )

        assert updated is not None
        assert updated.is_read is True

    async def test_mark_all_as_read(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test marking all notifications as read"""
        user, notifications = user_with_notifications

        affected = notification_service.mark_all_as_read(user_id=str(user.id))

        # Should mark 5 unread notifications as read
        assert affected == 5

    async def test_dismiss_notification(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test dismissing a notification"""
        user, notifications = user_with_notifications
        active_notif = notifications[5]

        assert active_notif.is_dismissed is False

        updated = notification_service.dismiss_notification(
            notification_id=str(active_notif.id),
            user_id=str(user.id)
        )

        assert updated is not None
        assert updated.is_dismissed is True

    async def test_delete_notification(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]],
        db_session: AsyncSession
    ):
        """Test deleting a notification"""
        user, notifications = user_with_notifications
        to_delete = notifications[0]

        success = notification_service.delete_notification(
            notification_id=str(to_delete.id),
            user_id=str(user.id)
        )

        assert success is True

        # Verify it's deleted
        retrieved = notification_service.get_notification(
            notification_id=str(to_delete.id),
            user_id=str(user.id)
        )

        assert retrieved is None

    async def test_bulk_mark_read(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk mark as read"""
        user, notifications = user_with_notifications

        # Get IDs of unread notifications
        unread_ids = [str(n.id) for n in notifications if not n.is_read][:3]

        action = BulkNotificationAction(
            action="mark_read",
            notification_ids=unread_ids
        )

        affected = notification_service.bulk_action(
            action=action,
            user_id=str(user.id)
        )

        assert affected == 3

    async def test_bulk_delete(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk delete"""
        user, notifications = user_with_notifications

        # Get IDs to delete
        to_delete = [str(n.id) for n in notifications[:3]]

        action = BulkNotificationAction(
            action="delete",
            notification_ids=to_delete
        )

        affected = notification_service.bulk_action(
            action=action,
            user_id=str(user.id)
        )

        assert affected == 3

    async def test_get_statistics(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test notification statistics"""
        user, notifications = user_with_notifications

        stats = notification_service.get_statistics(user_id=str(user.id))

        assert stats is not None
        assert stats.total_count >= 10
        assert stats.unread_count == 5
        assert stats.read_count == 5

        # Check type breakdown
        assert "type_breakdown" in stats.model_dump()
        assert "priority_breakdown" in stats.model_dump()

    async def test_get_or_create_preferences(
        self,
        notification_service: NotificationService,
        test_user: User
    ):
        """Test creating default preferences"""
        preferences = notification_service.get_or_create_preferences(
            user_id=str(test_user.id)
        )

        assert preferences is not None
        assert preferences.user_id == test_user.id
        assert preferences.email_enabled is True  # Default
        assert preferences.push_enabled is True  # Default

    async def test_update_preferences(
        self,
        notification_service: NotificationService,
        test_user: User
    ):
        """Test updating notification preferences"""
        # Create preferences first
        notification_service.get_or_create_preferences(user_id=str(test_user.id))

        # Update
        updated = notification_service.update_preferences(
            user_id=str(test_user.id),
            preferences_data={
                "email_enabled": False,
                "push_enabled": False,
                "daily_digest": True,
            }
        )

        assert updated is not None
        assert updated.email_enabled is False
        assert updated.push_enabled is False
        assert updated.daily_digest is True

    async def test_exclude_dismissed_by_default(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test that dismissed notifications are excluded by default"""
        user, notifications = user_with_notifications

        result = notification_service.get_user_notifications(
            user_id=str(user.id),
            include_dismissed=False,
            page=1,
            page_size=20
        )

        # Should exclude 2 dismissed notifications
        assert result.total == 8  # 10 - 2 dismissed

    async def test_include_dismissed_when_requested(
        self,
        notification_service: NotificationService,
        user_with_notifications: tuple[User, list[Notification]]
    ):
        """Test including dismissed notifications"""
        user, notifications = user_with_notifications

        result = notification_service.get_user_notifications(
            user_id=str(user.id),
            include_dismissed=True,
            page=1,
            page_size=20
        )

        # Should include all 10 notifications
        assert result.total == 10
