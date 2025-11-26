"""
Feature flags system for gradual rollout and A/B testing.

Supports:
- Boolean flags
- Percentage rollout
- User targeting
- Group/segment targeting
- Feature experiments
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.cache import cached
import logging

logger = logging.getLogger(__name__)


class FeatureFlag(str, Enum):
    """Feature flag definitions."""

    # AI Features
    ENABLE_GPT4 = "enable_gpt4"
    ENABLE_CLAUDE_OPUS = "enable_claude_opus"
    ENABLE_ADVANCED_INSIGHTS = "enable_advanced_insights"

    # ML Features
    ENABLE_ENERGY_PREDICTION = "enable_energy_prediction"
    ENABLE_MOOD_PREDICTION = "enable_mood_prediction"
    ENABLE_PATTERN_DETECTION = "enable_pattern_detection"

    # UI Features
    ENABLE_NEW_DASHBOARD = "enable_new_dashboard"
    ENABLE_DATA_EXPORT = "enable_data_export"
    ENABLE_SOCIAL_FEATURES = "enable_social_features"

    # Integrations
    ENABLE_GOOGLE_CALENDAR = "enable_google_calendar"
    ENABLE_FITBIT = "enable_fitbit"
    ENABLE_STRIPE_PAYMENTS = "enable_stripe_payments"

    # Experimental
    ENABLE_VOICE_COMMANDS = "enable_voice_commands"
    ENABLE_MOBILE_APP = "enable_mobile_app"
    ENABLE_GAMIFICATION = "enable_gamification"


class RolloutStrategy(str, Enum):
    """Feature rollout strategies."""
    ALL = "all"                    # Everyone gets the feature
    NONE = "none"                  # Nobody gets the feature
    PERCENTAGE = "percentage"      # Random percentage of users
    USER_IDS = "user_ids"         # Specific user IDs
    ROLES = "roles"               # Specific user roles
    SEGMENTS = "segments"         # User segments (premium, etc.)


class FeatureFlagConfig:
    """Configuration for a feature flag."""

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        strategy: RolloutStrategy = RolloutStrategy.NONE,
        rollout_percentage: int = 0,
        target_user_ids: Optional[List[str]] = None,
        target_roles: Optional[List[str]] = None,
        target_segments: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.enabled = enabled
        self.strategy = strategy
        self.rollout_percentage = rollout_percentage
        self.target_user_ids = target_user_ids or []
        self.target_roles = target_roles or []
        self.target_segments = target_segments or []
        self.metadata = metadata or {}


# Default feature flag configurations
DEFAULT_FLAGS: Dict[FeatureFlag, FeatureFlagConfig] = {
    # AI - Enabled for all
    FeatureFlag.ENABLE_GPT4: FeatureFlagConfig(
        name="enable_gpt4",
        enabled=True,
        strategy=RolloutStrategy.ALL
    ),
    FeatureFlag.ENABLE_CLAUDE_OPUS: FeatureFlagConfig(
        name="enable_claude_opus",
        enabled=True,
        strategy=RolloutStrategy.ALL
    ),

    # ML - Enabled for all
    FeatureFlag.ENABLE_ENERGY_PREDICTION: FeatureFlagConfig(
        name="enable_energy_prediction",
        enabled=True,
        strategy=RolloutStrategy.ALL
    ),
    FeatureFlag.ENABLE_MOOD_PREDICTION: FeatureFlagConfig(
        name="enable_mood_prediction",
        enabled=True,
        strategy=RolloutStrategy.ALL
    ),

    # Advanced features - Premium only
    FeatureFlag.ENABLE_ADVANCED_INSIGHTS: FeatureFlagConfig(
        name="enable_advanced_insights",
        enabled=True,
        strategy=RolloutStrategy.ROLES,
        target_roles=["premium", "admin"]
    ),

    # New UI - 50% rollout
    FeatureFlag.ENABLE_NEW_DASHBOARD: FeatureFlagConfig(
        name="enable_new_dashboard",
        enabled=True,
        strategy=RolloutStrategy.PERCENTAGE,
        rollout_percentage=50
    ),

    # Integrations - Beta
    FeatureFlag.ENABLE_GOOGLE_CALENDAR: FeatureFlagConfig(
        name="enable_google_calendar",
        enabled=True,
        strategy=RolloutStrategy.PERCENTAGE,
        rollout_percentage=25
    ),

    # Experimental - Disabled
    FeatureFlag.ENABLE_GAMIFICATION: FeatureFlagConfig(
        name="enable_gamification",
        enabled=False,
        strategy=RolloutStrategy.NONE
    ),
}


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.flags = DEFAULT_FLAGS.copy()

    async def is_enabled(
        self,
        flag: FeatureFlag,
        user: Optional[User] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if a feature flag is enabled for a user.

        Args:
            flag: Feature flag to check
            user: User object (optional)
            user_id: User ID string (optional)

        Returns:
            True if feature is enabled, False otherwise
        """
        config = self.flags.get(flag)

        if not config or not config.enabled:
            return False

        # Check strategy
        if config.strategy == RolloutStrategy.ALL:
            return True

        if config.strategy == RolloutStrategy.NONE:
            return False

        # For other strategies, we need user info
        if not user and not user_id:
            return False

        uid = str(user.id) if user else user_id

        # Specific user IDs
        if config.strategy == RolloutStrategy.USER_IDS:
            return uid in config.target_user_ids

        # Role-based
        if config.strategy == RolloutStrategy.ROLES:
            if user:
                return user.role in config.target_roles
            return False

        # Percentage rollout (deterministic based on user ID)
        if config.strategy == RolloutStrategy.PERCENTAGE:
            return self._is_in_rollout_percentage(
                uid,
                config.rollout_percentage,
                flag.value
            )

        # Segments
        if config.strategy == RolloutStrategy.SEGMENTS:
            if user:
                user_segments = self._get_user_segments(user)
                return any(seg in config.target_segments for seg in user_segments)
            return False

        return False

    def _is_in_rollout_percentage(
        self,
        user_id: str,
        percentage: int,
        flag_name: str
    ) -> bool:
        """
        Determine if user is in rollout percentage.

        Uses consistent hashing to ensure same user always gets same result.
        """
        if percentage == 0:
            return False
        if percentage >= 100:
            return True

        # Hash user_id + flag_name for consistency
        hash_input = f"{user_id}:{flag_name}".encode()
        hash_value = hashlib.md5(hash_input).hexdigest()

        # Convert to number 0-100
        bucket = int(hash_value[:8], 16) % 100

        return bucket < percentage

    def _get_user_segments(self, user: User) -> List[str]:
        """Get user segments (premium, active, etc.)."""
        segments = ["user"]

        if user.role == "premium":
            segments.append("premium")

        if user.role in ["admin", "super_admin"]:
            segments.append("admin")

        # Add more segment logic as needed
        # e.g., active users, long-time users, etc.

        return segments

    async def get_all_flags(
        self,
        user: Optional[User] = None
    ) -> Dict[str, bool]:
        """
        Get status of all feature flags for a user.

        Returns dict of flag_name -> enabled status.
        """
        result = {}

        for flag in FeatureFlag:
            result[flag.value] = await self.is_enabled(flag, user)

        return result

    async def update_flag(
        self,
        flag: FeatureFlag,
        config: FeatureFlagConfig
    ):
        """Update a feature flag configuration."""
        self.flags[flag] = config

        # Invalidate cache
        if self.db:
            # Clear cached values
            pass

        logger.info(
            f"Updated feature flag {flag.value}: "
            f"enabled={config.enabled}, strategy={config.strategy}"
        )

    async def enable_flag(self, flag: FeatureFlag):
        """Enable a feature flag for all users."""
        config = self.flags.get(flag)
        if config:
            config.enabled = True
            config.strategy = RolloutStrategy.ALL
            await self.update_flag(flag, config)

    async def disable_flag(self, flag: FeatureFlag):
        """Disable a feature flag for all users."""
        config = self.flags.get(flag)
        if config:
            config.enabled = False
            config.strategy = RolloutStrategy.NONE
            await self.update_flag(flag, config)


