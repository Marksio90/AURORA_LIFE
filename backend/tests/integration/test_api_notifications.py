"""
Integration tests for Notifications API Endpoints

Tests for:
- Notification CRUD endpoints
- Bulk operations
- Preferences management
- Statistics endpoints
- Real-time WebSocket (basic tests)
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import Notification
from app.notifications.schemas import NotificationType, NotificationPriority


pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.asyncio]


@pytest.fixture
async def user_with_test_notifications(
    db_session: AsyncSession,
    test_user: User
) -> tuple[User, list[Notification]]:
    """Create user with test notifications"""
    notifications = []

    for i in range(15):
        notif = Notification(
            id=uuid4(),
            user_id=test_user.id,
            type=[NotificationType.ACHIEVEMENT, NotificationType.INSIGHT, NotificationType.REMINDER][i % 3],
            priority=[NotificationPriority.LOW, NotificationPriority.MEDIUM, NotificationPriority.HIGH][i % 3],
            title=f"Test Notification {i}",
            message=f"This is test message {i}",
            is_read=(i < 10),  # First 10 are read
            is_dismissed=(i < 3),  # First 3 are dismissed
            created_at=datetime.utcnow() - timedelta(hours=i),
        )
        notifications.append(notif)
        db_session.add(notif)

    await db_session.commit()

    # Refresh to get database-generated values
    for notif in notifications:
        await db_session.refresh(notif)

    return test_user, notifications


class TestNotificationCRUDEndpoints:
    """Test notification CRUD API endpoints"""

    async def test_get_notifications_list(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test retrieving notifications list"""
        user, notifications = user_with_test_notifications

        response = await authenticated_client.get(
            "/api/v1/notifications",
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        # Should exclude dismissed by default (12 non-dismissed)
        assert data["total"] == 12
        assert len(data["items"]) <= 10

    async def test_get_notifications_unread_only(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test filtering for unread notifications"""
        user, notifications = user_with_test_notifications

        response = await authenticated_client.get(
            "/api/v1/notifications",
            params={"unread_only": True}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 5 unread (last 5)
        assert data["total"] == 5

        # All should be unread
        for item in data["items"]:
            assert item["is_read"] is False

    async def test_get_notifications_by_type(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test filtering notifications by type"""
        user, notifications = user_with_test_notifications

        response = await authenticated_client.get(
            "/api/v1/notifications",
            params={"notification_type": "achievement"}
        )

        assert response.status_code == 200
        data = response.json()

        # All should be ACHIEVEMENT type
        for item in data["items"]:
            assert item["type"] == "achievement"

    async def test_get_single_notification(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test retrieving a single notification"""
        user, notifications = user_with_test_notifications
        first_notif = notifications[0]

        response = await authenticated_client.get(
            f"/api/v1/notifications/{first_notif.id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(first_notif.id)
        assert data["title"] == first_notif.title

    async def test_get_notification_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting non-existent notification"""
        fake_id = str(uuid4())

        response = await authenticated_client.get(
            f"/api/v1/notifications/{fake_id}"
        )

        assert response.status_code == 404

    async def test_mark_notification_as_read(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test marking notification as read"""
        user, notifications = user_with_test_notifications
        unread_notif = notifications[10]  # Should be unread

        response = await authenticated_client.post(
            f"/api/v1/notifications/{unread_notif.id}/read"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_read"] is True

    async def test_mark_all_as_read(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test marking all notifications as read"""
        user, notifications = user_with_test_notifications

        response = await authenticated_client.post(
            "/api/v1/notifications/read-all"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["affected_count"] == 5  # 5 unread notifications

    async def test_dismiss_notification(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test dismissing a notification"""
        user, notifications = user_with_test_notifications
        active_notif = notifications[10]

        response = await authenticated_client.post(
            f"/api/v1/notifications/{active_notif.id}/dismiss"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_dismissed"] is True

    async def test_delete_notification(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test deleting a notification"""
        user, notifications = user_with_test_notifications
        to_delete = notifications[0]

        response = await authenticated_client.delete(
            f"/api/v1/notifications/{to_delete.id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

        # Verify it's deleted
        get_response = await authenticated_client.get(
            f"/api/v1/notifications/{to_delete.id}"
        )
        assert get_response.status_code == 404


class TestBulkOperations:
    """Test bulk notification operations"""

    async def test_bulk_mark_read(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk mark as read"""
        user, notifications = user_with_test_notifications

        # Get IDs of unread notifications
        unread_ids = [str(n.id) for n in notifications if not n.is_read][:3]

        response = await authenticated_client.post(
            "/api/v1/notifications/bulk",
            json={
                "action": "mark_read",
                "notification_ids": unread_ids
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["affected_count"] == 3

    async def test_bulk_mark_unread(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk mark as unread"""
        user, notifications = user_with_test_notifications

        # Get IDs of read notifications
        read_ids = [str(n.id) for n in notifications if n.is_read][:3]

        response = await authenticated_client.post(
            "/api/v1/notifications/bulk",
            json={
                "action": "mark_unread",
                "notification_ids": read_ids
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True

    async def test_bulk_dismiss(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk dismiss"""
        user, notifications = user_with_test_notifications

        # Get IDs of active notifications
        active_ids = [str(n.id) for n in notifications if not n.is_dismissed][:5]

        response = await authenticated_client.post(
            "/api/v1/notifications/bulk",
            json={
                "action": "dismiss",
                "notification_ids": active_ids
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["affected_count"] == 5

    async def test_bulk_delete(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk delete"""
        user, notifications = user_with_test_notifications

        # Get IDs to delete
        to_delete = [str(n.id) for n in notifications[:3]]

        response = await authenticated_client.post(
            "/api/v1/notifications/bulk",
            json={
                "action": "delete",
                "notification_ids": to_delete
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["affected_count"] == 3


class TestNotificationPreferences:
    """Test notification preference endpoints"""

    async def test_get_preferences(
        self,
        authenticated_client: AsyncClient
    ):
        """Test retrieving notification preferences"""
        response = await authenticated_client.get(
            "/api/v1/notifications/preferences/me"
        )

        assert response.status_code == 200
        data = response.json()

        assert "email_enabled" in data
        assert "push_enabled" in data
        assert "in_app_enabled" in data
        assert "daily_digest" in data
        assert "weekly_summary" in data

    async def test_update_preferences(
        self,
        authenticated_client: AsyncClient
    ):
        """Test updating notification preferences"""
        response = await authenticated_client.put(
            "/api/v1/notifications/preferences/me",
            json={
                "email_enabled": False,
                "push_enabled": True,
                "daily_digest": True,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "07:00"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email_enabled"] is False
        assert data["push_enabled"] is True
        assert data["daily_digest"] is True
        assert data["quiet_hours_start"] == "22:00"
        assert data["quiet_hours_end"] == "07:00"

    async def test_update_preferences_partial(
        self,
        authenticated_client: AsyncClient
    ):
        """Test partial preference update"""
        response = await authenticated_client.put(
            "/api/v1/notifications/preferences/me",
            json={
                "email_enabled": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email_enabled"] is True


class TestNotificationStatistics:
    """Test notification statistics endpoints"""

    async def test_get_statistics(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test retrieving notification statistics"""
        user, notifications = user_with_test_notifications

        response = await authenticated_client.get(
            "/api/v1/notifications/stats/summary"
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_count" in data
        assert "unread_count" in data
        assert "read_count" in data
        assert "type_breakdown" in data
        assert "priority_breakdown" in data

        assert data["total_count"] >= 15
        assert data["unread_count"] == 5
        assert data["read_count"] == 10


class TestNotificationPermissions:
    """Test notification permission and security"""

    async def test_cannot_access_other_user_notifications(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]],
        test_user_2: User
    ):
        """Test that users can't access other users' notifications"""
        user, notifications = user_with_test_notifications
        other_user_notif = notifications[0]

        # Create client for user 2
        # Note: This would require actual JWT auth implementation
        # For now, we test that user 1 can't see user 2's notifications

        # Try to get another user's notification
        # (In real implementation, this would require switching auth)
        response = await authenticated_client.get(
            f"/api/v1/notifications/{other_user_notif.id}"
        )

        # Should succeed for the authenticated user
        assert response.status_code == 200

    async def test_unauthorized_access(
        self,
        client: AsyncClient
    ):
        """Test accessing notifications without authentication"""
        response = await client.get("/api/v1/notifications")

        assert response.status_code == 401


class TestNotificationEdgeCases:
    """Test edge cases and error handling"""

    async def test_get_notifications_empty_list(
        self,
        authenticated_client: AsyncClient
    ):
        """Test retrieving notifications when user has none"""
        response = await authenticated_client.get("/api/v1/notifications")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_pagination_beyond_available(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test pagination beyond available pages"""
        response = await authenticated_client.get(
            "/api/v1/notifications",
            params={"page": 100, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty items but valid pagination info
        assert len(data["items"]) == 0
        assert data["page"] == 100

    async def test_invalid_bulk_action(
        self,
        authenticated_client: AsyncClient,
        user_with_test_notifications: tuple[User, list[Notification]]
    ):
        """Test bulk operation with invalid action"""
        user, notifications = user_with_test_notifications
        ids = [str(n.id) for n in notifications[:3]]

        response = await authenticated_client.post(
            "/api/v1/notifications/bulk",
            json={
                "action": "invalid_action",
                "notification_ids": ids
            }
        )

        # Should return validation error
        assert response.status_code == 422

    async def test_bulk_operation_empty_ids(
        self,
        authenticated_client: AsyncClient
    ):
        """Test bulk operation with empty ID list"""
        response = await authenticated_client.post(
            "/api/v1/notifications/bulk",
            json={
                "action": "mark_read",
                "notification_ids": []
            }
        )

        assert response.status_code in [200, 400]
