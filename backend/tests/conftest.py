"""
Pytest configuration and shared fixtures for AURORA_LIFE tests.

This module provides:
- Database fixtures (test database, session)
- Redis fixtures (test Redis connection)
- API client fixtures (FastAPI TestClient)
- User fixtures (test users, authentication)
- Event fixtures (test events, data)
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from redis.asyncio import Redis

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models.user import User
from app.models.event import LifeEvent
from app.models.timeline import TimelineEntry
from app.core.identity.service import IdentityService
from app.core.events.service import EventService


# ============================================================================
# Pytest Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Don't pool connections in tests
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_factory(test_engine):
    """Create a test session factory."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="function")
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def override_get_db(db_session):
    """Override the get_db dependency."""
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def redis_client() -> AsyncGenerator[Redis, None]:
    """Create a test Redis client."""
    client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    yield client

    # Clean up all keys
    await client.flushdb()
    await client.aclose()


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create a test API client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, test_user: User, access_token: str) -> AsyncClient:
    """Create an authenticated test API client."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {access_token}"
    }
    return client


# ============================================================================
# User Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def identity_service(db_session: AsyncSession) -> IdentityService:
    """Create an IdentityService instance."""
    return IdentityService(db_session)


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession, identity_service: IdentityService) -> User:
    """Create a test user."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "timezone": "UTC",
    }

    user = await identity_service.create_user(**user_data)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def test_user_2(db_session: AsyncSession, identity_service: IdentityService) -> User:
    """Create a second test user."""
    user_data = {
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "TestPassword123!",
        "full_name": "Test User 2",
        "timezone": "UTC",
    }

    user = await identity_service.create_user(**user_data)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession, identity_service: IdentityService) -> User:
    """Create an admin test user."""
    user_data = {
        "email": "admin@example.com",
        "username": "adminuser",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "timezone": "UTC",
    }

    user = await identity_service.create_user(**user_data)
    # TODO: Add admin role when RBAC is implemented
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
def access_token(test_user: User) -> str:
    """Generate an access token for the test user."""
    # TODO: Implement when JWT auth is added
    return "fake-jwt-token-for-testing"


# ============================================================================
# Event Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def event_service(db_session: AsyncSession, redis_client: Redis) -> EventService:
    """Create an EventService instance."""
    return EventService(db_session, redis_client)


@pytest_asyncio.fixture(scope="function")
async def test_sleep_event(db_session: AsyncSession, test_user: User) -> LifeEvent:
    """Create a test sleep event."""
    from datetime import datetime, timedelta

    event = LifeEvent(
        user_id=test_user.id,
        event_type="sleep",
        event_data={
            "duration_hours": 7.5,
            "quality": "good",
            "went_to_bed": "23:00",
            "woke_up": "06:30",
        },
        impact_score=0.8,
        timestamp=datetime.utcnow() - timedelta(hours=8),
        tags=["rest", "recovery"],
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    return event


@pytest_asyncio.fixture(scope="function")
async def test_exercise_event(db_session: AsyncSession, test_user: User) -> LifeEvent:
    """Create a test exercise event."""
    from datetime import datetime, timedelta

    event = LifeEvent(
        user_id=test_user.id,
        event_type="exercise",
        event_data={
            "type": "running",
            "duration_minutes": 30,
            "intensity": "moderate",
            "distance_km": 5.0,
        },
        impact_score=0.7,
        timestamp=datetime.utcnow() - timedelta(hours=2),
        tags=["fitness", "outdoor"],
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    return event


@pytest_asyncio.fixture(scope="function")
async def test_events_batch(db_session: AsyncSession, test_user: User) -> list[LifeEvent]:
    """Create a batch of test events for various scenarios."""
    from datetime import datetime, timedelta

    events = []

    # Create events for the last 7 days
    for i in range(7):
        # Sleep event
        sleep = LifeEvent(
            user_id=test_user.id,
            event_type="sleep",
            event_data={
                "duration_hours": 7.0 + (i % 3) * 0.5,
                "quality": ["poor", "good", "excellent"][i % 3],
            },
            impact_score=0.6 + (i % 3) * 0.15,
            timestamp=datetime.utcnow() - timedelta(days=i, hours=8),
        )
        events.append(sleep)

        # Exercise event
        if i % 2 == 0:
            exercise = LifeEvent(
                user_id=test_user.id,
                event_type="exercise",
                event_data={
                    "type": ["running", "gym", "yoga"][i % 3],
                    "duration_minutes": 30 + i * 5,
                },
                impact_score=0.7,
                timestamp=datetime.utcnow() - timedelta(days=i, hours=14),
            )
            events.append(exercise)

        # Work event
        work = LifeEvent(
            user_id=test_user.id,
            event_type="work",
            event_data={
                "hours": 8,
                "productivity": ["low", "medium", "high"][i % 3],
            },
            impact_score=0.5 + (i % 3) * 0.15,
            timestamp=datetime.utcnow() - timedelta(days=i, hours=10),
        )
        events.append(work)

    for event in events:
        db_session.add(event)

    await db_session.commit()

    for event in events:
        await db_session.refresh(event)

    return events


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mock_datetime(monkeypatch):
    """Mock datetime for deterministic testing."""
    from datetime import datetime

    class MockDatetime:
        @staticmethod
        def utcnow():
            return datetime(2024, 1, 15, 12, 0, 0)

        @staticmethod
        def now():
            return datetime(2024, 1, 15, 12, 0, 0)

    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return MockDatetime


@pytest.fixture(scope="function")
def sample_life_event_data() -> dict:
    """Provide sample life event data."""
    return {
        "event_type": "emotion",
        "event_data": {
            "emotion": "happy",
            "intensity": 8,
            "trigger": "good news",
        },
        "impact_score": 0.8,
        "tags": ["positive", "social"],
        "context": "Received promotion at work",
    }


@pytest.fixture(scope="function")
def sample_user_data() -> dict:
    """Provide sample user registration data."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "SecurePassword123!",
        "full_name": "New User",
        "timezone": "America/New_York",
    }