# Global service instance
_feature_flag_service = FeatureFlagService()


def get_feature_flag_service() -> FeatureFlagService:
    """Get feature flag service instance."""
    return _feature_flag_service


# Convenience function
async def is_feature_enabled(
    flag: FeatureFlag,
    user: Optional[User] = None,
    user_id: Optional[str] = None
) -> bool:
    """Check if a feature is enabled for a user."""
    service = get_feature_flag_service()
    return await service.is_enabled(flag, user, user_id)


# FastAPI dependency
from fastapi import Depends, HTTPException, status
from app.core.auth.dependencies import get_current_user


def require_feature(flag: FeatureFlag):
    """
    Dependency to require a feature flag.

    Usage:
        @app.get("/new-dashboard", dependencies=[Depends(require_feature(FeatureFlag.ENABLE_NEW_DASHBOARD))])
        async def new_dashboard(user: User = Depends(get_current_user)):
            ...
    """
    async def feature_checker(user: User = Depends(get_current_user)):
        service = get_feature_flag_service()
        enabled = await service.is_enabled(flag, user)

        if not enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature not available: {flag.value}"
            )

        return user

    return feature_checker


# Example usage:
"""
from app.core.feature_flags import FeatureFlag, is_feature_enabled

# In a route
@app.get("/insights/advanced")
async def get_advanced_insights(user: User = Depends(get_current_user)):
    if not await is_feature_enabled(FeatureFlag.ENABLE_ADVANCED_INSIGHTS, user):
        raise HTTPException(403, "Feature not available")

    # Feature logic here
    ...

# With dependency
@app.get(
    "/dashboard/new",
    dependencies=[Depends(require_feature(FeatureFlag.ENABLE_NEW_DASHBOARD))]
)
async def new_dashboard():
    # Automatically protected by feature flag
    ...
"""
