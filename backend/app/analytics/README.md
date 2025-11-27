# Analytics Module 📊

Advanced analytics, insights, and recommendations for Aurora Life.

## 📋 Overview

The Analytics module provides:
- **Time Series Analysis** - Track metrics over time
- **Statistical Insights** - Automatic pattern detection
- **Trend Analysis** - Identify trends and forecast future values
- **Correlations** - Discover relationships between metrics
- **Anomaly Detection** - Identify unusual patterns
- **Personalized Recommendations** - AI-driven suggestions
- **Comprehensive Reports** - Wellness and progress reports

## 🏗️ Architecture

```
analytics/
├── engine.py          # Core analytics engine (time series, stats, aggregations)
├── insights.py        # Insight generation (patterns, achievements, warnings)
├── trends.py          # Trend analysis (forecasting, correlations, anomalies)
├── recommendations.py # Recommendation engine (personalized suggestions)
├── reports.py         # Report generation (wellness, progress)
├── schemas.py         # Pydantic models
└── __init__.py        # Module exports
```

## 🚀 Quick Start

### Get Time Series Data

```python
from app.analytics import AnalyticsEngine, TimeGranularity

engine = AnalyticsEngine(db)

# Get daily energy levels for last 30 days
ts = engine.get_time_series(
    user_id="user-123",
    metric_name="energy_level",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    granularity=TimeGranularity.DAILY,
)

print(ts.statistics)
# Output: {'mean': 7.5, 'median': 8.0, 'std': 1.2, ...}
```

### Generate Insights

```python
from app.analytics import InsightGenerator, MetricCategory, InsightPriority

generator = InsightGenerator(db)

insights = generator.generate_insights(
    user_id="user-123",
    categories=[MetricCategory.SLEEP, MetricCategory.EXERCISE],
    priority_threshold=InsightPriority.MEDIUM,
    limit=10,
)

for insight in insights:
    print(f"{insight.insight_data.title}: {insight.insight_data.description}")
```

### Analyze Trends

```python
from app.analytics import TrendAnalyzer

analyzer = TrendAnalyzer(db)

# Analyze trend for sleep duration
trend = analyzer.analyze_trend(
    user_id="user-123",
    metric_name="sleep_duration",
    days=30,
)

print(f"Direction: {trend.direction}")
print(f"Change: {trend.change_percentage:.1f}%")
print(f"Forecast (next 7 days): {trend.forecast}")
```

### Generate Recommendations

```python
from app.analytics import RecommendationEngine, RecommendationType

engine = RecommendationEngine(db)

recommendations = engine.generate_recommendations(
    user_id="user-123",
    types=[RecommendationType.SLEEP, RecommendationType.EXERCISE],
    limit=5,
    personalization_level="high",
)

for rec in recommendations:
    print(f"{rec.recommendation_data.title}")
    print(f"Expected impact: {rec.recommendation_data.expected_impact}")
```

### Generate Wellness Report

```python
from app.analytics.reports import ReportGenerator

generator = ReportGenerator(db)

report = generator.generate_wellness_report(
    user_id="user-123",
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31),
)

print(f"Overall Score: {report.overall_score:.0f}/100")
print(f"Sleep Score: {report.sleep_score:.0f}/100")
print(f"Exercise Score: {report.exercise_score:.0f}/100")
```

## 📊 Available Metrics

### Life Event Metrics

- `energy_level` - Energy level (1-10)
- `mood_level` - Mood level (1-10)
- `sleep_duration` - Sleep duration (minutes)
- `exercise_duration` - Exercise duration (minutes)
- `exercise_count` - Number of exercise sessions

### Aggregated Metrics

- `activity_count_24h` / `7d` / `30d` - Activity counts
- `total_minutes_24h` / `7d` / `30d` - Total activity time
- `activity_diversity_7d` - Number of unique categories

## 🔧 Analytics Engine

### Time Series Functions

