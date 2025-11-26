"""
Pytest configuration for integration tests.

Provides fixtures for:
- HTTP client
- Authentication
- Sample data
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

from app.main import app
from app.core.database import get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict:
    """Create a test user."""
    from app.models.user import User
    from app.core.auth.jwt import hash_password

    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
        is_verified=True,
        role="user"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "password": "TestPassword123!"
    }


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: dict) -> dict:
    """Get authentication headers."""
    response = await client.post(
        "/api/auth/login",
        json={
            "username": test_user["username"],
            "password": test_user["password"]
        }
    )

    assert response.status_code == 200
    data = response.json()
    access_token = data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def sample_event(
    client: AsyncClient,
    auth_headers: dict
) -> dict:
    """Create a sample event."""
    event_data = {
        "event_type": "sleep",
        "title": "Sample sleep event",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "event_data": {"duration_hours": 7.5}
    }

    response = await client.post(
        "/api/v1/events",
        json=event_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def sample_events(
    client: AsyncClient,
    auth_headers: dict
) -> list:
    """Create multiple sample events."""
    events = []

    for i in range(10):
        event_data = {
            "event_type": "exercise" if i % 2 == 0 else "work",
            "title": f"Sample event {i}",
            "event_time": datetime.now(timezone.utc).isoformat(),
            "event_data": {"index": i}
        }

        response = await client.post(
            "/api/v1/events",
            json=event_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        events.append(response.json())

    return events


@pytest_asyncio.fixture
async def sample_insight(
    client: AsyncClient,
    auth_headers: dict,
    sample_events: list
) -> dict:
    """Create a sample insight."""
    response = await client.post(
        "/api/v1/insights/generate",
        json={"context": "test", "time_range_days": 7},
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    return data[0] if data else None
