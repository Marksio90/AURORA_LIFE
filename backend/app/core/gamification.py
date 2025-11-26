"""
Gamification system with badges, points, achievements, and streaks.

Features:
- Points system (earn points for activities)
- Badges and achievements
- Streak tracking (daily, weekly)
- Leaderboards
- Level progression
- Challenges and quests
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)


class BadgeType(str, Enum):
    """Available badge types."""
    # Streak badges
    STREAK_3_DAYS = "streak_3_days"
    STREAK_7_DAYS = "streak_7_days"
    STREAK_30_DAYS = "streak_30_days"
    STREAK_100_DAYS = "streak_100_days"

    # Activity badges
    FIRST_EVENT = "first_event"
    EVENT_MASTER_100 = "event_master_100"
    EVENT_MASTER_1000 = "event_master_1000"

    # Prediction badges
    PREDICTION_SEEKER = "prediction_seeker"
    PREDICTION_ADDICT = "prediction_addict"

    # Insight badges
    INSIGHT_EXPLORER = "insight_explorer"
    WISDOM_KEEPER = "wisdom_keeper"

    # Wellness badges
    HEALTHY_HABITS = "healthy_habits"
    FITNESS_FANATIC = "fitness_fanatic"
    SLEEP_CHAMPION = "sleep_champion"

    # Social badges
    SOCIAL_BUTTERFLY = "social_butterfly"
    COMMUNITY_STAR = "community_star"

    # Special badges
    EARLY_ADOPTER = "early_adopter"
    BETA_TESTER = "beta_tester"
    PREMIUM_MEMBER = "premium_member"


class AchievementLevel(str, Enum):
    """Achievement difficulty levels."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


BADGE_DEFINITIONS: Dict[BadgeType, Dict[str, Any]] = {
    BadgeType.FIRST_EVENT: {
        "name": "Getting Started",
        "description": "Created your first event",
        "points": 10,
        "icon": "🎯",
        "level": AchievementLevel.BRONZE
    },
    BadgeType.STREAK_7_DAYS: {
        "name": "Week Warrior",
        "description": "Logged events for 7 days in a row",
        "points": 50,
        "icon": "🔥",
        "level": AchievementLevel.SILVER
    },
    BadgeType.STREAK_30_DAYS: {
        "name": "Monthly Master",
        "description": "Logged events for 30 days in a row",
        "points": 200,
        "icon": "⭐",
        "level": AchievementLevel.GOLD
    },
    BadgeType.EVENT_MASTER_100: {
        "name": "Century Club",
        "description": "Created 100 events",
        "points": 100,
        "icon": "💯",
        "level": AchievementLevel.SILVER
    },
    BadgeType.HEALTHY_HABITS: {
        "name": "Health Guru",
        "description": "Maintained healthy habits for a month",
        "points": 150,
        "icon": "🏃",
        "level": AchievementLevel.GOLD
    },
}


