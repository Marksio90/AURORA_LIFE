"""
Analytics Module

Advanced analytics, insights, and recommendations for Aurora Life.
"""
from app.analytics.engine import AnalyticsEngine
from app.analytics.insights import InsightGenerator
from app.analytics.trends import TrendAnalyzer
from app.analytics.recommendations import RecommendationEngine
from app.analytics.schemas import (
    # Enums
    InsightType, InsightPriority, TrendDirection,
    RecommendationType, TimeGranularity, MetricCategory,

    # Analytics
    TimeSeries, TimeSeriesDataPoint, TrendAnalysis,
    CorrelationAnalysis, AnomalyDetection,
    AnalyticsQuery, AnalyticsResponse,

    # Insights
    Insight, InsightBase, PatternInsight,
    AnomalyInsight, TrendInsight, CorrelationInsight,

    # Recommendations
    Recommendation, RecommendationBase,
    ActivityRecommendation, SleepRecommendation,
    ExerciseRecommendation, SocialRecommendation,

    # Reports
    WellnessReport, ProgressReport, ReportSection,

    # Requests
    InsightRequest, RecommendationRequest,
    DataExportRequest, DataExportResponse,
)

__all__ = [
    # Engines
    "AnalyticsEngine",
    "InsightGenerator",
    "TrendAnalyzer",
    "RecommendationEngine",

    # Enums
    "InsightType",
    "InsightPriority",
    "TrendDirection",
    "RecommendationType",
    "TimeGranularity",
    "MetricCategory",

    # Analytics
    "TimeSeries",
    "TimeSeriesDataPoint",
    "TrendAnalysis",
    "CorrelationAnalysis",
    "AnomalyDetection",
    "AnalyticsQuery",
    "AnalyticsResponse",

    # Insights
    "Insight",
    "InsightBase",
    "PatternInsight",
    "AnomalyInsight",
    "TrendInsight",
    "CorrelationInsight",

    # Recommendations
    "Recommendation",
    "RecommendationBase",
    "ActivityRecommendation",
    "SleepRecommendation",
    "ExerciseRecommendation",
    "SocialRecommendation",

    # Reports
    "WellnessReport",
    "ProgressReport",
    "ReportSection",

    # Requests
    "InsightRequest",
    "RecommendationRequest",
    "DataExportRequest",
    "DataExportResponse",
]
