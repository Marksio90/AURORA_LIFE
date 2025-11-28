"""
Unit tests for Event Schemas

Tests for:
- Event type validation
- Event serialization
- Event deserialization
- Event data validation
"""
import pytest
from datetime import datetime
from uuid import uuid4
from pydantic import ValidationError

from app.events.schemas import (
    EventType,
    BaseEvent,
    UserRegisteredEvent,
    LifeEventCreatedEvent,
    XPEarnedEvent,
    LevelUpEvent,
    AchievementUnlockedEvent,
    StreakMilestoneEvent,
    GoalCompletedEvent,
    InsightGeneratedEvent,
    RecommendationCreatedEvent,
)


pytestmark = pytest.mark.unit


class TestEventType:
    """Test EventType enum"""

    def test_all_event_types_exist(self):
        """Test that all expected event types are defined"""
        assert EventType.USER_REGISTERED == "user.registered"
        assert EventType.USER_LOGIN == "user.login"
        assert EventType.LIFE_EVENT_CREATED == "life_event.created"
        assert EventType.XP_EARNED == "gamification.xp_earned"
        assert EventType.LEVEL_UP == "gamification.level_up"
        assert EventType.ACHIEVEMENT_UNLOCKED == "gamification.achievement_unlocked"
        assert EventType.STREAK_MILESTONE == "gamification.streak_milestone"
        assert EventType.GOAL_COMPLETED == "goal.completed"
        assert EventType.INSIGHT_GENERATED == "analytics.insight_generated"
        assert EventType.RECOMMENDATION_CREATED == "analytics.recommendation_created"


class TestBaseEvent:
    """Test BaseEvent schema"""

    def test_base_event_creation(self):
        """Test creating a base event"""
        event = BaseEvent(
            event_id=str(uuid4()),
            event_type=EventType.USER_LOGIN,
            user_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            metadata={"ip_address": "127.0.0.1"}
        )

        assert event is not None
        assert event.event_type == EventType.USER_LOGIN
        assert event.metadata["ip_address"] == "127.0.0.1"

    def test_base_event_auto_generates_id(self):
        """Test that event_id is auto-generated if not provided"""
        event = BaseEvent(
            event_type=EventType.USER_LOGIN,
            user_id=str(uuid4()),
        )

        assert event.event_id is not None
        assert len(event.event_id) > 0

    def test_base_event_auto_timestamp(self):
        """Test that timestamp is auto-generated if not provided"""
        event = BaseEvent(
            event_type=EventType.USER_LOGIN,
            user_id=str(uuid4()),
        )

        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_base_event_serialization(self):
        """Test event serialization to dict"""
        user_id = str(uuid4())
        event = BaseEvent(
            event_type=EventType.USER_LOGIN,
            user_id=user_id,
        )

        data = event.model_dump()

        assert data["event_type"] == "user.login"
        assert data["user_id"] == user_id
        assert "event_id" in data
        assert "timestamp" in data


class TestUserRegisteredEvent:
    """Test UserRegisteredEvent schema"""

    def test_user_registered_event_creation(self):
        """Test creating user registered event"""
        user_id = str(uuid4())
        event = UserRegisteredEvent(
            user_id=user_id,
            email="test@example.com",
            username="testuser",
            registration_source="web"
        )

        assert event is not None
        assert event.event_type == EventType.USER_REGISTERED
        assert event.email == "test@example.com"
        assert event.username == "testuser"
        assert event.registration_source == "web"

    def test_user_registered_event_validation(self):
        """Test user registered event validation"""
        # Missing required field should raise error
        with pytest.raises(ValidationError):
            UserRegisteredEvent(
                user_id=str(uuid4()),
                # Missing email
                username="testuser"
            )


class TestLifeEventCreatedEvent:
    """Test LifeEventCreatedEvent schema"""

    def test_life_event_created_event(self):
        """Test creating life event created event"""
        event_id = str(uuid4())
        user_id = str(uuid4())

        event = LifeEventCreatedEvent(
            user_id=user_id,
            life_event_id=event_id,
            event_type="sleep",
            event_data={"duration_hours": 8.0},
            energy_level=7,
            mood_level=8
        )

        assert event is not None
        assert event.event_type == EventType.LIFE_EVENT_CREATED
        assert event.life_event_id == event_id
        assert event.event_data["duration_hours"] == 8.0
        assert event.energy_level == 7
        assert event.mood_level == 8


class TestXPEarnedEvent:
    """Test XPEarnedEvent schema"""

    def test_xp_earned_event_creation(self):
        """Test creating XP earned event"""
        event = XPEarnedEvent(
            user_id=str(uuid4()),
            xp_amount=50,
            source="life_event",
            source_id=str(uuid4())
        )

        assert event is not None
        assert event.event_type == EventType.XP_EARNED
        assert event.xp_amount == 50
        assert event.source == "life_event"
        assert event.source_id is not None

    def test_xp_earned_event_validation(self):
        """Test XP amount must be positive"""
        with pytest.raises(ValidationError):
            XPEarnedEvent(
                user_id=str(uuid4()),
                xp_amount=-10,  # Negative XP should fail
                source="life_event"
            )


