"""
Trend Analysis Module

Analyzes trends, forecasts, and correlations in user data.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np
from scipy import stats
from collections import defaultdict
import logging

from app.analytics.schemas import (
    TrendAnalysis, TrendDirection, CorrelationAnalysis,
    AnomalyDetection, InsightPriority, TimeSeries,
)
from app.analytics.engine import AnalyticsEngine

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes trends and patterns in time series data"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = AnalyticsEngine(db)

    def analyze_trend(
        self,
        user_id: str,
        metric_name: str,
        days: int = 30,
    ) -> Optional[TrendAnalysis]:
        """
        Analyze trend for a metric.

        Args:
            user_id: User ID
            metric_name: Metric to analyze
            days: Number of days to analyze

        Returns:
            TrendAnalysis object or None
        """
        logger.info(f"Analyzing trend for {metric_name} (user {user_id}, {days} days)")

        # Get time series data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        ts = self.engine.get_time_series(
            user_id=user_id,
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date,
        )

        if len(ts.data_points) < 5:
            logger.warning(f"Insufficient data for trend analysis ({len(ts.data_points)} points)")
            return None

        # Extract values and indices
        values = np.array([dp.value for dp in ts.data_points])
        indices = np.arange(len(values))

        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(indices, values)

        # Determine trend direction
        if abs(slope) < 0.01:  # Minimal slope
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN

        # Calculate trend strength (based on R² value)
        r_squared = r_value ** 2
        strength = min(1.0, r_squared)

        # Check for volatility
        volatility = np.std(values) / np.mean(values) if np.mean(values) > 0 else 0
        if volatility > 0.3:  # High volatility
            direction = TrendDirection.VOLATILE

        # Calculate change
        start_value = float(values[0])
        end_value = float(values[-1])
        change = end_value - start_value
        change_percentage = (change / start_value * 100) if start_value != 0 else 0

        # Confidence (p-value based)
        confidence = 1.0 - p_value if p_value < 1.0 else 0.0

        # Simple forecast (linear extrapolation for next 7 days)
        forecast_indices = np.arange(len(values), len(values) + 7)
        forecast = [float(slope * i + intercept) for i in forecast_indices]

        return TrendAnalysis(
            metric_name=metric_name,
            direction=direction,
            strength=strength,
            change_percentage=change_percentage,
            start_value=start_value,
            end_value=end_value,
            period_days=days,
            confidence=confidence,
            forecast=forecast,
        )

    def analyze_multiple_trends(
        self,
        user_id: str,
        metric_names: List[str],
        days: int = 30,
    ) -> List[TrendAnalysis]:
        """
        Analyze trends for multiple metrics.

        Returns:
            List of TrendAnalysis objects
        """
        trends = []

        for metric in metric_names:
            trend = self.analyze_trend(user_id, metric, days)
            if trend:
                trends.append(trend)

        return trends

    def detect_correlations(
        self,
        user_id: str,
        metric_pairs: List[Tuple[str, str]],
        days: int = 30,
    ) -> List[CorrelationAnalysis]:
        """
        Detect correlations between metric pairs.

        Args:
            user_id: User ID
            metric_pairs: List of (metric_a, metric_b) tuples
            days: Number of days to analyze

        Returns:
            List of CorrelationAnalysis objects
        """
        logger.info(f"Detecting correlations for {len(metric_pairs)} pairs")

        correlations = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        for metric_a, metric_b in metric_pairs:
            # Get time series for both metrics
            ts_a = self.engine.get_time_series(
                user_id, metric_a, start_date, end_date
            )
            ts_b = self.engine.get_time_series(
                user_id, metric_b, start_date, end_date
            )

            if len(ts_a.data_points) < 5 or len(ts_b.data_points) < 5:
                continue

            # Align timestamps (use only common timestamps)
            values_a = {dp.timestamp: dp.value for dp in ts_a.data_points}
            values_b = {dp.timestamp: dp.value for dp in ts_b.data_points}

            common_timestamps = set(values_a.keys()) & set(values_b.keys())

            if len(common_timestamps) < 5:
                continue

            # Extract aligned values
            aligned_a = [values_a[ts] for ts in sorted(common_timestamps)]
            aligned_b = [values_b[ts] for ts in sorted(common_timestamps)]

            # Calculate Pearson correlation
            corr_coef, p_value = stats.pearsonr(aligned_a, aligned_b)

            # Determine significance (p < 0.05)
            is_significant = p_value < 0.05

            # Interpret correlation
            if abs(corr_coef) < 0.3:
                interpretation = "weak"
            elif abs(corr_coef) < 0.7:
                interpretation = "moderate"
            else:
                interpretation = "strong"

            if corr_coef > 0:
                interpretation += " positive"
            else:
                interpretation += " negative"

            correlation = CorrelationAnalysis(
                metric_a=metric_a,
                metric_b=metric_b,
                correlation_coefficient=float(corr_coef),
                p_value=float(p_value),
                is_significant=is_significant,
                sample_size=len(common_timestamps),
                interpretation=interpretation,
            )

            correlations.append(correlation)

        return correlations

    def detect_anomalies(
        self,
        user_id: str,
        metric_name: str,
        days: int = 30,
        threshold: float = 2.0,
    ) -> List[AnomalyDetection]:
        """
        Detect anomalies using z-score method.

        Args:
            user_id: User ID
            metric_name: Metric to analyze
            days: Number of days to analyze
            threshold: Z-score threshold (default: 2.0 = ~95% confidence)

        Returns:
            List of AnomalyDetection objects
        """
        logger.info(f"Detecting anomalies for {metric_name}")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        ts = self.engine.get_time_series(
            user_id, metric_name, start_date, end_date
        )

        if len(ts.data_points) < 10:
            return []

        # Calculate mean and std
        values = np.array([dp.value for dp in ts.data_points])
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:  # No variation
            return []

        # Detect anomalies
        anomalies = []

        for dp in ts.data_points:
            z_score = abs((dp.value - mean) / std)

            if z_score > threshold:
                # Determine severity based on z-score
                if z_score > 3:
                    severity = InsightPriority.URGENT
                elif z_score > 2.5:
                    severity = InsightPriority.HIGH
                else:
                    severity = InsightPriority.MEDIUM

                anomaly = AnomalyDetection(
                    timestamp=dp.timestamp,
                    metric_name=metric_name,
                    expected_value=float(mean),
                    actual_value=float(dp.value),
                    deviation=float(dp.value - mean),
                    severity=severity,
                    context={
                        'z_score': float(z_score),
                        'mean': float(mean),
                        'std': float(std),
                    },
                )

                anomalies.append(anomaly)

        logger.info(f"Found {len(anomalies)} anomalies")
        return anomalies

    def calculate_moving_average(
        self,
        ts: TimeSeries,
        window: int = 7,
    ) -> List[float]:
        """
        Calculate moving average for smoothing.

        Args:
            ts: TimeSeries object
            window: Window size for moving average

        Returns:
            List of smoothed values
        """
        values = [dp.value for dp in ts.data_points]

        if len(values) < window:
            return values

        # Simple moving average
        smoothed = []
        for i in range(len(values)):
            if i < window - 1:
                # Not enough data for full window
                smoothed.append(np.mean(values[:i+1]))
            else:
                # Full window
                smoothed.append(np.mean(values[i-window+1:i+1]))

        return smoothed

    def detect_seasonality(
        self,
        user_id: str,
        metric_name: str,
        days: int = 90,
    ) -> Optional[Dict[str, Any]]:
        """
        Detect weekly/monthly seasonality patterns.

        Args:
            user_id: User ID
            metric_name: Metric to analyze
            days: Number of days to analyze (min 90 for monthly)

        Returns:
            Dict with seasonality info or None
        """
        logger.info(f"Detecting seasonality for {metric_name}")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        ts = self.engine.get_time_series(
            user_id, metric_name, start_date, end_date
        )

        if len(ts.data_points) < 14:
            return None

        # Group by day of week
        dow_values = defaultdict(list)

        for dp in ts.data_points:
            dow = dp.timestamp.weekday()
            dow_values[dow].append(dp.value)

        # Calculate average for each day
        dow_averages = {
            dow: np.mean(values)
            for dow, values in dow_values.items()
        }

        # Check if there's significant variation
        all_avg = np.mean([v for v in dow_averages.values()])
        variation = np.std([v for v in dow_averages.values()])
        coefficient_of_variation = variation / all_avg if all_avg > 0 else 0

        has_weekly_seasonality = coefficient_of_variation > 0.15  # 15% variation

        return {
            'has_weekly_pattern': has_weekly_seasonality,
            'day_of_week_averages': dow_averages,
            'variation_coefficient': float(coefficient_of_variation),
        }

    def forecast_simple(
        self,
        user_id: str,
        metric_name: str,
        days_ahead: int = 7,
        history_days: int = 30,
    ) -> List[float]:
        """
        Simple forecast using linear regression.

        Args:
            user_id: User ID
            metric_name: Metric to forecast
            days_ahead: Number of days to forecast
            history_days: Days of history to use

        Returns:
            List of forecasted values
        """
        # Get historical trend
        trend = self.analyze_trend(user_id, metric_name, history_days)

        if not trend or not trend.forecast:
            return []

        # Return forecast
        return trend.forecast[:days_ahead]
