"""
Unit tests for Notification Helpers

Tests for:
- Achievement notifications
- Level up notifications
- Streak notifications
- Insight notifications
- Recommendation notifications
- Social notifications
- Alert notifications
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from app.notifications.helpers import (
    send_achievement_notification,
    send_level_up_notification,
    send_streak_notification,
    send_insight_notification,
    send_recommendation_notification,
    send_social_notification,
    send_alert_notification,
    send_reminder_notification,
    send_system_notification,
)
from app.notifications.schemas import NotificationType, NotificationPriority
from app.models.user import User


pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class TestAchievementNotifications:
    """Test achievement notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_achievement_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending achievement notification"""
        # Mock service
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.ACHIEVEMENT,
            title="Achievement Unlocked: Test Achievement",
        )
        mock_service_class.return_value = mock_service

        # Mock websocket send
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_achievement_notification(
            db=db_session,
            user_id=str(test_user.id),
            achievement_name="Test Achievement",
            achievement_description="You did something great!",
            xp_earned=100
        )

        assert result is not None
        mock_service.create_notification.assert_called_once()

        # Check that notification was created with correct type
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.ACHIEVEMENT
        assert notification_data.priority == NotificationPriority.MEDIUM
        assert "Test Achievement" in notification_data.title


class TestLevelUpNotifications:
    """Test level up notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_level_up_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending level up notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.LEVEL_UP,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_level_up_notification(
            db=db_session,
            user_id=str(test_user.id),
            new_level=10,
            rewards=["Badge", "Avatar"]
        )

        assert result is not None
        mock_service.create_notification.assert_called_once()

        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.LEVEL_UP
        assert notification_data.priority == NotificationPriority.HIGH
        assert "Level 10" in notification_data.title


class TestStreakNotifications:
    """Test streak notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_streak_notification_milestone(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending milestone streak notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.STREAK,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_streak_notification(
            db=db_session,
            user_id=str(test_user.id),
            streak_days=30,
            milestone=True
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.STREAK
        assert notification_data.priority == NotificationPriority.HIGH  # Milestone
        assert "30-Day" in notification_data.title

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_streak_notification_regular(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending regular streak notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.STREAK,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_streak_notification(
            db=db_session,
            user_id=str(test_user.id),
            streak_days=5,
            milestone=False
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.priority == NotificationPriority.LOW  # Regular


class TestInsightNotifications:
    """Test insight notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_insight_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending insight notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.INSIGHT,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_insight_notification(
            db=db_session,
            user_id=str(test_user.id),
            insight_title="Sleep Pattern Detected",
            insight_message="You sleep better after exercise",
            action_items=["Exercise more often", "Track your sleep"]
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.INSIGHT
        assert "💡" in notification_data.title
        assert notification_data.data["action_items"] == ["Exercise more often", "Track your sleep"]


class TestRecommendationNotifications:
    """Test recommendation notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_recommendation_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending recommendation notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.RECOMMENDATION,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_recommendation_notification(
            db=db_session,
            user_id=str(test_user.id),
            recommendation_title="Try morning exercise",
            recommendation_message="Based on your data, morning exercise improves your mood",
            expected_impact="+15% mood improvement"
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.RECOMMENDATION
        assert "🎯" in notification_data.title
        assert "+15% mood improvement" in notification_data.message


class TestSocialNotifications:
    """Test social notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_social_notification_friend_request(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending friend request notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.SOCIAL,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_social_notification(
            db=db_session,
            user_id=str(test_user.id),
            social_event="friend_request",
            actor_name="John Doe",
            action_url="/friends"
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.SOCIAL
        assert "John Doe" in notification_data.message
        assert "friend request" in notification_data.message

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_social_notification_post_like(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending post like notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.SOCIAL,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_social_notification(
            db=db_session,
            user_id=str(test_user.id),
            social_event="post_like",
            actor_name="Jane Smith",
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert "Jane Smith" in notification_data.message
        assert "liked your post" in notification_data.message


class TestAlertNotifications:
    """Test alert notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_alert_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending alert notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.ALERT,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_alert_notification(
            db=db_session,
            user_id=str(test_user.id),
            alert_title="Low Energy Alert",
            alert_message="Your energy has been below average for 3 days",
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.ALERT
        assert notification_data.priority == NotificationPriority.HIGH
        assert "⚠️" in notification_data.title


class TestReminderNotifications:
    """Test reminder notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_reminder_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending reminder notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.REMINDER,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_reminder_notification(
            db=db_session,
            user_id=str(test_user.id),
            reminder_title="Log your sleep",
            reminder_message="Don't forget to log your sleep from last night",
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.REMINDER
        assert "⏰" in notification_data.title


class TestSystemNotifications:
    """Test system notification helpers"""

    @patch('app.notifications.helpers.NotificationService')
    @patch('app.notifications.helpers.websocket_manager')
    async def test_send_system_notification(
        self,
        mock_ws_manager,
        mock_service_class,
        db_session: AsyncSession,
        test_user: User
    ):
        """Test sending system notification"""
        mock_service = MagicMock()
        mock_service.create_notification.return_value = MagicMock(
            id="test-notif-id",
            type=NotificationType.SYSTEM,
        )
        mock_service_class.return_value = mock_service
        mock_ws_manager.send_notification = AsyncMock()

        result = await send_system_notification(
            db=db_session,
            user_id=str(test_user.id),
            title="Maintenance Scheduled",
            message="System maintenance on Sunday at 3 AM",
        )

        assert result is not None
        call_args = mock_service.create_notification.call_args
        notification_data = call_args[1]['notification_data']
        assert notification_data.type == NotificationType.SYSTEM
