"""
Tests for gamification engine

Tests XP awarding, level progression, streak management, and achievement tracking.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gamification_engine import GamificationEngine
from app.models.gamification import UserLevel, Streak, Achievement, UserAchievement
from app.models.user import User


@pytest.fixture
async def user(db: AsyncSession):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def user_level(db: AsyncSession, user: User):
    """Create user level entry"""
    level = UserLevel(
        user_id=user.id,
        current_level=1,
        total_xp=0,
        xp_to_next_level=100
    )
    db.add(level)
    await db.commit()
    await db.refresh(level)
    return level


class TestXPSystem:
    """Test XP awarding and level progression"""

    def test_xp_for_level_formula(self):
        """Test XP calculation formula"""
        assert GamificationEngine.xp_for_level(1) == 100  # 100 * 1^1.5
        assert GamificationEngine.xp_for_level(2) == 282  # 100 * 2^1.5
        assert GamificationEngine.xp_for_level(5) == 1118  # 100 * 5^1.5
        assert GamificationEngine.xp_for_level(10) == 3162  # 100 * 10^1.5

    @pytest.mark.asyncio
    async def test_award_xp_basic(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test basic XP awarding without multipliers"""
        result = await GamificationEngine.award_xp(
            db=db,
            user_id=user.id,
            amount=50,
            source="test_action"
        )

        assert result['success'] is True
        assert result['xp_awarded'] == 50
        assert result['total_xp'] == 50
        assert result['current_level'] == 1
        assert result['leveled_up'] is False

    @pytest.mark.asyncio
    async def test_award_xp_with_level_up(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test XP awarding that triggers level up"""
        result = await GamificationEngine.award_xp(
            db=db,
            user_id=user.id,
            amount=150,
            source="test_action"
        )

        assert result['success'] is True
        assert result['xp_awarded'] == 150
        assert result['total_xp'] == 150
        assert result['current_level'] == 2
        assert result['leveled_up'] is True
        assert result['previous_level'] == 1

    @pytest.mark.asyncio
    async def test_award_xp_weekend_multiplier(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test weekend bonus multiplier (1.5x)"""
        # Mock weekend by passing is_weekend=True
        result = await GamificationEngine.award_xp(
            db=db,
            user_id=user.id,
            amount=100,
            source="test_action",
            metadata={"is_weekend": True}
        )

        # 100 * 1.5 = 150
        assert result['xp_awarded'] == 150
        assert result['multiplier'] == 1.5

    @pytest.mark.asyncio
    async def test_award_xp_streak_multiplier(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test streak multiplier (up to 2.0x for 100+ day streak)"""
        # Create a 100-day streak
        streak = Streak(
            user_id=user.id,
            streak_type="daily_login",
            current_streak=100,
            longest_streak=100,
            last_updated=datetime.utcnow()
        )
        db.add(streak)
        await db.commit()

        result = await GamificationEngine.award_xp(
            db=db,
            user_id=user.id,
            amount=100,
            source="test_action"
        )

        # 100 * 2.0 (max streak multiplier) = 200
        assert result['xp_awarded'] == 200
        assert result['multiplier'] == 2.0

    @pytest.mark.asyncio
    async def test_award_xp_multiple_level_ups(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test XP award that causes multiple level ups"""
        # Award enough XP to jump from level 1 to level 3
        # Level 1->2: 100 XP, Level 2->3: 282 XP = 382 total
        result = await GamificationEngine.award_xp(
            db=db,
            user_id=user.id,
            amount=400,
            source="huge_achievement"
        )

        assert result['current_level'] == 3
        assert result['leveled_up'] is True
        assert result['previous_level'] == 1


class TestStreakManagement:
    """Test streak tracking and milestone rewards"""

    @pytest.mark.asyncio
    async def test_start_new_streak(self, db: AsyncSession, user: User):
        """Test starting a new streak"""
        result = await GamificationEngine.update_streak(
            db=db,
            user_id=user.id,
            streak_type="exercise",
            completed_today=True
        )

        assert result['success'] is True
        assert result['current_streak'] == 1
        assert result['longest_streak'] == 1
        assert result['milestone_reached'] is False

    @pytest.mark.asyncio
    async def test_continue_streak(self, db: AsyncSession, user: User):
        """Test continuing an existing streak"""
        # Create existing streak from yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        streak = Streak(
            user_id=user.id,
            streak_type="exercise",
            current_streak=5,
            longest_streak=5,
            last_updated=yesterday
        )
        db.add(streak)
        await db.commit()

        result = await GamificationEngine.update_streak(
            db=db,
            user_id=user.id,
            streak_type="exercise",
            completed_today=True
        )

        assert result['success'] is True
        assert result['current_streak'] == 6
        assert result['longest_streak'] == 6

    @pytest.mark.asyncio
    async def test_break_streak(self, db: AsyncSession, user: User):
        """Test streak breaking when skipping a day"""
        # Create streak from 2 days ago (gap of 1 day)
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        streak = Streak(
            user_id=user.id,
            streak_type="exercise",
            current_streak=10,
            longest_streak=10,
            last_updated=two_days_ago
        )
        db.add(streak)
        await db.commit()

        result = await GamificationEngine.update_streak(
            db=db,
            user_id=user.id,
            streak_type="exercise",
            completed_today=True
        )

        assert result['success'] is True
        assert result['current_streak'] == 1  # Reset to 1
        assert result['longest_streak'] == 10  # Longest preserved
        assert result['streak_broken'] is True

    @pytest.mark.asyncio
    async def test_streak_milestone_rewards(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test XP rewards at streak milestones"""
        # Create user level for XP tracking
        initial_xp = user_level.total_xp

        # Milestones: 3, 7, 30, 100, 365 days
        milestone_tests = [
            (3, 50),     # 3 days = +50 XP
            (7, 100),    # 7 days = +100 XP
            (30, 300),   # 30 days = +300 XP
            (100, 1000), # 100 days = +1000 XP
        ]

        for days, expected_xp in milestone_tests:
            # Create streak at milestone
            streak = Streak(
                user_id=user.id,
                streak_type=f"test_{days}",
                current_streak=days - 1,
                longest_streak=days - 1,
                last_updated=datetime.utcnow() - timedelta(days=1)
            )
            db.add(streak)
            await db.commit()

            result = await GamificationEngine.update_streak(
                db=db,
                user_id=user.id,
                streak_type=f"test_{days}",
                completed_today=True
            )

            assert result['milestone_reached'] is True
            assert result['milestone_days'] == days
            assert result['xp_reward'] == expected_xp


class TestAchievements:
    """Test achievement unlocking and progress tracking"""

    @pytest.fixture
    async def achievement(self, db: AsyncSession):
        """Create test achievement"""
        ach = Achievement(
            name="Test Achievement",
            description="Complete 10 test actions",
            category="test",
            points=100,
            xp_reward=50,
            rarity="common",
            requirements={
                "type": "total_count",
                "metric": "test_actions",
                "value": 10
            }
        )
        db.add(ach)
        await db.commit()
        await db.refresh(ach)
        return ach

    @pytest.mark.asyncio
    async def test_check_achievement_progress(self, db: AsyncSession, user: User, achievement: Achievement):
        """Test checking progress toward achievement"""
        progress = await GamificationEngine.check_achievement_progress(
            db=db,
            user_id=user.id,
            achievement_id=achievement.id,
            current_value=5
        )

        assert progress['completed'] is False
        assert progress['progress_percentage'] == 50.0
        assert progress['current_value'] == 5
        assert progress['target_value'] == 10

    @pytest.mark.asyncio
    async def test_unlock_achievement(self, db: AsyncSession, user: User, achievement: Achievement, user_level: UserLevel):
        """Test achievement unlocking and XP reward"""
        result = await GamificationEngine.unlock_achievement(
            db=db,
            user_id=user.id,
            achievement_id=achievement.id
        )

        assert result['success'] is True
        assert result['achievement_unlocked'] is True
        assert result['xp_awarded'] == 50
        assert result['points_awarded'] == 100

        # Verify UserAchievement created
        user_ach = await db.get(UserAchievement, {"user_id": user.id, "achievement_id": achievement.id})
        assert user_ach is not None

    @pytest.mark.asyncio
    async def test_duplicate_achievement_unlock(self, db: AsyncSession, user: User, achievement: Achievement):
        """Test that achievements can't be unlocked twice"""
        # Unlock first time
        await GamificationEngine.unlock_achievement(db, user.id, achievement.id)

        # Try to unlock again
        result = await GamificationEngine.unlock_achievement(db, user.id, achievement.id)

        assert result['success'] is False
        assert result['error'] == "Achievement already unlocked"

    @pytest.mark.asyncio
    async def test_consecutive_days_achievement(self, db: AsyncSession, user: User):
        """Test achievement with consecutive days requirement"""
        ach = Achievement(
            name="Week Warrior",
            description="Log in 7 consecutive days",
            category="consistency",
            points=100,
            xp_reward=75,
            rarity="common",
            requirements={
                "type": "streak",
                "metric": "daily_login",
                "days": 7
            }
        )
        db.add(ach)
        await db.commit()

        # Create 7-day streak
        streak = Streak(
            user_id=user.id,
            streak_type="daily_login",
            current_streak=7,
            longest_streak=7,
            last_updated=datetime.utcnow()
        )
        db.add(streak)
        await db.commit()

        # Check if achievement should unlock
        should_unlock = await GamificationEngine.should_unlock_achievement(
            db=db,
            user_id=user.id,
            achievement=ach
        )

        assert should_unlock is True


class TestLeaderboards:
    """Test leaderboard calculations and rankings"""

    @pytest.mark.asyncio
    async def test_calculate_leaderboard_rankings(self, db: AsyncSession):
        """Test leaderboard ranking calculation"""
        # Create multiple users with different XP
        users = []
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                password_hash="hashed"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            level = UserLevel(
                user_id=user.id,
                current_level=i + 1,
                total_xp=(i + 1) * 1000,  # 1000, 2000, 3000, 4000, 5000
                xp_to_next_level=GamificationEngine.xp_for_level(i + 2)
            )
            db.add(level)
            users.append(user)

        await db.commit()

        # Calculate weekly leaderboard
        leaderboard = await GamificationEngine.calculate_leaderboard(
            db=db,
            leaderboard_type="xp",
            time_period="weekly",
            limit=10
        )

        assert len(leaderboard) == 5
        # Should be ordered by XP descending
        assert leaderboard[0]['rank'] == 1
        assert leaderboard[0]['score'] == 5000
        assert leaderboard[4]['rank'] == 5
        assert leaderboard[4]['score'] == 1000

    @pytest.mark.asyncio
    async def test_user_opt_out_leaderboard(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test that users can opt out of leaderboards"""
        # Update visibility
        result = await GamificationEngine.update_leaderboard_visibility(
            db=db,
            user_id=user.id,
            is_visible=False
        )

        assert result['success'] is True
        assert result['is_visible'] is False

        # Verify user not in leaderboard
        leaderboard = await GamificationEngine.calculate_leaderboard(
            db=db,
            leaderboard_type="xp",
            time_period="weekly"
        )

        user_in_leaderboard = any(entry['user_id'] == user.id for entry in leaderboard)
        assert user_in_leaderboard is False


class TestDailyChallenges:
    """Test daily challenge system"""

    @pytest.mark.asyncio
    async def test_generate_daily_challenges(self, db: AsyncSession):
        """Test generation of daily challenges"""
        challenges = await GamificationEngine.generate_daily_challenges(
            db=db,
            date=datetime.utcnow().date(),
            count=3  # Generate 3 challenges per day
        )

        assert len(challenges) == 3
        # Should have mix of difficulties
        difficulties = [c.difficulty for c in challenges]
        assert "easy" in difficulties or "medium" in difficulties or "hard" in difficulties

    @pytest.mark.asyncio
    async def test_complete_daily_challenge(self, db: AsyncSession, user: User, user_level: UserLevel):
        """Test completing a daily challenge"""
        from app.models.gamification import DailyChallenge

        # Create challenge
        challenge = DailyChallenge(
            title="Test Challenge",
            description="Complete test",
            category="test",
            difficulty="easy",
            xp_reward=25,
            points_reward=10,
            requirements={"type": "test"},
            active_date=datetime.utcnow().date(),
            is_active=True
        )
        db.add(challenge)
        await db.commit()
        await db.refresh(challenge)

        result = await GamificationEngine.complete_daily_challenge(
            db=db,
            user_id=user.id,
            challenge_id=challenge.id
        )

        assert result['success'] is True
        assert result['xp_awarded'] == 25
        assert result['points_awarded'] == 10
        assert result['challenge_completed'] is True


# Run tests with: pytest tests/test_gamification_engine.py -v
