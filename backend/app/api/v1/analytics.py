"""
Analytics API Endpoints

API routes for analytics, insights, and recommendations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.analytics import (
    AnalyticsEngine, InsightGenerator, TrendAnalyzer, RecommendationEngine,
    AnalyticsQuery, AnalyticsResponse, InsightRequest, Insight,
    RecommendationRequest, Recommendation, TimeGranularity,
    MetricCategory, RecommendationType, InsightPriority,
    TrendAnalysis, CorrelationAnalysis,
    WellnessReport, ProgressReport,
)
from app.analytics.reports import ReportGenerator

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ==================== ANALYTICS ENDPOINTS ====================

@router.post("/query", response_model=AnalyticsResponse)
async def execute_analytics_query(
    query: AnalyticsQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute analytics query for time series data.

    Returns metrics, trends, correlations, and anomalies based on query parameters.
    """
    # Verify user can only query their own data
    if str(query.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot query other users' data")

    engine = AnalyticsEngine(db)
    response = engine.execute_query(query)

    return response


@router.get("/time-series/{metric_name}")
async def get_time_series(
    metric_name: str,
    start_date: datetime = Query(..., description="Start date for time series"),
    end_date: datetime = Query(..., description="End date for time series"),
    granularity: TimeGranularity = Query(TimeGranularity.DAILY),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get time series data for a specific metric.

    Metrics available:
    - energy_level
    - mood_level
    - sleep_duration
    - exercise_duration
    - exercise_count
    """
    engine = AnalyticsEngine(db)

    ts = engine.get_time_series(
        user_id=str(current_user.id),
        metric_name=metric_name,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
    )

    return ts


@router.get("/summary")
async def get_summary_statistics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get summary statistics for all key metrics.

    Returns:
    - Mean, median, std, min, max for each metric
    - Based on specified number of days
    """
    engine = AnalyticsEngine(db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    stats = engine.get_summary_statistics(
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "period_days": days,
        "start_date": start_date,
        "end_date": end_date,
        "statistics": stats,
    }


@router.get("/category-breakdown")
async def get_category_breakdown(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get time spent breakdown by activity category.

    Returns total minutes for each category.
    """
    engine = AnalyticsEngine(db)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    breakdown = engine.get_category_breakdown(
        user_id=str(current_user.id),
        start_date=start_date,
        end_date=end_date,
    )

    # Calculate total
    total_minutes = sum(breakdown.values())

    # Calculate percentages
    percentages = {
        category: (minutes / total_minutes * 100) if total_minutes > 0 else 0
        for category, minutes in breakdown.items()
    }

    return {
        "period_days": days,
        "breakdown_minutes": breakdown,
        "breakdown_percentages": percentages,
        "total_minutes": total_minutes,
    }


@router.get("/hourly-distribution")
async def get_hourly_distribution(
    category: Optional[str] = Query(None, description="Filter by category"),
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get hourly distribution of activities.

    Shows average time spent in each hour of the day.
    """
    engine = AnalyticsEngine(db)

    distribution = engine.get_hourly_distribution(
        user_id=str(current_user.id),
        category=category,
        days=days,
    )

    return {
        "period_days": days,
        "category": category or "all",
        "hourly_distribution": distribution,
    }


@router.get("/weekly-pattern/{metric_name}")
async def get_weekly_pattern(
    metric_name: str,
    weeks: int = Query(default=4, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get weekly pattern for a metric.

    Returns average value for each day of week (Mon-Sun).
    """
    engine = AnalyticsEngine(db)

    pattern = engine.get_weekly_pattern(
        user_id=str(current_user.id),
        metric_name=metric_name,
        weeks=weeks,
    )

    # Map day numbers to names
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pattern_with_names = {
        day_names[dow]: value
        for dow, value in pattern.items()
    }

    return {
        "metric_name": metric_name,
        "weeks": weeks,
        "weekly_pattern": pattern_with_names,
    }


# ==================== TRENDS ENDPOINTS ====================

@router.get("/trends/{metric_name}", response_model=TrendAnalysis)
async def analyze_trend(
    metric_name: str,
    days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze trend for a specific metric.

    Returns:
    - Trend direction (up/down/stable/volatile)
    - Trend strength
    - Change percentage
    - Forecast for next 7 days
    """
    analyzer = TrendAnalyzer(db)

    trend = analyzer.analyze_trend(
        user_id=str(current_user.id),
        metric_name=metric_name,
        days=days,
    )

    if not trend:
        raise HTTPException(status_code=404, detail="Insufficient data for trend analysis")

    return trend


@router.post("/correlations", response_model=List[CorrelationAnalysis])
async def analyze_correlations(
    metric_pairs: List[tuple[str, str]],
    days: int = Query(default=30, ge=14, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze correlations between metric pairs.

    Example:
    ```json
    {
        "metric_pairs": [
            ["sleep_duration", "energy_level"],
            ["exercise_duration", "mood_level"]
        ]
    }
    ```
    """
    analyzer = TrendAnalyzer(db)

    correlations = analyzer.detect_correlations(
        user_id=str(current_user.id),
        metric_pairs=metric_pairs,
        days=days,
    )

    return correlations


@router.get("/anomalies/{metric_name}")
async def detect_anomalies(
    metric_name: str,
    days: int = Query(default=30, ge=14, le=90),
    threshold: float = Query(default=2.0, ge=1.5, le=4.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect anomalies in metric data.

    Uses z-score method to detect outliers.
    Higher threshold = fewer, more significant anomalies.
    """
    analyzer = TrendAnalyzer(db)

    anomalies = analyzer.detect_anomalies(
        user_id=str(current_user.id),
        metric_name=metric_name,
        days=days,
        threshold=threshold,
    )

    return {
        "metric_name": metric_name,
        "period_days": days,
        "threshold": threshold,
        "anomalies_found": len(anomalies),
        "anomalies": anomalies,
    }


# ==================== INSIGHTS ENDPOINTS ====================

@router.post("/insights", response_model=List[Insight])
async def generate_insights(
    request: InsightRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate personalized insights.

    Automatically analyzes user data and generates actionable insights.
    """
    # Verify user
    if str(request.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot generate insights for other users")

    generator = InsightGenerator(db)

    insights = generator.generate_insights(
        user_id=str(current_user.id),
        categories=request.categories,
        priority_threshold=request.priority_threshold,
        limit=request.limit,
    )

    return insights


@router.get("/insights", response_model=List[Insight])
async def get_insights_simple(
    categories: Optional[List[MetricCategory]] = Query(None),
    priority: InsightPriority = Query(InsightPriority.LOW),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate insights (simplified GET endpoint).

    Query parameters:
    - categories: Filter by categories (comma-separated)
    - priority: Minimum priority level
    - limit: Maximum number of insights
    """
    generator = InsightGenerator(db)

    insights = generator.generate_insights(
        user_id=str(current_user.id),
        categories=categories,
        priority_threshold=priority,
        limit=limit,
    )

    return insights


# ==================== RECOMMENDATIONS ENDPOINTS ====================

@router.post("/recommendations", response_model=List[Recommendation])
async def generate_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate personalized recommendations.

    Returns actionable recommendations based on user data.
    """
    # Verify user
    if str(request.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot generate recommendations for other users")

    engine = RecommendationEngine(db)

    recommendations = engine.generate_recommendations(
        user_id=str(current_user.id),
        types=request.types,
        limit=request.limit,
        personalization_level=request.personalization_level,
    )

    return recommendations


@router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations_simple(
    types: Optional[List[RecommendationType]] = Query(None),
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate recommendations (simplified GET endpoint).

    Query parameters:
    - types: Filter by recommendation types
    - limit: Maximum number of recommendations
    """
    engine = RecommendationEngine(db)

    recommendations = engine.generate_recommendations(
        user_id=str(current_user.id),
        types=types,
        limit=limit,
        personalization_level="high",
    )

    return recommendations


# ==================== COMPARISON ENDPOINTS ====================

@router.get("/compare/{metric_name}")
async def compare_periods(
    metric_name: str,
    period1_days: int = Query(default=7, ge=1, le=90),
    period2_days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare two time periods for a metric.

    Compares period1 (most recent) vs period2 (before period1).
    Returns change percentage and statistics.
    """
    engine = AnalyticsEngine(db)

    # Period 1: Most recent
    period1_end = datetime.utcnow()
    period1_start = period1_end - timedelta(days=period1_days)

    # Period 2: Before period 1
    period2_end = period1_start
    period2_start = period2_end - timedelta(days=period2_days)

    comparison = engine.compare_periods(
        user_id=str(current_user.id),
        metric_name=metric_name,
        period1_start=period1_start,
        period1_end=period1_end,
        period2_start=period2_start,
        period2_end=period2_end,
    )

    return {
        "metric_name": metric_name,
        "period1": {
            "start": period1_start,
            "end": period1_end,
            "days": period1_days,
        },
        "period2": {
            "start": period2_start,
            "end": period2_end,
            "days": period2_days,
        },
        "comparison": comparison,
    }


# ==================== REPORT ENDPOINTS ====================

@router.get("/reports/wellness", response_model=WellnessReport)
async def generate_wellness_report(
    period_days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive wellness report.

    Includes:
    - Overall wellness score
    - Category scores (sleep, activity, exercise, social, mental)
    - Key insights and recommendations
    - Trend analysis
    """
    generator = ReportGenerator(db)

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=period_days)

    report = generator.generate_wellness_report(
        user_id=str(current_user.id),
        period_start=start_date,
        period_end=end_date,
    )

    return report


@router.get("/reports/progress", response_model=ProgressReport)
async def generate_progress_report(
    period_days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate goal progress report.

    Includes:
    - Goals completed, in progress, at risk
    - Completion rate
    - Achievements unlocked
    """
    generator = ReportGenerator(db)

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=period_days)

    report = generator.generate_progress_report(
        user_id=str(current_user.id),
        period_start=start_date,
        period_end=end_date,
    )

    return report
