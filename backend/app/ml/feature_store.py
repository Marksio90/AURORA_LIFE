"""
Feature Store for ML feature management.

Features:
- Feature extraction and storage
- Feature versioning
- Online and offline feature serving
- Feature caching
- Historical feature retrieval
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Feature store for ML features.

    Stores computed features for ML models with versioning and caching.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client: Optional[redis.Redis] = None

    async def connect_redis(self):
        """Connect to Redis for feature caching."""
        self.redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    async def compute_features(
        self,
        user_id: UUID,
        feature_type: str = "all"
    ) -> Dict[str, Any]:
        """
        Compute features for a user.

        Args:
            user_id: User UUID
            feature_type: Type of features to compute ("energy", "mood", "all")

        Returns:
            Dictionary of computed features
        """
        from app.models.event import Event

        # Get user events (last 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        result = await self.db.execute(
            select(Event).where(
                and_(
                    Event.user_id == user_id,
                    Event.event_time >= cutoff_date
                )
            ).order_by(Event.event_time.desc())
        )
        events = result.scalars().all()

        features = {}

        # Time-based features
        now = datetime.utcnow()
        features.update({
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "is_weekend": now.weekday() >= 5,
            "is_morning": 6 <= now.hour < 12,
            "is_afternoon": 12 <= now.hour < 18,
            "is_evening": 18 <= now.hour < 24,
        })

        # Sleep features
        sleep_events = [e for e in events if e.event_type == "sleep"]
        if sleep_events:
            recent_sleep = sleep_events[0]
            sleep_duration = recent_sleep.event_data.get("duration_hours", 7.5)

            features.update({
                "hours_sleep_last_night": sleep_duration,
                "sleep_quality": recent_sleep.event_data.get("quality_score", 3) / 5.0,
                "time_since_wake": (now - recent_sleep.event_time).seconds / 3600,
            })

            # Sleep statistics (7 days)
            sleep_7d = [e for e in sleep_events if e.event_time >= now - timedelta(days=7)]
            if sleep_7d:
                avg_sleep = sum(e.event_data.get("duration_hours", 7.5) for e in sleep_7d) / len(sleep_7d)
                features["avg_sleep_7d"] = avg_sleep
                features["sleep_debt"] = max(0, 7.5 - avg_sleep) * len(sleep_7d)

        # Exercise features
        exercise_events = [e for e in events if e.event_type == "exercise"]
        if exercise_events:
            today_exercise = sum(
                e.event_data.get("duration_minutes", 0)
                for e in exercise_events
                if e.event_time.date() == now.date()
            )
            features["exercise_minutes_today"] = today_exercise

            # 7-day average
            exercise_7d = [e for e in exercise_events if e.event_time >= now - timedelta(days=7)]
            if exercise_7d:
                avg_exercise = sum(
                    e.event_data.get("duration_minutes", 0) for e in exercise_7d
                ) / 7
                features["avg_exercise_7d"] = avg_exercise

            # Days since last exercise
            if exercise_events:
                last_exercise = exercise_events[0]
                features["days_since_exercise"] = (now - last_exercise.event_time).days

        # Work features
        work_events = [e for e in events if e.event_type == "work"]
        today_work = [e for e in work_events if e.event_time.date() == now.date()]

        features["work_hours_today"] = sum(
            e.event_data.get("duration_hours", 0) for e in today_work
        )
        features["meetings_count"] = sum(
            e.event_data.get("meetings", 0) for e in today_work
        )

        # Mood features
        mood_events = [e for e in events if e.event_type == "mood"]
        if mood_events:
            recent_mood = mood_events[0]
            features["mood_score_current"] = recent_mood.event_data.get("mood_score", 5)

            # 7-day mood average
            mood_7d = [e for e in mood_events if e.event_time >= now - timedelta(days=7)]
            if mood_7d:
                avg_mood = sum(e.event_data.get("mood_score", 5) for e in mood_7d) / len(mood_7d)
                features["avg_mood_7d"] = avg_mood

                # Mood volatility (standard deviation)
                mood_scores = [e.event_data.get("mood_score", 5) for e in mood_7d]
                if len(mood_scores) > 1:
                    import numpy as np
                    features["mood_volatility"] = float(np.std(mood_scores))

        # Social features
        social_events = [e for e in events if e.event_type == "social"]
        social_3d = [e for e in social_events if e.event_time >= now - timedelta(days=3)]
        features["social_events_count_3d"] = len(social_3d)

        # Stress features
        features["stress_level"] = 5  # Default, could be computed from events

        # Weather (would need external API integration)
        features["weather_condition"] = "sunny"  # Placeholder

        return features

    async def store_features(
        self,
        user_id: UUID,
        features: Dict[str, Any],
        feature_version: str = "v1"
    ):
        """
        Store computed features.

        Args:
            user_id: User UUID
            features: Feature dictionary
            feature_version: Feature version identifier
        """
        from app.models.ml import FeatureSet

        # Store in database (offline store)
        feature_set = FeatureSet(
            user_id=user_id,
            features=features,
            feature_version=feature_version,
            created_at=datetime.utcnow()
        )

        self.db.add(feature_set)
        await self.db.commit()

        # Store in Redis (online store) with 24h TTL
        if self.redis_client:
            cache_key = f"features:{user_id}:{feature_version}"
            await self.redis_client.setex(
                cache_key,
                86400,  # 24 hours
                json.dumps(features, default=str)
            )

        logger.info(f"Stored features for user {user_id}, version {feature_version}")

    async def get_features(
        self,
        user_id: UUID,
        feature_version: str = "v1",
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve features for a user.

        Args:
            user_id: User UUID
            feature_version: Feature version to retrieve
            use_cache: Whether to use Redis cache

        Returns:
            Feature dictionary or None
        """
        # Try cache first
        if use_cache and self.redis_client:
            cache_key = f"features:{user_id}:{feature_version}"
            cached = await self.redis_client.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for features: {cache_key}")
                return json.loads(cached)

        # Fallback to database
        from app.models.ml import FeatureSet

        result = await self.db.execute(
            select(FeatureSet)
            .where(
                and_(
                    FeatureSet.user_id == user_id,
                    FeatureSet.feature_version == feature_version
                )
            )
            .order_by(FeatureSet.created_at.desc())
            .limit(1)
        )

        feature_set = result.scalar_one_or_none()

        if feature_set:
            # Refresh cache
            if self.redis_client:
                cache_key = f"features:{user_id}:{feature_version}"
                await self.redis_client.setex(
                    cache_key,
                    86400,
                    json.dumps(feature_set.features, default=str)
                )

            return feature_set.features

        return None

    async def get_or_compute_features(
        self,
        user_id: UUID,
        feature_version: str = "v1"
    ) -> Dict[str, Any]:
        """
        Get features from cache/db or compute if not available.

        Args:
            user_id: User UUID
            feature_version: Feature version

        Returns:
            Feature dictionary
        """
        # Try to get existing features
        features = await self.get_features(user_id, feature_version)

        if features:
            # Check if features are fresh (< 1 hour old)
            # If fresh, return them
            return features

        # Compute new features
        features = await self.compute_features(user_id)

        # Store features
        await self.store_features(user_id, features, feature_version)

        return features

    async def get_historical_features(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        feature_version: str = "v1"
    ) -> List[Dict[str, Any]]:
        """
        Get historical features for a date range.

        Useful for model training with historical data.
        """
        from app.models.ml import FeatureSet

        result = await self.db.execute(
            select(FeatureSet)
            .where(
                and_(
                    FeatureSet.user_id == user_id,
                    FeatureSet.feature_version == feature_version,
                    FeatureSet.created_at >= start_date,
                    FeatureSet.created_at <= end_date
                )
            )
            .order_by(FeatureSet.created_at)
        )

        feature_sets = result.scalars().all()

        return [
            {
                "timestamp": fs.created_at.isoformat(),
                **fs.features
            }
            for fs in feature_sets
        ]


# Usage in prediction endpoint:
"""
from app.ml.feature_store import FeatureStore

async def predict_energy(user_id: UUID, db: AsyncSession):
    # Get features from feature store
    feature_store = FeatureStore(db)
    await feature_store.connect_redis()

    features = await feature_store.get_or_compute_features(user_id)

    # Use features for prediction
    model = load_model("energy")
    prediction = model.predict([list(features.values())])

    return prediction
"""
