# Aurora Life - Feast Feature Store

Feature Store for ML feature management using Feast.

## 📋 Overview

Feast (Feature Store) provides:
- **Offline Store** (PostgreSQL) - Historical features for training
- **Online Store** (Redis) - Low-latency features for predictions
- **Feature Registry** - Centralized feature definitions
- **Feature Serving** - REST API for feature access

## 🏗️ Architecture

```
┌─────────────┐
│ PostgreSQL  │ ──► Offline Store (Training Data)
│ (Raw Data)  │
└─────────────┘
       │
       │ Materialization
       ▼
┌─────────────┐
│   Redis     │ ──► Online Store (Predictions)
│ (Features)  │
└─────────────┘
       │
       │ Feature Serving
       ▼
┌─────────────┐
│  ML Models  │
│ Predictions │
└─────────────┘
```

## 📁 Files

- `feature_store.yaml` - Feast configuration
- `features.py` - Feature view definitions
- `data_sources.py` - Data source definitions
- `materialize.py` - Feature materialization script
- `data/` - Feature registry database

## 🚀 Quick Start

### 1. Initialize Feature Store

```bash
cd feast

# Apply feature definitions
feast apply

# This will:
# - Create feature registry
# - Register feature views
# - Set up online/offline stores
```

### 2. Materialize Features

```bash
# Full materialization (last 7 days)
python materialize.py full

# Incremental materialization (since last run)
python materialize.py incremental

# Run examples
python materialize.py example
```

### 3. Use Features in Python

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feast/")

# Get online features for prediction
features = store.get_online_features(
    features=[
        "user_activity_features:avg_energy_7d",
        "sleep_features:sleep_quality_score",
        "exercise_features:exercise_consistency_score",
    ],
    entity_rows=[{"user_id": "user-123"}],
).to_dict()

print(features)
# Output: {
#   "user_id": ["user-123"],
#   "avg_energy_7d": [7.5],
#   "sleep_quality_score": [0.85],
#   "exercise_consistency_score": [0.6]
# }
```

## 📊 Feature Views

### 1. User Activity Features

**Features:**
- `activity_count_24h`, `activity_count_7d`, `activity_count_30d`
- `total_minutes_24h`, `total_minutes_7d`, `total_minutes_30d`
- `activity_diversity_7d`, `activity_diversity_30d`
- `most_common_activity_24h`
- `avg_energy_7d`, `avg_mood_7d`

**TTL:** 24 hours
**Update Frequency:** Every 6 hours

---

### 2. Sleep Features

**Features:**
- `avg_sleep_duration_7d`, `avg_sleep_duration_30d`
- `sleep_consistency_7d`
- `avg_bedtime_hour_7d`
- `sleep_sessions_7d`
- `sleep_debt_minutes`
- `sleep_quality_score`
- `avg_deep_sleep_minutes_7d`, `avg_rem_sleep_minutes_7d`

**TTL:** 12 hours
**Update Frequency:** Every 6 hours

---

### 3. Exercise Features

**Features:**
- `exercise_count_7d`, `exercise_count_30d`
- `exercise_minutes_7d`, `exercise_minutes_30d`
- `avg_exercise_duration_7d`
- `avg_energy_after_exercise_7d`
- `exercise_consistency_score`
- `workout_variety_score_7d`
- `high_intensity_count_7d`

**TTL:** 12 hours
**Update Frequency:** Every 6 hours

---

### 4. Social Features

**Features:**
- `friend_count`
- `posts_7d`, `comments_7d`
- `likes_received_7d`, `likes_given_7d`
- `social_engagement_score`
- `avg_post_likes`, `comment_rate_7d`
- `friend_interactions_7d`

**TTL:** 24 hours
**Update Frequency:** Every 6 hours

---

### 5. Integration Features

**Features:**
- `active_integrations_count`
- `last_sync_hours_ago`
- `avg_heart_rate_7d`
- `avg_steps_7d`
- `avg_calories_7d`
- `data_completeness_score`
- `sync_reliability_score`

**TTL:** 6 hours
**Update Frequency:** Every 6 hours

---

## 🎯 On-Demand Features

### Energy Prediction Features

Combines historical features with current context:
- `predicted_energy` (1-10 scale)
- `energy_confidence` (0-1 scale)

**Inputs:**
- User activity features
- Sleep features
- Exercise features
- Request context (hour, day_of_week)

---

### Mood Prediction Features

- `predicted_mood` (1-10 scale)
- `mood_confidence` (0-1 scale)

**Inputs:**
- Sleep features
- Social features
- Exercise features
- Activity features

---

### Wellness Composite Features

- `wellness_score` (0-1 scale)
- `wellness_trend` (excellent, good, fair, needs_improvement)

**Inputs:**
- Sleep score (40%)
- Exercise score (30%)
- Activity score (30%)

---

## 🔧 Feature Services

### 1. Energy Prediction Service (`energy_prediction_v1`)

Features for energy level predictions:
- User activity features
- Sleep features
- Exercise features
- Energy prediction on-demand features

**Usage:**
```python
features = store.get_online_features(
    feature_service="energy_prediction_v1",
    entity_rows=[
        {
            "user_id": "user-123",
            "current_hour": 14,
            "day_of_week": 3,
            "is_weekend": 0,
        }
    ],
).to_dict()
```

---

### 2. Mood Prediction Service (`mood_prediction_v1`)

Features for mood predictions:
- Sleep features
- Social features
- Exercise features
- Activity features
- Mood prediction on-demand features

---

### 3. Wellness Dashboard Service (`wellness_dashboard_v1`)

All features for user dashboard:
- Activity, sleep, exercise, social, integration features
- Wellness composite features

---

### 4. ML Training Service (`ml_training_v1`)

All base features for model training (no on-demand features).

---

## 📈 Usage Examples

### Get Features for Real-time Prediction

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feast/")

# Single user
features = store.get_online_features(
    features=[
        "sleep_features:sleep_quality_score",
        "exercise_features:exercise_consistency_score",
    ],
    entity_rows=[{"user_id": "user-123"}],
)

print(features.to_dict())
```

