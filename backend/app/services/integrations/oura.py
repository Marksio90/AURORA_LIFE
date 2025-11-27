"""
Oura Ring Integration

Advanced sleep and readiness tracking from Oura Ring.

Data types:
- Sleep (detailed stages, quality, HRV)
- Readiness score (recovery optimization)
- Activity (steps, calories, MET minutes)
- Heart rate (resting, variability)
- Body temperature (deviation from baseline)
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import httpx

from app.services.integrations.base_integration import BaseIntegration
from app.models.integrations import UserIntegration


class OuraIntegration(BaseIntegration):
    """
    Oura Ring integration.

    API Documentation: https://cloud.ouraring.com/v2/docs
    """

    PROVIDER_NAME = "oura"
    INTEGRATION_TYPE = "health"
    SUPPORTS_OAUTH = True
    SUPPORTS_WEBHOOKS = True
    DEFAULT_SYNC_FREQUENCY_MINUTES = 360  # 6 hours

    # OAuth configuration
    OAUTH_AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
    OAUTH_TOKEN_URL = "https://api.ouraring.com/oauth/token"
    SCOPES = ["email", "personal", "daily"]

    # API endpoints (v2)
    BASE_URL = "https://api.ouraring.com/v2/usercollection"

    PERSONAL_INFO_URL = f"{BASE_URL}/personal_info"
    DAILY_SLEEP_URL = f"{BASE_URL}/daily_sleep"
    DAILY_READINESS_URL = f"{BASE_URL}/daily_readiness"
    DAILY_ACTIVITY_URL = f"{BASE_URL}/daily_activity"
    HEART_RATE_URL = f"{BASE_URL}/heartrate"
    SLEEP_SESSIONS_URL = f"{BASE_URL}/sleep"
    WORKOUT_URL = f"{BASE_URL}/workout"

    def __init__(self, db, user_integration: UserIntegration, client_id: str, client_secret: str):
        super().__init__(db, user_integration)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get Oura OAuth authorization URL."""
        import urllib.parse

        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES)
        }

        if state:
            params['state'] = state

        return f"{self.OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    async def authorize(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth authorization."""
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data=data
            )

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': 'Failed to exchange authorization code',
                    'details': response.text
                }

            token_data = response.json()

            # Update user integration
            self.user_integration.access_token = token_data['access_token']
            self.user_integration.refresh_token = token_data['refresh_token']

            if 'expires_in' in token_data:
                self.user_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

            self.user_integration.is_authorized = True

            await self.db.commit()

            return {
                'success': True,
                'access_token': token_data['access_token']
            }

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token."""
        if not self.user_integration.refresh_token:
            return {'success': False, 'error': 'No refresh token available'}

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.user_integration.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data=data
            )

            if response.status_code != 200:
                return {'success': False, 'error': 'Failed to refresh token'}

            token_data = response.json()

            # Update tokens
            self.user_integration.access_token = token_data['access_token']
            self.user_integration.refresh_token = token_data.get('refresh_token', self.user_integration.refresh_token)

            if 'expires_in' in token_data:
                self.user_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

            await self.db.commit()

            return {'success': True}

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection by fetching personal info."""
        await self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.PERSONAL_INFO_URL, headers=headers)

            if response.status_code == 200:
                info = response.json()
                return {
                    'success': True,
                    'user': {
                        'age': info.get('age'),
                        'weight': info.get('weight'),
                        'height': info.get('height'),
                        'biological_sex': info.get('biological_sex')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch personal info: {response.status_code}'
                }

    async def sync_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync all health data from Oura."""
        await self._ensure_valid_token()

        # Default to last 7 days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        sync_log = await self._create_sync_log("incremental")

        try:
            total_created = 0

            # Sync different data types
            sleep_count = await self._sync_daily_sleep(start_date, end_date)
            readiness_count = await self._sync_daily_readiness(start_date, end_date)
            activity_count = await self._sync_daily_activity(start_date, end_date)
            sessions_count = await self._sync_sleep_sessions(start_date, end_date)

            total_created = sleep_count + readiness_count + activity_count + sessions_count

            # Update integration
            self.user_integration.last_sync_at = datetime.utcnow()
            self.user_integration.next_sync_at = datetime.utcnow() + timedelta(
                minutes=self.user_integration.sync_frequency_minutes
            )
            await self.db.commit()

            # Complete sync log
            await self._complete_sync_log(
                sync_log=sync_log,
                success=True,
                records_created=total_created
            )

            return {
                'success': True,
                'records_synced': total_created,
                'breakdown': {
                    'daily_sleep': sleep_count,
                    'daily_readiness': readiness_count,
                    'daily_activity': activity_count,
                    'sleep_sessions': sessions_count
                },
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

        except Exception as e:
            await self._complete_sync_log(
                sync_log=sync_log,
                success=False,
                error_message=str(e)
            )

            return {
                'success': False,
                'error': str(e)
            }

    async def _sync_daily_sleep(self, start_date: datetime, end_date: datetime) -> int:
        """
        Sync daily sleep scores.

        Includes:
        - Sleep score (0-100)
        - Total sleep time
        - Efficiency
        - REM, Deep, Light sleep
        - Sleep latency
        - Timing (bedtime/wake time)
        - Heart rate variability
        """
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        params = {
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }

        count = 0

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.DAILY_SLEEP_URL,
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()

                for sleep_data in data.get('data', []):
                    day_date = datetime.fromisoformat(sleep_data['day'])

                    await self._store_synced_data(
                        data_type='oura_daily_sleep',
                        raw_data=sleep_data,
                        data_timestamp=day_date,
                        external_id=sleep_data.get('id')
                    )
                    count += 1

        return count

    async def _sync_daily_readiness(self, start_date: datetime, end_date: datetime) -> int:
        """
        Sync daily readiness scores.

        Readiness indicates recovery state:
        - Readiness score (0-100)
        - Temperature deviation
        - HRV balance
        - Recovery index
        - Previous day activity
        - Sleep balance
        """
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        params = {
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }

        count = 0

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.DAILY_READINESS_URL,
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()

                for readiness_data in data.get('data', []):
                    day_date = datetime.fromisoformat(readiness_data['day'])

                    await self._store_synced_data(
                        data_type='oura_daily_readiness',
                        raw_data=readiness_data,
                        data_timestamp=day_date,
                        external_id=readiness_data.get('id')
                    )
                    count += 1

        return count

    async def _sync_daily_activity(self, start_date: datetime, end_date: datetime) -> int:
        """
        Sync daily activity data.

        Includes:
        - Activity score (0-100)
        - Steps
        - Calories
        - Active time
        - MET minutes
        - Inactivity alerts
        - Training frequency/volume
        """
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        params = {
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }

        count = 0

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.DAILY_ACTIVITY_URL,
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()

                for activity_data in data.get('data', []):
                    day_date = datetime.fromisoformat(activity_data['day'])

                    await self._store_synced_data(
                        data_type='oura_daily_activity',
                        raw_data=activity_data,
                        data_timestamp=day_date,
                        external_id=activity_data.get('id')
                    )
                    count += 1

        return count

    async def _sync_sleep_sessions(self, start_date: datetime, end_date: datetime) -> int:
        """
        Sync detailed sleep sessions.

        More granular than daily sleep - shows individual sleep periods.
        """
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        params = {
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat()
        }

        count = 0

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.SLEEP_SESSIONS_URL,
                headers=headers,
                params=params
            )

            if response.status_code == 200:
                data = response.json()

                for session in data.get('data', []):
                    bedtime_start = datetime.fromisoformat(session['bedtime_start'])

                    await self._store_synced_data(
                        data_type='oura_sleep_session',
                        raw_data=session,
                        data_timestamp=bedtime_start,
                        external_id=session.get('id')
                    )
                    count += 1

        return count

    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect Oura."""
        # Update integration
        self.user_integration.is_active = False
        self.user_integration.is_authorized = False
        self.user_integration.disconnected_at = datetime.utcnow()
        self.user_integration.access_token = None
        self.user_integration.refresh_token = None

        await self.db.commit()

        return {'success': True}

    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Oura webhook notifications.

        Oura sends notifications when new data is available.
        """
        # Webhook format varies by subscription type
        # Typically contains user_id and data_type

        # Trigger incremental sync for affected date range
        # For simplicity, sync last 2 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=2)

        result = await self.sync_data(start_date, end_date)

        return {
            'success': result['success'],
            'webhook_processed': True,
            'records_synced': result.get('records_synced', 0)
        }
