"""
Machine Learning background tasks - Model training, predictions, etc.
"""
from celery import shared_task
from typing import Dict, Any
import asyncio

from app.core.celery_app import celery_app
from app.core.database import async_session
from app.ml.models.model_trainer import ModelTrainer


@celery_app.task(name="app.tasks.ml_tasks.retrain_energy_model")
def retrain_energy_model(user_ids: list = None) -> Dict[str, Any]:
    """
    Retrain energy prediction model with latest data.

    Args:
        user_ids: Optional list of users to include in training

    Returns:
        Training metrics and model info
    """
    async def _train():
        async with async_session() as db:
            trainer = ModelTrainer(db)
            return await trainer.train_energy_model(user_ids=user_ids)

    return asyncio.run(_train())


@celery_app.task(name="app.tasks.ml_tasks.retrain_mood_model")
def retrain_mood_model(user_ids: list = None) -> Dict[str, Any]:
    """Retrain mood prediction model with latest data."""
    async def _train():
        async with async_session() as db:
            trainer = ModelTrainer(db)
            return await trainer.train_mood_model(user_ids=user_ids)

    return asyncio.run(_train())


@celery_app.task(name="app.tasks.ml_tasks.retrain_all_models")
def retrain_all_models() -> Dict[str, Any]:
    """Retrain all ML models (scheduled daily)."""
    results = {}

    # Retrain energy model
    results['energy'] = retrain_energy_model.delay().get()

    # Retrain mood model
    results['mood'] = retrain_mood_model.delay().get()

    return results


@celery_app.task(name="app.tasks.ml_tasks.batch_predictions")
def batch_predictions(user_ids: list) -> Dict[str, Any]:
    """
    Generate predictions for multiple users in batch.

    Args:
        user_ids: List of user IDs to generate predictions for

    Returns:
        Prediction results for all users
    """
    import logging
    logger = logging.getLogger(__name__)

    async def _predict():
        from app.ai.datagenius import DataGeniusService

        async with async_session() as db:
            results = {}
            errors = 0

            for user_id in user_ids:
                try:
                    datagenius = DataGeniusService(db)

                    # Generate predictions
                    energy_pred = await datagenius.predict_energy(user_id, "morning")
                    mood_pred = await datagenius.predict_mood(user_id)

                    results[user_id] = {
                        'energy': energy_pred.get("predicted_energy"),
                        'mood': mood_pred.get("predicted_mood_score"),
                        'success': True
                    }

                    logger.info(f"Generated predictions for user {user_id}")

                except Exception as e:
                    logger.error(f"Prediction failed for user {user_id}: {e}")
                    results[user_id] = {
                        'success': False,
                        'error': str(e)
                    }
                    errors += 1

            return {
                'success': True,
                'user_count': len(user_ids),
                'successful_predictions': len(user_ids) - errors,
                'errors': errors,
                'results': results
            }

    return asyncio.run(_predict())