class TestLevelUpEvent:
    """Test LevelUpEvent schema"""

    def test_level_up_event_creation(self):
        """Test creating level up event"""
        event = LevelUpEvent(
            user_id=str(uuid4()),
            old_level=9,
            new_level=10,
            total_xp=5000,
            rewards_unlocked=["Badge", "Avatar"]
        )

        assert event is not None
        assert event.event_type == EventType.LEVEL_UP
        assert event.old_level == 9
        assert event.new_level == 10
        assert event.total_xp == 5000
        assert len(event.rewards_unlocked) == 2

    def test_level_up_event_new_level_higher(self):
        """Test that new level must be higher than old level"""
        # This should work
        event = LevelUpEvent(
            user_id=str(uuid4()),
            old_level=5,
            new_level=6,
            total_xp=1000
        )
        assert event.new_level > event.old_level


class TestAchievementUnlockedEvent:
    """Test AchievementUnlockedEvent schema"""

    def test_achievement_unlocked_event(self):
        """Test creating achievement unlocked event"""
        achievement_id = str(uuid4())
        event = AchievementUnlockedEvent(
            user_id=str(uuid4()),
            achievement_id=achievement_id,
            achievement_name="First Steps",
            achievement_description="Log your first life event",
            xp_reward=100,
            rarity="common"
        )

        assert event is not None
        assert event.event_type == EventType.ACHIEVEMENT_UNLOCKED
        assert event.achievement_id == achievement_id
        assert event.achievement_name == "First Steps"
        assert event.xp_reward == 100
        assert event.rarity == "common"


class TestStreakMilestoneEvent:
    """Test StreakMilestoneEvent schema"""

    def test_streak_milestone_event(self):
        """Test creating streak milestone event"""
        event = StreakMilestoneEvent(
            user_id=str(uuid4()),
            streak_type="daily_login",
            streak_count=30,
            milestone_reached=True,
            xp_reward=200
        )

        assert event is not None
        assert event.event_type == EventType.STREAK_MILESTONE
        assert event.streak_type == "daily_login"
        assert event.streak_count == 30
        assert event.milestone_reached is True
        assert event.xp_reward == 200


class TestGoalCompletedEvent:
    """Test GoalCompletedEvent schema"""

    def test_goal_completed_event(self):
        """Test creating goal completed event"""
        goal_id = str(uuid4())
        event = GoalCompletedEvent(
            user_id=str(uuid4()),
            goal_id=goal_id,
            goal_title="Exercise 3 times per week",
            goal_type="fitness",
            completion_percentage=100.0,
            xp_reward=150
        )

        assert event is not None
        assert event.event_type == EventType.GOAL_COMPLETED
        assert event.goal_id == goal_id
        assert event.completion_percentage == 100.0
        assert event.xp_reward == 150


class TestInsightGeneratedEvent:
    """Test InsightGeneratedEvent schema"""

    def test_insight_generated_event(self):
        """Test creating insight generated event"""
        insight_id = str(uuid4())
        event = InsightGeneratedEvent(
            user_id=str(uuid4()),
            insight_id=insight_id,
            insight_type="pattern",
            insight_title="Consistent Sleep Pattern",
            insight_message="You sleep better on weekdays",
            confidence_score=0.85,
            priority="medium"
        )

        assert event is not None
        assert event.event_type == EventType.INSIGHT_GENERATED
        assert event.insight_id == insight_id
        assert event.insight_type == "pattern"
        assert event.confidence_score == 0.85
        assert 0.0 <= event.confidence_score <= 1.0


class TestRecommendationCreatedEvent:
    """Test RecommendationCreatedEvent schema"""

    def test_recommendation_created_event(self):
        """Test creating recommendation event"""
        recommendation_id = str(uuid4())
        event = RecommendationCreatedEvent(
            user_id=str(uuid4()),
            recommendation_id=recommendation_id,
            recommendation_type="activity",
            title="Try morning exercise",
            description="Based on your patterns, morning exercise improves mood",
            expected_impact="High",
            confidence_score=0.78
        )

        assert event is not None
        assert event.event_type == EventType.RECOMMENDATION_CREATED
        assert event.recommendation_id == recommendation_id
        assert event.recommendation_type == "activity"
        assert event.confidence_score == 0.78


class TestEventSerialization:
    """Test event serialization and deserialization"""

    def test_serialize_and_deserialize_xp_event(self):
        """Test round-trip serialization"""
        original = XPEarnedEvent(
            user_id=str(uuid4()),
            xp_amount=100,
            source="achievement",
            source_id=str(uuid4())
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back
        reconstructed = XPEarnedEvent(**data)

        assert reconstructed.xp_amount == original.xp_amount
        assert reconstructed.source == original.source
        assert reconstructed.user_id == original.user_id

    def test_serialize_to_json(self):
        """Test JSON serialization"""
        event = LevelUpEvent(
            user_id=str(uuid4()),
            old_level=5,
            new_level=6,
            total_xp=1000
        )

        json_str = event.model_dump_json()

        assert json_str is not None
        assert isinstance(json_str, str)
        assert "level_up" in json_str
        assert "new_level" in json_str
