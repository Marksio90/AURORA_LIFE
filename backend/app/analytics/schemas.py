"""
Analytics Schemas

Pydantic models for analytics, insights, and recommendations.
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, UUID4


# ==================== ENUMS ====================

class InsightType(str, Enum):
    """Types of insights"""
    PATTERN = "pattern"
    ANOMALY = "anomaly"
    ACHIEVEMENT = "achievement"
    SUGGESTION = "suggestion"
    WARNING = "warning"
    MILESTONE = "milestone"
    TREND = "trend"
    CORRELATION = "correlation"


class InsightPriority(str, Enum):
    """Priority levels for insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TrendDirection(str, Enum):
    """Trend direction"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    VOLATILE = "volatile"


class RecommendationType(str, Enum):
    """Types of recommendations"""
    ACTIVITY = "activity"
    SLEEP = "sleep"
    EXERCISE = "exercise"
    SOCIAL = "social"
    HABIT = "habit"
    GOAL = "goal"
    INTEGRATION = "integration"


class TimeGranularity(str, Enum):
    """Time granularity for analytics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class MetricCategory(str, Enum):
    """Metric categories"""
    WELLBEING = "wellbeing"
    PRODUCTIVITY = "productivity"
    SOCIAL = "social"
    PHYSICAL = "physical"
    MENTAL = "mental"
    SLEEP = "sleep"
    ACTIVITY = "activity"


# ==================== ANALYTICS MODELS ====================

class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimeSeries(BaseModel):
    """Time series data"""
    metric_name: str
    category: MetricCategory
    granularity: TimeGranularity
    data_points: List[TimeSeriesDataPoint]
    start_date: datetime
    end_date: datetime
    statistics: Optional[Dict[str, float]] = None


class TrendAnalysis(BaseModel):
    """Trend analysis result"""
    metric_name: str
    direction: TrendDirection
    strength: float = Field(ge=0, le=1, description="Trend strength 0-1")
    change_percentage: float
    start_value: float
    end_value: float
    period_days: int
    confidence: float = Field(ge=0, le=1)
    forecast: Optional[List[float]] = None


class CorrelationAnalysis(BaseModel):
    """Correlation between two metrics"""
    metric_a: str
    metric_b: str
    correlation_coefficient: float = Field(ge=-1, le=1)
    p_value: float
    is_significant: bool
    sample_size: int
    interpretation: str


class AnomalyDetection(BaseModel):
    """Anomaly detection result"""
    timestamp: datetime
    metric_name: str
    expected_value: float
    actual_value: float
    deviation: float
    severity: InsightPriority
    context: Dict[str, Any] = Field(default_factory=dict)


# ==================== INSIGHT MODELS ====================

class InsightBase(BaseModel):
    """Base insight model"""
    type: InsightType
    priority: InsightPriority
    title: str
    description: str
    category: MetricCategory
    actionable: bool = True
    action_items: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PatternInsight(InsightBase):
    """Pattern-based insight"""
    type: InsightType = InsightType.PATTERN
    pattern_type: str
    frequency: str
    confidence: float = Field(ge=0, le=1)
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class AnomalyInsight(InsightBase):
    """Anomaly-based insight"""
    type: InsightType = InsightType.ANOMALY
    anomaly: AnomalyDetection
    possible_causes: List[str] = Field(default_factory=list)


class TrendInsight(InsightBase):
    """Trend-based insight"""
    type: InsightType = InsightType.TREND
    trend: TrendAnalysis
    implications: List[str] = Field(default_factory=list)


class CorrelationInsight(InsightBase):
    """Correlation-based insight"""
    type: InsightType = InsightType.CORRELATION
    correlation: CorrelationAnalysis
    recommendations: List[str] = Field(default_factory=list)


class Insight(BaseModel):
    """Complete insight with metadata"""
    id: Optional[UUID4] = None
    user_id: UUID4
    insight_data: InsightBase
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_read: bool = False
    is_dismissed: bool = False
    engagement_score: float = Field(default=0.0, ge=0, le=1)


# ==================== RECOMMENDATION MODELS ====================

class RecommendationBase(BaseModel):
    """Base recommendation model"""
    type: RecommendationType
    title: str
    description: str
    rationale: str
    expected_impact: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    estimated_time_minutes: Optional[int] = None
    priority: InsightPriority = InsightPriority.MEDIUM


