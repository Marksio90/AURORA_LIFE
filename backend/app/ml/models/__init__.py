"""
Machine Learning models for AURORA_LIFE predictions

Includes:
- Basic predictors (Energy, Mood)
- Advanced forecasting (Prophet, LSTM)
- Anomaly detection (Isolation Forest, Autoencoders)
- Explainable AI (SHAP)
- Reinforcement Learning (Multi-Armed Bandits, Q-Learning)
"""
from .energy_predictor import EnergyPredictor
from .mood_predictor import MoodPredictor
from .model_trainer import ModelTrainer
from .time_series_forecaster import TimeSeriesForecaster
from .anomaly_detector import AnomalyDetector
from .explainable_ai import ExplainableAI
from .rl_recommender import (
    MultiArmedBandit,
    ContextualBandit,
    QLearningRecommender,
    RecommenderSystem
)

__all__ = [
    # Basic predictors
    "EnergyPredictor",
    "MoodPredictor",
    "ModelTrainer",

    # Advanced ML
    "TimeSeriesForecaster",
    "AnomalyDetector",
    "ExplainableAI",

    # Reinforcement Learning
    "MultiArmedBandit",
    "ContextualBandit",
    "QLearningRecommender",
    "RecommenderSystem"
]
