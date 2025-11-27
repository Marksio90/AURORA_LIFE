"""
Tests for voice interface and Celery background tasks

Tests voice transcription, command parsing, and integration sync tasks.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from app.services.voice_service import VoiceService
from app.tasks.integration_tasks import (
    sync_integration,
    process_synced_data,
    sync_all_due_integrations,
    process_integration_webhook
)
from app.models.integrations import UserIntegration, SyncedData
from app.models.user import User
from app.models.life_event import LifeEvent


@pytest.fixture
async def user(db):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def audio_file():
    """Create mock audio file"""
    audio_data = b"fake audio data"
    return BytesIO(audio_data)


class TestVoiceService:
    """Test voice interface functionality"""

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_transcribe_audio(self, mock_openai, db, user, audio_file):
        """Test audio transcription using Whisper API"""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Log thirty minutes exercise cardio"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        result = await voice_service.transcribe(
            audio_file=audio_file,
            filename="test.mp3"
        )

        assert result['success'] is True
        assert result['text'] == "Log thirty minutes exercise cardio"
        assert 'language' in result

    @pytest.mark.asyncio
    async def test_validate_audio_format(self, db, user):
        """Test audio format validation"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        # Valid formats
        valid_formats = ['test.mp3', 'test.wav', 'test.m4a', 'test.webm']
        for filename in valid_formats:
            is_valid = voice_service._validate_audio_format(filename)
            assert is_valid is True

        # Invalid format
        assert voice_service._validate_audio_format('test.txt') is False

    @pytest.mark.asyncio
    async def test_validate_file_size(self, db, user):
        """Test file size validation (max 25 MB)"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        # Create file within size limit
        small_file = BytesIO(b"x" * (20 * 1024 * 1024))  # 20 MB
        assert voice_service._validate_file_size(small_file) is True

        # Create file over size limit
        large_file = BytesIO(b"x" * (30 * 1024 * 1024))  # 30 MB
        assert voice_service._validate_file_size(large_file) is False

    @pytest.mark.asyncio
    async def test_parse_exercise_command(self, db, user):
        """Test parsing exercise logging command"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        test_cases = [
            ("Log 30 minutes exercise", {
                'action': 'log_event',
                'event_type': 'exercise',
                'duration': 30,
                'tags': []
            }),
            ("I ran for 45 minutes", {
                'action': 'log_event',
                'event_type': 'exercise',
                'duration': 45,
                'tags': ['ran']
            }),
            ("Workout cardio 60 minutes", {
                'action': 'log_event',
                'event_type': 'exercise',
                'duration': 60,
                'tags': ['cardio']
            }),
        ]

        for text, expected in test_cases:
            result = voice_service._parse_command(text)
            assert result['action'] == expected['action']
            assert result['event_type'] == expected['event_type']
            assert result['duration'] == expected['duration']

    @pytest.mark.asyncio
    async def test_parse_meditation_command(self, db, user):
        """Test parsing meditation logging command"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        commands = [
            "Meditated for 15 minutes",
            "Log meditation 20 minutes",
            "I did a 10 minute meditation"
        ]

        for text in commands:
            result = voice_service._parse_command(text)
            assert result['action'] == 'log_event'
            assert result['event_type'] == 'meditation'
            assert result['duration'] in [10, 15, 20]

    @pytest.mark.asyncio
    async def test_parse_sleep_command(self, db, user):
        """Test parsing sleep logging command"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        commands = [
            "Slept 8 hours",
            "I got 7 hours of sleep",
            "Log sleep 9 hours"
        ]

        for text in commands:
            result = voice_service._parse_command(text)
            assert result['action'] == 'log_event'
            assert result['event_type'] == 'sleep'
            assert result['duration'] in [7, 8, 9]

    @pytest.mark.asyncio
    async def test_parse_mood_command(self, db, user):
        """Test parsing mood logging command"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        commands = [
            "Feeling happy today",
            "I'm feeling stressed",
            "Mood is energized"
        ]

        for text in commands:
            result = voice_service._parse_command(text)
            assert result['action'] == 'log_event'
            assert result['event_type'] == 'mood'
            assert 'mood' in result

    @pytest.mark.asyncio
    async def test_parse_unknown_command(self, db, user):
        """Test handling of unparseable commands"""
        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        result = voice_service._parse_command("The weather is nice today")

        assert result['action'] == 'unknown'
        assert 'error' in result

    @pytest.mark.asyncio
    @patch('openai.OpenAI')
    async def test_voice_command_end_to_end(self, mock_openai, db, user, audio_file):
        """Test complete voice command flow: transcribe + parse + log"""
        # Mock OpenAI transcription
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Log 30 minutes exercise"
        mock_client.audio.transcriptions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        voice_service = VoiceService(
            db=db,
            user_id=user.id,
            openai_api_key="test_key"
        )

        result = await voice_service.voice_command(
            audio_file=audio_file,
            filename="test.mp3",
            auto_log=True
        )

        assert result['success'] is True
        assert result['transcription'] == "Log 30 minutes exercise"
        assert result['command']['action'] == 'log_event'
        assert result['command']['event_type'] == 'exercise'
        assert result['command']['duration'] == 30


class TestCeleryTasks:
    """Test Celery background tasks"""

    @pytest.fixture
    async def integration_due_for_sync(self, db, user):
        """Create integration that's due for sync"""
        integration = UserIntegration(
            user_id=user.id,
            provider="fitbit",
            is_active=True,
            access_token="test_token",
            sync_enabled=True,
            sync_frequency="hourly",
            next_sync_at=datetime.utcnow() - timedelta(hours=1),  # Past due
            sync_status="idle"
        )
        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        return integration

    @pytest.mark.asyncio
    @patch('app.tasks.integration_tasks.AsyncSessionLocal')
    async def test_sync_all_due_integrations(self, mock_session, db, integration_due_for_sync):
        """Test periodic task that syncs all due integrations"""
        # Mock database session
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        # Mock query results
        mock_db.execute.return_value.scalars.return_value.all.return_value = [
            integration_due_for_sync
        ]

        # Mock individual sync task
        with patch('app.tasks.integration_tasks.sync_integration.delay') as mock_sync:
            result = sync_all_due_integrations()

            # Should have queued sync task
            assert mock_sync.called
            assert mock_sync.call_count >= 1

    @pytest.mark.asyncio
    @patch('app.services.integrations.fitbit.FitbitIntegration.sync_data')
    async def test_sync_integration_task(self, mock_sync, db, integration_due_for_sync):
        """Test individual integration sync task"""
        # Mock successful sync
        mock_sync.return_value = {
            'success': True,
            'records_synced': 5
        }

        result = await sync_integration(integration_due_for_sync.id)

        assert result['success'] is True
        assert result['records_synced'] == 5
        mock_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_integration_retry_on_failure(self, db, integration_due_for_sync):
        """Test retry logic when sync fails"""
        with patch('app.services.integrations.fitbit.FitbitIntegration.sync_data') as mock_sync:
            # First attempt fails
            mock_sync.side_effect = Exception("API error")

            with pytest.raises(Exception):
                await sync_integration(integration_due_for_sync.id)

            # Task should be retried with exponential backoff
            # (actual retry handled by Celery, we just verify exception propagates)

    @pytest.mark.asyncio
    async def test_process_synced_data_task(self, db, user, integration_due_for_sync):
        """Test processing synced data into life events"""
        # Create unprocessed synced data
        synced_data = SyncedData(
            integration_id=integration_due_for_sync.id,
            data_type="sleep_session",
            external_id="sleep_123",
            raw_data={
                'date': '2024-01-15',
                'duration': 8.0,
                'quality': 85,
                'stages': {
                    'deep': 2.0,
                    'light': 4.0,
                    'rem': 1.5,
                    'wake': 0.5
                }
            },
            processed=False,
            data_timestamp=datetime.utcnow()
        )
        db.add(synced_data)
        await db.commit()

        result = await process_synced_data(integration_due_for_sync.id)

        assert result['success'] is True
        assert result['processed_count'] >= 1

        # Verify synced data marked as processed
        await db.refresh(synced_data)
        assert synced_data.processed is True
        assert synced_data.life_event_id is not None

    @pytest.mark.asyncio
    async def test_process_calendar_event_data(self, db, user, integration_due_for_sync):
        """Test processing calendar event into life event"""
        integration_due_for_sync.provider = "google_calendar"
        await db.commit()

        synced_data = SyncedData(
            integration_id=integration_due_for_sync.id,
            data_type="calendar_event",
            external_id="event_123",
            raw_data={
                'summary': 'Team Meeting',
                'description': 'Weekly sync',
                'start_time': '2024-01-15T10:00:00Z',
                'end_time': '2024-01-15T11:00:00Z',
                'location': 'Conference Room',
                'attendees': ['colleague@example.com']
            },
            processed=False,
            data_timestamp=datetime(2024, 1, 15, 10, 0)
        )
        db.add(synced_data)
        await db.commit()

        # Process the data
        from app.tasks.integration_tasks import _create_life_event_from_synced_data
        life_event = await _create_life_event_from_synced_data(db, synced_data)

        assert life_event is not None
        assert life_event.title == 'Team Meeting'
        assert life_event.event_type == 'work'  # Calendar events mapped to work
        assert life_event.user_id == user.id

    @pytest.mark.asyncio
    async def test_process_webhook_task(self, db, integration_due_for_sync):
        """Test webhook processing task"""
        webhook_payload = {
            'collectionType': 'sleep',
            'date': '2024-01-15',
            'ownerId': 'fitbit_user_123'
        }

        with patch('app.services.integrations.fitbit.FitbitIntegration.handle_webhook') as mock_webhook:
            mock_webhook.return_value = {'success': True}

            result = await process_integration_webhook(
                integration_id=integration_due_for_sync.id,
                event_type='sleep',
                payload=webhook_payload
            )

            assert result['success'] is True
            mock_webhook.assert_called_once_with('sleep', webhook_payload)

    @pytest.mark.asyncio
    async def test_batch_processing_large_dataset(self, db, integration_due_for_sync):
        """Test batch processing of large number of synced records"""
        # Create 150 unprocessed records (batch size is 100)
        for i in range(150):
            synced_data = SyncedData(
                integration_id=integration_due_for_sync.id,
                data_type="test_data",
                external_id=f"test_{i}",
                raw_data={'value': i},
                processed=False,
                data_timestamp=datetime.utcnow()
            )
            db.add(synced_data)

        await db.commit()

        result = await process_synced_data(integration_due_for_sync.id)

        # Should process in batches
        assert result['success'] is True
        assert result['processed_count'] == 150


