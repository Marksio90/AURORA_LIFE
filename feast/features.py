"""
Feast Feature Definitions

Defines all feature views and entities for Aurora Life.
"""
from datetime import timedelta
from feast import Entity, Feature, FeatureView, Field, ValueType
from feast.types import Float32, Float64, Int32, Int64, String
from feast.data_source import RequestSource
from feast.on_demand_feature_view import on_demand_feature_view

# Import data sources
from data_sources import (
    user_activity_source,
    sleep_metrics_source,
    exercise_metrics_source,
    social_metrics_source,
    integration_metrics_source,
)


# ==================== ENTITIES ====================

user = Entity(
    name="user_id",
    description="User entity for Aurora Life",
    value_type=ValueType.STRING,
)


# ==================== FEATURE VIEWS ====================

# Activity Features
user_activity_features = FeatureView(
    name="user_activity_features",
    entities=[user],
    schema=[
        Field(name="activity_count_24h", dtype=Int32),
        Field(name="activity_count_7d", dtype=Int32),
        Field(name="activity_count_30d", dtype=Int32),
        Field(name="total_minutes_24h", dtype=Float32),
        Field(name="total_minutes_7d", dtype=Float32),
        Field(name="total_minutes_30d", dtype=Float32),
        Field(name="activity_diversity_24h", dtype=Int32),
        Field(name="activity_diversity_7d", dtype=Int32),
        Field(name="activity_diversity_30d", dtype=Int32),
        Field(name="most_common_activity_24h", dtype=String),
        Field(name="avg_energy_7d", dtype=Float32),
        Field(name="avg_mood_7d", dtype=Float32),
    ],
    source=user_activity_source,
    ttl=timedelta(hours=24),
    online=True,
    tags={"team": "ml", "category": "activity"},
)


# Sleep Features
sleep_features = FeatureView(
    name="sleep_features",
    entities=[user],
    schema=[
        Field(name="avg_sleep_duration_7d", dtype=Float32),
        Field(name="avg_sleep_duration_30d", dtype=Float32),
        Field(name="sleep_consistency_7d", dtype=Float32),
        Field(name="avg_bedtime_hour_7d", dtype=Float32),
        Field(name="sleep_sessions_7d", dtype=Int32),
        Field(name="sleep_debt_minutes", dtype=Float32),
        Field(name="sleep_quality_score", dtype=Float32),
        Field(name="avg_deep_sleep_minutes_7d", dtype=Float32),
        Field(name="avg_rem_sleep_minutes_7d", dtype=Float32),
    ],
    source=sleep_metrics_source,
    ttl=timedelta(hours=12),
    online=True,
    tags={"team": "ml", "category": "sleep"},
)


# Exercise Features
exercise_features = FeatureView(
    name="exercise_features",
    entities=[user],
    schema=[
        Field(name="exercise_count_7d", dtype=Int32),
        Field(name="exercise_count_30d", dtype=Int32),
        Field(name="exercise_minutes_7d", dtype=Float32),
        Field(name="exercise_minutes_30d", dtype=Float32),
        Field(name="avg_exercise_duration_7d", dtype=Float32),
        Field(name="avg_energy_after_exercise_7d", dtype=Float32),
        Field(name="exercise_consistency_score", dtype=Float32),
        Field(name="workout_variety_score_7d", dtype=Float32),
        Field(name="high_intensity_count_7d", dtype=Int32),
    ],
    source=exercise_metrics_source,
    ttl=timedelta(hours=12),
    online=True,
    tags={"team": "ml", "category": "exercise"},
)


# Social Features
social_features = FeatureView(
    name="social_features",
    entities=[user],
    schema=[
        Field(name="friend_count", dtype=Int32),
        Field(name="posts_7d", dtype=Int32),
        Field(name="comments_7d", dtype=Int32),
        Field(name="likes_received_7d", dtype=Int32),
        Field(name="likes_given_7d", dtype=Int32),
        Field(name="social_engagement_score", dtype=Float32),
        Field(name="avg_post_likes", dtype=Float32),
        Field(name="comment_rate_7d", dtype=Float32),
        Field(name="friend_interactions_7d", dtype=Int32),
    ],
    source=social_metrics_source,
    ttl=timedelta(hours=24),
    online=True,
    tags={"team": "ml", "category": "social"},
)


# Integration Features
integration_features = FeatureView(
    name="integration_features",
    entities=[user],
    schema=[
        Field(name="active_integrations_count", dtype=Int32),
        Field(name="last_sync_hours_ago", dtype=Float32),
        Field(name="avg_heart_rate_7d", dtype=Float32),
        Field(name="avg_steps_7d", dtype=Int32),
        Field(name="avg_calories_7d", dtype=Float32),
        Field(name="data_completeness_score", dtype=Float32),
        Field(name="sync_reliability_score", dtype=Float32),
    ],
    source=integration_metrics_source,
    ttl=timedelta(hours=6),
    online=True,
    tags={"team": "ml", "category": "integration"},
)


# ==================== ON-DEMAND FEATURES ====================

# Request data source for on-demand features
request_source = RequestSource(
    name="request_data",
    schema=[
        Field(name="current_hour", dtype=Int32),
        Field(name="day_of_week", dtype=Int32),
        Field(name="is_weekend", dtype=Int32),
    ],
)


