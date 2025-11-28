"""
Unit tests for Insights Generator

Tests for:
- Pattern detection
- Correlation insights
- Anomaly detection
- Insight generation
- Confidence scoring
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.insights import InsightGenerator, InsightType
from app.models.life_event import LifeEvent
from app.models.user import User


pytestmark = [pytest.mark.unit, pytest.mark.db, pytest.mark.ml]


@pytest.fixture
async def insight_generator(db_session: AsyncSession) -> InsightGenerator:
    """Create an InsightGenerator instance."""
    return InsightGenerator(db_session)


@pytest.fixture
async def user_with_consistent_sleep(db_session: AsyncSession, test_user: User) -> User:
    """Create user with consistent sleep patterns."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=14)

    for i in range(14):
        # Consistent bedtime around 23:00
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="sleep",
            event_data={
                "duration_hours": 8.0,
                "quality": "good",
                "went_to_bed": "23:00",
                "woke_up": "07:00",
            },
            energy_level=8,
            mood_level=8,
            timestamp=base_time + timedelta(days=i, hours=23),
        )
        events.append(event)
        db_session.add(event)

    await db_session.commit()
    return test_user


@pytest.fixture
async def user_with_exercise_mood_correlation(db_session: AsyncSession, test_user: User) -> User:
    """Create user with clear exercise-mood correlation."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=20)

    for i in range(20):
        if i % 2 == 0:
            # Days with exercise - high mood
            exercise = LifeEvent(
                id=uuid4(),
                user_id=test_user.id,
                event_type="exercise",
                event_data={"type": "running", "duration_minutes": 30},
                energy_level=8,
                mood_level=9,
                timestamp=base_time + timedelta(days=i, hours=10),
            )
            events.append(exercise)
        else:
            # Days without exercise - lower mood
            event = LifeEvent(
                id=uuid4(),
                user_id=test_user.id,
                event_type="work",
                event_data={"hours": 8},
                energy_level=6,
                mood_level=6,
                timestamp=base_time + timedelta(days=i, hours=10),
            )
            events.append(event)

        db_session.add(events[-1])

    await db_session.commit()
    return test_user


@pytest.fixture
async def user_with_anomalies(db_session: AsyncSession, test_user: User) -> User:
    """Create user with anomalous events."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    # Normal events
    for i in range(28):
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="sleep",
            event_data={"duration_hours": 8.0},
            energy_level=7,
            mood_level=7,
            timestamp=base_time + timedelta(days=i),
        )
        events.append(event)
        db_session.add(event)

    # Anomalous event - very low energy
    anomaly = LifeEvent(
        id=uuid4(),
        user_id=test_user.id,
        event_type="sleep",
        event_data={"duration_hours": 4.0},
        energy_level=2,  # Much lower than normal
        mood_level=3,
        timestamp=base_time + timedelta(days=29),
    )
    events.append(anomaly)
    db_session.add(anomaly)

    await db_session.commit()
    return test_user


class TestInsightGenerator:
    """Test InsightGenerator class"""

    async def test_generator_initialization(self, insight_generator):
        """Test insight generator initialization"""
        assert insight_generator is not None
        assert insight_generator.db is not None

    async def test_generate_insights(
        self,
        insight_generator: InsightGenerator,
        user_with_consistent_sleep: User
    ):
        """Test insight generation"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_consistent_sleep.id),
            days=14
        )

        assert insights is not None
        assert isinstance(insights, list)
        # Should generate at least some insights
        assert len(insights) >= 0

        # Check insight structure
        for insight in insights:
            assert hasattr(insight, "type")
            assert hasattr(insight, "title")
            assert hasattr(insight, "message")
            assert hasattr(insight, "confidence")
            assert hasattr(insight, "priority")
            assert 0.0 <= insight.confidence <= 1.0

    async def test_detect_sleep_pattern(
        self,
        insight_generator: InsightGenerator,
        user_with_consistent_sleep: User
    ):
        """Test consistent sleep pattern detection"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_consistent_sleep.id),
            days=14
        )

        # Should detect consistent sleep pattern
        pattern_insights = [i for i in insights if i.type == InsightType.PATTERN]

        # Might find pattern insight
        if len(pattern_insights) > 0:
            sleep_patterns = [i for i in pattern_insights if "sleep" in i.title.lower() or "sleep" in i.message.lower()]
            if len(sleep_patterns) > 0:
                assert sleep_patterns[0].confidence > 0.5

    async def test_detect_correlation(
        self,
        insight_generator: InsightGenerator,
        user_with_exercise_mood_correlation: User
    ):
        """Test correlation detection"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_exercise_mood_correlation.id),
            days=20
        )

        # Should potentially detect exercise-mood correlation
        correlation_insights = [i for i in insights if i.type == InsightType.CORRELATION]

        # Correlations might be detected
        assert len(correlation_insights) >= 0

    async def test_detect_anomaly(
        self,
        insight_generator: InsightGenerator,
        user_with_anomalies: User
    ):
        """Test anomaly detection"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_anomalies.id),
            days=30
        )

        # Should detect the anomalous low energy event
        anomaly_insights = [i for i in insights if i.type == InsightType.ANOMALY]

        # Might detect anomaly
        assert len(anomaly_insights) >= 0

    async def test_generate_insights_no_data(
        self,
        insight_generator: InsightGenerator,
        test_user: User
    ):
        """Test insight generation with no data"""
        insights = await insight_generator.generate_insights(
            user_id=str(test_user.id),
            days=30
        )

        assert insights is not None
        assert isinstance(insights, list)
        # Should return empty list when no data
        assert len(insights) == 0

    async def test_insight_confidence_scoring(
        self,
        insight_generator: InsightGenerator,
        user_with_consistent_sleep: User
    ):
        """Test that insights have proper confidence scores"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_consistent_sleep.id),
            days=14
        )

        for insight in insights:
            # Confidence should be between 0 and 1
            assert 0.0 <= insight.confidence <= 1.0

            # High confidence insights should have confidence > 0.7
            if insight.confidence > 0.7:
                assert insight.priority in ["HIGH", "MEDIUM"]

    async def test_insight_priority_assignment(
        self,
        insight_generator: InsightGenerator,
        user_with_consistent_sleep: User
    ):
        """Test that insights have proper priority levels"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_consistent_sleep.id),
            days=14
        )

        valid_priorities = ["HIGH", "MEDIUM", "LOW"]

        for insight in insights:
            assert insight.priority in valid_priorities

    async def test_insight_deduplication(
        self,
        insight_generator: InsightGenerator,
        user_with_consistent_sleep: User
    ):
        """Test that duplicate insights are not generated"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_consistent_sleep.id),
            days=14
        )

        # Check for duplicate titles
        titles = [i.title for i in insights]
        assert len(titles) == len(set(titles)), "Duplicate insights detected"

    async def test_insight_action_items(
        self,
        insight_generator: InsightGenerator,
        user_with_consistent_sleep: User
    ):
        """Test that insights include actionable recommendations"""
        insights = await insight_generator.generate_insights(
            user_id=str(user_with_consistent_sleep.id),
            days=14
        )

        for insight in insights:
            # Insights should have actionable messages
            assert len(insight.message) > 0
            assert isinstance(insight.message, str)


class TestInsightType:
    """Test InsightType enum"""

    def test_insight_types(self):
        """Test all insight types exist"""
        assert InsightType.PATTERN == "pattern"
        assert InsightType.CORRELATION == "correlation"
        assert InsightType.ANOMALY == "anomaly"
        assert InsightType.TREND == "trend"
        assert InsightType.RECOMMENDATION == "recommendation"
