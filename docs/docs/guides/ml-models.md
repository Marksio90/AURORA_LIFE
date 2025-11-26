# Machine Learning Models

AURORA_LIFE uses state-of-the-art ML models to predict your energy levels and mood based on your life events and patterns.

## Model Architecture

### Energy Predictor (XGBoost Regressor)

Predicts your energy level on a scale of 0-10 based on recent life events.

**Algorithm**: XGBoost (Extreme Gradient Boosting)
**Type**: Regression
**Target**: Energy level (continuous 0-10)

**Hyperparameters**:
```python
{
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "tree_method": "hist",
    "random_state": 42
}
```

**Features (25 total)**:

1. **Sleep Features (5)**
   - `hours_sleep_last_night`: Hours of sleep
   - `avg_sleep_7d`: 7-day average sleep
   - `sleep_quality`: Quality rating (1-5)
   - `time_since_wake`: Hours since waking up
   - `sleep_debt`: Cumulative sleep deficit

2. **Exercise Features (4)**
   - `exercise_minutes_today`: Minutes of exercise
   - `avg_exercise_7d`: 7-day average
   - `exercise_intensity`: Light/Moderate/Intense
   - `days_since_exercise`: Days without exercise

3. **Work Features (4)**
   - `work_hours_today`: Hours worked
   - `avg_work_hours_7d`: 7-day average
   - `focus_sessions_count`: Number of deep work sessions
   - `meetings_count`: Number of meetings

4. **Mood Features (3)**
   - `mood_score_current`: Latest mood score
   - `avg_mood_7d`: 7-day average mood
   - `mood_volatility`: Standard deviation of mood

5. **Temporal Features (5)**
   - `hour_of_day`: 0-23
   - `day_of_week`: 0-6
   - `is_weekend`: Boolean
   - `is_morning`: Boolean (6am-12pm)
   - `is_evening`: Boolean (6pm-12am)

6. **Other Features (4)**
   - `caffeine_intake_mg`: Caffeine consumed
   - `social_events_count_3d`: Social interactions (3 days)
   - `stress_level`: Self-reported stress (1-10)
   - `weather_condition`: Sunny/Cloudy/Rainy (encoded)

**Performance Metrics**:
- **MAE (Mean Absolute Error)**: < 1.0
- **RMSE**: < 1.3
- **R² Score**: > 0.75
- **Cross-validation**: 5-fold CV

### Mood Predictor (LightGBM Classifier)

Predicts your mood category based on recent events and patterns.

**Algorithm**: LightGBM (Light Gradient Boosting Machine)
**Type**: Multi-class Classification
**Target**: 5 mood classes

**Classes**:
1. `very_negative` (1): Very low mood
2. `negative` (2): Low mood
3. `neutral` (3): Neutral mood
4. `positive` (4): Good mood
5. `very_positive` (5): Excellent mood

**Hyperparameters**:
```python
{
    "n_estimators": 150,
    "max_depth": 5,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "multiclass",
    "num_class": 5,
    "metric": "multi_logloss",
    "random_state": 42
}
```

**Features (23 total)**: Similar to energy predictor minus some exercise features

**Performance Metrics**:
- **Accuracy**: > 70%
- **F1 Score (weighted)**: > 0.68
- **Precision/Recall**: Balanced across classes
- **Confusion Matrix**: Low off-by-one errors

## Feature Engineering

### Time-Based Features

```python
def extract_time_features(event_time: datetime) -> Dict[str, Any]:
    """Extract temporal features from timestamp."""
    return {
        "hour_of_day": event_time.hour,
        "day_of_week": event_time.weekday(),
        "is_weekend": event_time.weekday() >= 5,
        "is_morning": 6 <= event_time.hour < 12,
        "is_afternoon": 12 <= event_time.hour < 18,
        "is_evening": 18 <= event_time.hour < 24,
        "day_of_month": event_time.day,
        "month": event_time.month
    }
```

### Aggregation Features