```python
# Get time series
ts = engine.get_time_series(user_id, metric_name, start, end, granularity)

# Get summary statistics
stats = engine.get_summary_statistics(user_id, start, end)

# Get category breakdown
breakdown = engine.get_category_breakdown(user_id, start, end)

# Get hourly distribution
dist = engine.get_hourly_distribution(user_id, category, days)

# Get weekly pattern (Mon-Sun averages)
pattern = engine.get_weekly_pattern(user_id, metric_name, weeks)

# Compare two periods
comparison = engine.compare_periods(
    user_id, metric_name,
    period1_start, period1_end,
    period2_start, period2_end
)
```

### Time Granularity

- `HOURLY` - Hourly aggregation
- `DAILY` - Daily aggregation (default)
- `WEEKLY` - Weekly aggregation
- `MONTHLY` - Monthly aggregation

## 💡 Insight Generation

### Insight Types

- `PATTERN` - Detected patterns (e.g., consistent bedtime)
- `ANOMALY` - Unusual values
- `ACHIEVEMENT` - Positive milestones
- `SUGGESTION` - Actionable suggestions
- `WARNING` - Issues requiring attention
- `MILESTONE` - Significant achievements
- `TREND` - Trend-based insights
- `CORRELATION` - Relationships between metrics

### Priority Levels

- `LOW` - General information
- `MEDIUM` - Noteworthy
- `HIGH` - Important
- `URGENT` - Requires immediate attention

### Auto-Generated Insights

- **Sleep**: Bedtime consistency, sleep duration, sleep debt
- **Exercise**: Frequency, duration, weekend vs weekday
- **Energy**: Peak hours, low energy warnings
- **Patterns**: Weekly patterns, hourly distributions
- **Streaks**: Current streak milestones
- **Achievements**: Recent unlocked achievements

## 📈 Trend Analysis

### Trend Detection

```python
# Analyze trend (uses linear regression)
trend = analyzer.analyze_trend(user_id, metric_name, days=30)

# Trend direction: UP, DOWN, STABLE, VOLATILE
print(trend.direction)

# Trend strength (0-1, based on R²)
print(trend.strength)

# 7-day forecast
print(trend.forecast)
```

### Correlation Analysis

```python
# Detect correlations between metric pairs
correlations = analyzer.detect_correlations(
    user_id=user_id,
    metric_pairs=[
        ("sleep_duration", "energy_level"),
        ("exercise_duration", "mood_level"),
    ],
    days=30,
)

for corr in correlations:
    print(f"{corr.metric_a} vs {corr.metric_b}: r={corr.correlation_coefficient:.2f}")
    print(f"Interpretation: {corr.interpretation}")
    print(f"Significant: {corr.is_significant}")
```

### Anomaly Detection

```python
# Detect anomalies using z-score method
anomalies = analyzer.detect_anomalies(
    user_id=user_id,
    metric_name="sleep_duration",
    days=30,
    threshold=2.0,  # 2 standard deviations
)

for anomaly in anomalies:
    print(f"Anomaly on {anomaly.timestamp}")
    print(f"Expected: {anomaly.expected_value}, Actual: {anomaly.actual_value}")
    print(f"Severity: {anomaly.severity}")
```

## 🎯 Recommendations

### Recommendation Types

- `ACTIVITY` - General activity suggestions
- `SLEEP` - Sleep improvement recommendations
- `EXERCISE` - Exercise recommendations
- `SOCIAL` - Social engagement suggestions
- `HABIT` - Habit-building recommendations
- `GOAL` - Goal-related suggestions

### Personalization Levels

- `low` - Generic recommendations
- `medium` - User-aware recommendations
- `high` - Fully personalized (default)

### Example Recommendations

**Sleep Recommendations:**
- Increase sleep duration if < 7h
- Establish consistent bedtime
- Sleep hygiene tips

**Exercise Recommendations:**
- Increase frequency if < 3/week
- Increase duration if < 150 min/week
- Add variety to workouts

**Activity Recommendations:**
- Diversify activity types
- Balance work and leisure

## 📄 Reports

### Wellness Report

Comprehensive wellness assessment:

- **Overall Score** (0-100)
- **Category Scores**:
  - Sleep (25%)
  - Activity (20%)
  - Exercise (20%)
  - Social (15%)
  - Mental Wellbeing (20%)