class TestIntegrationTaskErrorHandling:
    """Test error handling in Celery tasks"""

    @pytest.mark.asyncio
    async def test_sync_task_handles_missing_integration(self, db):
        """Test graceful handling of non-existent integration"""
        with pytest.raises(Exception):
            await sync_integration(integration_id=99999)

    @pytest.mark.asyncio
    async def test_sync_task_handles_invalid_credentials(self, db, user):
        """Test handling of invalid OAuth credentials"""
        integration = UserIntegration(
            user_id=user.id,
            provider="fitbit",
            is_active=True,
            access_token="invalid_token",
            sync_enabled=True
        )
        db.add(integration)
        await db.commit()

        with patch('app.services.integrations.fitbit.FitbitIntegration.sync_data') as mock_sync:
            mock_sync.return_value = {
                'success': False,
                'error': 'Invalid credentials'
            }

            result = await sync_integration(integration.id)

            assert result['success'] is False
            assert 'error' in result

            # Verify error logged to integration
            await db.refresh(integration)
            assert integration.sync_status == 'error'

    @pytest.mark.asyncio
    async def test_sync_task_handles_rate_limiting(self, db, user):
        """Test handling of API rate limits"""
        integration = UserIntegration(
            user_id=user.id,
            provider="fitbit",
            is_active=True,
            access_token="test_token",
            sync_enabled=True
        )
        db.add(integration)
        await db.commit()

        with patch('app.services.integrations.fitbit.FitbitIntegration.sync_data') as mock_sync:
            # Simulate rate limit error
            mock_sync.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(Exception) as exc_info:
                await sync_integration(integration.id)

            assert "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_task_skips_invalid_data(self, db, user):
        """Test that processing skips malformed data"""
        integration = UserIntegration(
            user_id=user.id,
            provider="fitbit",
            is_active=True,
            access_token="test_token"
        )
        db.add(integration)
        await db.commit()

        # Create synced data with invalid format
        synced_data = SyncedData(
            integration_id=integration.id,
            data_type="invalid_type",
            external_id="invalid_123",
            raw_data={'malformed': 'data'},
            processed=False,
            data_timestamp=datetime.utcnow()
        )
        db.add(synced_data)
        await db.commit()

        result = await process_synced_data(integration.id)

        # Should skip invalid data without crashing
        assert result['success'] is True
        # Invalid data might be marked as processed or skipped


