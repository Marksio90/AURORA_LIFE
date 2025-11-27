"""
Tests for external integrations (Fitbit, Oura, Spotify, Google Calendar)

Tests OAuth flows, data syncing, and integration management.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.integrations.fitbit import FitbitIntegration
from app.services.integrations.oura import OuraIntegration
from app.services.integrations.spotify import SpotifyIntegration
from app.services.integrations.google_calendar import GoogleCalendarIntegration
from app.models.integrations import UserIntegration, SyncedData
from app.models.user import User


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
async def user_integration(db, user):
    """Create test integration"""
    integration = UserIntegration(
        user_id=user.id,
        provider="fitbit",
        is_active=True,
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        scopes=["activity", "sleep", "heartrate"],
        sync_enabled=True,
        sync_frequency="hourly"
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return integration


class TestFitbitIntegration:
    """Test Fitbit integration"""

    @pytest.mark.asyncio
    async def test_get_authorization_url(self, db, user_integration):
        """Test OAuth authorization URL generation"""
        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        url = integration.get_authorization_url(
            redirect_uri="http://localhost:8000/callback",
            state="test_state"
        )

        assert "https://www.fitbit.com/oauth2/authorize" in url
        assert "client_id=test_client_id" in url
        assert "redirect_uri=" in url
        assert "state=test_state" in url

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.post')
    async def test_authorize_success(self, mock_post, db, user_integration):
        """Test successful OAuth authorization"""
        # Mock token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600,
            'user_id': 'fitbit_user_123'
        }
        mock_post.return_value = mock_response

        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        result = await integration.authorize(
            auth_code="test_code",
            redirect_uri="http://localhost:8000/callback"
        )

        assert result['success'] is True
        assert result['access_token'] == 'new_access_token'
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.request')
    async def test_sync_sleep_data(self, mock_request, db, user_integration):
        """Test syncing sleep data from Fitbit"""
        # Mock sleep API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'sleep': [
                {
                    'logId': 12345,
                    'dateOfSleep': '2024-01-15',
                    'startTime': '2024-01-14T23:00:00',
                    'endTime': '2024-01-15T07:00:00',
                    'duration': 28800000,  # 8 hours in ms
                    'efficiency': 92,
                    'minutesAsleep': 440,
                    'minutesAwake': 40,
                    'levels': {
                        'summary': {
                            'deep': {'minutes': 120},
                            'light': {'minutes': 220},
                            'rem': {'minutes': 100},
                            'wake': {'minutes': 40}
                        }
                    }
                }
            ]
        }
        mock_request.return_value = mock_response

        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        count = await integration._sync_sleep_data(
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 1, 15)
        )

        assert count == 1
        # Verify synced data was stored
        synced = await db.execute(
            "SELECT * FROM synced_data WHERE integration_id = :id",
            {"id": user_integration.id}
        )
        assert synced.rowcount > 0

    @pytest.mark.asyncio
    async def test_token_refresh_on_401(self, db, user_integration):
        """Test automatic token refresh when access token expires"""
        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        with patch.object(integration, 'http_client') as mock_client:
            # First request returns 401 (expired token)
            mock_401_response = MagicMock()
            mock_401_response.status_code = 401

            # After refresh, request succeeds
            mock_200_response = MagicMock()
            mock_200_response.status_code = 200
            mock_200_response.json.return_value = {'data': 'success'}

            mock_client.request.side_effect = [mock_401_response, mock_200_response]

            # Mock token refresh
            with patch.object(integration, 'refresh_access_token') as mock_refresh:
                mock_refresh.return_value = {'success': True}

                result = await integration._make_api_request('GET', 'https://api.example.com/data')

                # Should have refreshed token and retried
                assert mock_refresh.called
                assert result == {'data': 'success'}


class TestOuraIntegration:
    """Test Oura Ring integration"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.request')
    async def test_sync_daily_sleep(self, mock_request, db, user_integration):
        """Test syncing daily sleep data from Oura"""
        user_integration.provider = "oura"
        await db.commit()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'sleep_123',
                    'day': '2024-01-15',
                    'score': 85,
                    'contributors': {
                        'deep_sleep': 90,
                        'efficiency': 95,
                        'latency': 80,
                        'rem_sleep': 85,
                        'restfulness': 75,
                        'timing': 90,
                        'total_sleep': 88
                    },
                    'deep_sleep_duration': 7200,  # 2 hours
                    'rem_sleep_duration': 5400,   # 1.5 hours
                    'light_sleep_duration': 14400,  # 4 hours
                    'total_sleep_duration': 28800,  # 8 hours
                    'awake_duration': 600,  # 10 minutes
                    'average_hrv': 65,
                    'lowest_heart_rate': 48
                }
            ]
        }
        mock_request.return_value = mock_response

        integration = OuraIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        count = await integration._sync_daily_sleep(
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 1, 15)
        )

        assert count == 1

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.request')
    async def test_sync_daily_readiness(self, mock_request, db, user_integration):
        """Test syncing readiness data from Oura"""
        user_integration.provider = "oura"
        await db.commit()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'readiness_123',
                    'day': '2024-01-15',
                    'score': 82,
                    'temperature_deviation': -0.2,
                    'temperature_trend_deviation': 0.1,
                    'contributors': {
                        'activity_balance': 85,
                        'body_temperature': 90,
                        'hrv_balance': 80,
                        'previous_day_activity': 75,
                        'previous_night': 88,
                        'recovery_index': 78,
                        'resting_heart_rate': 85,
                        'sleep_balance': 80
                    }
                }
            ]
        }
        mock_request.return_value = mock_response

        integration = OuraIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        count = await integration._sync_daily_readiness(
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 1, 15)
        )

        assert count == 1


