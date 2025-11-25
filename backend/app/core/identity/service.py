"""
Identity Service - Logika biznesowa dla profilu użytkownika
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class IdentityService:
    """
    Identity Service - zarządza cyfrowym bliźniakiem użytkownika.

    Odpowiedzialności:
    - Tworzenie i aktualizacja profilu użytkownika
    - Zarządzanie danymi osobowymi, celami, wartościami
    - Obliczanie metryk życiowych (health, energy, mood, productivity)
    - Synchronizacja stanu cyfrowego bliźniaka
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash hasła"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Weryfikacja hasła"""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Tworzy nowego użytkownika i inicjalizuje cyfrowego bliźniaka.
        """
        # Sprawdź czy email/username już istnieje
        existing = await self.db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User with this email or username already exists")

        # Utwórz użytkownika
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=self.hash_password(user_data.password),
            full_name=user_data.full_name,
            timezone=user_data.timezone,
            profile_data={
                "goals": [],
                "values": [],
                "preferences": {},
                "life_state": {
                    "health": {},
                    "relationships": {},
                    "finances": {},
                    "career": {},
                    "personal_growth": {}
                }
            },
            last_active=datetime.utcnow()
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """Pobiera użytkownika po ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Pobiera użytkownika po email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Aktualizuje profil użytkownika.
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        # Aktualizuj podstawowe dane
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.timezone is not None:
            user.timezone = user_data.timezone

        # Aktualizuj profile_data
        if user_data.profile_data is not None:
            user.profile_data = user_data.profile_data.model_dump()

        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_life_scores(
        self,
        user_id: int,
        health_score: Optional[float] = None,
        energy_score: Optional[float] = None,
        mood_score: Optional[float] = None,
        productivity_score: Optional[float] = None
    ) -> Optional[User]:
        """
        Aktualizuje metryki życiowe użytkownika.
        Te wartości są obliczane przez inne moduły (DataGenius, Agents).
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        if health_score is not None:
            user.health_score = max(0.0, min(1.0, health_score))
        if energy_score is not None:
            user.energy_score = max(0.0, min(1.0, energy_score))
        if mood_score is not None:
            user.mood_score = max(0.0, min(1.0, mood_score))
        if productivity_score is not None:
            user.productivity_score = max(0.0, min(1.0, productivity_score))

        user.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_profile_data(
        self,
        user_id: int,
        field: str,
        value: Any
    ) -> Optional[User]:
        """
        Aktualizuje konkretne pole w profile_data.
        Np. dodaje nowy cel, wartość, aktualizuje stan życia.
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        if not user.profile_data:
            user.profile_data = {}

        user.profile_data[field] = value
        user.updated_at = datetime.utcnow()

        # Flag modified for JSONB update
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "profile_data")

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def get_digital_twin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Pobiera pełny cyfrowy profil użytkownika (digital twin).
        Zwraca kompletny obraz: dane osobowe, cele, wartości, metryki.
        """
        user = await self.get_user(user_id)
        if not user:
            return None

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "timezone": user.timezone,
            "profile": user.profile_data,
            "life_metrics": {
                "health_score": user.health_score,
                "energy_score": user.energy_score,
                "mood_score": user.mood_score,
                "productivity_score": user.productivity_score,
            },
            "last_active": user.last_active,
            "created_at": user.created_at,
        }
