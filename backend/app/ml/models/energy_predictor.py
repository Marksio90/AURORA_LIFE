"""
Energy Level Prediction Model using XGBoost
"""
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import xgboost as xgb
from sklearn.preprocessing import StandardScaler


class EnergyPredictor:
    """
    Predicts user energy levels based on life events and patterns.

    Uses XGBoost regressor trained on:
    - Sleep patterns (duration, quality, timing)
    - Activity levels (exercise, work hours)
    - Emotional state
    - Time-based features (hour of day, day of week)
    - Cross-domain interactions
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model: Optional[xgb.XGBRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names = [
            # Sleep features
            'sleep_duration_avg_7d', 'sleep_quality_avg_7d', 'sleep_regularity_7d',
            'hours_since_last_sleep',

            # Activity features
            'exercise_minutes_7d', 'exercise_intensity_avg_7d',
            'work_hours_7d', 'sedentary_hours_7d',

            # Emotional features
            'mood_avg_7d', 'stress_level_avg_7d', 'positive_emotions_7d',

            # Temporal features
            'hour_of_day', 'day_of_week', 'is_weekend',

            # Social features
            'social_interactions_7d', 'quality_time_hours_7d',

            # Health features
            'calories_intake_avg_7d', 'hydration_level_7d',

            # Cross-domain features
            'sleep_exercise_interaction', 'work_stress_interaction',
            'social_mood_interaction',

            # Historical energy
            'energy_avg_7d', 'energy_trend_7d', 'energy_volatility_7d'
        ]

        if model_path and model_path.exists():
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize a new XGBoost model with optimal hyperparameters."""
        self.model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='reg:squarederror',
            random_state=42,
            n_jobs=-1,
            tree_method='hist'
        )
        self.scaler = StandardScaler()

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict energy level from features.

        Args:
            features: Dictionary of feature values

        Returns:
            Dictionary with prediction, confidence, and feature importance
        """
        if self.model is None:
            # Fallback to heuristic if model not trained
            return self._heuristic_prediction(features)

        # Prepare feature vector
        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])

        # Scale features
        if self.scaler:
            X = self.scaler.transform(X)

        # Predict
        prediction = self.model.predict(X)[0]

        # Clamp to [0, 1]
        prediction = float(np.clip(prediction, 0.0, 1.0))

        # Get feature importance
        feature_importance = {}
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            top_features = sorted(
                zip(self.feature_names, importances),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            feature_importance = {name: float(imp) for name, imp in top_features}

        return {
            'prediction': prediction,
            'confidence': 0.85,  # TODO: Calculate actual confidence interval
            'top_features': feature_importance,
            'model_version': '1.0.0'
        }

    def _heuristic_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fallback heuristic prediction when model is not trained."""
        sleep_score = features.get('sleep_duration_avg_7d', 0.5) / 8.0
        exercise_score = min(features.get('exercise_minutes_7d', 0) / 150.0, 1.0)
        mood_score = features.get('mood_avg_7d', 0.5)
        work_penalty = min(features.get('work_hours_7d', 40) / 60.0, 1.0) * 0.3

        prediction = (
            sleep_score * 0.4 +
            exercise_score * 0.2 +
            mood_score * 0.3 +
            (1 - work_penalty) * 0.1
        )

        return {
            'prediction': float(np.clip(prediction, 0.0, 1.0)),
            'confidence': 0.6,
            'top_features': {
                'sleep_duration_avg_7d': 0.4,
                'mood_avg_7d': 0.3,
                'exercise_minutes_7d': 0.2
            },
            'model_version': 'heuristic'
        }

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Train the energy prediction model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target energy levels (n_samples,)

        Returns:
            Training metrics
        """
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train model
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_val_scaled, y_val)],
            verbose=False
        )

        # Evaluate
        y_pred = self.model.predict(X_val_scaled)

        metrics = {
            'rmse': float(np.sqrt(mean_squared_error(y_val, y_pred))),
            'mae': float(mean_absolute_error(y_val, y_pred)),
            'r2': float(r2_score(y_val, y_pred)),
            'n_samples': len(X),
            'n_features': X.shape[1]
        }

        return metrics

    def save_model(self, path: Path):
        """Save model and scaler to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'version': '1.0.0'
        }

        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

    def load_model(self, path: Path):
        """Load model and scaler from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)

        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data.get('feature_names', self.feature_names)