class TestSpotifyIntegration:
    """Test Spotify integration"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.request')
    async def test_sync_recently_played(self, mock_request, db, user_integration):
        """Test syncing recently played tracks"""
        user_integration.provider = "spotify"
        await db.commit()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {
                    'track': {
                        'id': 'track_123',
                        'name': 'Happy Song',
                        'artists': [{'name': 'Artist Name'}],
                        'album': {'name': 'Album Name'},
                        'duration_ms': 240000,
                        'popularity': 75
                    },
                    'played_at': '2024-01-15T12:00:00Z'
                }
            ]
        }
        mock_request.return_value = mock_response

        integration = SpotifyIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        # Mock audio features call
        with patch.object(integration, '_get_audio_features') as mock_features:
            mock_features.return_value = {
                'track_123': {
                    'valence': 0.8,
                    'energy': 0.7,
                    'tempo': 120.0
                }
            }

            count = await integration._sync_recently_played(limit=50)

            assert count == 1

    @pytest.mark.asyncio
    async def test_mood_inference(self, db, user_integration):
        """Test mood inference from audio features"""
        user_integration.provider = "spotify"
        await db.commit()

        integration = SpotifyIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        # Test all quadrants
        assert integration._infer_mood_from_features(0.8, 0.8) == "happy"  # High valence, high energy
        assert integration._infer_mood_from_features(0.8, 0.2) == "calm"   # High valence, low energy
        assert integration._infer_mood_from_features(0.2, 0.8) == "tense"  # Low valence, high energy
        assert integration._infer_mood_from_features(0.2, 0.2) == "sad"    # Low valence, low energy

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.request')
    async def test_analyze_listening_mood(self, mock_request, db, user_integration):
        """Test overall mood analysis from listening patterns"""
        user_integration.provider = "spotify"
        await db.commit()

        # Mock recently played response
        mock_recently_played = MagicMock()
        mock_recently_played.status_code = 200
        mock_recently_played.json.return_value = {
            'items': [
                {'track': {'id': f'track_{i}'}}
                for i in range(10)
            ]
        }

        # Mock audio features response
        mock_audio_features = MagicMock()
        mock_audio_features.status_code = 200
        mock_audio_features.json.return_value = {
            'audio_features': [
                {
                    'id': f'track_{i}',
                    'valence': 0.7,
                    'energy': 0.8,
                    'tempo': 120 + i * 5
                }
                for i in range(10)
            ]
        }

        mock_request.side_effect = [mock_recently_played, mock_audio_features]

        integration = SpotifyIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        mood_analysis = await integration._analyze_listening_mood()

        assert mood_analysis is not None
        assert 'avg_valence' in mood_analysis
        assert 'avg_energy' in mood_analysis
        assert 'inferred_mood' in mood_analysis
        assert mood_analysis['inferred_mood'] == "happy"  # High valence + energy


class TestGoogleCalendarIntegration:
    """Test Google Calendar integration"""

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.request')
    async def test_sync_calendar_events(self, mock_request, db, user_integration):
        """Test syncing calendar events"""
        user_integration.provider = "google_calendar"
        await db.commit()

        # Mock calendar list response
        mock_calendars = MagicMock()
        mock_calendars.status_code = 200
        mock_calendars.json.return_value = {
            'items': [
                {
                    'id': 'calendar_123',
                    'summary': 'Work Calendar',
                    'primary': True
                }
            ]
        }

        # Mock events response
        mock_events = MagicMock()
        mock_events.status_code = 200
        mock_events.json.return_value = {
            'items': [
                {
                    'id': 'event_123',
                    'summary': 'Team Meeting',
                    'description': 'Weekly sync',
                    'start': {'dateTime': '2024-01-15T10:00:00Z'},
                    'end': {'dateTime': '2024-01-15T11:00:00Z'},
                    'location': 'Conference Room A',
                    'attendees': [
                        {'email': 'colleague@example.com'}
                    ]
                }
            ]
        }

        mock_request.side_effect = [mock_calendars, mock_events]

        integration = GoogleCalendarIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        result = await integration.sync_data(
            start_date=datetime(2024, 1, 15),
            end_date=datetime(2024, 1, 15)
        )

        assert result['success'] is True
        assert result['records_synced'] > 0


class TestIntegrationManagement:
    """Test general integration management"""

    @pytest.mark.asyncio
    async def test_disconnect_integration(self, db, user_integration):
        """Test disconnecting an integration"""
        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        result = await integration.disconnect()

        assert result['success'] is True
        # Verify integration deactivated
        await db.refresh(user_integration)
        assert user_integration.is_active is False

    @pytest.mark.asyncio
    async def test_sync_frequency_update(self, db, user_integration):
        """Test updating sync frequency"""
        # Change from hourly to daily
        user_integration.sync_frequency = "daily"
        await db.commit()

        await db.refresh(user_integration)
        assert user_integration.sync_frequency == "daily"

    @pytest.mark.asyncio
    async def test_store_synced_data(self, db, user_integration):
        """Test storing synced data"""
        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        synced_data = await integration._store_synced_data(
            data_type="test_data",
            raw_data={"key": "value"},
            external_id="test_123",
            data_timestamp=datetime.utcnow()
        )

        assert synced_data.id is not None
        assert synced_data.data_type == "test_data"
        assert synced_data.raw_data == {"key": "value"}
        assert synced_data.processed is False

    @pytest.mark.asyncio
    async def test_get_integration_by_provider(self, db, user, user_integration):
        """Test retrieving integration by provider"""
        from sqlalchemy import select

        result = await db.execute(
            select(UserIntegration).where(
                UserIntegration.user_id == user.id,
                UserIntegration.provider == "fitbit"
            )
        )
        integration = result.scalar_one_or_none()

        assert integration is not None
        assert integration.provider == "fitbit"


class TestWebhooks:
    """Test webhook handling"""

    @pytest.mark.asyncio
    async def test_fitbit_webhook(self, db, user_integration):
        """Test Fitbit webhook processing"""
        integration = FitbitIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        result = await integration.handle_webhook(
            event_type="sleep",
            payload={
                "collectionType": "sleep",
                "date": "2024-01-15",
                "ownerId": "fitbit_user_123",
                "ownerType": "user",
                "subscriptionId": "1"
            }
        )

        # Webhook should trigger sync
        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_spotify_no_webhook_support(self, db, user_integration):
        """Test that Spotify doesn't support webhooks"""
        user_integration.provider = "spotify"
        await db.commit()

        integration = SpotifyIntegration(
            db=db,
            user_integration=user_integration,
            client_id="test_client_id",
            client_secret="test_client_secret"
        )

        result = await integration.handle_webhook("test", {})

        assert result['success'] is False
        assert "not support" in result['error'].lower()


# Run tests with: pytest tests/test_integrations.py -v
