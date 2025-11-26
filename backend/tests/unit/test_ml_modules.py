"""
Unit tests for ML modules (Natural Language Interface, Feature Store, MLflow).
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from uuid import uuid4
from app.ml.natural_language import NaturalLanguageInterface
from app.ml.feature_store import FeatureStore
from app.ml.mlflow_integration import MLflowModelTracker


class TestNaturalLanguageInterface:
    """Tests for Natural Language Interface."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def nli(self, mock_db):
        """Create NLI instance."""
        with patch('app.ml.natural_language.OpenAIClient'), \
             patch('app.ml.natural_language.ClaudeClient'):
            return NaturalLanguageInterface(mock_db)

    @pytest.mark.asyncio
    async def test_parse_time_range_last_week(self, nli):
        """Test parsing 'last_week' time range."""
        result = nli._parse_time_range("last_week")

        assert "start_date" in result
        assert "end_date" in result

        start = datetime.fromisoformat(result["start_date"])
        end = datetime.fromisoformat(result["end_date"])

        # Should be approximately 7 days apart
        delta = (end - start).days
        assert 6 <= delta <= 8

    @pytest.mark.asyncio
    async def test_parse_time_range_this_month(self, nli):
        """Test parsing 'this_month' time range."""
        result = nli._parse_time_range("this_month")

        start = datetime.fromisoformat(result["start_date"])
        assert start.day == 1  # Should start on first day of month

    @pytest.mark.asyncio
    async def test_extract_intent(self, nli):
        """Test intent extraction from query."""
        # Mock OpenAI response
        nli.openai_client.generate = AsyncMock(return_value='{"type": "aggregation", "metric": "sleep", "time_range": "last_week"}')

        result = await nli._extract_intent("How much sleep did I get last week?")

        assert result["type"] == "aggregation"
        assert result["metric"] == "sleep"
        assert "start_date" in result  # Time range should be parsed

    @pytest.mark.asyncio
    async def test_extract_intent_with_invalid_json(self, nli):
        """Test intent extraction with invalid JSON response."""
        # Mock OpenAI returning invalid JSON
        nli.openai_client.generate = AsyncMock(return_value="Invalid JSON response")

        result = await nli._extract_intent("Random query")

        # Should return default intent
        assert result["type"] == "general"
        assert result["metric"] == "general"

    @pytest.mark.asyncio
    async def test_is_user_in_experiment(self):
        """Test traffic allocation logic."""
        from app.core.ab_testing import ABTestingService

        service = ABTestingService(AsyncMock())

        # 100% allocation should always include user
        assert service._is_user_in_experiment("user123", 1.0) is True

        # 0% allocation should never include user
        # (deterministic, so we can't test randomness easily)
        # Just test that it's a boolean
        result = service._is_user_in_experiment("user123", 0.5)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_assign_variant(self):
        """Test variant assignment logic."""
        from app.core.ab_testing import ABTestingService

        service = ABTestingService(AsyncMock())

        variants = [
            {"name": "control", "weight": 0.5},
            {"name": "variant_a", "weight": 0.5}
        ]

        # Should return one of the variants
        result = service._assign_variant("user123", variants)
        assert result in ["control", "variant_a"]

        # Should be deterministic for same user
        result2 = service._assign_variant("user123", variants)
        assert result == result2


class TestFeatureStore:
    """Tests for Feature Store."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def feature_store(self, mock_db):
        """Create FeatureStore instance."""
        return FeatureStore(mock_db)

    @pytest.mark.asyncio
    async def test_compute_features_basic(self, feature_store, mock_db):
        """Test basic feature computation."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        features = await feature_store.compute_features(user_id)

        # Should compute time-based features even without events
        assert "hour_of_day" in features
        assert "day_of_week" in features
        assert "is_weekend" in features
        assert "is_morning" in features
        assert "is_afternoon" in features
        assert "is_evening" in features

    @pytest.mark.asyncio
    async def test_compute_features_with_sleep_data(self, feature_store, mock_db):
        """Test feature computation with sleep events."""
        # Mock sleep event
        mock_event = Mock()
        mock_event.event_type = "sleep"
        mock_event.event_time = datetime.utcnow() - timedelta(hours=8)
        mock_event.event_data = {"duration_hours": 7.5, "quality_score": 4}

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_event]
        mock_db.execute = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        features = await feature_store.compute_features(user_id)

        assert "hours_sleep_last_night" in features
        assert features["hours_sleep_last_night"] == 7.5
        assert "sleep_quality" in features
        assert "time_since_wake" in features

    @pytest.mark.asyncio
    async def test_store_features(self, feature_store, mock_db):
        """Test storing features."""
        user_id = uuid4()
        features = {"feature1": 1.0, "feature2": 2.0}

        await feature_store.store_features(user_id, features, "v1")

        # Should add to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_features_from_cache(self, feature_store):
        """Test getting features from Redis cache."""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"feature1": 1.0}'
        feature_store.redis_client = mock_redis

        user_id = uuid4()
        features = await feature_store.get_features(user_id, "v1")

        assert features["feature1"] == 1.0
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_features_from_db(self, feature_store, mock_db):
        """Test getting features from database when not in cache."""
        feature_store.redis_client = None  # No cache

        # Mock database query
        mock_feature_set = Mock()
        mock_feature_set.features = {"feature1": 1.0}

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_feature_set
        mock_db.execute = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        features = await feature_store.get_features(user_id, "v1", use_cache=False)

        assert features["feature1"] == 1.0


class TestMLflowIntegration:
    """Tests for MLflow integration."""

    @pytest.fixture
    def mlflow_tracker(self):
        """Create MLflow tracker instance."""
        with patch('app.ml.mlflow_integration.MlflowClient'), \
             patch('app.ml.mlflow_integration.mlflow'):
            return MLflowModelTracker()

    def test_start_run(self, mlflow_tracker):
        """Test starting MLflow run."""
        import mlflow
        with patch.object(mlflow, 'start_run') as mock_start:
            mock_run = Mock()
            mock_run.info.run_id = "test-run-id"
            mock_start.return_value = mock_run

            run_id = mlflow_tracker.start_run("test-run")

            assert run_id == "test-run-id"
            mock_start.assert_called_once_with(run_name="test-run")

    def test_log_params(self, mlflow_tracker):
        """Test logging parameters."""
        import mlflow
        with patch.object(mlflow, 'log_param') as mock_log:
            params = {"learning_rate": 0.01, "max_depth": 5}
            mlflow_tracker.log_params(params)

            assert mock_log.call_count == 2

    def test_log_metrics(self, mlflow_tracker):
        """Test logging metrics."""
        import mlflow
        with patch.object(mlflow, 'log_metric') as mock_log:
            metrics = {"accuracy": 0.85, "loss": 0.15}
            mlflow_tracker.log_metrics(metrics, step=1)

            assert mock_log.call_count == 2

    def test_get_model_version(self, mlflow_tracker):
        """Test getting model version."""
        # Mock client response
        mock_version = Mock()
        mock_version.version = "3"
        mlflow_tracker.client.get_latest_versions.return_value = [mock_version]

        version = mlflow_tracker.get_model_version("test-model", "Production")

        assert version == "3"

    def test_get_model_version_not_found(self, mlflow_tracker):
        """Test getting model version when not found."""
        mlflow_tracker.client.get_latest_versions.return_value = []

        version = mlflow_tracker.get_model_version("test-model", "Production")

        assert version is None
