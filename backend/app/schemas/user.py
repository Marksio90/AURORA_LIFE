"""
User Schemas - Pydantic models dla API
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class UserProfileData(BaseModel):
    """Struktura danych profilu użytkownika"""
    goals: List[str] = Field(default_factory=list, description="Cele życiowe")
    values: List[str] = Field(default_factory=list, description="Wartości użytkownika")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Preferencje")
    life_state: Dict[str, Any] = Field(default_factory=dict, description="Stan życia")


class UserCreate(BaseModel):
    """Schema dla tworzenia nowego użytkownika"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    timezone: str = "UTC"


class UserUpdate(BaseModel):
    """Schema dla aktualizacji użytkownika"""
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    profile_data: Optional[UserProfileData] = None


class UserResponse(BaseModel):
    """Schema odpowiedzi z danymi użytkownika"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    timezone: str
    profile_data: Dict[str, Any]
    health_score: float
    energy_score: float
    mood_score: float
    productivity_score: float
    created_at: datetime
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True
