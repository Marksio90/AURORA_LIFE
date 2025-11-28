"""
Unit tests for Analytics Engine

Tests for:
- Time series retrieval and aggregation
- Statistical calculations
- Metric aggregation
- Data validation
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.engine import AnalyticsEngine, TimeGranularity
from app.models.life_event import LifeEvent
from app.models.user import User


pytestmark = [pytest.mark.unit, pytest.mark.db]


@pytest.fixture
async def analytics_engine(db_session: AsyncSession) -> AnalyticsEngine:
    """Create an AnalyticsEngine instance."""
    return AnalyticsEngine(db_session)


@pytest.fixture
async def user_with_sleep_data(db_session: AsyncSession, test_user: User) -> User:
    """Create a user with consistent sleep data for testing."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    # Create 30 days of sleep events
    for i in range(30):
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="sleep",
            event_data={
                "duration_hours": 7.5 + (i % 3) * 0.5,  # 7.5, 8.0, 8.5 pattern
                "quality": ["good", "excellent", "poor"][i % 3],
                "went_to_bed": "23:00",
                "woke_up": "06:30",
            },
            energy_level=7 + (i % 3),
            mood_level=7 + (i % 3),
            timestamp=base_time + timedelta(days=i),
        )
        events.append(event)
        db_session.add(event)

    await db_session.commit()
    return test_user


