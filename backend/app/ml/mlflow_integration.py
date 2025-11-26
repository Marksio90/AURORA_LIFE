"""
MLflow integration for ML model versioning and tracking.

Features:
- Model versioning
- Experiment tracking
- Model registry
- Artifact storage
- Metrics logging
- Model deployment tracking
"""

import mlflow
from mlflow.tracking import MlflowClient
from typing import Dict, Any, Optional
from datetime import datetime
import numpy as np
from pathlib import Path

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure MLflow
mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI or "sqlite:///mlflow.db")
mlflow.set_experiment("aurora_life_ml")


class MLflowModelTracker:
    """Service for tracking ML models with MLflow."""

    def __init__(self):
        self.client = MlflowClient()

    def start_run(self, run_name: str) -> str:
        """Start a new MLflow run."""
        run = mlflow.start_run(run_name=run_name)
        logger.info(f"Started MLflow run: {run.info.run_id}")
        return run.info.run_id

    def log_params(self, params: Dict[str, Any]):
        """Log model parameters."""
        for key, value in params.items():
            mlflow.log_param(key, value)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log model metrics."""
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=step)

    def log_model(
        self,
        model,
        model_name: str,
        artifact_path: str = "model",
        signature: Optional[Any] = None
    ):
        """
        Log model to MLflow.

        Args:
            model: Trained model object
            model_name: Name for the model
            artifact_path: Path within run artifacts
            signature: MLflow model signature
        """
        if hasattr(model, 'save_model'):
            # XGBoost/LightGBM models
            import tempfile
            import joblib

            with tempfile.TemporaryDirectory() as tmpdir:
                model_path = Path(tmpdir) / f"{model_name}.pkl"
                joblib.dump(model, model_path)
                mlflow.log_artifact(str(model_path), artifact_path)
        else:
            # Scikit-learn models
            mlflow.sklearn.log_model(
                model,
                artifact_path,
                registered_model_name=model_name,
                signature=signature
            )

        logger.info(f"Logged model: {model_name}")

    def register_model(
        self,
        model_uri: str,
        model_name: str,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Register model in MLflow Model Registry.

        Returns:
            Model version
        """
        result = mlflow.register_model(model_uri, model_name)

        if tags:
            for key, value in tags.items():
                self.client.set_model_version_tag(
                    model_name,
                    result.version,
                    key,
                    value
                )

        logger.info(f"Registered model {model_name} version {result.version}")

        return result.version

    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str  # "Staging", "Production", "Archived"
    ):
        """Transition model to a different stage."""
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage
        )

        logger.info(f"Transitioned {model_name} v{version} to {stage}")

    def get_model_version(self, model_name: str, stage: str = "Production"):
        """Get model version in specified stage."""
        versions = self.client.get_latest_versions(model_name, stages=[stage])

        if versions:
            return versions[0].version

        return None

    def load_model(self, model_name: str, version: Optional[str] = None):
        """Load a model from MLflow."""
        if version:
            model_uri = f"models:/{model_name}/{version}"
        else:
            model_uri = f"models:/{model_name}/Production"

        try:
            model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Loaded model {model_name} from {model_uri}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return None

    def end_run(self):
        """End the current MLflow run."""
        mlflow.end_run()


# Integration with existing model training
def train_with_mlflow(
    model_type: str,
    model,
    X_train,
    y_train,
    X_test,
    y_test,
    hyperparameters: Dict[str, Any]
):
    """
    Train model with MLflow tracking.

    Args:
        model_type: "energy" or "mood"
        model: Model instance
        X_train, y_train: Training data
        X_test, y_test: Test data
        hyperparameters: Model hyperparameters
    """
    tracker = MLflowModelTracker()

    # Start run
    run_name = f"{model_type}_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    tracker.start_run(run_name)

    try:
        # Log parameters
        tracker.log_params(hyperparameters)
        tracker.log_params({
            "model_type": model_type,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "features": X_train.shape[1] if hasattr(X_train, 'shape') else len(X_train[0])
        })

        # Train model
        model.fit(X_train, y_train)

        # Evaluate
        if model_type == "energy":
            # Regression metrics
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

            y_pred = model.predict(X_test)

            metrics = {
                "mae": mean_absolute_error(y_test, y_pred),
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "r2": r2_score(y_test, y_pred)
            }
        else:
            # Classification metrics
            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

            y_pred = model.predict(X_test)

            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "f1": f1_score(y_test, y_pred, average='weighted'),
                "precision": precision_score(y_test, y_pred, average='weighted'),
                "recall": recall_score(y_test, y_pred, average='weighted')
            }

        # Log metrics
        tracker.log_metrics(metrics)

        # Log model
        tracker.log_model(model, f"aurora_{model_type}_predictor")

        # Register model if metrics are good
        if (model_type == "energy" and metrics["r2"] > 0.7) or \
           (model_type == "mood" and metrics["accuracy"] > 0.65):

            model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
            version = tracker.register_model(
                model_uri,
                f"aurora_{model_type}_predictor",
                tags={
                    "trained_at": datetime.now().isoformat(),
                    "model_type": model_type
                }
            )

            # Auto-promote to Production if metrics are excellent
            if (model_type == "energy" and metrics["r2"] > 0.8) or \
               (model_type == "mood" and metrics["accuracy"] > 0.75):
                tracker.transition_model_stage(
                    f"aurora_{model_type}_predictor",
                    version,
                    "Production"
                )

        logger.info(f"Model training completed with metrics: {metrics}")

        return model, metrics

    finally:
        tracker.end_run()


# Example usage in model training pipeline:
"""
from app.ml.mlflow_integration import train_with_mlflow

# Train energy model
energy_model, metrics = train_with_mlflow(
    model_type="energy",
    model=xgb.XGBRegressor(**hyperparameters),
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
    hyperparameters=hyperparameters
)

# Load production model
tracker = MLflowModelTracker()
production_model = tracker.load_model("aurora_energy_predictor")
"""
