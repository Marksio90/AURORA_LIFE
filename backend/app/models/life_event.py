"""
Life Event Stream (LES) - LifeEvent Model
Strumień zdarzeń życiowych
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Float, ForeignKey, Index
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base


class LifeEvent(Base):
    """
    Life Event Model - reprezentuje pojedyncze zdarzenie życiowe.

    Każdy aspekt życia jest rejestrowany jako zdarzenie:
    - Sen, aktywność fizyczna
    - Spotkania, interakcje społeczne
    - Emocje, nastroje
    - Sukcesy, porażki
    - Zakupy, wydatki
    - Itp.
    """
    __tablename__ = "life_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Event Classification
    event_type = Column(String, nullable=False, index=True)
    # Types: sleep, activity, meeting, emotion, health, finance, social, work, etc.

    event_category = Column(String, index=True)
    # Categories: wellness, productivity, social, personal, etc.

    # Event Details
    title = Column(String, nullable=False)
    description = Column(String)

    # Event Data (flexible JSONB structure)
    # Przykłady:
    # - sleep: {duration: 7.5, quality: 8, deep_sleep: 2.1, rem: 1.8}
    # - activity: {type: "running", duration: 30, distance: 5, calories: 350}
    # - emotion: {type: "happy", intensity: 8, trigger: "promotion"}
    event_data = Column(JSON, default=dict)

    # Temporal Information
    event_time = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer)  # Opcjonalny czas trwania
    end_time = Column(DateTime(timezone=True))

    # Metrics (automatycznie wyznaczane przez system)
    impact_score = Column(Float)  # Wpływ na życie użytkownika (-1.0 do 1.0)
    energy_impact = Column(Float)  # Wpływ na energię
    mood_impact = Column(Float)  # Wpływ na nastrój

    # Tags and Context
    tags = Column(JSON, default=list)  # Lista tagów: ["important", "recurring", ...]
    context = Column(JSON, default=dict)  # Kontekst: {location: ..., weather: ..., ...}

    # Source
    source = Column(String, default="manual")
    # Sources: manual, api, wearable, calendar, automation

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<LifeEvent(id={self.id}, type={self.event_type}, time={self.event_time})>"


# Indeksy dla wydajnych zapytań temporalnych
Index("idx_user_event_time", LifeEvent.user_id, LifeEvent.event_time)
Index("idx_user_event_type_time", LifeEvent.user_id, LifeEvent.event_type, LifeEvent.event_time)