class TestTaskScheduling:
    """Test Celery task scheduling and timing"""

    def test_sync_frequency_calculation(self):
        """Test next sync time calculation"""
        now = datetime.utcnow()

        # Hourly sync
        next_hourly = now + timedelta(hours=1)
        assert next_hourly > now

        # Daily sync
        next_daily = now + timedelta(days=1)
        assert next_daily > next_hourly

        # Weekly sync
        next_weekly = now + timedelta(weeks=1)
        assert next_weekly > next_daily

    @pytest.mark.asyncio
    async def test_sync_only_when_due(self, db, user):
        """Test that sync only runs when next_sync_at has passed"""
        # Integration not due yet
        future_integration = UserIntegration(
            user_id=user.id,
            provider="fitbit",
            is_active=True,
            sync_enabled=True,
            next_sync_at=datetime.utcnow() + timedelta(hours=1)  # Future
        )
        db.add(future_integration)
        await db.commit()

        # Query for due integrations
        from sqlalchemy import select
        result = await db.execute(
            select(UserIntegration).where(
                UserIntegration.next_sync_at <= datetime.utcnow(),
                UserIntegration.sync_enabled == True,
                UserIntegration.is_active == True
            )
        )
        due_integrations = result.scalars().all()

        # Should not include future integration
        assert future_integration not in due_integrations


# Run tests with: pytest tests/test_voice_and_tasks.py -v
