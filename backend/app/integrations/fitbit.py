"""
Fitbit integration for fitness and health data sync.

Features:
- OAuth2 authentication
- Activity data (steps, distance, calories)
- Heart rate and sleep data
- Weight and body metrics
- Automatic daily sync
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FitbitClient:
    """
    Fitbit API client for Aurora Life.

    OAuth2 flow:
    1. User authorizes app at Fitbit
    2. Exchange code for access/refresh tokens
    3. Store tokens in database
    4. Auto-refresh when needed
    """

    BASE_URL = "https://api.fitbit.com/1"
    AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
    TOKEN_URL = "https://api.fitbit.com/oauth2/token"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        self.client_id = getattr(settings, 'FITBIT_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'FITBIT_CLIENT_SECRET', None)

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """
        Get Fitbit OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            state: CSRF protection state parameter

        Returns:
            Authorization URL
        """
        scopes = [
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

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(scopes),
            "redirect_uri": redirect_uri,
            "state": state
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Token response with access_token and refresh_token
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )

            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )

            response.raise_for_status()
            return response.json()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated request to Fitbit API."""
        if not self.access_token:
            raise ValueError("Access token not set")

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            **kwargs.pop("headers", {})
        }

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                **kwargs
            )

            if response.status_code == 401:
                logger.warning("Fitbit token expired")
                raise ValueError("Token expired - refresh needed")

            response.raise_for_status()
            return response.json()

    async def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        return await self._make_request("GET", "user/-/profile.json")

    async def get_activity_summary(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get activity summary for a specific date.

        Args:
            date_str: Date in YYYY-MM-DD format (default: today)

        Returns:
            Activity summary with steps, calories, distance, etc.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return await self._make_request("GET", f"user/-/activities/date/{date_str}.json")

    async def get_activity_time_series(
        self,
        resource: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get activity time series data.

        Args:
            resource: Activity resource (steps, calories, distance, etc.)
            start_date: Start date
            end_date: End date

        Returns:
            List of daily values
        """
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        response = await self._make_request(
            "GET",
            f"user/-/activities/{resource}/date/{start_str}/{end_str}.json"
        )

        return response.get(f"activities-{resource}", [])

    async def get_heart_rate(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get heart rate data for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Heart rate zones and intraday data
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return await self._make_request("GET", f"user/-/activities/heart/date/{date_str}/1d.json")

    async def get_sleep_logs(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Get sleep logs for a date.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Sleep data including stages and duration
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return await self._make_request("GET", f"user/-/sleep/date/{date_str}.json")

    async def get_weight(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """Get weight/body fat data."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        return await self._make_request("GET", f"user/-/body/log/weight/date/{date_str}.json")


class FitbitSync:
    """
    Service for syncing Fitbit data to Aurora Life events.

    Automatically imports:
    - Daily activity (steps, calories, distance)
    - Sleep data
    - Heart rate
    - Weight logs
    """

    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.client: Optional[FitbitClient] = None

    async def initialize(self):
        """Initialize Fitbit client with user's access token."""
        from app.models.integration import Integration

        # Get user's Fitbit integration
        result = await self.db.execute(
            select(Integration).where(
                Integration.user_id == self.user_id,
                Integration.integration_type == "fitbit",
                Integration.is_active == True
            )
        )

        integration = result.scalar_one_or_none()

        if not integration:
            raise ValueError("Fitbit integration not found or not active")

        # Check if token needs refresh
        if integration.token_expires_at and integration.token_expires_at < datetime.utcnow():
            # Refresh token
            client = FitbitClient()
            token_data = await client.refresh_access_token(integration.refresh_token)

            # Update integration
            integration.access_token = token_data["access_token"]
            integration.refresh_token = token_data.get("refresh_token", integration.refresh_token)
            integration.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            await self.db.commit()

        self.client = FitbitClient(access_token=integration.access_token)

    async def sync_activity(self, sync_date: date) -> Dict[str, Any]:
        """
        Sync activity data for a specific date.

        Args:
            sync_date: Date to sync

        Returns:
            Created event data
        """
        from app.models.event import Event

        # Get activity summary
        date_str = sync_date.strftime("%Y-%m-%d")
        activity_data = await self.client.get_activity_summary(date_str)

        summary = activity_data.get("summary", {})

        # Create activity event
        event = Event(
            user_id=self.user_id,
            event_type="exercise",
            title=f"Daily Activity - {sync_date.strftime('%b %d')}",
            event_time=datetime.combine(sync_date, datetime.min.time()),
            event_data={
                "source": "fitbit",
                "steps": summary.get("steps", 0),
                "calories": summary.get("caloriesOut", 0),
                "distance_km": summary.get("distances", [{}])[0].get("distance", 0),
                "active_minutes": summary.get("veryActiveMinutes", 0) + summary.get("fairlyActiveMinutes", 0),
                "floors": summary.get("floors", 0),
                "elevation": summary.get("elevation", 0)
            }
        )

        self.db.add(event)
        await self.db.commit()

        logger.info(f"Synced Fitbit activity for {date_str}: {summary.get('steps')} steps")

        return {"event_id": str(event.id), "date": date_str, "steps": summary.get("steps")}

    async def sync_sleep(self, sync_date: date) -> Optional[Dict[str, Any]]:
        """Sync sleep data for a specific date."""
        from app.models.event import Event

        date_str = sync_date.strftime("%Y-%m-%d")
        sleep_data = await self.client.get_sleep_logs(date_str)

        sleep_logs = sleep_data.get("sleep", [])

        if not sleep_logs:
            return None

        # Get main sleep log (usually first one)
        main_sleep = sleep_logs[0]

        # Create sleep event
        event = Event(
            user_id=self.user_id,
            event_type="sleep",
            title=f"Sleep - {sync_date.strftime('%b %d')}",
            event_time=datetime.fromisoformat(main_sleep["startTime"].replace("Z", "+00:00")),
            event_data={
                "source": "fitbit",
                "duration_hours": main_sleep["duration"] / (1000 * 60 * 60),  # Convert ms to hours
                "duration_minutes": main_sleep["duration"] / (1000 * 60),
                "efficiency": main_sleep.get("efficiency", 0),
                "quality_score": main_sleep.get("efficiency", 0) / 20,  # Convert to 0-5 scale
                "deep_sleep_minutes": main_sleep.get("levels", {}).get("summary", {}).get("deep", {}).get("minutes", 0),
                "light_sleep_minutes": main_sleep.get("levels", {}).get("summary", {}).get("light", {}).get("minutes", 0),
                "rem_sleep_minutes": main_sleep.get("levels", {}).get("summary", {}).get("rem", {}).get("minutes", 0),
                "wake_minutes": main_sleep.get("levels", {}).get("summary", {}).get("wake", {}).get("minutes", 0)
            }
        )

        self.db.add(event)
        await self.db.commit()

        logger.info(f"Synced Fitbit sleep for {date_str}")

        return {"event_id": str(event.id), "date": date_str}

    async def sync_daily_data(self, sync_date: Optional[date] = None):
        """
        Sync all data types for a date.

        Args:
            sync_date: Date to sync (default: yesterday)
        """
        if not sync_date:
            sync_date = date.today() - timedelta(days=1)

        await self.initialize()

        results = {}

        try:
            results["activity"] = await self.sync_activity(sync_date)
        except Exception as e:
            logger.error(f"Failed to sync activity: {e}")
            results["activity"] = {"error": str(e)}

        try:
            results["sleep"] = await self.sync_sleep(sync_date)
        except Exception as e:
            logger.error(f"Failed to sync sleep: {e}")
            results["sleep"] = {"error": str(e)}

        return results


# Usage example:
"""
from app.integrations.fitbit import FitbitSync

# Daily sync (run as Celery task)
sync = FitbitSync(db, user_id)
await sync.sync_daily_data()

# Sync specific date
from datetime import date
await sync.sync_daily_data(date(2024, 1, 15))
"""
