"""
Core Identity Layer - User Model (Cyfrowy Bliźniak)
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
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

    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String, default="user", nullable=False)  # user, admin, moderator

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

    # Relationships
    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class OAuthAccount(Base):
    """
    OAuth Account Model - links User to external OAuth providers (Google, GitHub, etc.)
    """
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)  # google, github, etc.
    provider_user_id = Column(String, nullable=False)  # User ID from the provider
    access_token = Column(String)  # OAuth access token (encrypted in production)
    refresh_token = Column(String)  # OAuth refresh token (encrypted in production)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="oauth_accounts")

    def __repr__(self):
        return f"<OAuthAccount(user_id={self.user_id}, provider={self.provider})>"
