"""
Celery Tasks for Integration Auto-Sync

Background tasks for:
- Automatic integration syncing
- Webhook processing
- Data processing from synced data
- Error handling & retry
"""
from celery import shared_task
from sqlalchemy import select
from datetime import datetime, timedelta
import logging

from app.database import SessionLocal
from app.models.integrations import UserIntegration, IntegrationProvider
from app.services.integrations.google_calendar import GoogleCalendarIntegration
from app.services.integrations.fitbit import FitbitIntegration
from app.services.integrations.oura import OuraIntegration
from app.config import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_all_due_integrations(self):
    """
    Sync all integrations that are due for syncing.

    Runs periodically (e.g., every hour).
    """
    db = SessionLocal()

    try:
        # Find all integrations due for sync
        now = datetime.utcnow()

        result = db.execute(
            select(UserIntegration).where(
                UserIntegration.is_active == True,
                UserIntegration.is_authorized == True,
                UserIntegration.auto_sync == True,
                UserIntegration.next_sync_at <= now
            )
        )

        integrations = result.scalars().all()

        logger.info(f"Found {len(integrations)} integrations due for sync")

        synced_count = 0
        failed_count = 0

        for integration in integrations:
            try:
                # Queue individual sync task
                sync_integration.delay(integration.id)
                synced_count += 1

            except Exception as e:
                logger.error(f"Failed to queue sync for integration {integration.id}: {e}")
                failed_count += 1

        return {
            'total': len(integrations),
            'queued': synced_count,
            'failed': failed_count
        }

    except Exception as e:
        logger.error(f"Error in sync_all_due_integrations: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def sync_integration(self, integration_id: int):
    """
    Sync a specific integration.

    Args:
        integration_id: UserIntegration ID to sync
    """
    db = SessionLocal()

    try:
        # Get integration
        integration = db.get(UserIntegration, integration_id)

        if not integration:
            logger.warning(f"Integration {integration_id} not found")
            return {'success': False, 'error': 'Integration not found'}

        if not integration.is_active or not integration.is_authorized:
            logger.info(f"Integration {integration_id} is not active/authorized")
            return {'success': False, 'error': 'Integration not active'}

        # Get integration service
        service = _get_integration_service(db, integration)

        if not service:
            logger.error(f"Unknown provider: {integration.provider}")
            return {'success': False, 'error': 'Unknown provider'}

        # Sync data
        logger.info(f"Syncing integration {integration_id} ({integration.provider})")

        # Default to last 7 days
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        import asyncio
        result = asyncio.run(service.sync_data(start_date, end_date))

        if result['success']:
            logger.info(f"Successfully synced integration {integration_id}: {result.get('records_synced', 0)} records")

            # Queue data processing
            process_synced_data.delay(integration_id)

        else:
            logger.error(f"Failed to sync integration {integration_id}: {result.get('error')}")

            # Increment error count
            integration.error_count += 1
            integration.last_error = result.get('error')
            db.commit()

        return result

    except Exception as e:
        logger.error(f"Error syncing integration {integration_id}: {e}")

        # Update error count
        integration = db.get(UserIntegration, integration_id)
        if integration:
            integration.error_count += 1
            integration.last_error = str(e)
            db.commit()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def process_synced_data(self, integration_id: int):
    """
    Process synced data into life events.

    Converts raw synced data into meaningful life events.

    Args:
        integration_id: UserIntegration ID
    """
    db = SessionLocal()

    try:
        from app.models.integrations import SyncedData
        from app.models.life_event import LifeEvent

        # Get unprocessed synced data for this integration
        result = db.execute(
            select(SyncedData).where(
                SyncedData.integration_id == integration_id,
                SyncedData.is_processed == False
            ).limit(100)  # Process in batches
        )

        synced_data_records = result.scalars().all()

        logger.info(f"Processing {len(synced_data_records)} synced records for integration {integration_id}")

        processed_count = 0

        for synced_data in synced_data_records:
            try:
                # Process based on data type
                life_event = _create_life_event_from_synced_data(db, synced_data)

                if life_event:
                    synced_data.is_processed = True
                    synced_data.processed_at = datetime.utcnow()
                    synced_data.life_event_id = life_event.id
                    processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process synced data {synced_data.id}: {e}")

        db.commit()

        logger.info(f"Processed {processed_count}/{len(synced_data_records)} records")

        return {
            'success': True,
            'processed': processed_count,
            'total': len(synced_data_records)
        }

    except Exception as e:
        logger.error(f"Error processing synced data for integration {integration_id}: {e}")
        raise self.retry(exc=e, countdown=120)

    finally:
        db.close()


@shared_task
def process_integration_webhook(integration_id: int, event_type: str, payload: dict):
    """
    Process incoming webhook from integration.

    Args:
        integration_id: UserIntegration ID
        event_type: Type of webhook event
        payload: Webhook payload
    """
    db = SessionLocal()

    try:
        integration = db.get(UserIntegration, integration_id)

        if not integration:
            logger.warning(f"Integration {integration_id} not found for webhook")
            return {'success': False}

        service = _get_integration_service(db, integration)

        if not service or not service.SUPPORTS_WEBHOOKS:
            logger.warning(f"Integration {integration_id} does not support webhooks")
            return {'success': False}

        # Handle webhook
        import asyncio
        result = asyncio.run(service.handle_webhook(event_type, payload))

        logger.info(f"Webhook processed for integration {integration_id}: {result}")

        # Queue data processing if new data synced
        if result.get('success') and result.get('records_synced', 0) > 0:
            process_synced_data.delay(integration_id)

        return result

    except Exception as e:
        logger.error(f"Error processing webhook for integration {integration_id}: {e}")
        return {'success': False, 'error': str(e)}

    finally:
        db.close()


def _get_integration_service(db, integration: UserIntegration):
    """Get integration service instance for provider."""
    provider = integration.provider

    # Get credentials from settings
    # In production, these would be in environment variables
    credentials = {
        'google_calendar': {
            'client_id': settings.GOOGLE_CALENDAR_CLIENT_ID,
            'client_secret': settings.GOOGLE_CALENDAR_CLIENT_SECRET
        },
        'fitbit': {
            'client_id': getattr(settings, 'FITBIT_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'FITBIT_CLIENT_SECRET', '')
        },
        'oura': {
            'client_id': getattr(settings, 'OURA_CLIENT_ID', ''),
            'client_secret': getattr(settings, 'OURA_CLIENT_SECRET', '')
        }
    }

    if provider == IntegrationProvider.GOOGLE_CALENDAR:
        creds = credentials.get('google_calendar', {})
        return GoogleCalendarIntegration(
            db=db,
            user_integration=integration,
            client_id=creds.get('client_id', ''),
            client_secret=creds.get('client_secret', '')
        )

    elif provider == IntegrationProvider.FITBIT:
        creds = credentials.get('fitbit', {})
        return FitbitIntegration(
            db=db,
            user_integration=integration,
            client_id=creds.get('client_id', ''),
            client_secret=creds.get('client_secret', '')
        )

    elif provider == IntegrationProvider.OURA:
        creds = credentials.get('oura', {})
        return OuraIntegration(
            db=db,
            user_integration=integration,
            client_id=creds.get('client_id', ''),
            client_secret=creds.get('client_secret', '')
        )

    return None


def _create_life_event_from_synced_data(db, synced_data):
    """
    Create LifeEvent from SyncedData.

    Maps external data to our life event schema.
    """
    from app.models.life_event import LifeEvent

    data_type = synced_data.data_type
    raw_data = synced_data.raw_data

    # Calendar events
    if data_type == 'calendar_event':
        event = LifeEvent(
            user_id=synced_data.user_id,
            title=raw_data.get('summary', 'Calendar Event'),
            description=raw_data.get('description'),
            category='work' if 'meeting' in raw_data.get('summary', '').lower() else 'other',
            start_time=synced_data.data_timestamp,
            end_time=datetime.fromisoformat(raw_data.get('end', {}).get('dateTime', synced_data.data_timestamp.isoformat())),
            metadata={
                'source': 'google_calendar',
                'external_id': synced_data.external_id,
                'location': raw_data.get('location'),
                'attendees': raw_data.get('attendees', [])
            }
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # Fitbit sleep
    elif data_type == 'sleep_session':
        duration_ms = raw_data.get('duration', 0)
        duration_hours = duration_ms / (1000 * 60 * 60)

        event = LifeEvent(
            user_id=synced_data.user_id,
            title=f"Sleep ({duration_hours:.1f}h)",
            category='sleep',
            start_time=synced_data.data_timestamp,
            intensity=raw_data.get('efficiency', 85) / 10,  # Convert to 0-10 scale
            metadata={
                'source': 'fitbit',
                'duration_hours': duration_hours,
                'efficiency': raw_data.get('efficiency'),
                'stages': raw_data.get('levels', {}).get('summary', {}),
                'external_id': synced_data.external_id
            }
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # Fitbit activity
    elif data_type == 'activity_summary':
        steps = raw_data.get('steps', 0)

        event = LifeEvent(
            user_id=synced_data.user_id,
            title=f"Daily Activity ({steps} steps)",
            category='exercise',
            start_time=synced_data.data_timestamp,
            intensity=min(steps / 1000, 10),  # Rough scale
            metadata={
                'source': 'fitbit',
                'steps': steps,
                'calories': raw_data.get('caloriesOut'),
                'distance': raw_data.get('distances', [{}])[0].get('distance'),
                'active_minutes': raw_data.get('veryActiveMinutes', 0) + raw_data.get('fairlyActiveMinutes', 0)
            }
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # Oura sleep
    elif data_type == 'oura_daily_sleep':
        score = raw_data.get('score', 0)

        event = LifeEvent(
            user_id=synced_data.user_id,
            title=f"Sleep Score: {score}/100",
            category='sleep',
            start_time=synced_data.data_timestamp,
            intensity=score / 10,  # Convert to 0-10
            metadata={
                'source': 'oura',
                'score': score,
                'total_sleep': raw_data.get('contributors', {}).get('total_sleep'),
                'efficiency': raw_data.get('contributors', {}).get('efficiency'),
                'rem_sleep': raw_data.get('contributors', {}).get('rem_sleep'),
                'deep_sleep': raw_data.get('contributors', {}).get('deep_sleep'),
                'latency': raw_data.get('contributors', {}).get('latency')
            }
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # Oura readiness
    elif data_type == 'oura_daily_readiness':
        score = raw_data.get('score', 0)

        event = LifeEvent(
            user_id=synced_data.user_id,
            title=f"Readiness Score: {score}/100",
            category='health',
            start_time=synced_data.data_timestamp,
            intensity=score / 10,
            metadata={
                'source': 'oura',
                'readiness_score': score,
                'temperature_deviation': raw_data.get('contributors', {}).get('temperature_deviation'),
                'hrv_balance': raw_data.get('contributors', {}).get('hrv_balance'),
                'recovery_index': raw_data.get('contributors', {}).get('recovery_index')
            }
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    return None


# Periodic task configuration (in celeryconfig.py or similar):
"""
from celery.schedules import crontab

beat_schedule = {
    'sync-integrations-hourly': {
        'task': 'app.tasks.integration_tasks.sync_all_due_integrations',
        'schedule': crontab(minute=0),  # Every hour
    },
}
"""
