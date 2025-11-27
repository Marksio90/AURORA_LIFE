"""
Insight Generation System

Automatically generates actionable insights from user data.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
import logging

from app.models.life_event import LifeEvent
from app.models.gamification import UserProfile, UserAchievement
from app.analytics.schemas import (
    Insight, InsightBase, PatternInsight, AnomalyInsight,
    TrendInsight, InsightType, InsightPriority, MetricCategory,
    AnomalyDetection, TrendAnalysis, TrendDirection,
)
from app.analytics.engine import AnalyticsEngine

logger = logging.getLogger(__name__)


class InsightGenerator:
    """Generates insights from user data"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = AnalyticsEngine(db)

    def generate_insights(
        self,
        user_id: str,
        categories: Optional[List[MetricCategory]] = None,
        priority_threshold: InsightPriority = InsightPriority.LOW,
        limit: int = 10,
    ) -> List[Insight]:
        """
        Generate insights for a user.

        Args:
            user_id: User ID
            categories: Filter by categories (None = all)
            priority_threshold: Minimum priority level
            limit: Maximum number of insights

        Returns:
            List of Insight objects
        """
        logger.info(f"Generating insights for user {user_id}")

        insights = []

        # Generate different types of insights
        insights.extend(self._generate_pattern_insights(user_id))
        insights.extend(self._generate_sleep_insights(user_id))
        insights.extend(self._generate_exercise_insights(user_id))
        insights.extend(self._generate_energy_insights(user_id))
        insights.extend(self._generate_social_insights(user_id))
        insights.extend(self._generate_streak_insights(user_id))
        insights.extend(self._generate_milestone_insights(user_id))

        # Filter by category
        if categories:
            insights = [i for i in insights if i.insight_data.category in categories]

        # Filter by priority
        priority_order = {
            InsightPriority.LOW: 0,
            InsightPriority.MEDIUM: 1,
            InsightPriority.HIGH: 2,
            InsightPriority.URGENT: 3,
        }
        threshold_value = priority_order[priority_threshold]
        insights = [
            i for i in insights
            if priority_order[i.insight_data.priority] >= threshold_value
        ]

        # Sort by priority (highest first)
        insights.sort(
            key=lambda x: priority_order[x.insight_data.priority],
            reverse=True
        )

        # Limit
        insights = insights[:limit]

        return insights

    def _generate_pattern_insights(self, user_id: str) -> List[Insight]:
        """Generate pattern-based insights"""
        insights = []

        # Pattern: Consistent bedtime
        bedtime_pattern = self._detect_bedtime_pattern(user_id)
        if bedtime_pattern:
            insights.append(bedtime_pattern)

        # Pattern: Weekend vs weekday activity
        weekend_pattern = self._detect_weekend_pattern(user_id)
        if weekend_pattern:
            insights.append(weekend_pattern)

        # Pattern: Peak energy hours
        energy_pattern = self._detect_energy_pattern(user_id)
        if energy_pattern:
            insights.append(energy_pattern)

        return insights

    def _detect_bedtime_pattern(self, user_id: str) -> Optional[Insight]:
        """Detect bedtime consistency pattern"""
        start_date = datetime.utcnow() - timedelta(days=14)

        # Get sleep events
        sleep_events = self.db.query(LifeEvent).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'sleep',
                LifeEvent.start_time >= start_date,
            )
        ).all()

        if len(sleep_events) < 5:
            return None

        # Extract bedtimes (hour of day)
        bedtimes = [
            event.start_time.hour + event.start_time.minute / 60
            for event in sleep_events
        ]

        # Calculate standard deviation
        std = np.std(bedtimes)

        # Consistent if std < 1 hour
        if std < 1.0:
            avg_bedtime = np.mean(bedtimes)
            hour = int(avg_bedtime)
            minute = int((avg_bedtime - hour) * 60)

            insight_data = PatternInsight(
                type=InsightType.PATTERN,
                priority=InsightPriority.LOW,
                title="Consistent Sleep Schedule",
                description=f"You have a consistent bedtime around {hour:02d}:{minute:02d}",
                category=MetricCategory.SLEEP,
                pattern_type="bedtime_consistency",
                frequency="daily",
                confidence=min(1.0, 1.0 - std),
                actionable=True,
                action_items=[
                    "Keep maintaining this consistent sleep schedule",
                    "Your body appreciates the routine!",
                ],
            )

            return Insight(
                user_id=user_id,
                insight_data=insight_data,
            )

        return None

    def _detect_weekend_pattern(self, user_id: str) -> Optional[Insight]:
        """Detect weekend vs weekday pattern"""
        start_date = datetime.utcnow() - timedelta(days=30)

        # Get exercise distribution by day of week
        pattern = self.engine.get_weekly_pattern(
            user_id=user_id,
            metric_name='exercise_duration',
            weeks=4,
        )

        if not pattern:
            return None

        # Calculate weekend vs weekday average
        weekday_avg = np.mean([pattern.get(i, 0) for i in range(5)])  # Mon-Fri
        weekend_avg = np.mean([pattern.get(i, 0) for i in [5, 6]])    # Sat-Sun

        # Significant difference?
        if weekend_avg > weekday_avg * 1.5:
            insight_data = PatternInsight(
                type=InsightType.PATTERN,
                priority=InsightPriority.MEDIUM,
                title="Weekend Warrior",
                description=f"You exercise {weekend_avg:.0f} min on weekends vs {weekday_avg:.0f} min on weekdays",
                category=MetricCategory.PHYSICAL,
                pattern_type="weekend_vs_weekday",
                frequency="weekly",
                confidence=0.85,
                actionable=True,
                action_items=[
                    "Try adding 1-2 short weekday workouts",
                    "Even 15-20 minutes can make a difference",
                    "Consistency > intensity for long-term health",
                ],
            )

            return Insight(
                user_id=user_id,
                insight_data=insight_data,
            )

        return None

    def _detect_energy_pattern(self, user_id: str) -> Optional[Insight]:
        """Detect peak energy hours"""
        # Get hourly energy distribution
        distribution = self.engine.get_hourly_distribution(
            user_id=user_id,
            category=None,  # All activities
            days=30,
        )

        if not distribution:
            return None

        # Find peak energy hours (assuming higher activity = higher energy)
        sorted_hours = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        peak_hours = sorted_hours[:3]  # Top 3 hours

        if peak_hours:
            hours_str = ", ".join([f"{h:02d}:00" for h, _ in peak_hours])

            insight_data = PatternInsight(
                type=InsightType.PATTERN,
                priority=InsightPriority.MEDIUM,
                title="Peak Productivity Hours",
                description=f"Your most active hours are: {hours_str}",
                category=MetricCategory.PRODUCTIVITY,
                pattern_type="peak_hours",
                frequency="daily",
                confidence=0.8,
                actionable=True,
                action_items=[
                    "Schedule important tasks during these hours",
                    "Protect this time from distractions",
                    "Use other hours for less demanding activities",
                ],
            )

            return Insight(
                user_id=user_id,
                insight_data=insight_data,
            )

        return None

    def _generate_sleep_insights(self, user_id: str) -> List[Insight]:
        """Generate sleep-related insights"""
        insights = []

        # Get sleep data for last 14 days
        start_date = datetime.utcnow() - timedelta(days=14)

        sleep_events = self.db.query(LifeEvent).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'sleep',
                LifeEvent.start_time >= start_date,
            )
        ).all()

        if len(sleep_events) < 5:
            return insights

        # Calculate average sleep duration
        avg_duration = np.mean([e.duration_minutes for e in sleep_events])
        avg_hours = avg_duration / 60

        # Sleep debt insight
        if avg_hours < 7:
            deficit = 7 - avg_hours
            insight_data = InsightBase(
                type=InsightType.WARNING,
                priority=InsightPriority.HIGH,
                title="Sleep Deficit Detected",
                description=f"You're averaging {avg_hours:.1f}h of sleep, {deficit:.1f}h below recommended",
                category=MetricCategory.SLEEP,
                actionable=True,
                action_items=[
                    f"Try going to bed {int(deficit * 60)} minutes earlier",
                    "Aim for 7-9 hours of sleep per night",
                    "Consider a consistent bedtime routine",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        # Excellent sleep insight
        elif avg_hours >= 7.5 and avg_hours <= 9:
            insight_data = InsightBase(
                type=InsightType.ACHIEVEMENT,
                priority=InsightPriority.LOW,
                title="Excellent Sleep Duration",
                description=f"You're averaging {avg_hours:.1f}h of sleep - perfect!",
                category=MetricCategory.SLEEP,
                actionable=False,
                action_items=[
                    "Keep up the great sleep habits!",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        return insights

    def _generate_exercise_insights(self, user_id: str) -> List[Insight]:
        """Generate exercise-related insights"""
        insights = []

        # Get exercise count for last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)

        exercise_count = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_date,
            )
        ).scalar()

        # Low exercise warning
        if exercise_count < 2:
            insight_data = InsightBase(
                type=InsightType.SUGGESTION,
                priority=InsightPriority.MEDIUM,
                title="Low Exercise Activity",
                description=f"Only {exercise_count} workout(s) this week",
                category=MetricCategory.PHYSICAL,
                actionable=True,
                action_items=[
                    "Aim for at least 3-4 workouts per week",
                    "Start with 20-30 minute sessions",
                    "Try activities you enjoy to stay consistent",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        # Exercise streak
        elif exercise_count >= 5:
            insight_data = InsightBase(
                type=InsightType.ACHIEVEMENT,
                priority=InsightPriority.LOW,
                title="Consistent Exercise Habit",
                description=f"{exercise_count} workouts this week - amazing!",
                category=MetricCategory.PHYSICAL,
                actionable=False,
                action_items=[
                    "You're building a strong exercise habit!",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        return insights

    def _generate_energy_insights(self, user_id: str) -> List[Insight]:
        """Generate energy-related insights"""
        insights = []

        # Get energy trends
        start_date = datetime.utcnow() - timedelta(days=14)

        ts = self.engine.get_time_series(
            user_id=user_id,
            metric_name='energy_level',
            start_date=start_date,
            end_date=datetime.utcnow(),
        )

        if not ts.statistics:
            return insights

        avg_energy = ts.statistics.get('mean', 0)

        # Low energy warning
        if avg_energy < 5:
            insight_data = InsightBase(
                type=InsightType.WARNING,
                priority=InsightPriority.HIGH,
                title="Low Energy Levels",
                description=f"Your average energy is {avg_energy:.1f}/10",
                category=MetricCategory.MENTAL,
                actionable=True,
                action_items=[
                    "Check your sleep quality and duration",
                    "Ensure adequate hydration and nutrition",
                    "Consider taking short breaks throughout the day",
                    "Try light exercise to boost energy",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        return insights

    def _generate_social_insights(self, user_id: str) -> List[Insight]:
        """Generate social-related insights"""
        insights = []

        # Social activity check (implement when social features are ready)
        # For now, return empty
        return insights

    def _generate_streak_insights(self, user_id: str) -> List[Insight]:
        """Generate streak-related insights"""
        insights = []

        # Get user profile for streak data
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            return insights

        # Current streak milestone
        if profile.current_streak >= 30:
            insight_data = InsightBase(
                type=InsightType.MILESTONE,
                priority=InsightPriority.MEDIUM,
                title=f"{profile.current_streak}-Day Streak!",
                description=f"You've logged activities for {profile.current_streak} consecutive days",
                category=MetricCategory.ACTIVITY,
                actionable=False,
                action_items=[
                    "Keep the momentum going!",
                    f"Next milestone: {((profile.current_streak // 10) + 1) * 10} days",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        return insights

    def _generate_milestone_insights(self, user_id: str) -> List[Insight]:
        """Generate milestone-related insights"""
        insights = []

        # Recent achievements
        recent_achievements = self.db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.unlocked_at >= datetime.utcnow() - timedelta(days=7),
            )
        ).all()

        if recent_achievements:
            count = len(recent_achievements)
            insight_data = InsightBase(
                type=InsightType.ACHIEVEMENT,
                priority=InsightPriority.LOW,
                title=f"{count} Achievement(s) Unlocked!",
                description=f"You've unlocked {count} achievement(s) this week",
                category=MetricCategory.ACTIVITY,
                actionable=False,
                action_items=[
                    "Check your profile to see all achievements",
                ],
            )
            insights.append(Insight(user_id=user_id, insight_data=insight_data))

        return insights
