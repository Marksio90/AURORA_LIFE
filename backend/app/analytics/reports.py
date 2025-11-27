"""
Report Generation System

Generates comprehensive wellness and progress reports.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import numpy as np
import logging

from app.models.life_event import LifeEvent
from app.models.gamification import UserProfile, UserAchievement, Goal
from app.analytics.schemas import (
    WellnessReport, ProgressReport, ReportSection,
    Insight, Recommendation, TrendAnalysis,
)
from app.analytics.engine import AnalyticsEngine
from app.analytics.insights import InsightGenerator
from app.analytics.recommendations import RecommendationEngine
from app.analytics.trends import TrendAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive reports"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = AnalyticsEngine(db)
        self.insight_generator = InsightGenerator(db)
        self.recommendation_engine = RecommendationEngine(db)
        self.trend_analyzer = TrendAnalyzer(db)

    def generate_wellness_report(
        self,
        user_id: str,
        period_start: date,
        period_end: date,
    ) -> WellnessReport:
        """
        Generate comprehensive wellness report.

        Args:
            user_id: User ID
            period_start: Report period start date
            period_end: Report period end date

        Returns:
            WellnessReport object
        """
        logger.info(f"Generating wellness report for user {user_id}")

        # Convert dates to datetime
        start_dt = datetime.combine(period_start, datetime.min.time())
        end_dt = datetime.combine(period_end, datetime.max.time())

        # Calculate category scores
        sleep_score = self._calculate_sleep_score(user_id, start_dt, end_dt)
        activity_score = self._calculate_activity_score(user_id, start_dt, end_dt)
        exercise_score = self._calculate_exercise_score(user_id, start_dt, end_dt)
        social_score = self._calculate_social_score(user_id, start_dt, end_dt)
        mental_score = self._calculate_mental_wellbeing_score(user_id, start_dt, end_dt)

        # Calculate overall score (weighted average)
        overall_score = (
            sleep_score * 0.25 +
            activity_score * 0.20 +
            exercise_score * 0.20 +
            social_score * 0.15 +
            mental_score * 0.20
        )

        # Generate sections
        sections = self._generate_report_sections(
            user_id, start_dt, end_dt,
            sleep_score, activity_score, exercise_score, social_score, mental_score
        )

        # Get key metrics
        key_metrics = self._get_key_metrics(user_id, start_dt, end_dt)

        # Get insights and recommendations
        insights = self.insight_generator.generate_insights(
            user_id=user_id,
            limit=5,
        )

        recommendations = self.recommendation_engine.generate_recommendations(
            user_id=user_id,
            limit=5,
        )

        # Get trends
        metrics_to_analyze = ['energy_level', 'mood_level', 'sleep_duration']
        trends = self.trend_analyzer.analyze_multiple_trends(
            user_id=user_id,
            metric_names=metrics_to_analyze,
            days=(period_end - period_start).days,
        )

        return WellnessReport(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            overall_score=overall_score,
            sleep_score=sleep_score,
            activity_score=activity_score,
            exercise_score=exercise_score,
            social_score=social_score,
            mental_wellbeing_score=mental_score,
            sections=sections,
            key_metrics=key_metrics,
            top_insights=insights,
            top_recommendations=recommendations,
            trends=trends,
        )

    def _calculate_sleep_score(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate sleep score (0-100)"""

        sleep_events = self.db.query(LifeEvent).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'sleep',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).all()

        if not sleep_events:
            return 50.0  # Default score

        # Average duration
        avg_duration = np.mean([e.duration_minutes for e in sleep_events])
        avg_hours = avg_duration / 60

        # Score based on 7-9 hours being optimal
        if 7 <= avg_hours <= 9:
            duration_score = 100
        elif 6 <= avg_hours < 7:
            duration_score = 80
        elif 5 <= avg_hours < 6:
            duration_score = 60
        else:
            duration_score = 40

        # Consistency score
        bedtimes = [e.start_time.hour + e.start_time.minute / 60 for e in sleep_events]
        consistency_std = np.std(bedtimes)

        if consistency_std < 0.5:
            consistency_score = 100
        elif consistency_std < 1:
            consistency_score = 80
        elif consistency_std < 2:
            consistency_score = 60
        else:
            consistency_score = 40

        # Combined score (70% duration, 30% consistency)
        score = duration_score * 0.7 + consistency_score * 0.3

        return min(100, max(0, score))

    def _calculate_activity_score(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate activity score (0-100)"""

        # Get activity count
        activity_count = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        # Get activity diversity
        category_count = self.db.query(
            func.count(func.distinct(LifeEvent.category))
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        # Get total time
        total_minutes = self.db.query(
            func.sum(LifeEvent.duration_minutes)
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        days = (end_dt - start_dt).days + 1

        # Score components
        count_score = min(100, (activity_count / days) * 20)  # 5 per day = 100
        diversity_score = min(100, category_count * 20)  # 5 categories = 100
        time_score = min(100, (total_minutes / days / 300) * 100)  # 5h/day = 100

        # Combined score
        score = (count_score * 0.4 + diversity_score * 0.3 + time_score * 0.3)

        return min(100, max(0, score))

    def _calculate_exercise_score(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate exercise score (0-100)"""

        exercise_count = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        exercise_minutes = self.db.query(
            func.sum(LifeEvent.duration_minutes)
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        days = (end_dt - start_dt).days + 1

        # Frequency score (3-5 times per week optimal)
        sessions_per_week = (exercise_count / days) * 7
        if 3 <= sessions_per_week <= 5:
            frequency_score = 100
        elif 2 <= sessions_per_week < 3:
            frequency_score = 70
        elif 1 <= sessions_per_week < 2:
            frequency_score = 50
        else:
            frequency_score = 30

        # Duration score (150+ min per week optimal)
        minutes_per_week = (exercise_minutes / days) * 7
        duration_score = min(100, (minutes_per_week / 150) * 100)

        # Combined score
        score = frequency_score * 0.5 + duration_score * 0.5

        return min(100, max(0, score))

    def _calculate_social_score(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate social score (0-100)"""

        # Get social activities
        social_count = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'social',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        days = (end_dt - start_dt).days + 1

        # Score based on social activity frequency
        social_per_week = (social_count / days) * 7

        if social_per_week >= 3:
            score = 100
        elif social_per_week >= 2:
            score = 80
        elif social_per_week >= 1:
            score = 60
        else:
            score = 40

        return score

    def _calculate_mental_wellbeing_score(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
    ) -> float:
        """Calculate mental wellbeing score (0-100)"""

        # Get average mood and energy
        avg_mood = self.db.query(func.avg(LifeEvent.mood_level)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.mood_level.isnot(None),
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 7.0

        avg_energy = self.db.query(func.avg(LifeEvent.energy_level)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.energy_level.isnot(None),
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 7.0

        # Convert 1-10 scale to 0-100
        mood_score = (avg_mood / 10) * 100
        energy_score = (avg_energy / 10) * 100

        # Combined score
        score = (mood_score + energy_score) / 2

        return min(100, max(0, score))

    def _generate_report_sections(
        self,
        user_id: str,
        start_dt: datetime,
        end_dt: datetime,
        sleep_score: float,
        activity_score: float,
        exercise_score: float,
        social_score: float,
        mental_score: float,
    ) -> List[ReportSection]:
        """Generate report sections with content"""

        sections = []

        # Overview section
        sections.append(ReportSection(
            title="Overview",
            content=f"Your wellness score for this period is based on multiple factors including sleep quality, physical activity, exercise, social engagement, and mental wellbeing.",
            metrics={
                "sleep": sleep_score,
                "activity": activity_score,
                "exercise": exercise_score,
                "social": social_score,
                "mental_wellbeing": mental_score,
            },
            order=0,
        ))

        # Sleep section
        sections.append(ReportSection(
            title="Sleep",
            content=self._generate_sleep_content(user_id, start_dt, end_dt, sleep_score),
            metrics={"score": sleep_score},
            order=1,
        ))

        # Activity section
        sections.append(ReportSection(
            title="Activity",
            content=self._generate_activity_content(user_id, start_dt, end_dt, activity_score),
            metrics={"score": activity_score},
            order=2,
        ))

        # Exercise section
        sections.append(ReportSection(
            title="Exercise",
            content=self._generate_exercise_content(user_id, start_dt, end_dt, exercise_score),
            metrics={"score": exercise_score},
            order=3,
        ))

        return sections

    def _generate_sleep_content(
        self, user_id: str, start_dt: datetime, end_dt: datetime, score: float
    ) -> str:
        """Generate sleep section content"""

        sleep_events = self.db.query(LifeEvent).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'sleep',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).all()

        if not sleep_events:
            return "No sleep data recorded for this period."

        avg_duration = np.mean([e.duration_minutes for e in sleep_events])
        avg_hours = avg_duration / 60

        return f"You averaged {avg_hours:.1f} hours of sleep per night. " \
               f"Your sleep score is {score:.0f}/100. " \
               f"Optimal sleep duration is 7-9 hours."

    def _generate_activity_content(
        self, user_id: str, start_dt: datetime, end_dt: datetime, score: float
    ) -> str:
        """Generate activity section content"""

        total_events = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        return f"You logged {total_events} activities during this period. " \
               f"Your activity score is {score:.0f}/100. " \
               f"Keep tracking to build better habits!"

    def _generate_exercise_content(
        self, user_id: str, start_dt: datetime, end_dt: datetime, score: float
    ) -> str:
        """Generate exercise section content"""

        exercise_count = self.db.query(func.count(LifeEvent.id)).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        exercise_minutes = self.db.query(
            func.sum(LifeEvent.duration_minutes)
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == 'exercise',
                LifeEvent.start_time >= start_dt,
                LifeEvent.start_time <= end_dt,
            )
        ).scalar() or 0

        return f"You completed {exercise_count} workout(s) totaling {exercise_minutes:.0f} minutes. " \
               f"Your exercise score is {score:.0f}/100. " \
               f"WHO recommends 150+ minutes of moderate activity per week."

    def _get_key_metrics(
        self, user_id: str, start_dt: datetime, end_dt: datetime
    ) -> Dict[str, Any]:
        """Get key metrics for report"""

        stats = self.engine.get_summary_statistics(
            user_id=user_id,
            start_date=start_dt,
            end_date=end_dt,
        )

        return {
            "total_activities": self.db.query(func.count(LifeEvent.id)).filter(
                and_(
                    LifeEvent.user_id == user_id,
                    LifeEvent.start_time >= start_dt,
                    LifeEvent.start_time <= end_dt,
                )
            ).scalar() or 0,
            "summary_statistics": stats,
        }

    def generate_progress_report(
        self,
        user_id: str,
        period_start: date,
        period_end: date,
    ) -> ProgressReport:
        """
        Generate goal progress report.

        Args:
            user_id: User ID
            period_start: Report period start
            period_end: Report period end

        Returns:
            ProgressReport object
        """
        logger.info(f"Generating progress report for user {user_id}")

        # Get goals (assuming Goal model exists)
        # For now, use placeholder data

        # Get achievements
        achievements = self.db.query(UserAchievement).filter(
            and_(
                UserAchievement.user_id == user_id,
                UserAchievement.unlocked_at >= datetime.combine(period_start, datetime.min.time()),
                UserAchievement.unlocked_at <= datetime.combine(period_end, datetime.max.time()),
            )
        ).all()

        return ProgressReport(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            goals_completed=0,  # Placeholder
            goals_in_progress=0,  # Placeholder
            goals_at_risk=0,  # Placeholder
            completion_rate=0.0,  # Placeholder
            average_progress=0.0,  # Placeholder
            goal_details=[],  # Placeholder
            achievements_unlocked=[
                {
                    "id": str(ach.achievement_id),
                    "unlocked_at": ach.unlocked_at.isoformat(),
                }
                for ach in achievements
            ],
        )