@on_demand_feature_view(
    sources=[
        user_activity_features,
        sleep_features,
        exercise_features,
        request_source,
    ],
    schema=[
        Field(name="predicted_energy", dtype=Float32),
        Field(name="energy_confidence", dtype=Float32),
    ],
)
def energy_prediction_features(inputs: dict) -> dict:
    """
    On-demand energy prediction features.

    Combines historical patterns with current context
    to predict energy levels.
    """
    output = {}

    # Base energy from average
    base_energy = inputs.get("avg_energy_7d", 7.0)

    # Time of day effect
    hour = inputs.get("current_hour", 12)
    if 6 <= hour <= 10:
        time_effect = 2.0  # Morning peak
    elif 11 <= hour <= 14:
        time_effect = 1.5  # Midday
    elif 15 <= hour <= 18:
        time_effect = 1.0  # Afternoon
    elif 19 <= hour <= 22:
        time_effect = 0.5  # Evening
    else:
        time_effect = -2.0  # Night

    # Sleep effect
    sleep_quality = inputs.get("sleep_quality_score", 0.7)
    sleep_effect = (sleep_quality - 0.7) * 3

    # Exercise effect
    exercise_consistency = inputs.get("exercise_consistency_score", 0.5)
    exercise_effect = (exercise_consistency - 0.5) * 2

    # Calculate prediction
    predicted = base_energy + time_effect + sleep_effect + exercise_effect
    predicted = max(1.0, min(10.0, predicted))

    # Confidence based on data quality
    confidence = min(0.95, sleep_quality * exercise_consistency * 1.3)

    output["predicted_energy"] = predicted
    output["energy_confidence"] = confidence

    return output


@on_demand_feature_view(
    sources=[
        sleep_features,
        social_features,
        exercise_features,
        user_activity_features,
    ],
    schema=[
        Field(name="predicted_mood", dtype=Float32),
        Field(name="mood_confidence", dtype=Float32),
    ],
)
def mood_prediction_features(inputs: dict) -> dict:
    """
    On-demand mood prediction features.
    """
    output = {}

    # Base mood
    base_mood = 7.0

    # Sleep effect (strong correlation)
    sleep_quality = inputs.get("sleep_quality_score", 0.7)
    sleep_effect = (sleep_quality - 0.7) * 4

    # Social effect
    social_score = inputs.get("social_engagement_score", 0.5)
    social_effect = (social_score - 0.5) * 2

    # Exercise effect
    exercise_consistency = inputs.get("exercise_consistency_score", 0.5)
    exercise_effect = (exercise_consistency - 0.5) * 1.5

    # Activity diversity
    diversity = inputs.get("activity_diversity_7d", 3) / 10
    diversity_effect = diversity * 1.0

    predicted = base_mood + sleep_effect + social_effect + exercise_effect + diversity_effect
    predicted = max(1.0, min(10.0, predicted))

    confidence = min(0.92, (sleep_quality + social_score + exercise_consistency) / 3 * 1.2)

    output["predicted_mood"] = predicted
    output["mood_confidence"] = confidence

    return output


@on_demand_feature_view(
    sources=[
        sleep_features,
        exercise_features,
        user_activity_features,
    ],
    schema=[
        Field(name="wellness_score", dtype=Float32),
        Field(name="wellness_trend", dtype=String),
    ],
)
def wellness_composite_features(inputs: dict) -> dict:
    """
    Composite wellness score from multiple dimensions.
    """
    output = {}

    # Components (0-1 scale)
    sleep_score = inputs.get("sleep_quality_score", 0.7)
    exercise_score = inputs.get("exercise_consistency_score", 0.5)
    activity_score = min(1.0, inputs.get("total_minutes_7d", 0) / 2100)  # 5h/day optimal

    # Weighted wellness score
    wellness = (
        sleep_score * 0.4 +
        exercise_score * 0.3 +
        activity_score * 0.3
    )

    # Trend (simplified)
    if wellness >= 0.75:
        trend = "excellent"
    elif wellness >= 0.6:
        trend = "good"
    elif wellness >= 0.4:
        trend = "fair"
    else:
        trend = "needs_improvement"

    output["wellness_score"] = wellness
    output["wellness_trend"] = trend

    return output


# ==================== FEATURE SERVICES ====================

from feast import FeatureService

# Energy prediction service
energy_prediction_service = FeatureService(
    name="energy_prediction_v1",
    features=[
        user_activity_features,
        sleep_features,
        exercise_features,
        energy_prediction_features,
    ],
    tags={"model": "energy_predictor", "version": "v1"},
)

# Mood prediction service
mood_prediction_service = FeatureService(
    name="mood_prediction_v1",
    features=[
        sleep_features,
        social_features,
        exercise_features,
        user_activity_features,
        mood_prediction_features,
    ],
    tags={"model": "mood_predictor", "version": "v1"},
)

# Wellness dashboard service
wellness_dashboard_service = FeatureService(
    name="wellness_dashboard_v1",
    features=[
        user_activity_features,
        sleep_features,
        exercise_features,
        social_features,
        integration_features,
        wellness_composite_features,
    ],
    tags={"use_case": "dashboard", "version": "v1"},
)

# ML training service (all features)
ml_training_service = FeatureService(
    name="ml_training_v1",
    features=[
        user_activity_features,
        sleep_features,
        exercise_features,
        social_features,
        integration_features,
    ],
    tags={"use_case": "training", "version": "v1"},
)
