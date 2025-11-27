"""
Gamification Models - Points, XP, Badges, Achievements, Streaks

Engagement-driving game mechanics for AURORA_LIFE.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, JSON, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any

from app.models.base import Base


class AchievementCategory(str, Enum):
    """Achievement categories"""
    HEALTH = "health"
    PRODUCTIVITY = "productivity"
    SOCIAL = "social"
    CONSISTENCY = "consistency"
    MILESTONES = "milestones"
    SPECIAL = "special"


class BadgeRarity(str, Enum):
    """Badge rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class UserLevel(Base):
    """
    User progression levels.

    Level system based on total XP earned.
    """
    __tablename__ = "user_levels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Level & XP
    current_level = Column(Integer, default=1)
    total_xp = Column(Integer, default=0)
    current_level_xp = Column(Integer, default=0)  # XP in current level
    xp_to_next_level = Column(Integer, default=100)

    # Prestige (after level 100, can reset for prestige)
    prestige_level = Column(Integer, default=0)

    # Stats
    total_points = Column(Integer, default=0)  # Separate from XP
    lifetime_points = Column(Integer, default=0)  # Never decreases

    # Timestamps
    level_up_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="level_data")


class Achievement(Base):
    """
    Achievement definitions.

    Unlockable achievements for various accomplishments.
    """
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)

    # Achievement details
    code = Column(String, unique=True, nullable=False)  # e.g., "sleep_master_7"
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(SQLEnum(AchievementCategory), nullable=False)

    # Rewards
    xp_reward = Column(Integer, default=0)
    points_reward = Column(Integer, default=0)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=True)

    # Requirements (stored as JSON)
    requirements = Column(JSON, nullable=False)
    # Example: {"type": "streak", "metric": "sleep", "days": 7, "min_value": 7}

    # Metadata
    rarity = Column(SQLEnum(BadgeRarity), default=BadgeRarity.COMMON)
    icon = Column(String, nullable=True)
    is_hidden = Column(Boolean, default=False)  # Secret achievements
    is_repeatable = Column(Boolean, default=False)

    # Stats
    unlock_count = Column(Integer, default=0)  # How many users unlocked this

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    badge = relationship("Badge", back_populates="achievement")
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class Badge(Base):
    """
    Visual badges/icons earned through achievements.
    """
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)

    # Badge details
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon_url = Column(String, nullable=True)
    rarity = Column(SQLEnum(BadgeRarity), default=BadgeRarity.COMMON)

    # Display
    color = Column(String, nullable=True)  # Hex color
    order = Column(Integer, default=0)  # Display order

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    achievement = relationship("Achievement", back_populates="badge", uselist=False)
    user_badges = relationship("UserBadge", back_populates="badge")


class UserAchievement(Base):
    """
    User's unlocked achievements.
    """
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)

    # Unlock details
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0 (for tracking progress before unlock)
    times_completed = Column(Integer, default=1)  # For repeatable achievements

    # Metadata
    notification_sent = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


class UserBadge(Base):
    """
    User's earned badges.
    """
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)

    earned_at = Column(DateTime, default=datetime.utcnow)
    is_equipped = Column(Boolean, default=False)  # Can equip badge to profile

    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")


class Streak(Base):
    """
    User streaks for different activities.
    """
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Streak details
    streak_type = Column(String, nullable=False)  # e.g., "daily_login", "sleep_log", "exercise"
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)

    # Dates
    last_activity_date = Column(DateTime, nullable=True)
    streak_start_date = Column(DateTime, nullable=True)

    # Stats
    total_completions = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="streaks")


class DailyChallenge(Base):
    """
    Daily challenges for users.
    """
    __tablename__ = "daily_challenges"

    id = Column(Integer, primary_key=True, index=True)

    # Challenge details
    code = Column(String, nullable=False)  # e.g., "exercise_30min"
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # Requirements
    requirements = Column(JSON, nullable=False)
    # Example: {"type": "activity", "category": "exercise", "duration_minutes": 30}

    # Rewards
    xp_reward = Column(Integer, default=50)
    points_reward = Column(Integer, default=10)

    # Scheduling
    day_of_week = Column(Integer, nullable=True)  # 0-6, None = any day
    difficulty = Column(Integer, default=1)  # 1-5

    # Metadata
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_completions = relationship("UserChallengeCompletion", back_populates="challenge")


class UserChallengeCompletion(Base):
    """
    User's completed daily challenges.
    """
    __tablename__ = "user_challenge_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("daily_challenges.id"), nullable=False)

    # Completion details
    completed_at = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime, nullable=False)  # Date of the challenge (for daily tracking)

    # Rewards given
    xp_earned = Column(Integer, default=0)
    points_earned = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="challenge_completions")
    challenge = relationship("DailyChallenge", back_populates="user_completions")


class Leaderboard(Base):
    """
    Leaderboard entries (privacy-aware).
    """
    __tablename__ = "leaderboards"

    id = Column(Integer, primary_key=True, index=True)

    # Leaderboard type
    leaderboard_type = Column(String, nullable=False)  # "weekly_xp", "monthly_points", "alltime_level"
    timeframe = Column(String, nullable=False)  # "weekly", "monthly", "alltime"

    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Metadata
    is_current = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    entries = relationship("LeaderboardEntry", back_populates="leaderboard")


class LeaderboardEntry(Base):
    """
    Individual leaderboard entries.
    """
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    leaderboard_id = Column(Integer, ForeignKey("leaderboards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Ranking
    rank = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)  # XP, points, or other metric

    # User info (cached for display)
    username = Column(String, nullable=True)  # Anonymized if user opted out
    is_anonymous = Column(Boolean, default=False)

    # Change from previous period
    rank_change = Column(Integer, default=0)  # +5 = moved up 5 places

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leaderboard = relationship("Leaderboard", back_populates="entries")
    user = relationship("User", back_populates="leaderboard_entries")


class PointTransaction(Base):
    """
    Log of all point transactions (earning/spending).
    """
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Transaction details
    amount = Column(Integer, nullable=False)  # Can be negative for spending
    transaction_type = Column(String, nullable=False)  # "earned", "spent", "bonus", "penalty"
    source = Column(String, nullable=False)  # "achievement", "challenge", "streak", "purchase"

    # Reference
    reference_id = Column(Integer, nullable=True)  # ID of related achievement, challenge, etc.
    reference_type = Column(String, nullable=True)  # "achievement", "challenge", etc.

    # Description
    description = Column(String, nullable=True)

    # Balance after transaction
    balance_after = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="point_transactions")


# Update User model to include gamification relationships
# This should be added to app/models/user.py:
"""
Add to User class:

    # Gamification
    level_data = relationship("UserLevel", back_populates="user", uselist=False)
    achievements = relationship("UserAchievement", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    streaks = relationship("Streak", back_populates="user")
    challenge_completions = relationship("UserChallengeCompletion", back_populates="user")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="user")
    point_transactions = relationship("PointTransaction", back_populates="user")

    # Privacy settings for gamification
    show_in_leaderboards = Column(Boolean, default=True)
    public_profile = Column(Boolean, default=False)
"""
