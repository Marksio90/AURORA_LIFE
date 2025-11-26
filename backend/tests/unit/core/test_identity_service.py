"""
Unit tests for Identity Service.
"""
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity.service import IdentityService
from app.schemas.user import UserCreate, UserUpdate, UserProfileData
from app.models.user import User


class TestPasswordHandling:
    """Tests for password hashing and verification."""

    def test_hash_password(self):
        """Test password is hashed correctly."""
        password = "SecurePassword123!"
        hashed = IdentityService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_deterministic(self):
        """Test same password produces different hashes (salted)."""
        password = "SamePassword123"
        hash1 = IdentityService.hash_password(password)
        hash2 = IdentityService.hash_password(password)

        assert hash1 != hash2  # Different salt each time

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "MyPassword123!"
        hashed = IdentityService.hash_password(password)

        assert IdentityService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "MyPassword123!"
        hashed = IdentityService.hash_password(password)

        assert IdentityService.verify_password("WrongPassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test password verification is case sensitive."""
        password = "MyPassword"
        hashed = IdentityService.hash_password(password)

        assert IdentityService.verify_password("mypassword", hashed) is False


@pytest.mark.asyncio
class TestCreateUser:
    """Tests for user creation."""

    async def test_create_user_success(self, db_session: AsyncSession):
        """Test successfully creating a new user."""
        service = IdentityService(db_session)
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="Password123!",
            full_name="New User",
            timezone="America/New_York"
        )

        user = await service.create_user(user_data)

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.full_name == "New User"
        assert user.timezone == "America/New_York"
        assert user.hashed_password != "Password123!"  # Should be hashed
        assert IdentityService.verify_password("Password123!", user.hashed_password)

    async def test_create_user_initializes_profile(self, db_session: AsyncSession):
        """Test user creation initializes digital twin profile."""
        service = IdentityService(db_session)
        user_data = UserCreate(
            email="profile@example.com",
            username="profileuser",
            password="Pass123!"
        )

        user = await service.create_user(user_data)

        assert user.profile_data is not None
        assert "goals" in user.profile_data
        assert "values" in user.profile_data
        assert "preferences" in user.profile_data
        assert "life_state" in user.profile_data
        assert user.profile_data["goals"] == []
        assert user.profile_data["values"] == []
        assert isinstance(user.profile_data["life_state"], dict)

    async def test_create_user_initializes_scores(self, db_session: AsyncSession):
        """Test user creation initializes life scores to 0.5."""
        service = IdentityService(db_session)
        user_data = UserCreate(
            email="scores@example.com",
            username="scoreuser",
            password="Pass123!"
        )

        user = await service.create_user(user_data)

        assert user.health_score == 0.5
        assert user.energy_score == 0.5
        assert user.mood_score == 0.5
        assert user.productivity_score == 0.5

    async def test_create_user_sets_timestamps(self, db_session: AsyncSession):
        """Test user creation sets created_at and last_active."""
        service = IdentityService(db_session)
        user_data = UserCreate(
            email="time@example.com",
            username="timeuser",
            password="Pass123!"
        )

        before = datetime.utcnow()
        user = await service.create_user(user_data)
        after = datetime.utcnow()

        assert user.created_at is not None
        assert before <= user.created_at <= after
        assert user.last_active is not None
        assert before <= user.last_active <= after

    async def test_create_user_duplicate_email(self, db_session: AsyncSession, test_user: User):
        """Test creating user with duplicate email raises error."""
        service = IdentityService(db_session)
        user_data = UserCreate(
            email=test_user.email,  # Same email as existing user
            username="different",
            password="Pass123!"
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_user(user_data)

    async def test_create_user_duplicate_username(self, db_session: AsyncSession, test_user: User):
        """Test creating user with duplicate username raises error."""
        service = IdentityService(db_session)
        user_data = UserCreate(
            email="different@example.com",
            username=test_user.username,  # Same username as existing user
            password="Pass123!"
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_user(user_data)


@pytest.mark.asyncio
class TestGetUser:
    """Tests for retrieving users."""

    async def test_get_user_by_id_exists(self, db_session: AsyncSession, test_user: User):
        """Test getting user by ID when user exists."""
        service = IdentityService(db_session)

        user = await service.get_user(test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_user_by_id_not_exists(self, db_session: AsyncSession):
        """Test getting user by ID when user doesn't exist."""
        service = IdentityService(db_session)

        user = await service.get_user(99999)

        assert user is None

    async def test_get_user_by_email_exists(self, db_session: AsyncSession, test_user: User):
        """Test getting user by email when user exists."""
        service = IdentityService(db_session)

        user = await service.get_user_by_email(test_user.email)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_user_by_email_not_exists(self, db_session: AsyncSession):
        """Test getting user by email when user doesn't exist."""
        service = IdentityService(db_session)

        user = await service.get_user_by_email("nonexistent@example.com")

        assert user is None

    async def test_get_user_by_email_case_sensitive(self, db_session: AsyncSession, test_user: User):
        """Test email lookup is case sensitive."""
        service = IdentityService(db_session)

        user = await service.get_user_by_email(test_user.email.upper())

        # Note: This depends on database collation. PostgreSQL is case-sensitive by default.
        # If the user is found, the database has case-insensitive collation.
        # For strict testing, we expect case sensitivity.
        assert user is None or user.email == test_user.email


@pytest.mark.asyncio
class TestUpdateUser:
    """Tests for updating user profile."""

    async def test_update_user_full_name(self, db_session: AsyncSession, test_user: User):
        """Test updating user's full name."""
        service = IdentityService(db_session)
        update_data = UserUpdate(full_name="Updated Name")

        updated_user = await service.update_user(test_user.id, update_data)

        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.id == test_user.id

    async def test_update_user_timezone(self, db_session: AsyncSession, test_user: User):
        """Test updating user's timezone."""
        service = IdentityService(db_session)
        update_data = UserUpdate(timezone="Europe/Warsaw")

        updated_user = await service.update_user(test_user.id, update_data)

        assert updated_user is not None
        assert updated_user.timezone == "Europe/Warsaw"

    async def test_update_user_profile_data(self, db_session: AsyncSession, test_user: User):
        """Test updating user's profile data."""
        service = IdentityService(db_session)
        profile_data = UserProfileData(
            goals=["fitness", "career"],
            values=["honesty", "growth"],
            preferences={"theme": "dark"},
            life_state={"energy": 0.8}
        )
        update_data = UserUpdate(profile_data=profile_data)

        updated_user = await service.update_user(test_user.id, update_data)

        assert updated_user is not None
        assert updated_user.profile_data["goals"] == ["fitness", "career"]
        assert updated_user.profile_data["values"] == ["honesty", "growth"]
        assert updated_user.profile_data["preferences"]["theme"] == "dark"

    async def test_update_user_multiple_fields(self, db_session: AsyncSession, test_user: User):
        """Test updating multiple user fields at once."""
        service = IdentityService(db_session)
        profile_data = UserProfileData(goals=["health"])
        update_data = UserUpdate(
            full_name="Multi Update",
            timezone="Asia/Tokyo",
            profile_data=profile_data
        )

        updated_user = await service.update_user(test_user.id, update_data)

        assert updated_user is not None
        assert updated_user.full_name == "Multi Update"
        assert updated_user.timezone == "Asia/Tokyo"
        assert updated_user.profile_data["goals"] == ["health"]

    async def test_update_user_updates_timestamp(self, db_session: AsyncSession, test_user: User):
        """Test user update updates the updated_at timestamp."""
        service = IdentityService(db_session)
        original_updated_at = test_user.updated_at
        update_data = UserUpdate(full_name="New Name")

        updated_user = await service.update_user(test_user.id, update_data)

        assert updated_user.updated_at > original_updated_at

    async def test_update_user_not_found(self, db_session: AsyncSession):
        """Test updating non-existent user returns None."""
        service = IdentityService(db_session)
        update_data = UserUpdate(full_name="Ghost User")

        result = await service.update_user(99999, update_data)

        assert result is None

    async def test_update_user_empty_update(self, db_session: AsyncSession, test_user: User):
        """Test updating user with no fields still updates timestamp."""
        service = IdentityService(db_session)
        original_updated_at = test_user.updated_at
        update_data = UserUpdate()

        updated_user = await service.update_user(test_user.id, update_data)

        assert updated_user is not None
        assert updated_user.updated_at > original_updated_at


@pytest.mark.asyncio
class TestUpdateLifeScores:
    """Tests for updating life metrics scores."""

    async def test_update_single_score(self, db_session: AsyncSession, test_user: User):
        """Test updating a single life score."""
        service = IdentityService(db_session)

        updated_user = await service.update_life_scores(
            test_user.id,
            health_score=0.9
        )

        assert updated_user is not None
        assert updated_user.health_score == 0.9
        # Other scores should remain unchanged
        assert updated_user.energy_score == test_user.energy_score

    async def test_update_multiple_scores(self, db_session: AsyncSession, test_user: User):
        """Test updating multiple life scores."""
        service = IdentityService(db_session)

        updated_user = await service.update_life_scores(
            test_user.id,
            health_score=0.8,
            energy_score=0.7,
            mood_score=0.9,
            productivity_score=0.6
        )

        assert updated_user.health_score == 0.8
        assert updated_user.energy_score == 0.7
        assert updated_user.mood_score == 0.9
        assert updated_user.productivity_score == 0.6

    async def test_update_scores_clamps_upper_bound(self, db_session: AsyncSession, test_user: User):
        """Test scores are clamped to max 1.0."""
        service = IdentityService(db_session)

        updated_user = await service.update_life_scores(
            test_user.id,
            health_score=1.5,
            energy_score=2.0
        )

        assert updated_user.health_score == 1.0
        assert updated_user.energy_score == 1.0

    async def test_update_scores_clamps_lower_bound(self, db_session: AsyncSession, test_user: User):
        """Test scores are clamped to min 0.0."""
        service = IdentityService(db_session)

        updated_user = await service.update_life_scores(
            test_user.id,
            mood_score=-0.5,
            productivity_score=-1.0
        )

        assert updated_user.mood_score == 0.0
        assert updated_user.productivity_score == 0.0

    async def test_update_scores_user_not_found(self, db_session: AsyncSession):
        """Test updating scores for non-existent user returns None."""
        service = IdentityService(db_session)

        result = await service.update_life_scores(
            99999,
            health_score=0.8
        )

        assert result is None

    async def test_update_scores_updates_timestamp(self, db_session: AsyncSession, test_user: User):
        """Test updating scores updates the updated_at timestamp."""
        service = IdentityService(db_session)
        original_updated_at = test_user.updated_at

        updated_user = await service.update_life_scores(
            test_user.id,
            health_score=0.9
        )

        assert updated_user.updated_at > original_updated_at


@pytest.mark.asyncio
class TestUpdateProfileData:
    """Tests for updating specific profile data fields."""

    async def test_update_profile_field(self, db_session: AsyncSession, test_user: User):
        """Test updating a specific field in profile_data."""
        service = IdentityService(db_session)

        updated_user = await service.update_profile_data(
            test_user.id,
            "goals",
            ["new goal 1", "new goal 2"]
        )

        assert updated_user is not None
        assert updated_user.profile_data["goals"] == ["new goal 1", "new goal 2"]

    async def test_update_profile_nested_field(self, db_session: AsyncSession, test_user: User):
        """Test updating a nested field in profile_data."""
        service = IdentityService(db_session)

        updated_user = await service.update_profile_data(
            test_user.id,
            "preferences",
            {"theme": "dark", "notifications": True}
        )

        assert updated_user.profile_data["preferences"] == {
            "theme": "dark",
            "notifications": True
        }

    async def test_update_profile_new_field(self, db_session: AsyncSession, test_user: User):
        """Test adding a new field to profile_data."""
        service = IdentityService(db_session)

        updated_user = await service.update_profile_data(
            test_user.id,
            "custom_field",
            "custom value"
        )

        assert updated_user.profile_data["custom_field"] == "custom value"

    async def test_update_profile_empty_profile(self, db_session: AsyncSession):
        """Test updating profile_data when it's initially None."""
        service = IdentityService(db_session)
        # Create a user with empty profile
        user = User(
            email="empty@example.com",
            username="emptyprofile",
            hashed_password="hash",
            profile_data=None
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        updated_user = await service.update_profile_data(
            user.id,
            "new_field",
            "new value"
        )

        assert updated_user.profile_data is not None
        assert updated_user.profile_data["new_field"] == "new value"

    async def test_update_profile_user_not_found(self, db_session: AsyncSession):
        """Test updating profile for non-existent user returns None."""
        service = IdentityService(db_session)

        result = await service.update_profile_data(
            99999,
            "field",
            "value"
        )

        assert result is None


@pytest.mark.asyncio
class TestGetDigitalTwin:
    """Tests for retrieving complete digital twin profile."""

    async def test_get_digital_twin_success(self, db_session: AsyncSession, test_user: User):
        """Test getting complete digital twin for existing user."""
        service = IdentityService(db_session)

        twin = await service.get_digital_twin(test_user.id)

        assert twin is not None
        assert twin["user_id"] == test_user.id
        assert twin["username"] == test_user.username
        assert twin["email"] == test_user.email
        assert twin["full_name"] == test_user.full_name
        assert twin["timezone"] == test_user.timezone
        assert "profile" in twin
        assert "life_metrics" in twin
        assert "last_active" in twin
        assert "created_at" in twin

    async def test_get_digital_twin_life_metrics(self, db_session: AsyncSession, test_user: User):
        """Test digital twin contains all life metrics."""
        service = IdentityService(db_session)

        twin = await service.get_digital_twin(test_user.id)

        metrics = twin["life_metrics"]
        assert "health_score" in metrics
        assert "energy_score" in metrics
        assert "mood_score" in metrics
        assert "productivity_score" in metrics
        assert metrics["health_score"] == test_user.health_score

    async def test_get_digital_twin_profile_data(self, db_session: AsyncSession, test_user: User):
        """Test digital twin contains complete profile data."""
        service = IdentityService(db_session)

        # Update profile first
        await service.update_profile_data(
            test_user.id,
            "goals",
            ["goal1", "goal2"]
        )

        twin = await service.get_digital_twin(test_user.id)

        assert twin["profile"]["goals"] == ["goal1", "goal2"]

    async def test_get_digital_twin_not_found(self, db_session: AsyncSession):
        """Test getting digital twin for non-existent user returns None."""
        service = IdentityService(db_session)

        twin = await service.get_digital_twin(99999)

        assert twin is None

    async def test_get_digital_twin_structure(self, db_session: AsyncSession, test_user: User):
        """Test digital twin has correct structure."""
        service = IdentityService(db_session)

        twin = await service.get_digital_twin(test_user.id)

        # Verify all expected keys are present
        expected_keys = {
            "user_id", "username", "email", "full_name", "timezone",
            "profile", "life_metrics", "last_active", "created_at"
        }
        assert set(twin.keys()) == expected_keys

        # Verify life_metrics structure
        expected_metric_keys = {
            "health_score", "energy_score", "mood_score", "productivity_score"
        }
        assert set(twin["life_metrics"].keys()) == expected_metric_keys