```python
def compute_rolling_features(
    events: List[Event],
    window_days: int = 7
) -> Dict[str, float]:
    """Compute rolling statistics over time window."""
    recent_events = filter_last_n_days(events, window_days)

    return {
        f"avg_sleep_{window_days}d": mean([e.sleep_hours for e in recent_events]),
        f"avg_exercise_{window_days}d": mean([e.exercise_mins for e in recent_events]),
        f"avg_mood_{window_days}d": mean([e.mood_score for e in recent_events]),
        f"avg_energy_{window_days}d": mean([e.energy_score for e in recent_events]),
        f"total_social_{window_days}d": sum([e.social_count for e in recent_events])
    }
```

### Normalization

```python
from sklearn.preprocessing import StandardScaler

# Fit scaler on training data
scaler = StandardScaler()
scaler.fit(X_train)

# Transform features
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

## Training Pipeline

### Daily Retraining

Models are retrained daily at 2 AM UTC using Celery Beat:

```python
@celery_app.task(name="retrain_all_models")
def retrain_all_models():
    """Retrain all ML models with latest data."""
    # Fetch data from last 90 days
    training_data = fetch_training_data(days=90)

    # Train energy predictor
    energy_model = EnergyPredictor()
    energy_model.train(training_data)
    energy_model.save_model(f"models/energy_{date.today()}.pkl")

    # Train mood predictor
    mood_model = MoodPredictor()
    mood_model.train(training_data)
    mood_model.save_model(f"models/mood_{date.today()}.pkl")

    # Evaluate models
    metrics = evaluate_models(energy_model, mood_model, test_data)
    log_metrics(metrics)
```

### Training Data Requirements

**Minimum Data**:
- At least 30 days of event history
- At least 100 events total
- At least 5 events of each type (sleep, exercise, work, etc.)

**Data Quality Checks**:
- Remove outliers (> 3 standard deviations)
- Handle missing values (imputation)
- Check for data drift
- Validate feature distributions

### Model Evaluation

```python
def evaluate_model(model, X_test, y_test):
    """Comprehensive model evaluation."""
    predictions = model.predict(X_test)

    # Regression metrics (energy)
    if is_regressor(model):
        return {
            "mae": mean_absolute_error(y_test, predictions),
            "rmse": sqrt(mean_squared_error(y_test, predictions)),
            "r2": r2_score(y_test, predictions),
            "mape": mean_absolute_percentage_error(y_test, predictions)
        }

    # Classification metrics (mood)
    else:
        return {
            "accuracy": accuracy_score(y_test, predictions),
            "precision": precision_score(y_test, predictions, average='weighted'),
            "recall": recall_score(y_test, predictions, average='weighted'),
            "f1": f1_score(y_test, predictions, average='weighted'),
            "confusion_matrix": confusion_matrix(y_test, predictions)
        }
```

## Making Predictions

### API Usage

```bash
# Get energy prediction
curl -X GET http://localhost:8000/api/v1/predictions/energy \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "prediction": 7.8,
  "confidence": 0.85,
  "model_version": "2024-01-16",
  "features_used": 25,
  "created_at": "2024-01-16T10:30:00Z"
}
```

### Python SDK Usage

```python
from aurora_life_sdk import AuroraLifeClient

client = AuroraLifeClient(api_key="YOUR_TOKEN")

# Get energy prediction
energy = client.predictions.energy()
print(f"Predicted energy: {energy.prediction}/10")
print(f"Confidence: {energy.confidence * 100:.1f}%")

# Get mood prediction
mood = client.predictions.mood()
print(f"Predicted mood: {mood.prediction}")  # e.g., "positive"
print(f"Probabilities: {mood.class_probabilities}")
```

## Model Versioning

### Saving Models

Models are saved with timestamps:

```
models/
├── energy_2024-01-15.pkl
├── energy_2024-01-16.pkl
├── mood_2024-01-15.pkl
└── mood_2024-01-16.pkl
```

### Loading Models

```python
import joblib
from datetime import date

# Load latest model
def load_latest_model(model_type: str):
    """Load the most recent model version."""
    model_dir = Path("models")
    pattern = f"{model_type}_*.pkl"

    models = sorted(model_dir.glob(pattern), reverse=True)
    if not models:
        raise FileNotFoundError(f"No {model_type} model found")

    latest = models[0]
    return joblib.load(latest)

energy_model = load_latest_model("energy")
mood_model = load_latest_model("mood")
```

### Rollback

If a new model performs poorly:

```bash
# Rollback to previous version
kubectl rollout undo deployment/api-deployment