class GamificationService:
    """Service for managing gamification features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def award_points(
        self,
        user_id: UUID,
        points: int,
        reason: str
    ) -> int:
        """
        Award points to a user.

        Returns new total points.
        """
        from app.models.user import UserProfile

        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            # Create profile
            profile = UserProfile(
                id=uuid4(),
                user_id=user_id,
                gamification_points=points,
                level=1
            )
            self.db.add(profile)
        else:
            profile.gamification_points += points
            # Check for level up
            new_level = self._calculate_level(profile.gamification_points)
            if new_level > profile.level:
                profile.level = new_level
                await self._on_level_up(user_id, new_level)

        await self.db.commit()

        logger.info(f"Awarded {points} points to user {user_id} for: {reason}")

        return profile.gamification_points

    def _calculate_level(self, points: int) -> int:
        """Calculate user level based on points."""
        # Level formula: level = floor(sqrt(points / 100))
        import math
        return max(1, math.floor(math.sqrt(points / 100)))

    async def _on_level_up(self, user_id: UUID, new_level: int):
        """Handle level up event."""
        # Award bonus points
        bonus_points = new_level * 50

        logger.info(f"User {user_id} leveled up to {new_level}! Bonus: {bonus_points} points")

        # Send notification
        # await send_notification(user_id, f"🎉 Level Up! You're now level {new_level}!")

    async def unlock_badge(
        self,
        user_id: UUID,
        badge_type: BadgeType
    ) -> bool:
        """
        Unlock a badge for a user.

        Returns True if badge was newly unlocked, False if already had it.
        """
        from app.models.user import UserBadge

        # Check if already has badge
        result = await self.db.execute(
            select(UserBadge).where(
                UserBadge.user_id == user_id,
                UserBadge.badge_type == badge_type.value
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            return False

        # Award badge
        badge_def = BADGE_DEFINITIONS[badge_type]
        badge = UserBadge(
            id=uuid4(),
            user_id=user_id,
            badge_type=badge_type.value,
            unlocked_at=datetime.utcnow()
        )

        self.db.add(badge)
        await self.db.commit()

        # Award points
        await self.award_points(
            user_id,
            badge_def["points"],
            f"Unlocked badge: {badge_def['name']}"
        )

        logger.info(f"User {user_id} unlocked badge: {badge_type.value}")

        return True

    async def check_and_award_badges(self, user_id: UUID):
        """Check all badge conditions and award any newly earned badges."""
        from app.models.event import Event

        # Check event count badges
        result = await self.db.execute(
            select(func.count(Event.id)).where(Event.user_id == user_id)
        )
        event_count = result.scalar() or 0

        if event_count == 1:
            await self.unlock_badge(user_id, BadgeType.FIRST_EVENT)
        elif event_count >= 100:
            await self.unlock_badge(user_id, BadgeType.EVENT_MASTER_100)
        elif event_count >= 1000:
            await self.unlock_badge(user_id, BadgeType.EVENT_MASTER_1000)

        # Check streaks
        streak = await self.get_current_streak(user_id)
        if streak >= 3:
            await self.unlock_badge(user_id, BadgeType.STREAK_3_DAYS)
        if streak >= 7:
            await self.unlock_badge(user_id, BadgeType.STREAK_7_DAYS)
        if streak >= 30:
            await self.unlock_badge(user_id, BadgeType.STREAK_30_DAYS)

    async def get_current_streak(self, user_id: UUID) -> int:
        """Get user's current daily streak."""
        from app.models.event import Event
        from sqlalchemy import desc

        # Get events ordered by date
        result = await self.db.execute(
            select(func.date(Event.event_time))
            .where(Event.user_id == user_id)
            .group_by(func.date(Event.event_time))
            .order_by(desc(func.date(Event.event_time)))
            .limit(100)
        )

        dates = [row[0] for row in result.fetchall()]

        if not dates:
            return 0

        # Count consecutive days
        streak = 0
        today = datetime.utcnow().date()

        for i, date in enumerate(dates):
            expected_date = today - timedelta(days=i)
            if date == expected_date:
                streak += 1
            else:
                break

        return streak

    async def get_leaderboard(
        self,
        limit: int = 10,
        time_period: str = "all_time"
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard rankings.

        Args:
            limit: Number of users to return
            time_period: "all_time", "monthly", "weekly"
        """
        from app.models.user import User, UserProfile

        query = (
            select(
                User.id,
                User.username,
                UserProfile.gamification_points,
                UserProfile.level
            )
            .join(UserProfile, User.id == UserProfile.user_id)
            .order_by(UserProfile.gamification_points.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.fetchall()

        return [
            {
                "rank": i + 1,
                "user_id": str(row[0]),
                "username": row[1],
                "points": row[2],
                "level": row[3]
            }
            for i, row in enumerate(rows)
        ]

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get comprehensive gamification stats for a user."""
        from app.models.user import UserProfile, UserBadge

        # Get profile
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        # Get badges
        result = await self.db.execute(
            select(UserBadge).where(UserBadge.user_id == user_id)
        )
        badges = result.scalars().all()

        # Get streak
        streak = await self.get_current_streak(user_id)

        # Get rank
        leaderboard = await self.get_leaderboard(limit=100)
        rank = next(
            (i + 1 for i, entry in enumerate(leaderboard) if entry["user_id"] == str(user_id)),
            None
        )

        return {
            "points": profile.gamification_points if profile else 0,
            "level": profile.level if profile else 1,
            "streak": streak,
            "badges_count": len(badges),
            "badges": [
                {
                    "type": badge.badge_type,
                    "unlocked_at": badge.unlocked_at.isoformat(),
                    **BADGE_DEFINITIONS.get(BadgeType(badge.badge_type), {})
                }
                for badge in badges
            ],
            "rank": rank,
            "next_level_points": self._points_for_next_level(profile.level if profile else 1)
        }

    def _points_for_next_level(self, current_level: int) -> int:
        """Calculate points needed for next level."""
        # level = floor(sqrt(points / 100))
        # points = (level + 1)^2 * 100
        return ((current_level + 1) ** 2) * 100


# Events that trigger point awards
POINT_REWARDS = {
    "event_created": 5,
    "prediction_viewed": 2,
    "insight_generated": 10,
    "profile_completed": 20,
    "friend_invited": 50,
    "daily_login": 10,
}


async def award_activity_points(
    db: AsyncSession,
    user_id: UUID,
    activity: str
):
    """Award points for user activity."""
    points = POINT_REWARDS.get(activity, 0)

    if points > 0:
        service = GamificationService(db)
        await service.award_points(user_id, points, activity)
