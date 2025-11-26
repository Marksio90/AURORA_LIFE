"""
Google Calendar integration for AURORA_LIFE.

Features:
- OAuth2 authentication with Google
- Sync calendar events to AURORA_LIFE events
- Two-way sync support
- Automatic event categorization
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.core.config import settings
from app.models.user import User, Integration
from app.models.event import Event
import logging

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for Google Calendar integration."""

    API_BASE = "https://www.googleapis.com/calendar/v3"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_integration(self, user_id: uuid4) -> Optional[Integration]:
        """Get user's Google Calendar integration."""
        from sqlalchemy import select

        result = await self.db.execute(
            select(Integration).where(
                Integration.user_id == user_id,
                Integration.integration_type == "google_calendar"
            )
        )
        return result.scalar_one_or_none()

    async def connect(
        self,
        user_id: uuid4,
        access_token: str,
        refresh_token: str
    ):
        """Connect user's Google Calendar."""
        integration = Integration(
            id=uuid4(),
            user_id=user_id,
            integration_type="google_calendar",
            access_token=access_token,
            refresh_token=refresh_token,
            is_active=True,
            settings={
                "sync_enabled": True,
                "auto_categorize": True,
                "sync_direction": "both"  # both, to_aurora, to_calendar
            }
        )

        self.db.add(integration)
        await self.db.commit()

        logger.info(f"Connected Google Calendar for user {user_id}")

        return integration

    async def sync_events(
        self,
        user_id: uuid4,
        days_back: int = 7,
        days_forward: int = 30
    ) -> Dict[str, int]:
        """
        Sync events from Google Calendar.

        Returns:
            Dict with sync statistics (imported, updated, errors)
        """
        integration = await self.get_user_integration(user_id)

        if not integration or not integration.is_active:
            raise ValueError("Google Calendar not connected")

        stats = {"imported": 0, "updated": 0, "errors": 0}

        # Get calendar events
        calendar_events = await self._fetch_calendar_events(
            integration.access_token,
            days_back,
            days_forward
        )

        for cal_event in calendar_events:
            try:
                await self._import_calendar_event(user_id, cal_event, integration)
                stats["imported"] += 1
            except Exception as e:
                logger.error(f"Failed to import event {cal_event['id']}: {e}")
                stats["errors"] += 1

        logger.info(
            f"Synced Google Calendar for user {user_id}: "
            f"{stats['imported']} imported, {stats['errors']} errors"
        )

        return stats

    async def _fetch_calendar_events(
        self,
        access_token: str,
        days_back: int,
        days_forward: int
    ) -> List[Dict[str, Any]]:
        """Fetch events from Google Calendar API."""
        time_min = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z"
        time_max = (datetime.utcnow() + timedelta(days=days_forward)).isoformat() + "Z"

        url = f"{self.API_BASE}/calendars/primary/events"
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 250
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                logger.error(f"Google Calendar API error: {response.text}")
                raise ValueError("Failed to fetch calendar events")

            data = response.json()
            return data.get("items", [])

    async def _import_calendar_event(
        self,
        user_id: uuid4,
        cal_event: Dict[str, Any],
        integration: Integration
    ):
        """Import a calendar event as AURORA_LIFE event."""
        from sqlalchemy import select

        # Check if event already imported
        external_id = f"gcal_{cal_event['id']}"
        result = await self.db.execute(
            select(Event).where(
                Event.user_id == user_id,
                Event.external_id == external_id
            )
        )
        existing_event = result.scalar_one_or_none()

        # Extract event data
        summary = cal_event.get("summary", "Untitled Event")
        description = cal_event.get("description", "")

        start = cal_event.get("start", {})
        start_time = start.get("dateTime") or start.get("date")
        if start_time:
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))

        # Categorize event
        event_type = self._categorize_event(summary, description, integration)

        event_data = {
            "calendar_id": cal_event.get("id"),
            "location": cal_event.get("location"),
            "attendees": len(cal_event.get("attendees", [])),
            "duration_minutes": self._calculate_duration(cal_event)
        }

        if existing_event:
            # Update existing
            existing_event.title = summary
            existing_event.description = description
            existing_event.event_time = start_time
            existing_event.event_data = event_data
        else:
            # Create new
            event = Event(
                id=uuid4(),
                user_id=user_id,
                event_type=event_type,
                title=summary,
                description=description,
                event_time=start_time,
                event_data=event_data,
                external_id=external_id,
                tags=["google-calendar"]
            )
            self.db.add(event)

        await self.db.commit()

    def _categorize_event(
        self,
        summary: str,
        description: str,
        integration: Integration
    ) -> str:
        """Auto-categorize calendar event."""
        if not integration.settings.get("auto_categorize", True):
            return "calendar"

        text = f"{summary} {description}".lower()

        # Simple keyword matching (can be enhanced with ML)
        if any(word in text for word in ["workout", "gym", "run", "exercise", "yoga"]):
            return "exercise"
        elif any(word in text for word in ["meeting", "call", "standup", "sync"]):
            return "work"
        elif any(word in text for word in ["lunch", "dinner", "breakfast", "meal"]):
            return "meal"
        elif any(word in text for word in ["doctor", "appointment", "clinic", "hospital"]):
            return "health"
        elif any(word in text for word in ["birthday", "party", "celebration", "hangout"]):
            return "social"
        else:
            return "calendar"

    def _calculate_duration(self, cal_event: Dict[str, Any]) -> int:
        """Calculate event duration in minutes."""
        start = cal_event.get("start", {})
        end = cal_event.get("end", {})

        start_time = start.get("dateTime") or start.get("date")
        end_time = end.get("dateTime") or end.get("date")

        if not start_time or not end_time:
            return 0

        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

        duration = (end_dt - start_dt).total_seconds() / 60
        return int(duration)

    async def export_event_to_calendar(
        self,
        event: Event,
        integration: Integration
    ):
        """Export AURORA_LIFE event to Google Calendar."""
        if integration.settings.get("sync_direction") not in ["both", "to_calendar"]:
            return

        # Create calendar event
        calendar_event = {
            "summary": event.title,
            "description": event.description or "",
            "start": {
                "dateTime": event.event_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": (
                    event.event_time +
                    timedelta(minutes=event.event_data.get("duration_minutes", 60))
                ).isoformat(),
                "timeZone": "UTC"
            }
        }

        url = f"{self.API_BASE}/calendars/primary/events"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=calendar_event,
                headers={"Authorization": f"Bearer {integration.access_token}"}
            )

            if response.status_code == 200:
                cal_event = response.json()
                event.external_id = f"gcal_{cal_event['id']}"
                await self.db.commit()
                logger.info(f"Exported event {event.id} to Google Calendar")
            else:
                logger.error(f"Failed to export event: {response.text}")
