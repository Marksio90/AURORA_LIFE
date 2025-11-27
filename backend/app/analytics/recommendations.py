"""
Recommendation Engine

Generates personalized recommendations based on user data and ML predictions.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
import logging

from app.models.life_event import LifeEvent
from app.models.gamification import UserProfile
from app.analytics.schemas import (
    Recommendation, RecommendationBase,
    ActivityRecommendation, SleepRecommendation,
    ExerciseRecommendation, SocialRecommendation,
    RecommendationType, InsightPriority,
)
from app.analytics.engine import AnalyticsEngine
from app.analytics.trends import TrendAnalyzer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates personalized recommendations"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = AnalyticsEngine(db)
        self.trend_analyzer = TrendAnalyzer(db)

    def generate_recommendations(
        self,
        user_id: str,
        types: Optional[List[RecommendationType]] = None,
        limit: int = 5,
        personalization_level: str = "high",
    ) -> List[Recommendation]:
        """
        Generate personalized recommendations.

        Args:
            user_id: User ID
            types: Filter by recommendation types (None = all)
            limit: Maximum recommendations
            personalization_level: low/medium/high

        Returns:
            List of Recommendation objects
        """
        logger.info(f"Generating recommendations for user {user_id}")

        recommendations = []

        # Generate different types of recommendations
        if not types or RecommendationType.SLEEP in types:
            recommendations.extend(self._generate_sleep_recommendations(user_id))

        if not types or RecommendationType.EXERCISE in types:
            recommendations.extend(self._generate_exercise_recommendations(user_id))

        if not types or RecommendationType.ACTIVITY in types:
            recommendations.extend(self._generate_activity_recommendations(user_id))

        if not types or RecommendationType.SOCIAL in types:
            recommendations.extend(self._generate_social_recommendations(user_id))

        if not types or RecommendationType.HABIT in types:
            recommendations.extend(self._generate_habit_recommendations(user_id))

        # Sort by priority
        priority_order = {
            InsightPriority.LOW: 0,
            InsightPriority.MEDIUM: 1,
            InsightPriority.HIGH: 2,
            InsightPriority.URGENT: 3,
        }

        recommendations.sort(
            key=lambda x: priority_order[x.recommendation_data.priority],
            reverse=True
        )

        # Limit
        recommendations = recommendations[:limit]

        return recommendations

    def _generate_sleep_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate sleep recommendations"""
        recommendations = []

        # Get sleep data
        start_date = datetime.utcnow() - timedelta(days=14)

        sleep_events = self.db.query(LifeEvent).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'sleep',
                LifeEvent.start_time >= start_date,
            )
        ).all()

        if len(sleep_events) < 5:
            return recommendations

        # Calculate average duration
        avg_duration = np.mean([e.duration_minutes for e in sleep_events])
        avg_hours = avg_duration / 60

        # Recommendation: Increase sleep if below 7h
        if avg_hours < 7:
            deficit_hours = 7 - avg_hours

            rec_data = SleepRecommendation(
                type=RecommendationType.SLEEP,
                title="Improve Sleep Duration",
                description=f"You're averaging {avg_hours:.1f}h of sleep per night",
                rationale=f"Recommended sleep is 7-9 hours. You need {deficit_hours:.1f}h more per night.",
                expected_impact="Better energy, mood, and cognitive function",
                difficulty="medium",
                estimated_time_minutes=int(deficit_hours * 60),
                priority=InsightPriority.HIGH,
                suggested_duration_hours=7.5,
                sleep_hygiene_tips=[
                    f"Set bedtime {int(deficit_hours * 60)} minutes earlier",
                    "Avoid screens 1 hour before bed",
                    "Keep bedroom cool (60-67°F / 15-19°C)",
                    "Use blackout curtains or eye mask",
                ],
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        # Recommendation: Consistent bedtime
        bedtimes = [e.start_time.hour + e.start_time.minute / 60 for e in sleep_events]
        bedtime_std = np.std(bedtimes)

        if bedtime_std > 1.5:  # Inconsistent
            avg_bedtime = np.mean(bedtimes)
            hour = int(avg_bedtime)
            minute = int((avg_bedtime - hour) * 60)

            rec_data = SleepRecommendation(
                type=RecommendationType.SLEEP,
                title="Establish Consistent Bedtime",
                description="Your bedtime varies significantly",
                rationale="Consistent sleep schedule improves sleep quality",
                expected_impact="Better sleep quality and easier wake-ups",
                difficulty="easy",
                priority=InsightPriority.MEDIUM,
                suggested_bedtime=f"{hour:02d}:{minute:02d}",
                sleep_hygiene_tips=[
                    f"Try going to bed around {hour:02d}:{minute:02d} every night",
                    "Set a bedtime alarm reminder",
                    "Create a relaxing pre-bed routine",
                ],
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        return recommendations

    def _generate_exercise_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate exercise recommendations"""
        recommendations = []

        # Get exercise data
        start_date = datetime.utcnow() - timedelta(days=7)

        exercise_count = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_date,
            )
        ).scalar()

        total_minutes = self.db.query(
            func.sum(LifeEvent.duration_minutes)
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_date,
            )
        ).scalar() or 0

        # Recommendation: Increase frequency if < 3/week
        if exercise_count < 3:
            rec_data = ExerciseRecommendation(
                type=RecommendationType.EXERCISE,
                title="Increase Exercise Frequency",
                description=f"Only {exercise_count} workout(s) this week",
                rationale="Aim for at least 3-4 workouts per week for health benefits",
                expected_impact="Improved cardiovascular health, energy, and mood",
                difficulty="medium",
                estimated_time_minutes=120,  # 2 hours/week
                priority=InsightPriority.HIGH,
                exercise_type="moderate cardio or strength training",
                intensity="moderate",
                frequency_per_week=4,
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        # Recommendation: Increase duration if < 150 min/week
        elif total_minutes < 150:
            deficit = 150 - total_minutes

            rec_data = ExerciseRecommendation(
                type=RecommendationType.EXERCISE,
                title="Increase Exercise Duration",
                description=f"You've exercised {total_minutes:.0f} min this week",
                rationale="WHO recommends 150+ minutes of moderate activity per week",
                expected_impact="Meet health guidelines for physical activity",
                difficulty="medium",
                estimated_time_minutes=int(deficit),
                priority=InsightPriority.MEDIUM,
                exercise_type="any moderate-intensity activity",
                intensity="moderate",
                frequency_per_week=exercise_count,
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        # Recommendation: Try variety
        else:
            rec_data = ExerciseRecommendation(
                type=RecommendationType.EXERCISE,
                title="Add Exercise Variety",
                description="You're doing great with consistency!",
                rationale="Variety prevents plateaus and works different muscle groups",
                expected_impact="Better overall fitness and reduced injury risk",
                difficulty="easy",
                estimated_time_minutes=30,
                priority=InsightPriority.LOW,
                exercise_type="yoga, swimming, cycling, or HIIT",
                intensity="moderate",
                frequency_per_week=1,
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        return recommendations

    def _generate_activity_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate general activity recommendations"""
        recommendations = []

        # Get activity diversity
        start_date = datetime.utcnow() - timedelta(days=7)

        category_count = self.db.query(
            func.count(func.distinct(LifeEvent.category))
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_date,
            )
        ).scalar() or 0

        # Recommendation: Increase variety
        if category_count < 4:
            rec_data = ActivityRecommendation(
                type=RecommendationType.ACTIVITY,
                title="Diversify Your Activities",
                description=f"You're only doing {category_count} different activity types",
                rationale="Variety improves overall wellbeing and prevents boredom",
                expected_impact="More balanced lifestyle and better engagement",
                difficulty="easy",
                estimated_time_minutes=30,
                priority=InsightPriority.MEDIUM,
                suggested_category="Try: hobbies, learning, or creative activities",
                suggested_duration_minutes=30,
                best_time_of_day="evening",
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        return recommendations

    def _generate_social_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate social recommendations"""
        recommendations = []

        # Get friend count (if social features implemented)
        # For now, general recommendation

        rec_data = SocialRecommendation(
            type=RecommendationType.SOCIAL,
            title="Schedule Social Time",
            description="Social connections are vital for wellbeing",
            rationale="Regular social interaction improves mood and reduces stress",
            expected_impact="Better mood, reduced loneliness, stronger relationships",
            difficulty="easy",
            estimated_time_minutes=60,
            priority=InsightPriority.MEDIUM,
            activity_type="Call a friend, coffee meetup, or group activity",
        )

        recommendations.append(
            Recommendation(user_id=user_id, recommendation_data=rec_data)
        )

        return recommendations

    def _generate_habit_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate habit-building recommendations"""
        recommendations = []

        # Get profile for streak data
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not profile:
            return recommendations

        # Recommendation: Build streak
        if profile.current_streak < 7:
            rec_data = RecommendationBase(
                type=RecommendationType.HABIT,
                title="Build Your Daily Streak",
                description=f"Current streak: {profile.current_streak} days",
                rationale="Consistent daily logging builds awareness and habits",
                expected_impact="Better self-awareness and habit formation",
                difficulty="easy",
                estimated_time_minutes=5,
                priority=InsightPriority.LOW,
            )

            recommendations.append(
                Recommendation(user_id=user_id, recommendation_data=rec_data)
            )

        return recommendations

    def personalize_recommendations(
        self,
        recommendations: List[Recommendation],
        user_id: str,
        level: str = "high",
    ) -> List[Recommendation]:
        """
        Personalize recommendations based on user history.

        Args:
            recommendations: Base recommendations
            user_id: User ID
            level: Personalization level (low/medium/high)

        Returns:
            Personalized recommendations
        """
        if level == "low":
            return recommendations

        # Get user preferences (implement when user preferences model exists)
        # For now, just return as-is

        return recommendations
