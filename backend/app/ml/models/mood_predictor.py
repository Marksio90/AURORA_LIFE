"""
Mood Prediction Model using LightGBM
"""
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler


class MoodPredictor:
    """
    Predicts user mood state using LightGBM classifier.

    Predicts mood categories:
    - 0: Very Low (depression, sadness)
    - 1: Low (mild negative emotions)
    - 2: Neutral (balanced state)
    - 3: Good (positive, happy)
    - 4: Excellent (euphoric, energized)
    """

    MOOD_LABELS = {
        0: 'very_low',
        1: 'low',
        2: 'neutral',
        3: 'good',
        4: 'excellent'
    }

    def __init__(self, model_path: Optional[Path] = None):
        self.model: Optional[lgb.LGBMClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names = [
            # Sleep features
            'sleep_quality_avg_7d', 'sleep_deficit_7d',

            # Social features
            'social_interactions_7d', 'meaningful_conversations_7d',
            'social_satisfaction_7d',

            # Activity features
            'exercise_minutes_7d', 'outdoor_time_7d',
            'productive_hours_7d',

            # Emotional history
            'mood_avg_7d', 'mood_volatility_7d',
            'positive_events_7d', 'negative_events_7d',

            # Stress features
            'work_stress_7d', 'life_stress_7d',
            'relaxation_time_7d',

            # Health features
            'nutrition_quality_7d', 'illness_days_7d',

            # Temporal features
            'day_of_week', 'is_weekend', 'season',

            # Achievement features
            'goals_completed_7d', 'progress_score_7d'
        ]

        if model_path and model_path.exists():
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize a new LightGBM model."""
        self.model = lgb.LGBMClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.05,
            num_leaves=31,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='multiclass',
            num_class=5,
            random_state=42,
            n_jobs=-1,
            verbose=-1
        )
        self.scaler = StandardScaler()

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict mood category and probabilities.

        Args:
            features: Dictionary of feature values

        Returns:
            Dictionary with prediction, probabilities, and insights
        """
        if self.model is None:
            return self._heuristic_prediction(features)

        # Prepare feature vector
        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])

        # Scale features
        if self.scaler:
            X = self.scaler.transform(X)

        # Predict
        prediction = int(self.model.predict(X)[0])
        probabilities = self.model.predict_proba(X)[0]

        # Get top influencing features
        feature_importance = self._get_feature_importance()

        return {
            'mood_category': self.MOOD_LABELS[prediction],
            'mood_score': float(prediction / 4.0),  # Normalize to 0-1
            'probabilities': {
                self.MOOD_LABELS[i]: float(prob)
                for i, prob in enumerate(probabilities)
            },
            'confidence': float(probabilities[prediction]),
            'top_features': feature_importance,
            'model_version': '1.0.0'
        }

    def predict_regression(self, features: Dict[str, float]) -> float:
        """
        Predict mood as continuous value (0-1) instead of categories.

        Args:
            features: Dictionary of feature values

        Returns:
            Mood score between 0 and 1
        """
        result = self.predict(features)

        # Weighted average based on probabilities
        mood_score = sum(
            (i / 4.0) * result['probabilities'][self.MOOD_LABELS[i]]
            for i in range(5)
        )

        return float(mood_score)

    def _heuristic_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fallback heuristic when model not trained."""
        social_score = min(features.get('social_interactions_7d', 0) / 10.0, 1.0)
        sleep_score = features.get('sleep_quality_avg_7d', 0.5)
        exercise_score = min(features.get('exercise_minutes_7d', 0) / 150.0, 1.0)
        stress_penalty = features.get('work_stress_7d', 0.5)

        mood_score = (
            social_score * 0.3 +
            sleep_score * 0.25 +
            exercise_score * 0.2 +
            (1 - stress_penalty) * 0.25
        )

        # Map to category
        if mood_score < 0.2:
            category = 0
        elif mood_score < 0.4:
            category = 1
        elif mood_score < 0.6:
            category = 2
        elif mood_score < 0.8:
            category = 3
        else:
            category = 4

        return {
            'mood_category': self.MOOD_LABELS[category],
            'mood_score': float(mood_score),
            'probabilities': {label: 0.2 for label in self.MOOD_LABELS.values()},
            'confidence': 0.6,
            'top_features': {},
            'model_version': 'heuristic'
        }

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get top important features for the prediction."""
        if not hasattr(self.model, 'feature_importances_'):
            return {}

        importances = self.model.feature_importances_
        top_features = sorted(
            zip(self.feature_names, importances),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {name: float(imp) for name, imp in top_features}

    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train the mood prediction model."""
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, f1_score, classification_report

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train model
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = self.model.predict(X_val_scaled)

        metrics = {
            'accuracy': float(accuracy_score(y_val, y_pred)),
            'f1_score': float(f1_score(y_val, y_pred, average='weighted')),
            'n_samples': len(X),
            'n_features': X.shape[1],
            'class_distribution': {
                self.MOOD_LABELS[i]: int(np.sum(y == i))
                for i in range(5)
            }
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
