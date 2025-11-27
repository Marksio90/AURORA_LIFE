"""
Gamification API Endpoints

Endpoints for:
- XP & Levels
- Achievements & Badges
- Streaks
- Leaderboards
- Daily Challenges
- Points
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.services.gamification_engine import GamificationEngine


router = APIRouter(prefix="/api/v1/gamification", tags=["Gamification"])


# ========== Pydantic Models ==========

class UserStatsResponse(BaseModel):
    level: int
    total_xp: int
    current_level_xp: int
    xp_to_next_level: int
    total_points: int
    lifetime_points: int
    achievements_unlocked: int
    badges_earned: int
    streaks: List[dict]


class AwardXPRequest(BaseModel):
    amount: int = Field(..., gt=0, le=10000)
    source: str
    description: Optional[str] = None


class UpdateStreakRequest(BaseModel):
    streak_type: str
    activity_date: Optional[datetime] = None


# ========== Endpoints ==========

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive gamification stats for current user.

    Includes:
    - Level & XP
    - Points
    - Achievements count
    - Badges count
    - All streaks
    """
    engine = GamificationEngine(db)

    stats = await engine.get_user_stats(current_user.id)

    return UserStatsResponse(**stats)


@router.post("/xp/award")
async def award_xp(
    request: AwardXPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Award XP to user (admin/system use).

    Automatically handles:
    - XP multipliers (streaks, weekends)
    - Level ups
    - Level-based achievement checks
    """
    engine = GamificationEngine(db)

    result = await engine.award_xp(
        user_id=current_user.id,
        amount=request.amount,
        source=request.source,
        description=request.description
    )

    return result


@router.post("/streaks/update")
async def update_streak(
    request: UpdateStreakRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update streak for an activity.

    Automatically:
    - Continues streak if consecutive day
    - Breaks streak if gap
    - Awards milestone rewards (3, 7, 14, 30 days...)
    """
    engine = GamificationEngine(db)

    result = await engine.update_streak(
        user_id=current_user.id,
        streak_type=request.streak_type,
        activity_date=request.activity_date
    )

    return result


@router.get("/achievements")
async def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all unlocked achievements for user.
    """
    # TODO: Implement achievement fetching
    return {
        'achievements': [],
        'total_unlocked': 0,
        'total_available': 50  # Example
    }


@router.get("/badges")
async def get_user_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all earned badges for user.
    """
    # TODO: Implement badge fetching
    return {
        'badges': [],
        'total_earned': 0,
        'equipped_badge': None
    }


@router.get("/leaderboard")
async def get_leaderboard(
    leaderboard_type: str = Query("weekly_xp", description="Type of leaderboard"),
    limit: int = Query(50, ge=10, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get leaderboard.

    Types:
    - weekly_xp: Weekly XP earned
    - monthly_xp: Monthly XP earned
    - alltime_level: All-time levels
    - weekly_points: Weekly points earned

    Privacy-aware: Users can opt-out in settings.
    """
    # TODO: Implement leaderboard fetching
    return {
        'leaderboard_type': leaderboard_type,
        'entries': [],
        'user_rank': None,
        'user_score': 0,
        'total_participants': 0
    }


@router.get("/challenges/daily")
async def get_daily_challenges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get today's daily challenges.

    Returns personalized challenges based on:
    - User level
    - Past completion rate
    - Current goals
    """
    # TODO: Implement daily challenge fetching
    return {
        'date': datetime.now().date().isoformat(),
        'challenges': [],
        'total_available': 0,
        'completed_today': 0
    }


@router.post("/challenges/{challenge_id}/complete")
async def complete_challenge(
    challenge_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a daily challenge as completed.

    Awards:
    - XP
    - Points
    - Potential achievement progress
    """
    # TODO: Implement challenge completion
    return {
        'success': True,
        'challenge_id': challenge_id,
        'xp_earned': 50,
        'points_earned': 10,
        'achievements_unlocked': []
    }


@router.get("/points/history")
async def get_points_history(
    limit: int = Query(50, ge=10, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get point transaction history.
    """
    # TODO: Implement point history
    return {
        'transactions': [],
        'current_balance': 0,
        'lifetime_points': 0
    }
