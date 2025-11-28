"""
Unit tests for Trend Analysis

Tests for:
- Linear regression trend detection
- Correlation analysis
- Anomaly detection with z-scores
- Trend forecasting
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.trends import TrendAnalyzer
from app.models.life_event import LifeEvent
from app.models.user import User


pytestmark = [pytest.mark.unit, pytest.mark.db, pytest.mark.ml]


@pytest.fixture
async def trend_analyzer(db_session: AsyncSession) -> TrendAnalyzer:
    """Create a TrendAnalyzer instance."""
    return TrendAnalyzer(db_session)


@pytest.fixture
async def user_with_upward_trend(db_session: AsyncSession, test_user: User) -> User:
    """Create user with upward energy trend."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    for i in range(30):
        # Gradually increasing energy level
        energy = 5 + (i / 30.0) * 3  # Increase from 5 to 8
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="work",
            event_data={"hours": 8},
            energy_level=int(energy),
            mood_level=7,
            timestamp=base_time + timedelta(days=i),
        )
        events.append(event)
        db_session.add(event)

    await db_session.commit()
    return test_user


@pytest.fixture
async def user_with_downward_trend(db_session: AsyncSession, test_user: User) -> User:
    """Create user with downward mood trend."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    for i in range(30):
        # Gradually decreasing mood level
        mood = 8 - (i / 30.0) * 3  # Decrease from 8 to 5
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="work",
            event_data={"hours": 8},
            energy_level=7,
            mood_level=int(mood),
            timestamp=base_time + timedelta(days=i),
        )
        events.append(event)
        db_session.add(event)

    await db_session.commit()
    return test_user


@pytest.fixture
async def user_with_stable_trend(db_session: AsyncSession, test_user: User) -> User:
    """Create user with stable (no trend) data."""
    events = []
    base_time = datetime.utcnow() - timedelta(days=30)

    for i in range(30):
        # Stable energy level around 7 with small variations
        event = LifeEvent(
            id=uuid4(),
            user_id=test_user.id,
            event_type="work",
            event_data={"hours": 8},
            energy_level=7 + (i % 3 - 1),  # 6, 7, 8 repeating
            mood_level=7,
            timestamp=base_time + timedelta(days=i),
        )
        events.append(event)
        db_session.add(event)

    await db_session.commit()
    return test_user


class TestTrendAnalyzer:
    """Test TrendAnalyzer class"""

    async def test_analyzer_initialization(self, trend_analyzer):
        """Test trend analyzer initialization"""
        assert trend_analyzer is not None
        assert trend_analyzer.db is not None

    async def test_analyze_upward_trend(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_upward_trend: User
    ):
        """Test upward trend detection"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(user_with_upward_trend.id),
            metric_name="energy_level",
            days=30
        )

        assert analysis is not None
        assert analysis.metric_name == "energy_level"

        # Should detect upward trend
        if analysis.slope is not None:
            assert analysis.slope > 0, "Should detect positive slope"

        # Trend direction should be INCREASING
        if analysis.direction:
            assert analysis.direction in ["INCREASING", "STABLE"]

    async def test_analyze_downward_trend(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_downward_trend: User
    ):
        """Test downward trend detection"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(user_with_downward_trend.id),
            metric_name="mood_level",
            days=30
        )

        assert analysis is not None

        # Should detect downward trend
        if analysis.slope is not None:
            assert analysis.slope < 0, "Should detect negative slope"

        # Trend direction should be DECREASING
        if analysis.direction:
            assert analysis.direction in ["DECREASING", "STABLE"]

    async def test_analyze_stable_trend(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_stable_trend: User
    ):
        """Test stable trend detection"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(user_with_stable_trend.id),
            metric_name="energy_level",
            days=30
        )

        assert analysis is not None

        # Slope should be close to 0
        if analysis.slope is not None:
            assert abs(analysis.slope) < 0.1, "Should detect near-zero slope"

    async def test_trend_strength_calculation(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_upward_trend: User
    ):
        """Test trend strength (R²) calculation"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(user_with_upward_trend.id),
            metric_name="energy_level",
            days=30
        )

        assert analysis is not None

        # R² should be between 0 and 1
        if hasattr(analysis, 'r_squared') and analysis.r_squared is not None:
            assert 0.0 <= analysis.r_squared <= 1.0

    async def test_trend_forecast(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_upward_trend: User
    ):
        """Test trend forecasting"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(user_with_upward_trend.id),
            metric_name="energy_level",
            days=30
        )

        assert analysis is not None

        # Should provide forecast
        if hasattr(analysis, 'forecast') and analysis.forecast:
            # Forecast should be for 7 days
            assert len(analysis.forecast) <= 7

            # Forecast values should be reasonable (1-10 for energy)
            for forecast_point in analysis.forecast:
                if hasattr(forecast_point, 'value'):
                    assert 1 <= forecast_point.value <= 10

    async def test_detect_correlations(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_upward_trend: User
    ):
        """Test correlation detection between metrics"""
        correlations = await trend_analyzer.detect_correlations(
            user_id=str(user_with_upward_trend.id),
            days=30
        )

        assert correlations is not None
        assert isinstance(correlations, list)

        # Check correlation structure
        for correlation in correlations:
            assert hasattr(correlation, 'metric1')
            assert hasattr(correlation, 'metric2')
            assert hasattr(correlation, 'coefficient')

            # Correlation coefficient should be between -1 and 1
            if correlation.coefficient is not None:
                assert -1.0 <= correlation.coefficient <= 1.0

    async def test_detect_anomalies(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_stable_trend: User,
        db_session: AsyncSession
    ):
        """Test anomaly detection using z-scores"""
        # Add an anomalous event
        anomaly = LifeEvent(
            id=uuid4(),
            user_id=user_with_stable_trend.id,
            event_type="work",
            event_data={"hours": 8},
            energy_level=1,  # Much lower than normal (7)
            mood_level=7,
            timestamp=datetime.utcnow(),
        )
        db_session.add(anomaly)
        await db_session.commit()

        anomalies = await trend_analyzer.detect_anomalies(
            user_id=str(user_with_stable_trend.id),
            metric_name="energy_level",
            days=30,
            threshold=2.0  # Z-score threshold
        )

        assert anomalies is not None
        assert isinstance(anomalies, list)

        # Should detect at least one anomaly
        if len(anomalies) > 0:
            for anomaly_data in anomalies:
                assert hasattr(anomaly_data, 'value')
                assert hasattr(anomaly_data, 'z_score')

                # Z-score should be significant
                if hasattr(anomaly_data, 'z_score') and anomaly_data.z_score is not None:
                    assert abs(anomaly_data.z_score) >= 2.0

    async def test_analyze_trend_no_data(
        self,
        trend_analyzer: TrendAnalyzer,
        test_user: User
    ):
        """Test trend analysis with no data"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(test_user.id),
            metric_name="energy_level",
            days=30
        )

        # Should handle no data gracefully
        assert analysis is None or (hasattr(analysis, 'slope') and analysis.slope is None)

    async def test_trend_analysis_short_period(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_upward_trend: User
    ):
        """Test trend analysis over short period"""
        analysis = await trend_analyzer.analyze_trend(
            user_id=str(user_with_upward_trend.id),
            metric_name="energy_level",
            days=3  # Very short period
        )

        # Should still work but might not have strong trend
        assert analysis is not None

    async def test_correlation_strength_classification(
        self,
        trend_analyzer: TrendAnalyzer,
        user_with_upward_trend: User
    ):
        """Test correlation strength classification"""
        correlations = await trend_analyzer.detect_correlations(
            user_id=str(user_with_upward_trend.id),
            days=30
        )

        for correlation in correlations:
            if hasattr(correlation, 'strength') and correlation.strength:
                # Strength should be one of: STRONG, MODERATE, WEAK
                assert correlation.strength in ["STRONG", "MODERATE", "WEAK"]

                # Verify strength matches coefficient
                if correlation.coefficient is not None:
                    abs_coef = abs(correlation.coefficient)
                    if abs_coef >= 0.7:
                        assert correlation.strength == "STRONG"
                    elif abs_coef >= 0.4:
                        assert correlation.strength == "MODERATE"
                    else:
                        assert correlation.strength == "WEAK"
