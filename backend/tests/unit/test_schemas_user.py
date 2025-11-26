"""
Unit tests for User Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.user import (
    UserProfileData,
    UserCreate,
    UserUpdate,
    UserResponse
)


class TestUserProfileData:
    """Tests for UserProfileData schema."""

    def test_create_empty_profile_data(self):
        """Test creating empty profile data with defaults."""
        profile = UserProfileData()
        assert profile.goals == []
        assert profile.values == []
        assert profile.preferences == {}
        assert profile.life_state == {}

    def test_create_profile_data_with_values(self):
        """Test creating profile data with values."""
        profile = UserProfileData(
            goals=["health", "career"],
            values=["honesty", "growth"],
            preferences={"theme": "dark"},
            life_state={"energy": 0.8}
        )
        assert profile.goals == ["health", "career"]
        assert profile.values == ["honesty", "growth"]
        assert profile.preferences == {"theme": "dark"}
        assert profile.life_state == {"energy": 0.8}

    def test_profile_data_serialization(self):
        """Test profile data serialization to dict."""
        profile = UserProfileData(goals=["fitness"])
        data = profile.model_dump()
        assert isinstance(data, dict)
        assert data["goals"] == ["fitness"]


class TestUserCreate:
    """Tests for UserCreate schema."""

    def test_create_user_minimum_fields(self):
        """Test creating user with minimum required fields."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "password123"
        assert user.timezone == "UTC"  # default
        assert user.full_name is None  # optional

    def test_create_user_all_fields(self):
        """Test creating user with all fields."""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User",
            timezone="America/New_York"
        )
        assert user.full_name == "Test User"
        assert user.timezone == "America/New_York"

    def test_create_user_invalid_email(self):
        """Test validation fails for invalid email."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="not-an-email",
                username="testuser",
                password="password123"
            )
        assert "email" in str(exc_info.value)

    def test_create_user_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")


class TestUserUpdate:
    """Tests for UserUpdate schema."""

    def test_update_user_empty(self):
        """Test update with no fields."""
        update = UserUpdate()
        assert update.full_name is None
        assert update.timezone is None
        assert update.profile_data is None

    def test_update_user_partial(self):
        """Test partial update."""
        update = UserUpdate(full_name="New Name")
        assert update.full_name == "New Name"
        assert update.timezone is None

    def test_update_user_all_fields(self):
        """Test updating all fields."""
        profile = UserProfileData(goals=["new goal"])
        update = UserUpdate(
            full_name="Updated Name",
            timezone="Europe/Warsaw",
            profile_data=profile
        )
        assert update.full_name == "Updated Name"
        assert update.timezone == "Europe/Warsaw"
        assert update.profile_data.goals == ["new goal"]


class TestUserResponse:
    """Tests for UserResponse schema."""

    def test_create_user_response(self):
        """Test creating user response."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            timezone="UTC",
            profile_data={},
            health_score=0.8,
            energy_score=0.7,
            mood_score=0.9,
            productivity_score=0.6,
            created_at=datetime(2024, 1, 1),
            last_active=None
        )
        assert response.id == 1
        assert response.email == "test@example.com"
        assert response.health_score == 0.8

    def test_user_response_serialization(self):
        """Test user response serialization."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            username="testuser",
            timezone="UTC",
            profile_data={"test": "data"},
            health_score=0.8,
            energy_score=0.7,
            mood_score=0.9,
            productivity_score=0.6,
            created_at=datetime(2024, 1, 1)
        )
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["id"] == 1
        assert data["profile_data"] == {"test": "data"}

    def test_user_response_from_orm(self):
        """Test creating response from ORM model."""
        # This will be tested in integration tests with actual ORM models
        # Here we just verify the Config is set correctly
        assert UserResponse.model_config.get("from_attributes") is True
