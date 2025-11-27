"""
Analytics Engine

Core analytics engine for computing metrics, statistics, and aggregations.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from collections import defaultdict
import logging

from app.models.life_event import LifeEvent
from app.models.user import User
from app.models.gamification import UserProfile
from app.analytics.schemas import (
    TimeSeries, TimeSeriesDataPoint, TimeGranularity,
    MetricCategory, AnalyticsQuery, AnalyticsResponse,
)

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Core analytics engine"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== TIME SERIES ====================

    def get_time_series(
        self,
        user_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity = TimeGranularity.DAILY,
    ) -> TimeSeries:
        """
        Get time series data for a metric.

        Args:
            user_id: User ID
            metric_name: Metric name (e.g., 'energy_level', 'mood_level', 'sleep_duration')
            start_date: Start date
            end_date: End date
            granularity: Time granularity

        Returns:
            TimeSeries object with data points
        """
        logger.info(f"Getting time series: {metric_name} for user {user_id}")

        # Determine category from metric name
        category = self._get_metric_category(metric_name)

        # Get data based on metric
        if metric_name in ['energy_level', 'mood_level']:
            data_points = self._get_level_time_series(
                user_id, metric_name, start_date, end_date, granularity
            )
        elif metric_name.endswith('_duration'):
            data_points = self._get_duration_time_series(
                user_id, metric_name, start_date, end_date, granularity
            )
        elif metric_name.endswith('_count'):
            data_points = self._get_count_time_series(
                user_id, metric_name, start_date, end_date, granularity
            )
        else:
            # Generic metric
            data_points = self._get_generic_time_series(
                user_id, metric_name, start_date, end_date, granularity
            )

        # Calculate statistics
        values = [dp.value for dp in data_points]
        statistics = self._calculate_statistics(values) if values else {}

        return TimeSeries(
            metric_name=metric_name,
            category=category,
            granularity=granularity,
            data_points=data_points,
            start_date=start_date,
            end_date=end_date,
            statistics=statistics,
        )

    def _get_level_time_series(
        self,
        user_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity,
    ) -> List[TimeSeriesDataPoint]:
        """Get time series for level metrics (energy, mood)"""

        field = getattr(LifeEvent, metric_name, None)
        if not field:
            return []

        # Query based on granularity
        if granularity == TimeGranularity.HOURLY:
            # Group by hour
            query = self.db.query(
                func.date_trunc('hour', LifeEvent.start_time).label('timestamp'),
                func.avg(field).label('value'),
            ).filter(
                and_(
                    LifeEvent.user_id == user_id,
                    LifeEvent.start_time >= start_date,
                    LifeEvent.start_time <= end_date,
                    field.isnot(None),
                )
            ).group_by('timestamp').order_by('timestamp')

        elif granularity == TimeGranularity.DAILY:
            # Group by day
            query = self.db.query(
                func.date_trunc('day', LifeEvent.start_time).label('timestamp'),
                func.avg(field).label('value'),
            ).filter(
                and_(
                    LifeEvent.user_id == user_id,
                    LifeEvent.start_time >= start_date,
                    LifeEvent.start_time <= end_date,
                    field.isnot(None),
                )
            ).group_by('timestamp').order_by('timestamp')

        elif granularity == TimeGranularity.WEEKLY:
            # Group by week
            query = self.db.query(
                func.date_trunc('week', LifeEvent.start_time).label('timestamp'),
                func.avg(field).label('value'),
            ).filter(
                and_(
                    LifeEvent.user_id == user_id,
                    LifeEvent.start_time >= start_date,
                    LifeEvent.start_time <= end_date,
                    field.isnot(None),
                )
            ).group_by('timestamp').order_by('timestamp')

        else:  # MONTHLY
            query = self.db.query(
                func.date_trunc('month', LifeEvent.start_time).label('timestamp'),
                func.avg(field).label('value'),
            ).filter(
                and_(
                    LifeEvent.user_id == user_id,
                    LifeEvent.start_time >= start_date,
                    LifeEvent.start_time <= end_date,
                    field.isnot(None),
                )
            ).group_by('timestamp').order_by('timestamp')

        results = query.all()

        return [
            TimeSeriesDataPoint(
                timestamp=row.timestamp,
                value=float(row.value),
            )
            for row in results
        ]

    def _get_duration_time_series(
        self,
        user_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity,
    ) -> List[TimeSeriesDataPoint]:
        """Get time series for duration metrics"""

        # Extract category from metric name (e.g., 'sleep_duration' -> 'sleep')
        category = metric_name.replace('_duration', '')

        # Group by time period
        if granularity == TimeGranularity.DAILY:
            truncate = 'day'
        elif granularity == TimeGranularity.WEEKLY:
            truncate = 'week'
        elif granularity == TimeGranularity.MONTHLY:
            truncate = 'month'
        else:
            truncate = 'day'

        query = self.db.query(
            func.date_trunc(truncate, LifeEvent.start_time).label('timestamp'),
            func.sum(LifeEvent.duration_minutes).label('value'),
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == category,
                LifeEvent.start_time >= start_date,
                LifeEvent.start_time <= end_date,
            )
        ).group_by('timestamp').order_by('timestamp')

        results = query.all()

        return [
            TimeSeriesDataPoint(
                timestamp=row.timestamp,
                value=float(row.value or 0),
            )
            for row in results
        ]

    def _get_count_time_series(
        self,
        user_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity,
    ) -> List[TimeSeriesDataPoint]:
        """Get time series for count metrics"""

        # Extract category from metric name (e.g., 'exercise_count' -> 'exercise')
        category = metric_name.replace('_count', '')

        # Group by time period
        if granularity == TimeGranularity.DAILY:
            truncate = 'day'
        elif granularity == TimeGranularity.WEEKLY:
            truncate = 'week'
        elif granularity == TimeGranularity.MONTHLY:
            truncate = 'month'
        else:
            truncate = 'day'

        query = self.db.query(
            func.date_trunc(truncate, LifeEvent.start_time).label('timestamp'),
            func.count(LifeEvent.id).label('value'),
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.category == category,
                LifeEvent.start_time >= start_date,
                LifeEvent.start_time <= end_date,
            )
        ).group_by('timestamp').order_by('timestamp')

        results = query.all()

        return [
            TimeSeriesDataPoint(
                timestamp=row.timestamp,
                value=float(row.value),
            )
            for row in results
        ]

    def _get_generic_time_series(
        self,
        user_id: str,
        metric_name: str,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity,
    ) -> List[TimeSeriesDataPoint]:
        """Get generic time series (fallback)"""
        # Return empty for now - can be extended
        return []

    # ==================== STATISTICS ====================

    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical measures"""
        if not values:
            return {}

        arr = np.array(values)

        return {
            'count': len(values),
            'mean': float(np.mean(arr)),
            'median': float(np.median(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'q25': float(np.percentile(arr, 25)),
            'q75': float(np.percentile(arr, 75)),
        }

    def get_summary_statistics(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get summary statistics for all key metrics.

        Returns:
            Dict mapping metric names to their statistics
        """
        logger.info(f"Calculating summary statistics for user {user_id}")

        metrics = [
            'energy_level',
            'mood_level',
            'sleep_duration',
            'exercise_duration',
            'exercise_count',
        ]

        statistics = {}

        for metric in metrics:
            ts = self.get_time_series(
                user_id=user_id,
                metric_name=metric,
                start_date=start_date,
                end_date=end_date,
                granularity=TimeGranularity.DAILY,
            )

            if ts.statistics:
                statistics[metric] = ts.statistics

        return statistics

    # ==================== AGGREGATIONS ====================

    def get_category_breakdown(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, float]:
        """
        Get time spent in each category.

        Returns:
            Dict mapping categories to total minutes
        """
        query = self.db.query(
            LifeEvent.category,
            func.sum(LifeEvent.duration_minutes).label('total_minutes'),
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_date,
                LifeEvent.start_time <= end_date,
            )
        ).group_by(LifeEvent.category)

        results = query.all()

        return {
            row.category: float(row.total_minutes or 0)
            for row in results
        }

    def get_hourly_distribution(
        self,
        user_id: str,
        category: Optional[str] = None,
        days: int = 30,
    ) -> Dict[int, float]:
        """
        Get distribution of activities by hour of day.

        Returns:
            Dict mapping hour (0-23) to average minutes
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(
            func.extract('hour', LifeEvent.start_time).label('hour'),
            func.avg(LifeEvent.duration_minutes).label('avg_minutes'),
        ).filter(
            and_(
                LifeEvent.user_id == user_id,
                LifeEvent.start_time >= start_date,
            )
        )

        if category:
            query = query.filter(LifeEvent.category == category)

        query = query.group_by('hour').order_by('hour')

        results = query.all()

        return {
            int(row.hour): float(row.avg_minutes or 0)
            for row in results
        }

    def get_weekly_pattern(
        self,
        user_id: str,
        metric_name: str,
        weeks: int = 4,
    ) -> Dict[int, float]:
        """
        Get weekly pattern (Mon-Sun averages).

        Returns:
            Dict mapping day of week (0=Mon, 6=Sun) to average value
        """
        start_date = datetime.utcnow() - timedelta(weeks=weeks)

        # Get data for metric
        ts = self.get_time_series(
            user_id=user_id,
            metric_name=metric_name,
            start_date=start_date,
            end_date=datetime.utcnow(),
            granularity=TimeGranularity.DAILY,
        )

        # Group by day of week
        dow_values = defaultdict(list)

        for dp in ts.data_points:
            dow = dp.timestamp.weekday()  # 0=Mon, 6=Sun
            dow_values[dow].append(dp.value)

        # Average for each day
        return {
            dow: float(np.mean(values))
            for dow, values in dow_values.items()
        }

    # ==================== COMPARISONS ====================

    def compare_periods(
        self,
        user_id: str,
        metric_name: str,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime,
    ) -> Dict[str, Any]:
        """
        Compare two time periods.

        Returns:
            Comparison metrics (change, percentage, etc.)
        """
        # Get data for both periods
        ts1 = self.get_time_series(
            user_id, metric_name, period1_start, period1_end
        )
        ts2 = self.get_time_series(
            user_id, metric_name, period2_start, period2_end
        )

        if not ts1.statistics or not ts2.statistics:
            return {}

        mean1 = ts1.statistics.get('mean', 0)
        mean2 = ts2.statistics.get('mean', 0)

        change = mean2 - mean1
        percent_change = (change / mean1 * 100) if mean1 != 0 else 0

        return {
            'period1_mean': mean1,
            'period2_mean': mean2,
            'absolute_change': change,
            'percent_change': percent_change,
            'improved': change > 0,  # Assuming higher is better
            'period1_stats': ts1.statistics,
            'period2_stats': ts2.statistics,
        }

    # ==================== UTILITY ====================

    def _get_metric_category(self, metric_name: str) -> MetricCategory:
        """Determine category from metric name"""
        if 'sleep' in metric_name:
            return MetricCategory.SLEEP
        elif 'exercise' in metric_name or 'workout' in metric_name:
            return MetricCategory.PHYSICAL
        elif 'energy' in metric_name or 'mood' in metric_name:
            return MetricCategory.MENTAL
        elif 'social' in metric_name or 'friend' in metric_name:
            return MetricCategory.SOCIAL
        elif 'activity' in metric_name:
            return MetricCategory.ACTIVITY
        else:
            return MetricCategory.WELLBEING

    def execute_query(self, query: AnalyticsQuery) -> AnalyticsResponse:
        """
        Execute full analytics query.

        Args:
            query: AnalyticsQuery object

        Returns:
            AnalyticsResponse with all requested data
        """
        logger.info(f"Executing analytics query for user {query.user_id}")

        # Get time series for all metrics
        time_series = []
        for metric in query.metrics:
            ts = self.get_time_series(
                user_id=str(query.user_id),
                metric_name=metric,
                start_date=query.start_date,
                end_date=query.end_date,
                granularity=query.granularity,
            )
            time_series.append(ts)

        # Get summary statistics
        summary_stats = {}
        for ts in time_series:
            if ts.statistics:
                summary_stats[ts.metric_name] = ts.statistics

        response = AnalyticsResponse(
            query=query,
            time_series=time_series,
            summary_statistics=summary_stats,
        )

        # Optional: Add trends, correlations, anomalies
        # (These will be implemented in separate modules)

        return response