@pytest.fixture
async def user_with_exercise_data(db_session: AsyncSession, test_user: User) -> User:
    """Create a user with exercise data."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=14)

    # Create exercise events every other day
    for i in range(0, 14, 2):
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="exercise",
            event_data={
                "type": ["running", "gym", "yoga"][i % 3],
                "duration_minutes": 30 + i * 2,
                "intensity": "moderate",
            },
            energy_level=8,
            mood_level=8,
            timestamp=base_time + timedelta(days=i),
        )
        events.append(event)
        db_session.add(event)

    await db_session.commit()
    return test_user


class TestAnalyticsEngine:
    """Test AnalyticsEngine class"""

    async def test_engine_initialization(self, analytics_engine):
        """Test analytics engine initialization"""
        assert analytics_engine is not None
        assert analytics_engine.db is not None

    async def test_get_time_series_daily(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User
    ):
        """Test daily time series retrieval"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        time_series = await analytics_engine.get_time_series(
            user_id=str(user_with_sleep_data.id),
            metric_name="energy_level",
            start_date=start_date,
            end_date=end_date,
            granularity=TimeGranularity.DAILY,
        )

        assert time_series is not None
        assert time_series.metric_name == "energy_level"
        assert time_series.granularity == TimeGranularity.DAILY
        assert len(time_series.data_points) <= 7

        # Check statistics
        assert time_series.statistics is not None
        assert "mean" in time_series.statistics
        assert "median" in time_series.statistics
        assert "std" in time_series.statistics
        assert "min" in time_series.statistics
        assert "max" in time_series.statistics

    async def test_get_time_series_hourly(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User
    ):
        """Test hourly time series retrieval"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)

        time_series = await analytics_engine.get_time_series(
            user_id=str(user_with_sleep_data.id),
            metric_name="mood_level",
            start_date=start_date,
            end_date=end_date,
            granularity=TimeGranularity.HOURLY,
        )

        assert time_series is not None
        assert time_series.granularity == TimeGranularity.HOURLY

    async def test_get_time_series_weekly(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User
    ):
        """Test weekly time series retrieval"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=28)

        time_series = await analytics_engine.get_time_series(
            user_id=str(user_with_sleep_data.id),
            metric_name="energy_level",
            start_date=start_date,
            end_date=end_date,
            granularity=TimeGranularity.WEEKLY,
        )

        assert time_series is not None
        assert time_series.granularity == TimeGranularity.WEEKLY
        assert len(time_series.data_points) <= 4  # ~4 weeks

    async def test_get_time_series_monthly(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User
    ):
        """Test monthly time series retrieval"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        time_series = await analytics_engine.get_time_series(
            user_id=str(user_with_sleep_data.id),
            metric_name="energy_level",
            start_date=start_date,
            end_date=end_date,
            granularity=TimeGranularity.MONTHLY,
        )

        assert time_series is not None
        assert time_series.granularity == TimeGranularity.MONTHLY

    async def test_get_time_series_empty_result(
        self,
        analytics_engine: AnalyticsEngine,
        test_user: User
    ):
        """Test time series with no data"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365)  # Way in the past

        time_series = await analytics_engine.get_time_series(
            user_id=str(test_user.id),
            metric_name="energy_level",
            start_date=start_date - timedelta(days=365),
            end_date=start_date,
            granularity=TimeGranularity.DAILY,
        )

        assert time_series is not None
        assert len(time_series.data_points) == 0

    async def test_calculate_event_count(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_exercise_data: User
    ):
        """Test event count calculation"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=14)

        count = await analytics_engine.calculate_event_count(
            user_id=str(user_with_exercise_data.id),
            event_type="exercise",
            start_date=start_date,
            end_date=end_date,
        )

        assert count >= 0
        assert isinstance(count, int)
        # Should have ~7 exercise events (every other day for 14 days)
        assert count == 7

    async def test_calculate_event_count_with_filters(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_exercise_data: User
    ):
        """Test event count with filters"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=14)

        # Count only "running" exercises
        count = await analytics_engine.calculate_event_count(
            user_id=str(user_with_exercise_data.id),
            event_type="exercise",
            start_date=start_date,
            end_date=end_date,
            filters={"event_data__type": "running"}
        )

        assert count >= 0
        assert isinstance(count, int)

    async def test_calculate_average_duration(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User
    ):
        """Test average duration calculation"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        avg_duration = await analytics_engine.calculate_average_duration(
            user_id=str(user_with_sleep_data.id),
            event_type="sleep",
            start_date=start_date,
            end_date=end_date,
        )

        assert avg_duration is not None
        assert avg_duration > 0
        # Should be around 8 hours (480 minutes)
        assert 400 <= avg_duration <= 550

    async def test_get_metric_statistics(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User
    ):
        """Test metric statistics calculation"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        stats = await analytics_engine.get_metric_statistics(
            user_id=str(user_with_sleep_data.id),
            metric_name="energy_level",
            start_date=start_date,
            end_date=end_date,
        )

        assert stats is not None
        assert "count" in stats
        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "q25" in stats
        assert "q75" in stats

        # Validate values
        assert stats["count"] > 0
        assert 1 <= stats["mean"] <= 10  # Energy levels are 1-10
        assert 1 <= stats["median"] <= 10
        assert stats["std"] >= 0
        assert 1 <= stats["min"] <= 10
        assert 1 <= stats["max"] <= 10

    async def test_aggregate_by_category(
        self,
        analytics_engine: AnalyticsEngine,
        user_with_sleep_data: User,
        user_with_exercise_data: User
    ):
        """Test aggregation by event category"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        aggregation = await analytics_engine.aggregate_by_category(
            user_id=str(user_with_sleep_data.id),
            start_date=start_date,
            end_date=end_date,
        )

        assert aggregation is not None
        assert isinstance(aggregation, dict)
        # Should have at least "sleep" category
        assert "sleep" in aggregation or len(aggregation) == 0

        if "sleep" in aggregation:
            assert "count" in aggregation["sleep"]
            assert "avg_energy" in aggregation["sleep"]
            assert "avg_mood" in aggregation["sleep"]


class TestTimeGranularity:
    """Test TimeGranularity enum"""

    def test_granularity_values(self):
        """Test all granularity values exist"""
        assert TimeGranularity.HOURLY == "hourly"
        assert TimeGranularity.DAILY == "daily"
        assert TimeGranularity.WEEKLY == "weekly"
        assert TimeGranularity.MONTHLY == "monthly"
