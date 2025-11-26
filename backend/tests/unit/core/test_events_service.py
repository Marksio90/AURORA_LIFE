"""Unit tests for Life Event Service."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.service import LifeEventService
from app.schemas.life_event import LifeEventCreate, LifeEventUpdate
from app.models.user import User
from app.models.life_event import LifeEvent


@pytest.mark.asyncio
class TestCreateEvent:
    async def test_create_event_basic(self, db_session: AsyncSession, test_user: User):
        service = LifeEventService(db_session)
        event_data = LifeEventCreate(
            event_type="sleep",
            title="Good night",
            event_time=datetime(2024, 1, 1, 23, 0),
            event_data={"duration_hours": 8}
        )
        event = await service.create_event(test_user.id, event_data)
        assert event.id is not None
        assert event.user_id == test_user.id
        assert event.event_type == "sleep"
        assert event.title == "Good night"

    async def test_create_event_calculates_end_time(self, db_session: AsyncSession, test_user: User):
        service = LifeEventService(db_session)
        start_time = datetime(2024, 1, 1, 9, 0)
        event_data = LifeEventCreate(
            event_type="work",
            title="Work session",
            event_time=start_time,
            duration_minutes=120
        )
        event = await service.create_event(test_user.id, event_data)
        expected_end = start_time + timedelta(minutes=120)
        assert event.end_time == expected_end


@pytest.mark.asyncio
class TestGetEvents:
    async def test_get_event_by_id(self, db_session: AsyncSession, test_sleep_event: LifeEvent):
        service = LifeEventService(db_session)
        event = await service.get_event(test_sleep_event.id, test_sleep_event.user_id)
        assert event is not None
        assert event.id == test_sleep_event.id

    async def test_get_events_with_filters(self, db_session: AsyncSession, test_events_batch: list[LifeEvent], test_user: User):
        service = LifeEventService(db_session)
        events = await service.get_events(test_user.id, event_type="sleep")
        assert len(events) > 0
        assert all(e.event_type == "sleep" for e in events)

    async def test_get_recent_events(self, db_session: AsyncSession, test_user: User):
        service = LifeEventService(db_session)
        events = await service.get_recent_events(test_user.id, days=7)
        assert isinstance(events, list)