- **Report Sections**: Detailed content for each category
- **Key Metrics**: Summary statistics
- **Top Insights**: Most important insights
- **Top Recommendations**: Personalized suggestions
- **Trends**: Trend analysis for key metrics

### Progress Report

Goal tracking and achievements:

- Goals completed, in progress, at risk
- Completion rate
- Average progress
- Achievements unlocked
- Goal details

## 🌐 API Endpoints

### Analytics

- `POST /api/v1/analytics/query` - Execute analytics query
- `GET /api/v1/analytics/time-series/{metric}` - Get time series
- `GET /api/v1/analytics/summary` - Get summary statistics
- `GET /api/v1/analytics/category-breakdown` - Category breakdown
- `GET /api/v1/analytics/hourly-distribution` - Hourly distribution
- `GET /api/v1/analytics/weekly-pattern/{metric}` - Weekly pattern

### Trends

- `GET /api/v1/analytics/trends/{metric}` - Analyze trend
- `POST /api/v1/analytics/correlations` - Analyze correlations
- `GET /api/v1/analytics/anomalies/{metric}` - Detect anomalies

### Insights

- `GET /api/v1/analytics/insights` - Generate insights
- `POST /api/v1/analytics/insights` - Generate insights (detailed)

### Recommendations

- `GET /api/v1/analytics/recommendations` - Generate recommendations
- `POST /api/v1/analytics/recommendations` - Generate recommendations (detailed)

### Reports

- `GET /api/v1/analytics/reports/wellness` - Wellness report
- `GET /api/v1/analytics/reports/progress` - Progress report

### Comparison

- `GET /api/v1/analytics/compare/{metric}` - Compare two periods

## 🧪 Testing

```bash
# Test insight generation
curl -X GET "http://localhost:8000/api/v1/analytics/insights?limit=5" \
  -H "Authorization: Bearer $TOKEN"

# Test trend analysis
curl -X GET "http://localhost:8000/api/v1/analytics/trends/energy_level?days=30" \
  -H "Authorization: Bearer $TOKEN"

# Test wellness report
curl -X GET "http://localhost:8000/api/v1/analytics/reports/wellness?period_days=30" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Score Calculations

### Sleep Score (0-100)

- **Duration (70%)**: Optimal 7-9h = 100 points
- **Consistency (30%)**: Bedtime std < 0.5h = 100 points

### Activity Score (0-100)

- **Count (40%)**: 5 activities/day = 100 points
- **Diversity (30%)**: 5 categories = 100 points
- **Time (30%)**: 5h/day = 100 points

### Exercise Score (0-100)

- **Frequency (50%)**: 3-5 sessions/week = 100 points
- **Duration (50%)**: 150+ min/week = 100 points

### Mental Wellbeing Score (0-100)

- **Mood (50%)**: Average mood level * 10
- **Energy (50%)**: Average energy level * 10

## 🔬 Statistical Methods

- **Linear Regression**: Trend analysis and forecasting
- **Pearson Correlation**: Relationship detection
- **Z-Score**: Anomaly detection
- **Moving Averages**: Data smoothing
- **Percentiles**: Quartile calculations

## 📚 Dependencies

- `numpy` - Numerical operations
- `scipy` - Statistical functions
- `pandas` - Data manipulation (via engine)
- `sqlalchemy` - Database queries

## 🚀 Performance

- Time series queries use database aggregations (fast)
- Statistics calculated in-memory (NumPy)
- Caching recommended for frequently accessed reports
- Consider Redis for time series caching

## 🔮 Future Enhancements

- [ ] Machine learning models for predictions
- [ ] Advanced forecasting (ARIMA, Prophet)
- [ ] Clustering analysis for user segments
- [ ] Sentiment analysis for notes
- [ ] Multi-variate trend analysis
- [ ] Automated insight scheduling
- [ ] Export reports as PDF
- [ ] Scheduled email reports

---

**Last Updated:** 2025-01-27
**Version:** 1.0
**Maintained by:** Aurora Analytics Team