### Get Historical Features for Training

```python
import pandas as pd
from datetime import datetime, timedelta

# Entity dataframe (users + timestamps)
entity_df = pd.DataFrame({
    "user_id": ["user-1", "user-2", "user-3"] * 30,
    "event_timestamp": [
        datetime.utcnow() - timedelta(days=i)
        for i in range(30)
        for _ in range(3)
    ],
})

# Get features
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "user_activity_features:avg_energy_7d",
        "sleep_features:sleep_quality_score",
        "exercise_features:exercise_consistency_score",
    ],
).to_df()

# Use for training
X = training_df.drop(columns=["user_id", "event_timestamp"])
y = training_df["target_variable"]
```

### Use Feature Service

```python
# Get all features for energy prediction
features = store.get_online_features(
    feature_service="energy_prediction_v1",
    entity_rows=[
        {
            "user_id": "user-123",
            "current_hour": 14,  # 2 PM
            "day_of_week": 3,    # Thursday
            "is_weekend": 0,
        }
    ],
).to_dict()

predicted_energy = features["predicted_energy"][0]
confidence = features["energy_confidence"][0]
```

### Push Real-time Features

```python
from feast import FeatureStore, PushMode
import pandas as pd
from datetime import datetime

store = FeatureStore(repo_path="feast/")

# New activity data
df = pd.DataFrame({
    "user_id": ["user-123"],
    "event_timestamp": [datetime.utcnow()],
    "activity_count_24h": [5],
    "total_minutes_24h": [180.0],
    "avg_energy_7d": [7.5],
})

# Push to online store
store.push("user_activity_push", df, to=PushMode.ONLINE)
```

---

## 🔄 Integration with Airflow

### Materialize Features (Scheduled DAG)

```python
# airflow/dags/feature_materialization.py
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG("feature_materialization", schedule_interval="0 */6 * * *") as dag:
    materialize = BashOperator(
        task_id="materialize_features",
        bash_command="cd /app/feast && python materialize.py incremental",
    )
```

This runs every 6 hours to keep online features fresh.

---

## 🧪 Testing

### Test Feature Retrieval

```bash
# Get feature view info
feast feature-views list

# Get feature service info
feast feature-services list

# Test online retrieval
feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%S)
```

### Validate Feature Definitions

```bash
# Check for errors
feast plan

# Apply changes
feast apply
```

---

## 📊 Monitoring

### Feature Freshness

Monitor when features were last materialized:

```python
from feast import FeatureStore
store = FeatureStore(repo_path="feast/")

# Check registry metadata
# (Implementation depends on Feast version)
```

### Feature Quality

Check for:
- Missing values
- Outliers
- Staleness (last update time)
- Data drift

---

## 🐛 Troubleshooting

### Features not appearing

**Solution:**
```bash
# Reapply feature definitions
feast apply

# Rematerialize
python materialize.py full
```

### Connection errors

**Check:**
- PostgreSQL is running (`docker ps | grep postgres`)
- Redis is running (`docker ps | grep redis`)
- Connection strings in `feature_store.yaml` are correct
- Network connectivity between containers

### Slow queries

**Optimize:**
- Add database indexes on `user_id`, `timestamp` columns
- Reduce materialization window
- Use incremental materialization
- Scale up PostgreSQL resources

---

## 🔐 Security

### Access Control

In production:
- Use separate database users with limited permissions
- Store credentials in environment variables
- Use SSL/TLS for database connections
- Implement feature-level access control

### Example:
```yaml
# feature_store.yaml
offline_store:
  type: postgres
  host: ${POSTGRES_HOST}
  database: ${POSTGRES_DB}
  user: ${FEAST_POSTGRES_USER}
  password: ${FEAST_POSTGRES_PASSWORD}
```

---

## 📚 Resources

- [Feast Documentation](https://docs.feast.dev/)
- [Feast Examples](https://github.com/feast-dev/feast)
- [Feature Store Concepts](https://docs.feast.dev/getting-started/concepts)

---

**Last Updated:** 2025-01-27
**Version:** 1.0
**Maintained by:** Aurora ML Team
