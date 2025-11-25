"""
Life Event Schemas - Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class LifeEventCreate(BaseModel):
    """Schema dla tworzenia nowego zdarzenia życiowego"""
    event_type: str = Field(..., description="Typ zdarzenia: sleep, activity, emotion, etc.")
    event_category: Optional[str] = Field(None, description="Kategoria: wellness, productivity, social, etc.")
    title: str = Field(..., description="Tytuł zdarzenia")
    description: Optional[str] = None
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Szczegółowe dane zdarzenia")
    event_time: datetime = Field(..., description="Czas wystąpienia zdarzenia")
    duration_minutes: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="manual", description="Źródło: manual, api, wearable, etc.")


class LifeEventUpdate(BaseModel):
    """Schema dla aktualizacji zdarzenia"""
    title: Optional[str] = None
    description: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


class LifeEventResponse(BaseModel):
    """Schema odpowiedzi ze zdarzeniem"""
    id: int
    user_id: int
    event_type: str
    event_category: Optional[str]
    title: str
    description: Optional[str]
    event_data: Dict[str, Any]
    event_time: datetime
    duration_minutes: Optional[int]
    end_time: Optional[datetime]
    impact_score: Optional[float]
    energy_impact: Optional[float]
    mood_impact: Optional[float]
    tags: List[str]
    context: Dict[str, Any]
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class EventStreamMessage(BaseModel):
    """Wiadomość w strumieniu Redis"""
    event_id: int
    user_id: int
    event_type: str
    event_time: datetime
    data: Dict[str, Any]
