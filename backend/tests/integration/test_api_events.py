"""
Integration tests for Events API endpoints.

Tests the full request/response cycle including:
- Authentication
- Validation
- Database operations
- Response formatting
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestEventsAPI:
    """Test suite for /api/v1/events endpoints."""

    async def test_create_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession
    ):
        """Test successful event creation."""
        event_data = {
            "event_type": "sleep",
            "title": "Good night sleep",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_data": {
                "duration_hours": 8,
                "quality": "excellent"
            },
            "tags": ["restful", "deep-sleep"]
        }

        response = await client.post(
            "/api/v1/events",
            json=event_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert data["id"] is not None
        assert data["event_type"] == "sleep"
        assert data["title"] == "Good night sleep"
        assert data["event_data"]["duration_hours"] == 8
        assert "restful" in data["tags"]

    async def test_create_event_unauthorized(self, client: AsyncClient):
        """Test event creation without authentication."""
        response = await client.post(
            "/api/v1/events",
            json={"event_type": "sleep", "title": "Test"}
        )

        assert response.status_code == 401

    async def test_create_event_validation_error(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test event creation with invalid data."""
        invalid_data = {
            "event_type": "",  # Empty event type
            "title": "Test"
            # Missing event_time (required)
        }

        response = await client.post(
            "/api/v1/events",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    async def test_list_events_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_events: list
    ):
        """Test listing events with pagination."""
        response = await client.get(
            "/api/v1/events",
            params={"page": 1, "page_size": 10},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "has_next" in data
        assert isinstance(data["items"], list)

    async def test_list_events_filter_by_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_events: list
    ):
        """Test filtering events by type."""
        response = await client.get(
            "/api/v1/events",
            params={"event_type": "exercise"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        for event in data["items"]:
            assert event["event_type"] == "exercise"

    async def test_get_event_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event: dict
    ):
        """Test retrieving a specific event."""
        event_id = sample_event["id"]

        response = await client.get(
            f"/api/v1/events/{event_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == event_id
        assert data["event_type"] == sample_event["event_type"]

    async def test_get_event_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting non-existent event."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/v1/events/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_event(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event: dict
    ):
        """Test updating an event."""
        event_id = sample_event["id"]
        update_data = {
            "title": "Updated Title",
            "event_data": {"duration_hours": 9}
        }

        response = await client.put(
            f"/api/v1/events/{event_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "Updated Title"
        assert data["event_data"]["duration_hours"] == 9

    async def test_delete_event(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event: dict
    ):
        """Test deleting an event."""
        event_id = sample_event["id"]

        response = await client.delete(
            f"/api/v1/events/{event_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/v1/events/{event_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_batch_create_events(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test batch event creation."""
        events = [
            {
                "event_type": "exercise",
                "title": f"Workout {i}",
                "event_time": datetime.now(timezone.utc).isoformat(),
                "event_data": {"duration_minutes": 30 + i * 5}
            }
            for i in range(5)
        ]

        response = await client.post(
            "/api/v1/events/batch",
            json={"events": events},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert len(data) == 5
        assert all(event["id"] is not None for event in data)

    async def test_rate_limiting(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test API rate limiting."""
        event_data = {
            "event_type": "test",
            "title": "Rate limit test",
            "event_time": datetime.now(timezone.utc).isoformat()
        }

        # Make 101 requests (assuming limit is 100/min)
        responses = []
        for _ in range(101):
            response = await client.post(
                "/api/v1/events",
                json=event_data,
                headers=auth_headers
            )
            responses.append(response.status_code)

        # At least one should be rate limited
        assert 429 in responses


@pytest.mark.asyncio
class TestPredictionsAPI:
    """Test suite for /api/v1/predictions endpoints."""

    async def test_get_energy_prediction(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_events: list
    ):
        """Test energy prediction endpoint."""
        response = await client.get(
            "/api/v1/predictions/energy",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "prediction" in data
        assert "confidence" in data
        assert 0 <= data["prediction"] <= 10

    async def test_get_mood_prediction(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_events: list
    ):
        """Test mood prediction endpoint."""
        response = await client.get(
            "/api/v1/predictions/mood",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "prediction_class" in data
        assert data["prediction_class"] in [
            "very_negative", "negative", "neutral", "positive", "very_positive"
        ]


@pytest.mark.asyncio
class TestInsightsAPI:
    """Test suite for /api/v1/insights endpoints."""

    async def test_generate_insights(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_events: list
    ):
        """Test insight generation."""
        response = await client.post(
            "/api/v1/insights/generate",
            json={"context": "health", "time_range_days": 7},
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert isinstance(data, list)
        if len(data) > 0:
            assert "title" in data[0]
            assert "content" in data[0]

    async def test_list_insights(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing insights."""
        response = await client.get(
            "/api/v1/insights",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data

    async def test_mark_insight_as_read(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_insight: dict
    ):
        """Test marking insight as read."""
        insight_id = sample_insight["id"]

        response = await client.patch(
            f"/api/v1/insights/{insight_id}/read",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_read"] is True


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    async def test_basic_health(self, client: AsyncClient):
        """Test basic health check."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"

    async def test_readiness_check(self, client: AsyncClient):
        """Test readiness check."""
        response = await client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()

        assert "database" in data
        assert "redis" in data

    async def test_detailed_health(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test detailed health check."""
        response = await client.get(
            "/health/detailed",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "database" in data
        assert "redis" in data
        assert "system" in data
