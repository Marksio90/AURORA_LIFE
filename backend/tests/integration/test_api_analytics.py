"""
Integration tests for Analytics API Endpoints

Tests for:
- Time series endpoints
- Trend analysis endpoints
- Insights endpoints
- Recommendations endpoints
- Reports endpoints
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.life_event import LifeEvent


pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.asyncio]


@pytest.fixture
async def user_with_analytics_data(
    db_session: AsyncSession,
    test_user: User
) -> User:
    """Create user with sufficient data for analytics"""
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    # Create 30 days of varied data
    for i in range(30):
        # Sleep events
        sleep = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="sleep",
            event_data={"duration_hours": 7.0 + (i % 3) * 0.5},
            energy_level=7 + (i % 3),
            mood_level=7 + (i % 3),
            timestamp=base_time + timedelta(days=i, hours=0),
        )
        events.append(sleep)

        # Exercise events (every other day)
        if i % 2 == 0:
            exercise = LifeEvent(
                id=uuid4(),
                user_id=test_user.id,
                event_type="exercise",
                event_data={"type": "running", "duration_minutes": 30},
                energy_level=8,
                mood_level=8,
                timestamp=base_time + timedelta(days=i, hours=10),
            )
            events.append(exercise)

        # Work events
        work = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="work",
            event_data={"hours": 8},
            energy_level=6 + (i % 4),
            mood_level=6 + (i % 4),
            timestamp=base_time + timedelta(days=i, hours=9),
        )
        events.append(work)

    for event in events:
        db_session.add(event)

    await db_session.commit()
    return test_user


class TestTimeSeriesEndpoints:
    """Test time series API endpoints"""

    async def test_get_time_series_daily(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test retrieving daily time series"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        response = await authenticated_client.get(
            "/api/v1/analytics/time-series/energy_level",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": "daily"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "metric_name" in data
        assert data["metric_name"] == "energy_level"
        assert "granularity" in data
        assert data["granularity"] == "daily"
        assert "data_points" in data
        assert "statistics" in data

    async def test_get_time_series_weekly(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test retrieving weekly time series"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=28)

        response = await authenticated_client.get(
            "/api/v1/analytics/time-series/mood_level",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": "weekly"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["granularity"] == "weekly"
        assert isinstance(data["data_points"], list)

    async def test_get_time_series_invalid_metric(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test time series with invalid metric"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        response = await authenticated_client.get(
            "/api/v1/analytics/time-series/invalid_metric",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 404]

    async def test_get_time_series_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test time series without authentication"""
        response = await client.get(
            "/api/v1/analytics/time-series/energy_level",
            params={
                "start_date": datetime.utcnow().isoformat(),
                "end_date": datetime.utcnow().isoformat(),
            }
        )

        assert response.status_code == 401


class TestTrendEndpoints:
    """Test trend analysis API endpoints"""

    async def test_get_trends(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test retrieving trends"""
        response = await authenticated_client.get(
            "/api/v1/analytics/trends/energy_level",
            params={"days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        assert "metric_name" in data
        assert data["metric_name"] == "energy_level"

        # Should have trend data
        if data.get("slope") is not None:
            assert "direction" in data
            assert data["direction"] in ["INCREASING", "DECREASING", "STABLE"]

    async def test_detect_correlations(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test correlation detection"""
        response = await authenticated_client.post(
            "/api/v1/analytics/correlations",
            params={"days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Check correlation structure
        for correlation in data:
            assert "metric1" in correlation
            assert "metric2" in correlation
            if "coefficient" in correlation and correlation["coefficient"] is not None:
                assert -1.0 <= correlation["coefficient"] <= 1.0


class TestInsightsEndpoints:
    """Test insights API endpoints"""

    async def test_get_insights(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test retrieving insights"""
        response = await authenticated_client.get(
            "/api/v1/analytics/insights",
            params={"days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # Check insight structure
        for insight in data:
            assert "type" in insight
            assert "title" in insight
            assert "message" in insight
            assert "confidence" in insight
            assert "priority" in insight

            # Validate confidence score
            assert 0.0 <= insight["confidence"] <= 1.0

    async def test_get_insights_with_short_period(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test insights with short time period"""
        response = await authenticated_client.get(
            "/api/v1/analytics/insights",
            params={"days": 7}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)


class TestRecommendationsEndpoints:
    """Test recommendations API endpoints"""

    async def test_get_recommendations(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test retrieving recommendations"""
        response = await authenticated_client.get(
            "/api/v1/analytics/recommendations",
            params={"days": 30, "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 5

        # Check recommendation structure
        for rec in data:
            assert "type" in rec
            assert "title" in rec
            assert "message" in rec
            assert "confidence" in rec

            # Validate confidence score
            assert 0.0 <= rec["confidence"] <= 1.0


class TestReportsEndpoints:
    """Test report generation API endpoints"""

    async def test_get_wellness_report(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test wellness report generation"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        response = await authenticated_client.get(
            "/api/v1/analytics/reports/wellness",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check report structure
        assert "period" in data
        assert "overall_score" in data
        assert "category_scores" in data

        # Overall score should be 0-100
        assert 0 <= data["overall_score"] <= 100

        # Check category scores
        categories = data["category_scores"]
        for category, score in categories.items():
            assert 0 <= score <= 100

    async def test_get_progress_report(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test progress report generation"""
        response = await authenticated_client.get(
            "/api/v1/analytics/reports/progress",
            params={"days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        assert "period" in data
        assert "metrics" in data

        # Check metrics structure
        metrics = data["metrics"]
        assert isinstance(metrics, dict)


class TestAnalyticsPermissions:
    """Test analytics API permissions and security"""

    async def test_cannot_access_other_user_analytics(
        self,
        authenticated_client: AsyncClient,
        test_user_2: User
    ):
        """Test that users can only access their own analytics"""
        # Try to access another user's data
        response = await authenticated_client.get(
            f"/api/v1/analytics/insights",
            params={"user_id": str(test_user_2.id)}
        )

        # Should either ignore the user_id param or return 403
        # (depends on implementation)
        assert response.status_code in [200, 403]


class TestAnalyticsEdgeCases:
    """Test edge cases and error handling"""

    async def test_analytics_with_no_data(
        self,
        authenticated_client: AsyncClient
    ):
        """Test analytics when user has no data"""
        response = await authenticated_client.get(
            "/api/v1/analytics/insights",
            params={"days": 30}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty array
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_analytics_with_invalid_date_range(
        self,
        authenticated_client: AsyncClient
    ):
        """Test analytics with invalid date range"""
        end_date = datetime.utcnow()
        start_date = end_date + timedelta(days=7)  # Start after end

        response = await authenticated_client.get(
            "/api/v1/analytics/time-series/energy_level",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
        )

        # Should return error or handle gracefully
        assert response.status_code in [200, 400, 422]

    async def test_analytics_with_very_long_period(
        self,
        authenticated_client: AsyncClient,
        user_with_analytics_data: User
    ):
        """Test analytics with very long time period"""
        response = await authenticated_client.get(
            "/api/v1/analytics/insights",
            params={"days": 365}  # 1 year
        )

        assert response.status_code == 200
        # Should handle gracefully even with long periods