# Or manually update model version in ConfigMap
kubectl edit configmap api-config
# Change MODEL_VERSION to previous date
```

## Feature Importance

### Analyzing Features

```python
import matplotlib.pyplot as plt

# Get feature importance from XGBoost
importance = model.feature_importances_
feature_names = model.feature_names_

# Sort by importance
indices = importance.argsort()[::-1]

# Plot
plt.figure(figsize=(12, 8))
plt.title("Feature Importance - Energy Predictor")
plt.bar(range(len(importance)), importance[indices])
plt.xticks(range(len(importance)), [feature_names[i] for i in indices], rotation=45)
plt.tight_layout()
plt.savefig("energy_feature_importance.png")
```

**Top 5 Features (Energy)**:
1. `hours_sleep_last_night` (25.3%)
2. `time_since_wake` (15.7%)
3. `caffeine_intake_mg` (12.4%)
4. `avg_mood_7d` (10.9%)
5. `exercise_minutes_today` (8.6%)

**Top 5 Features (Mood)**:
1. `avg_mood_7d` (22.1%)
2. `social_events_count_3d` (18.5%)
3. `hours_sleep_last_night` (14.3%)
4. `stress_level` (11.7%)
5. `exercise_minutes_today` (9.2%)

## Handling Edge Cases

### New Users

For users with insufficient data:

```python
def predict_with_fallback(user_id: int, model_type: str):
    """Make prediction with fallback for new users."""
    user_events = fetch_user_events(user_id, days=30)

    if len(user_events) < MIN_EVENTS_FOR_PREDICTION:
        # Use population average
        return get_population_average(model_type)

    # Use ML model
    features = engineer_features(user_events)
    prediction = model.predict([features])[0]
    return prediction
```

### Missing Features

```python
def impute_missing_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """Fill in missing feature values."""
    defaults = {
        "hours_sleep_last_night": 7.5,
        "exercise_minutes_today": 0,
        "caffeine_intake_mg": 100,
        "stress_level": 5,
        "social_events_count_3d": 2
    }

    for key, default_value in defaults.items():
        if key not in features or features[key] is None:
            features[key] = default_value

    return features
```

## Model Monitoring

### Performance Tracking

```python
# Track prediction accuracy over time
@app.post("/api/v1/predictions/{prediction_id}/feedback")
async def record_feedback(
    prediction_id: UUID,
    actual_value: float,
    db: AsyncSession = Depends(get_db)
):
    """User reports actual value vs. prediction."""
    prediction = await db.get(Prediction, prediction_id)

    # Calculate error
    error = abs(prediction.value - actual_value)

    # Store for model evaluation
    await db.execute(
        insert(PredictionFeedback).values(
            prediction_id=prediction_id,
            predicted_value=prediction.value,
            actual_value=actual_value,
            error=error
        )
    )

    # Alert if error is too high
    if error > 2.0:
        alert_model_performance_issue(prediction.model_type, error)
```

### Drift Detection

```python
from scipy.stats import ks_2samp

def detect_feature_drift(
    historical_features: np.ndarray,
    current_features: np.ndarray,
    threshold: float = 0.05
):
    """Detect if feature distribution has changed."""
    for i, feature_name in enumerate(feature_names):
        # Kolmogorov-Smirnov test
        statistic, p_value = ks_2samp(
            historical_features[:, i],
            current_features[:, i]
        )

        if p_value < threshold:
            logger.warning(
                f"Feature drift detected: {feature_name} "
                f"(p-value: {p_value:.4f})"
            )
```

## Future Improvements

1. **Deep Learning Models**
   - LSTM for time series prediction
   - Transformer for sequence modeling
   - Attention mechanisms for feature importance

2. **Personalization**
   - User-specific model fine-tuning
   - Transfer learning from similar users
   - Active learning for data efficiency

3. **Multi-Task Learning**
   - Joint prediction of energy + mood
   - Shared representations
   - Auxiliary tasks for better features

4. **Explainability**
   - SHAP values for predictions
   - LIME for local explanations
   - Counterfactual explanations

5. **AutoML**
   - Hyperparameter tuning with Optuna
   - Feature selection automation
   - Model selection (try multiple algorithms)

6. **Real-time Learning**
   - Online learning for immediate updates
   - Incremental model updates
   - Adaptive learning rates
