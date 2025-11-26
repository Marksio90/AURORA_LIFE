"""
Analytics background tasks - Data processing, cleanup, insights generation
"""
from celery import shared_task
from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging

from app.core.celery_app import celery_app
from app.core.database import async_session
from app.ai.datagenius import DataGeniusService
from sqlalchemy import select, delete
from app.models.user import User

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.analytics_tasks.generate_daily_insights")
def generate_daily_insights() -> Dict[str, Any]:
    """
    Generate daily insights for all active users (scheduled task).

    Returns:
        Processing statistics
    """
    async def _generate():
        async with async_session() as db:
            # Get all active user IDs (optimized: only select id column)
            result = await db.execute(
                select(User.id).where(User.is_active == True)
            )
            user_ids = result.scalars().all()

            insights_generated = 0
            errors = 0

            for user_id in user_ids:
                try:
                    # Generate insights using DataGenius
                    datagenius = DataGeniusService(db)
                    analysis = await datagenius.analyze_user_patterns(user_id, days=7)

                    if analysis.get("message") != "No data available for analysis":
                        insights_generated += 1
                        logger.info(f"Generated daily insights for user {user_id}")
                    else:
                        logger.debug(f"Insufficient data for user {user_id}")

                except Exception as e:
                    logger.error(f"Failed to generate insights for user {user_id}: {e}")
                    errors += 1

            return {
                'success': True,
                'users_processed': len(user_ids),
                'insights_generated': insights_generated,
                'errors': errors,
                'timestamp': datetime.utcnow().isoformat()
            }

    return asyncio.run(_generate())


@celery_app.task(name="app.tasks.analytics_tasks.cleanup_old_data")
def cleanup_old_data(days_to_keep: int = 365) -> Dict[str, Any]:
    """
    Cleanup old data beyond retention period (scheduled weekly).

    Args:
        days_to_keep: Number of days to keep data

    Returns:
        Cleanup statistics
    """
    async def _cleanup():
        async with async_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Clean up old events (if Events model exists)
            # This is a template - adjust based on actual models
            events_deleted = 0
            entries_deleted = 0

            try:
                # Example: Delete old events
                # from app.models.event import Event
                # result = await db.execute(
                #     delete(Event).where(Event.created_at < cutoff_date)
                # )
                # events_deleted = result.rowcount
                # await db.commit()

                logger.info(f"Cleanup completed. Cutoff date: {cutoff_date}")

            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
                await db.rollback()
                raise

            return {
                'success': True,
                'cutoff_date': cutoff_date.isoformat(),
                'events_deleted': events_deleted,
                'entries_deleted': entries_deleted
            }

    return asyncio.run(_cleanup())


@celery_app.task(name="app.tasks.analytics_tasks.calculate_user_metrics")
def calculate_user_metrics(user_id: int) -> Dict[str, Any]:
    """
    Calculate and update all metrics for a specific user.

    Args:
        user_id: User ID

    Returns:
        Updated metrics
    """
    async def _calculate():
        async with async_session() as db:
            try:
                datagenius = DataGeniusService(db)

                # Predict current metrics
                energy = await datagenius.predict_energy(user_id, "morning")
                mood = await datagenius.predict_mood(user_id)

                # Update user metrics
                user = await db.get(User, user_id)
                if user:
                    user.energy_score = energy.get("predicted_energy", 5.0) / 10.0
                    user.mood_score = mood.get("predicted_mood_score", 5.0) / 10.0
                    await db.commit()

                    logger.info(f"Updated metrics for user {user_id}")

                    return {
                        'success': True,
                        'user_id': user_id,
                        'metrics_updated': ['energy_score', 'mood_score']
                    }
                else:
                    return {
                        'success': False,
                        'user_id': user_id,
                        'error': 'User not found'
                    }

            except Exception as e:
                logger.error(f"Failed to calculate metrics for user {user_id}: {e}")
                return {
                    'success': False,
                    'user_id': user_id,
                    'error': str(e)
                }

    return asyncio.run(_calculate())
