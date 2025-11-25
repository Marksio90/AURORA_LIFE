"""
Core Identity Layer - User Model (Cyfrowy Bliźniak)
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Float
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class User(Base):
    """
    User Model - reprezentuje cyfrowego bliźniaka użytkownika.

    Przechowuje:
    - Podstawowe dane osobowe
    - Cele życiowe
    - Wartości i preferencje
    - Stan życia (zdrowie, relacje, finanse)
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Profile Information
    full_name = Column(String)
    date_of_birth = Column(DateTime)
    timezone = Column(String, default="UTC")

    # Digital Twin Core Data (JSONB for flexibility)
    # Struktura: {goals: [], values: [], preferences: {}, life_state: {}}
    profile_data = Column(JSON, default=dict)

    # Life State Metrics (aktualizowane przez system)
    health_score = Column(Float, default=0.0)
    energy_score = Column(Float, default=0.0)
    mood_score = Column(Float, default=0.0)
    productivity_score = Column(Float, default=0.0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True))

    # Settings
    settings = Column(JSON, default=dict)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
