"""
Timeline Schemas - Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class TimelineEntryCreate(BaseModel):
    """Schema dla tworzenia wpisu timeline"""
    entry_type: str = Field(..., description="Typ: pattern, cycle, anomaly, trend, milestone, insight")
    start_time: datetime
    end_time: datetime
    title: str
    description: Optional[str] = None
    analysis_data: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    related_event_ids: List[int] = Field(default_factory=list)
    is_recurring: bool = False
    is_significant: bool = False
    tags: List[str] = Field(default_factory=list)


class TimelineEntryResponse(BaseModel):
    """Schema odpowiedzi"""
    id: int
    user_id: int
    entry_type: str
    start_time: datetime
    end_time: datetime
    title: str
    description: Optional[str]
    analysis_data: Dict[str, Any]
    confidence_score: Optional[float]
    importance_score: Optional[float]
    related_event_ids: List[int]
    is_recurring: bool
    is_significant: bool
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PatternDetectionResult(BaseModel):
    """Wynik wykrywania wzorca"""
    pattern_type: str
    confidence: float
    description: str
    data: Dict[str, Any]