class ActivityRecommendation(RecommendationBase):
    """Activity recommendation"""
    type: RecommendationType = RecommendationType.ACTIVITY
    suggested_category: str
    suggested_duration_minutes: int
    best_time_of_day: Optional[str] = None


class SleepRecommendation(RecommendationBase):
    """Sleep recommendation"""
    type: RecommendationType = RecommendationType.SLEEP
    suggested_bedtime: Optional[str] = None
    suggested_duration_hours: Optional[float] = None
    sleep_hygiene_tips: List[str] = Field(default_factory=list)


class ExerciseRecommendation(RecommendationBase):
    """Exercise recommendation"""
    type: RecommendationType = RecommendationType.EXERCISE
    exercise_type: str
    intensity: Literal["low", "moderate", "high"]
    frequency_per_week: int


class SocialRecommendation(RecommendationBase):
    """Social recommendation"""
    type: RecommendationType = RecommendationType.SOCIAL
    activity_type: str
    suggested_friends: Optional[List[UUID4]] = None


class Recommendation(BaseModel):
    """Complete recommendation with metadata"""
    id: Optional[UUID4] = None
    user_id: UUID4
    recommendation_data: RecommendationBase
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_accepted: bool = False
    is_dismissed: bool = False
    effectiveness_score: Optional[float] = Field(default=None, ge=0, le=1)


# ==================== REPORT MODELS ====================

class ReportSection(BaseModel):
    """Report section"""
    title: str
    content: str
    visualizations: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    order: int = 0


class WellnessReport(BaseModel):
    """Comprehensive wellness report"""
    user_id: UUID4
    period_start: date
    period_end: date
    overall_score: float = Field(ge=0, le=100)

    # Category scores
    sleep_score: float = Field(ge=0, le=100)
    activity_score: float = Field(ge=0, le=100)
    exercise_score: float = Field(ge=0, le=100)
    social_score: float = Field(ge=0, le=100)
    mental_wellbeing_score: float = Field(ge=0, le=100)

    # Sections
    sections: List[ReportSection]

    # Key metrics
    key_metrics: Dict[str, Any]

    # Insights & Recommendations
    top_insights: List[Insight]
    top_recommendations: List[Recommendation]

    # Trends
    trends: List[TrendAnalysis]

    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ProgressReport(BaseModel):
    """Goal progress report"""
    user_id: UUID4
    period_start: date
    period_end: date

    goals_completed: int
    goals_in_progress: int
    goals_at_risk: int

    completion_rate: float = Field(ge=0, le=1)
    average_progress: float = Field(ge=0, le=1)

    goal_details: List[Dict[str, Any]]
    achievements_unlocked: List[Dict[str, Any]]

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== ANALYTICS REQUEST/RESPONSE ====================

class AnalyticsQuery(BaseModel):
    """Analytics query parameters"""
    user_id: UUID4
    start_date: datetime
    end_date: datetime
    metrics: List[str]
    granularity: TimeGranularity = TimeGranularity.DAILY
    include_trends: bool = True
    include_correlations: bool = False
    include_anomalies: bool = False


class AnalyticsResponse(BaseModel):
    """Analytics query response"""
    query: AnalyticsQuery
    time_series: List[TimeSeries]
    trends: Optional[List[TrendAnalysis]] = None
    correlations: Optional[List[CorrelationAnalysis]] = None
    anomalies: Optional[List[AnomalyDetection]] = None
    summary_statistics: Dict[str, Dict[str, float]]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class InsightRequest(BaseModel):
    """Request for generating insights"""
    user_id: UUID4
    categories: Optional[List[MetricCategory]] = None
    priority_threshold: InsightPriority = InsightPriority.LOW
    limit: int = Field(default=10, ge=1, le=100)


class RecommendationRequest(BaseModel):
    """Request for generating recommendations"""
    user_id: UUID4
    types: Optional[List[RecommendationType]] = None
    limit: int = Field(default=5, ge=1, le=20)
    personalization_level: Literal["low", "medium", "high"] = "high"


# ==================== EXPORT MODELS ====================

class DataExportRequest(BaseModel):
    """Data export request"""
    user_id: UUID4
    start_date: date
    end_date: date
    include_life_events: bool = True
    include_analytics: bool = True
    include_insights: bool = True
    include_recommendations: bool = True
    format: Literal["json", "csv", "pdf"] = "json"


class DataExportResponse(BaseModel):
    """Data export response"""
    export_id: UUID4
    status: Literal["processing", "completed", "failed"]
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
