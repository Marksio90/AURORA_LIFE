"""
Fitbit Integration

Sync health and fitness data from Fitbit devices.

Data types:
- Sleep (duration, stages, quality)
- Activity (steps, distance, calories)
- Heart rate (resting, zones)
- Body metrics (weight, BMI, body fat %)
- Food & water logging
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import httpx

from app.services.integrations.base_integration import BaseIntegration
from app.models.integrations import UserIntegration


class FitbitIntegration(BaseIntegration):
    """
    Fitbit integration.

    API Documentation: https://dev.fitbit.com/build/reference/web-api/
    """

    PROVIDER_NAME = "fitbit"
    INTEGRATION_TYPE = "health"
    SUPPORTS_OAUTH = True
    SUPPORTS_WEBHOOKS = True
    DEFAULT_SYNC_FREQUENCY_MINUTES = 360  # 6 hours

    # OAuth configuration
    OAUTH_AUTHORIZE_URL = "https://www.fitbit.com/oauth2/authorize"
    OAUTH_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
    SCOPES = [
        "activity",
        "heartrate",
        "location",
        "nutrition",
        "profile",
        "settings",
        "sleep",
        "social",
        "weight"
    ]

    # API endpoints
    BASE_URL = "https://api.fitbit.com/1"
    USER_PROFILE_URL = f"{BASE_URL}/user/-/profile.json"

    # Sleep
    SLEEP_LOG_URL = f"{BASE_URL}/user/-/sleep/date/{{date}}.json"

    # Activity
    ACTIVITY_SUMMARY_URL = f"{BASE_URL}/user/-/activities/date/{{date}}.json"
    STEPS_URL = f"{BASE_URL}/user/-/activities/steps/date/{{start_date}}/{{end_date}}.json"

    # Heart rate
    HEART_RATE_URL = f"{BASE_URL}/user/-/activities/heart/date/{{date}}/1d.json"

    # Body
    WEIGHT_LOG_URL = f"{BASE_URL}/user/-/body/log/weight/date/{{date}}.json"

    def __init__(self, db, user_integration: UserIntegration, client_id: str, client_secret: str):
        super().__init__(db, user_integration)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get Fitbit OAuth authorization URL."""
        import urllib.parse

        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES),
            'expires_in': '31536000'  # 1 year
        }

        if state:
            params['state'] = state

        return f"{self.OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    async def authorize(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth authorization."""
        import base64

        # Fitbit uses Basic auth with client_id:client_secret
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers=headers,
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
            self.user_integration.provider_user_id = token_data['user_id']

            if 'expires_in' in token_data:
                self.user_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

            self.user_integration.is_authorized = True

            await self.db.commit()

            return {
                'success': True,
                'user_id': token_data['user_id'],
                'access_token': token_data['access_token']
            }

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token."""
        import base64

        if not self.user_integration.refresh_token:
            return {'success': False, 'error': 'No refresh token available'}

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.user_integration.refresh_token
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                headers=headers,
                data=data
            )

            if response.status_code != 200:
                return {'success': False, 'error': 'Failed to refresh token'}

            token_data = response.json()

            # Update tokens
            self.user_integration.access_token = token_data['access_token']
            self.user_integration.refresh_token = token_data['refresh_token']

            if 'expires_in' in token_data:
                self.user_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

            await self.db.commit()

            return {'success': True}

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection by fetching user profile."""
        await self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.USER_PROFILE_URL, headers=headers)

            if response.status_code == 200:
                profile = response.json()['user']
                return {
                    'success': True,
                    'user': {
                        'display_name': profile.get('displayName'),
                        'member_since': profile.get('memberSince'),
                        'timezone': profile.get('timezone')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch profile: {response.status_code}'
                }

    async def sync_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync all health data from Fitbit."""
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
            sleep_count = await self._sync_sleep_data(start_date, end_date)
            activity_count = await self._sync_activity_data(start_date, end_date)
            heart_count = await self._sync_heart_rate_data(start_date, end_date)
            body_count = await self._sync_body_data(start_date, end_date)

            total_created = sleep_count + activity_count + heart_count + body_count

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
                    'sleep': sleep_count,
                    'activity': activity_count,
                    'heart_rate': heart_count,
                    'body': body_count
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

    async def _sync_sleep_data(self, start_date: datetime, end_date: datetime) -> int:
        """Sync sleep data."""
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        count = 0
        current_date = start_date.date()
        end = end_date.date()

        async with httpx.AsyncClient() as client:
            while current_date <= end:
                url = self.SLEEP_LOG_URL.format(date=current_date.isoformat())
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    if 'sleep' in data and data['sleep']:
                        for sleep_log in data['sleep']:
                            # Store sleep session
                            sleep_start = datetime.fromisoformat(
                                sleep_log['startTime'].replace('Z', '+00:00')
                            )

                            await self._store_synced_data(
                                data_type='sleep_session',
                                raw_data=sleep_log,
                                data_timestamp=sleep_start,
                                external_id=str(sleep_log.get('logId'))
                            )
                            count += 1

                current_date += timedelta(days=1)

        return count

    async def _sync_activity_data(self, start_date: datetime, end_date: datetime) -> int:
        """Sync activity data (steps, calories, distance)."""
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        count = 0
        current_date = start_date.date()
        end = end_date.date()

        async with httpx.AsyncClient() as client:
            while current_date <= end:
                url = self.ACTIVITY_SUMMARY_URL.format(date=current_date.isoformat())
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    if 'summary' in data:
                        # Store daily activity summary
                        await self._store_synced_data(
                            data_type='activity_summary',
                            raw_data=data['summary'],
                            data_timestamp=datetime.combine(current_date, datetime.min.time()),
                            external_id=current_date.isoformat()
                        )
                        count += 1

                current_date += timedelta(days=1)

        return count

    async def _sync_heart_rate_data(self, start_date: datetime, end_date: datetime) -> int:
        """Sync heart rate data."""
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        count = 0
        current_date = start_date.date()
        end = end_date.date()

        async with httpx.AsyncClient() as client:
            while current_date <= end:
                url = self.HEART_RATE_URL.format(date=current_date.isoformat())
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    if 'activities-heart' in data and data['activities-heart']:
                        for heart_data in data['activities-heart']:
                            if 'value' in heart_data:
                                await self._store_synced_data(
                                    data_type='heart_rate',
                                    raw_data=heart_data['value'],
                                    data_timestamp=datetime.combine(current_date, datetime.min.time()),
                                    external_id=f"{current_date.isoformat()}_hr"
                                )
                                count += 1

                current_date += timedelta(days=1)

        return count

    async def _sync_body_data(self, start_date: datetime, end_date: datetime) -> int:
        """Sync body metrics (weight, BMI, etc)."""
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        count = 0
        current_date = start_date.date()
        end = end_date.date()

        async with httpx.AsyncClient() as client:
            while current_date <= end:
                url = self.WEIGHT_LOG_URL.format(date=current_date.isoformat())
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    if 'weight' in data and data['weight']:
                        for weight_log in data['weight']:
                            log_time = datetime.fromisoformat(
                                weight_log['date'] + 'T' + weight_log.get('time', '00:00:00')
                            )

                            await self._store_synced_data(
                                data_type='body_weight',
                                raw_data=weight_log,
                                data_timestamp=log_time,
                                external_id=str(weight_log.get('logId'))
                            )
                            count += 1

                current_date += timedelta(days=1)

        return count

    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect Fitbit."""
        # Revoke token
        if self.user_integration.access_token:
            import base64

            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                'Authorization': f'Basic {encoded_credentials}'
            }

            async with httpx.AsyncClient() as client:
                await client.post(
                    'https://api.fitbit.com/oauth2/revoke',
                    headers=headers,
                    data={'token': self.user_integration.access_token}
                )

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
        Handle Fitbit webhook notifications.

        Fitbit sends notifications for new data.
        """
        # Webhook format:
        # {
        #   "collectionType": "sleep",
        #   "date": "2024-01-15",
        #   "ownerId": "...",
        #   "ownerType": "user"
        # }

        collection_type = payload.get('collectionType')
        date_str = payload.get('date')

        if not collection_type or not date_str:
            return {'success': False, 'error': 'Invalid webhook payload'}

        # Sync specific data type for specific date
        sync_date = datetime.fromisoformat(date_str)

        if collection_type == 'sleep':
            count = await self._sync_sleep_data(sync_date, sync_date)
        elif collection_type == 'activities':
            count = await self._sync_activity_data(sync_date, sync_date)
        elif collection_type == 'body':
            count = await self._sync_body_data(sync_date, sync_date)
        else:
            count = 0

        return {
            'success': True,
            'collection_type': collection_type,
            'date': date_str,
            'records_synced': count
        }
