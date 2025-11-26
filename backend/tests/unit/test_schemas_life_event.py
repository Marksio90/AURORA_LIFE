"""
Unit tests for Life Event Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.life_event import (
    LifeEventCreate,
    LifeEventUpdate,
    LifeEventResponse,
    EventStreamMessage
)


class TestLifeEventCreate:
    """Tests for LifeEventCreate schema."""

    def test_create_event_minimum_fields(self):
        """Test creating event with minimum required fields."""
        event = LifeEventCreate(
            event_type="sleep",
            title="Good night sleep",
            event_time=datetime(2024, 1, 1, 23, 0)
        )
        assert event.event_type == "sleep"
        assert event.title == "Good night sleep"
        assert event.event_time == datetime(2024, 1, 1, 23, 0)
        assert event.source == "manual"  # default
        assert event.event_data == {}  # default
        assert event.tags == []  # default

    def test_create_event_all_fields(self):
        """Test creating event with all fields."""
        event_time = datetime(2024, 1, 1, 23, 0)
        event = LifeEventCreate(
            event_type="sleep",
            event_category="wellness",
            title="Good night sleep",
            description="Slept well with good dreams",
            event_data={"duration_hours": 8, "quality": "excellent"},
            event_time=event_time,
            duration_minutes=480,
            tags=["rest", "recovery"],
            context={"location": "home"},
            source="wearable"
        )
        assert event.event_category == "wellness"
        assert event.description == "Slept well with good dreams"
        assert event.event_data["duration_hours"] == 8
        assert event.duration_minutes == 480
        assert event.tags == ["rest", "recovery"]
        assert event.context == {"location": "home"}
        assert event.source == "wearable"

    def test_create_event_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            LifeEventCreate(
                event_type="sleep",
                title="Sleep"
                # missing event_time
            )
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "event_time" in field_names

    def test_create_event_with_empty_lists(self):
        """Test creating event with empty lists."""
        event = LifeEventCreate(
            event_type="exercise",
            title="Morning run",
            event_time=datetime(2024, 1, 1, 6, 0),
            tags=[],
            event_data={}
        )
        assert event.tags == []
        assert event.event_data == {}


class TestLifeEventUpdate:
    """Tests for LifeEventUpdate schema."""

    def test_update_event_empty(self):
        """Test update with no fields."""
        update = LifeEventUpdate()
        assert update.title is None
        assert update.description is None
        assert update.event_data is None

    def test_update_event_partial(self):
        """Test partial update."""
        update = LifeEventUpdate(
            title="Updated title",
            tags=["new", "tags"]
        )
        assert update.title == "Updated title"
        assert update.tags == ["new", "tags"]
        assert update.description is None

    def test_update_event_all_fields(self):
        """Test updating all fields."""
        update = LifeEventUpdate(
            title="Updated",
            description="New description",
            event_data={"key": "value"},
            tags=["tag1"],
            context={"ctx": "data"}
        )
        assert update.title == "Updated"
        assert update.description == "New description"
        assert update.event_data == {"key": "value"}


class TestLifeEventResponse:
    """Tests for LifeEventResponse schema."""

    def test_create_event_response(self):
        """Test creating event response."""
        event_time = datetime(2024, 1, 1, 23, 0)
        created_at = datetime(2024, 1, 1, 22, 0)

        response = LifeEventResponse(
            id=1,
            user_id=10,
            event_type="sleep",
            event_category="wellness",
            title="Good sleep",
            description="Well rested",
            event_data={"duration": 8},
            event_time=event_time,
            duration_minutes=480,
            end_time=datetime(2024, 1, 2, 7, 0),
            impact_score=0.8,
            energy_impact=0.7,
            mood_impact=0.9,
            tags=["rest"],
            context={"location": "home"},
            source="manual",
            created_at=created_at
        )
        assert response.id == 1
        assert response.user_id == 10
        assert response.event_type == "sleep"
        assert response.impact_score == 0.8

    def test_event_response_serialization(self):
        """Test event response serialization."""
        response = LifeEventResponse(
            id=1,
            user_id=10,
            event_type="exercise",
            event_category=None,
            title="Morning run",
            description=None,
            event_data={},
            event_time=datetime(2024, 1, 1, 6, 0),
            duration_minutes=30,
            end_time=None,
            impact_score=None,
            energy_impact=None,
            mood_impact=None,
            tags=[],
            context={},
            source="manual",
            created_at=datetime(2024, 1, 1, 6, 0)
        )
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == 1
        assert data["event_type"] == "exercise"

    def test_event_response_from_orm(self):
        """Test Config for ORM mode."""
        assert LifeEventResponse.model_config.get("from_attributes") is True


class TestEventStreamMessage:
    """Tests for EventStreamMessage schema."""

    def test_create_stream_message(self):
        """Test creating stream message."""
        event_time = datetime(2024, 1, 1, 12, 0)
        message = EventStreamMessage(
            event_id=123,
            user_id=10,
            event_type="emotion",
            event_time=event_time,
            data={"emotion": "happy", "intensity": 8}
        )
        assert message.event_id == 123
        assert message.user_id == 10
        assert message.event_type == "emotion"
        assert message.data["emotion"] == "happy"

    def test_stream_message_serialization(self):
        """Test stream message can be serialized for Redis."""
        message = EventStreamMessage(
            event_id=1,
            user_id=10,
            event_type="work",
            event_time=datetime(2024, 1, 1),
            data={"hours": 8}
        )
        data = message.model_dump()
        assert isinstance(data, dict)
        # Verify can be converted to JSON-like format for Redis
        import json
        json_str = json.dumps(data, default=str)
        assert isinstance(json_str, str)

    def test_stream_message_missing_required(self):
        """Test validation fails for missing required fields."""
        with pytest.raises(ValidationError):
            EventStreamMessage(
                event_id=1,
                user_id=10
                # missing event_type, event_time, data
            )
