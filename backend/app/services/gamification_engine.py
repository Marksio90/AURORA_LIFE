"""
Gamification Engine - Core game mechanics

Handles:
- XP earning and leveling
- Achievement checking and unlocking
- Streak tracking
- Point transactions
- Challenge completion
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import math

from app.models.user import User
from app.models.gamification import (
    UserLevel, Achievement, UserAchievement, Badge, UserBadge,
    Streak, DailyChallenge, UserChallengeCompletion,
    Leaderboard, LeaderboardEntry, PointTransaction,
    AchievementCategory, BadgeRarity
)


class GamificationEngine:
    """
    Core gamification engine.

    Manages all game mechanics and progression systems.
    """

    # XP curve - level requirements
    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate XP required for a level."""
        # Formula: XP = 100 * level^1.5
        # Level 1: 100 XP
        # Level 10: 3,162 XP
        # Level 50: 35,355 XP
        # Level 100: 100,000 XP
        return int(100 * (level ** 1.5))

    # Point values for different actions
    POINT_VALUES = {
        "life_event_log": 5,
        "daily_login": 10,
        "complete_goal": 25,
        "week_streak": 50,
        "month_streak": 200,
        "achievement_unlock": 100,
        "challenge_complete": 20,
        "social_interaction": 5,
    }

    # XP multipliers
    XP_MULTIPLIERS = {
        "weekend": 1.5,
        "streak_3day": 1.1,
        "streak_7day": 1.25,
        "streak_30day": 1.5,
        "streak_100day": 2.0,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def initialize_user_gamification(self, user_id: int) -> UserLevel:
        """Initialize gamification data for a new user."""
        # Create UserLevel entry
        user_level = UserLevel(
            user_id=user_id,
            current_level=1,
            total_xp=0,
            current_level_xp=0,
            xp_to_next_level=self.xp_for_level(2),
            total_points=0,
            lifetime_points=0
        )

        self.db.add(user_level)

        # Initialize common streaks
        streak_types = ["daily_login", "life_event_log", "exercise", "sleep_log"]
        for streak_type in streak_types:
            streak = Streak(
                user_id=user_id,
                streak_type=streak_type,
                current_streak=0,
                longest_streak=0
            )
            self.db.add(streak)

        await self.db.commit()
        await self.db.refresh(user_level)

        return user_level

    async def award_xp(
        self,
        user_id: int,
        amount: int,
        source: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Award XP to user and handle level ups.

        Args:
            user_id: User ID
            amount: XP amount
            source: Source of XP (e.g., "life_event", "achievement")
            description: Optional description

        Returns:
            Dict with level_up info and new stats
        """
        # Get user level data
        result = await self.db.execute(
            select(UserLevel).where(UserLevel.user_id == user_id)
        )
        user_level = result.scalar_one_or_none()

        if not user_level:
            user_level = await self.initialize_user_gamification(user_id)

        # Apply XP multipliers
        multiplier = await self._calculate_xp_multiplier(user_id)
        final_xp = int(amount * multiplier)

        # Add XP
        user_level.total_xp += final_xp
        user_level.current_level_xp += final_xp

        # Check for level ups
        level_ups = []
        while user_level.current_level_xp >= user_level.xp_to_next_level:
            # Level up!
            user_level.current_level_xp -= user_level.xp_to_next_level
            user_level.current_level += 1
            user_level.level_up_at = datetime.utcnow()

            # Calculate new XP requirement
            user_level.xp_to_next_level = self.xp_for_level(user_level.current_level + 1)

            level_ups.append({
                'level': user_level.current_level,
                'timestamp': user_level.level_up_at.isoformat()
            })

            # Check for level-based achievements
            await self._check_level_achievements(user_id, user_level.current_level)

        await self.db.commit()
        await self.db.refresh(user_level)

        return {
            'xp_awarded': final_xp,
            'multiplier': multiplier,
            'total_xp': user_level.total_xp,
            'current_level': user_level.current_level,
            'current_level_xp': user_level.current_level_xp,
            'xp_to_next_level': user_level.xp_to_next_level,
            'level_ups': level_ups,
            'leveled_up': len(level_ups) > 0
        }

    async def award_points(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        source: str,
        reference_id: Optional[int] = None,
        reference_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Award points to user.

        Args:
            user_id: User ID
            amount: Point amount (can be negative)
            transaction_type: "earned", "spent", "bonus", "penalty"
            source: Source of points
            reference_id: Optional reference ID
            reference_type: Optional reference type
            description: Optional description

        Returns:
            Transaction details
        """
        # Get user level data
        result = await self.db.execute(
            select(UserLevel).where(UserLevel.user_id == user_id)
        )
        user_level = result.scalar_one_or_none()

        if not user_level:
            user_level = await self.initialize_user_gamification(user_id)

        # Update points
        user_level.total_points += amount
        if amount > 0:
            user_level.lifetime_points += amount

        # Create transaction record
        transaction = PointTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            source=source,
            reference_id=reference_id,
            reference_type=reference_type,
            description=description,
            balance_after=user_level.total_points
        )

        self.db.add(transaction)
        await self.db.commit()
        await self.db.refresh(transaction)

        return {
            'transaction_id': transaction.id,
            'amount': amount,
            'new_balance': user_level.total_points,
            'lifetime_points': user_level.lifetime_points
        }

    async def update_streak(
        self,
        user_id: int,
        streak_type: str,
        activity_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update user's streak for an activity.

        Args:
            user_id: User ID
            streak_type: Type of streak (e.g., "daily_login")
            activity_date: Date of activity (defaults to now)

        Returns:
            Streak info
        """
        if activity_date is None:
            activity_date = datetime.utcnow()

        # Get streak
        result = await self.db.execute(
            select(Streak).where(
                and_(
                    Streak.user_id == user_id,
                    Streak.streak_type == streak_type
                )
            )
        )
        streak = result.scalar_one_or_none()

        if not streak:
            streak = Streak(
                user_id=user_id,
                streak_type=streak_type,
                current_streak=0,
                longest_streak=0
            )
            self.db.add(streak)

        # Check if activity is for today
        activity_date_only = activity_date.date()

        if streak.last_activity_date:
            last_date = streak.last_activity_date.date()

            # Same day - no change
            if last_date == activity_date_only:
                return {
                    'current_streak': streak.current_streak,
                    'longest_streak': streak.longest_streak,
                    'streak_continued': False,
                    'streak_broken': False
                }

            # Consecutive day
            elif last_date == activity_date_only - timedelta(days=1):
                streak.current_streak += 1
                streak.last_activity_date = activity_date
                streak.total_completions += 1

                # Update longest
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak

                # Award XP and points for milestone streaks
                rewards = await self._award_streak_rewards(user_id, streak_type, streak.current_streak)

                await self.db.commit()
                await self.db.refresh(streak)

                return {
                    'current_streak': streak.current_streak,
                    'longest_streak': streak.longest_streak,
                    'streak_continued': True,
                    'streak_broken': False,
                    'milestone_rewards': rewards
                }

            # Streak broken
            else:
                old_streak = streak.current_streak
                streak.current_streak = 1
                streak.last_activity_date = activity_date
                streak.total_completions += 1

                await self.db.commit()
                await self.db.refresh(streak)

                return {
                    'current_streak': streak.current_streak,
                    'longest_streak': streak.longest_streak,
                    'streak_continued': False,
                    'streak_broken': True,
                    'broken_streak_length': old_streak
                }

        # First activity
        else:
            streak.current_streak = 1
            streak.longest_streak = 1
            streak.last_activity_date = activity_date
            streak.streak_start_date = activity_date
            streak.total_completions = 1

            await self.db.commit()
            await self.db.refresh(streak)

            return {
                'current_streak': 1,
                'longest_streak': 1,
                'streak_continued': False,
                'streak_broken': False,
                'first_activity': True
            }

    async def _award_streak_rewards(
        self,
        user_id: int,
        streak_type: str,
        streak_length: int
    ) -> Optional[Dict[str, Any]]:
        """Award rewards for streak milestones."""
        # Milestone rewards
        milestones = {
            3: {'xp': 50, 'points': 10},
            7: {'xp': 100, 'points': 25},
            14: {'xp': 200, 'points': 50},
            30: {'xp': 500, 'points': 100},
            60: {'xp': 1000, 'points': 250},
            100: {'xp': 2000, 'points': 500},
            365: {'xp': 10000, 'points': 2500},
        }

        if streak_length in milestones:
            rewards = milestones[streak_length]

            # Award XP
            await self.award_xp(
                user_id=user_id,
                amount=rewards['xp'],
                source=f"streak_milestone",
                description=f"{streak_length}-day {streak_type} streak"
            )

            # Award points
            await self.award_points(
                user_id=user_id,
                amount=rewards['points'],
                transaction_type="earned",
                source="streak_milestone",
                description=f"{streak_length}-day {streak_type} streak"
            )

            return {
                'milestone': streak_length,
                'xp_awarded': rewards['xp'],
                'points_awarded': rewards['points']
            }

        return None

    async def check_and_unlock_achievements(
        self,
        user_id: int,
        trigger_type: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check if user unlocked any achievements.

        Args:
            user_id: User ID
            trigger_type: What triggered the check (e.g., "streak", "level_up")
            context: Context data for checking

        Returns:
            List of unlocked achievements
        """
        # Get all achievements for this trigger type
        result = await self.db.execute(
            select(Achievement).where(
                Achievement.requirements.op('->>')('type') == trigger_type
            )
        )
        relevant_achievements = result.scalars().all()

        unlocked = []

        for achievement in relevant_achievements:
            # Check if already unlocked (and not repeatable)
            existing = await self.db.execute(
                select(UserAchievement).where(
                    and_(
                        UserAchievement.user_id == user_id,
                        UserAchievement.achievement_id == achievement.id
                    )
                )
            )
            user_achievement = existing.scalar_one_or_none()

            if user_achievement and not achievement.is_repeatable:
                continue

            # Check requirements
            if await self._check_achievement_requirements(user_id, achievement.requirements, context):
                # Unlock!
                if user_achievement:
                    # Repeatable achievement
                    user_achievement.times_completed += 1
                else:
                    # New unlock
                    user_achievement = UserAchievement(
                        user_id=user_id,
                        achievement_id=achievement.id,
                        progress=1.0
                    )
                    self.db.add(user_achievement)

                    # Update achievement stats
                    achievement.unlock_count += 1

                # Award rewards
                xp_result = await self.award_xp(
                    user_id=user_id,
                    amount=achievement.xp_reward,
                    source="achievement",
                    description=f"Achievement: {achievement.name}"
                )

                points_result = await self.award_points(
                    user_id=user_id,
                    amount=achievement.points_reward,
                    transaction_type="earned",
                    source="achievement",
                    reference_id=achievement.id,
                    reference_type="achievement"
                )

                # Award badge if exists
                if achievement.badge_id:
                    badge_result = await self._award_badge(user_id, achievement.badge_id)
                else:
                    badge_result = None

                await self.db.commit()

                unlocked.append({
                    'achievement': {
                        'id': achievement.id,
                        'code': achievement.code,
                        'name': achievement.name,
                        'description': achievement.description,
                        'category': achievement.category,
                        'rarity': achievement.rarity
                    },
                    'xp_earned': achievement.xp_reward,
                    'points_earned': achievement.points_reward,
                    'badge_earned': badge_result,
                    'times_completed': user_achievement.times_completed if user_achievement else 1
                })

        return unlocked

    async def _check_achievement_requirements(
        self,
        user_id: int,
        requirements: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if achievement requirements are met."""
        req_type = requirements.get('type')

        if req_type == 'streak':
            # Check streak requirement
            streak_type = requirements.get('metric')
            required_days = requirements.get('days')

            result = await self.db.execute(
                select(Streak).where(
                    and_(
                        Streak.user_id == user_id,
                        Streak.streak_type == streak_type
                    )
                )
            )
            streak = result.scalar_one_or_none()

            return streak and streak.current_streak >= required_days

        elif req_type == 'level':
            # Check level requirement
            required_level = requirements.get('level')

            result = await self.db.execute(
                select(UserLevel).where(UserLevel.user_id == user_id)
            )
            user_level = result.scalar_one_or_none()

            return user_level and user_level.current_level >= required_level

        elif req_type == 'points':
            # Check lifetime points
            required_points = requirements.get('points')

            result = await self.db.execute(
                select(UserLevel).where(UserLevel.user_id == user_id)
            )
            user_level = result.scalar_one_or_none()

            return user_level and user_level.lifetime_points >= required_points

        # Add more requirement types as needed...

        return False

    async def _award_badge(self, user_id: int, badge_id: int) -> Dict[str, Any]:
        """Award a badge to user."""
        # Check if already has badge
        existing = await self.db.execute(
            select(UserBadge).where(
                and_(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge_id
                )
            )
        )

        if existing.scalar_one_or_none():
            return {'already_owned': True}

        # Award badge
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id
        )
        self.db.add(user_badge)
        await self.db.commit()

        # Get badge details
        badge = await self.db.get(Badge, badge_id)

        return {
            'badge_id': badge.id,
            'name': badge.name,
            'rarity': badge.rarity,
            'icon_url': badge.icon_url
        }

    async def _calculate_xp_multiplier(self, user_id: int) -> float:
        """Calculate XP multiplier based on streaks and other factors."""
        multiplier = 1.0

        # Check for weekend bonus
        if datetime.utcnow().weekday() >= 5:  # Saturday or Sunday
            multiplier *= self.XP_MULTIPLIERS["weekend"]

        # Check daily login streak
        result = await self.db.execute(
            select(Streak).where(
                and_(
                    Streak.user_id == user_id,
                    Streak.streak_type == "daily_login"
                )
            )
        )
        streak = result.scalar_one_or_none()

        if streak:
            if streak.current_streak >= 100:
                multiplier *= self.XP_MULTIPLIERS["streak_100day"]
            elif streak.current_streak >= 30:
                multiplier *= self.XP_MULTIPLIERS["streak_30day"]
            elif streak.current_streak >= 7:
                multiplier *= self.XP_MULTIPLIERS["streak_7day"]
            elif streak.current_streak >= 3:
                multiplier *= self.XP_MULTIPLIERS["streak_3day"]

        return multiplier

    async def _check_level_achievements(self, user_id: int, level: int):
        """Check for level-based achievements."""
        # Trigger achievement check
        await self.check_and_unlock_achievements(
            user_id=user_id,
            trigger_type="level",
            context={'level': level}
        )

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive gamification stats for user."""
        # Get level data
        level_result = await self.db.execute(
            select(UserLevel).where(UserLevel.user_id == user_id)
        )
        level_data = level_result.scalar_one_or_none()

        # Get achievements
        achievements_result = await self.db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        achievements = achievements_result.scalars().all()

        # Get streaks
        streaks_result = await self.db.execute(
            select(Streak).where(Streak.user_id == user_id)
        )
        streaks = streaks_result.scalars().all()

        # Get badges
        badges_result = await self.db.execute(
            select(UserBadge).where(UserBadge.user_id == user_id)
        )
        badges = badges_result.scalars().all()

        return {
            'level': level_data.current_level if level_data else 1,
            'total_xp': level_data.total_xp if level_data else 0,
            'current_level_xp': level_data.current_level_xp if level_data else 0,
            'xp_to_next_level': level_data.xp_to_next_level if level_data else 100,
            'total_points': level_data.total_points if level_data else 0,
            'lifetime_points': level_data.lifetime_points if level_data else 0,
            'achievements_unlocked': len(achievements),
            'badges_earned': len(badges),
            'streaks': [
                {
                    'type': s.streak_type,
                    'current': s.current_streak,
                    'longest': s.longest_streak
                }
                for s in streaks
            ]
        }
