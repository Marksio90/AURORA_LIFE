"""
Google Calendar Integration

Sync calendar events for context and time tracking.
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx

from app.services.integrations.base_integration import BaseIntegration
from app.models.integrations import UserIntegration


class GoogleCalendarIntegration(BaseIntegration):
    """
    Google Calendar integration.

    Features:
    - Sync calendar events
    - Auto-create life events from meetings
    - Track time spent in meetings
    - Provide context for productivity analysis
    """

    PROVIDER_NAME = "google_calendar"
    INTEGRATION_TYPE = "calendar"
    SUPPORTS_OAUTH = True
    SUPPORTS_WEBHOOKS = True

    # OAuth configuration
    OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly"
    ]

    # API endpoints
    CALENDAR_LIST_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

    def __init__(self, db, user_integration: UserIntegration, client_id: str, client_secret: str):
        super().__init__(db, user_integration)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL."""
        import urllib.parse

        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.SCOPES),
            'access_type': 'offline',  # Get refresh token
            'prompt': 'consent'  # Force consent to get refresh token
        }

        if state:
            params['state'] = state

        return f"{self.OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    async def authorize(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth authorization."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    'code': auth_code,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code'
                }
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
            self.user_integration.refresh_token = token_data.get('refresh_token')

            if 'expires_in' in token_data:
                self.user_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

            self.user_integration.is_authorized = True

            await self.db.commit()

            return {
                'success': True,
                'access_token': token_data['access_token'],
                'expires_in': token_data.get('expires_in')
            }

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh access token."""
        if not self.user_integration.refresh_token:
            return {'success': False, 'error': 'No refresh token available'}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data={
                    'refresh_token': self.user_integration.refresh_token,
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'grant_type': 'refresh_token'
                }
            )

            if response.status_code != 200:
                return {'success': False, 'error': 'Failed to refresh token'}

            token_data = response.json()

            # Update tokens
            self.user_integration.access_token = token_data['access_token']

            if 'expires_in' in token_data:
                self.user_integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])

            await self.db.commit()

            return {'success': True}

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection by fetching calendar list."""
        await self._ensure_valid_token()

        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.CALENDAR_LIST_URL, headers=headers)

            if response.status_code == 200:
                calendars = response.json().get('items', [])
                return {
                    'success': True,
                    'calendar_count': len(calendars),
                    'calendars': [
                        {
                            'id': cal['id'],
                            'summary': cal.get('summary', 'Unknown'),
                            'primary': cal.get('primary', False)
                        }
                        for cal in calendars
                    ]
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch calendars: {response.status_code}'
                }

    async def sync_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Sync calendar events."""
        await self._ensure_valid_token()

        # Default to last 7 days if not specified
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Create sync log
        sync_log = await self._create_sync_log("incremental")

        try:
            # Get all calendars
            calendars = await self._get_calendars()

            total_events_synced = 0
            total_created = 0

            # Sync events from each calendar
            for calendar in calendars:
                events = await self._get_calendar_events(
                    calendar_id=calendar['id'],
                    start_date=start_date,
                    end_date=end_date
                )

                # Store synced events
                for event in events:
                    event_start = self._parse_datetime(event.get('start', {}))

                    if event_start:
                        await self._store_synced_data(
                            data_type='calendar_event',
                            raw_data={
                                'calendar_id': calendar['id'],
                                'calendar_name': calendar['summary'],
                                **event
                            },
                            data_timestamp=event_start,
                            external_id=event.get('id')
                        )

                        total_created += 1

                total_events_synced += len(events)

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
                'calendars_synced': len(calendars),
                'events_synced': total_events_synced,
                'events_created': total_created,
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

    async def _get_calendars(self) -> List[Dict[str, Any]]:
        """Get list of user's calendars."""
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.CALENDAR_LIST_URL, headers=headers)

            if response.status_code == 200:
                return response.json().get('items', [])
            else:
                raise Exception(f"Failed to fetch calendars: {response.status_code}")

    async def _get_calendar_events(
        self,
        calendar_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get events from a specific calendar."""
        headers = {
            'Authorization': f'Bearer {self.user_integration.access_token}'
        }

        params = {
            'timeMin': start_date.isoformat() + 'Z',
            'timeMax': end_date.isoformat() + 'Z',
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 2500  # Google's limit
        }

        events = []

        async with httpx.AsyncClient() as client:
            url = self.EVENTS_URL.format(calendar_id=calendar_id)
            response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                events.extend(data.get('items', []))

                # Handle pagination
                while 'nextPageToken' in data:
                    params['pageToken'] = data['nextPageToken']
                    response = await client.get(url, headers=headers, params=params)

                    if response.status_code == 200:
                        data = response.json()
                        events.extend(data.get('items', []))
                    else:
                        break

        return events

    def _parse_datetime(self, time_dict: Dict[str, Any]) -> Optional[datetime]:
        """Parse Google Calendar datetime."""
        if 'dateTime' in time_dict:
            # Event with specific time
            return datetime.fromisoformat(time_dict['dateTime'].replace('Z', '+00:00'))
        elif 'date' in time_dict:
            # All-day event
            return datetime.fromisoformat(time_dict['date'])
        return None

    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect Google Calendar."""
        # Revoke token
        if self.user_integration.access_token:
            async with httpx.AsyncClient() as client:
                await client.post(
                    'https://oauth2.googleapis.com/revoke',
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
