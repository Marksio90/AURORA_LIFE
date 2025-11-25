"""
Users API - Endpoints dla Core Identity Layer
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.core.identity import IdentityService
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Tworzy nowego użytkownika"""
    service = IdentityService(db)
    try:
        user = await service.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pobiera użytkownika po ID"""
    service = IdentityService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Aktualizuje profil użytkownika"""
    service = IdentityService(db)
    user = await service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/digital-twin")
async def get_digital_twin(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pobiera pełny cyfrowy profil użytkownika (digital twin)"""
    service = IdentityService(db)
    digital_twin = await service.get_digital_twin(user_id)
    if not digital_twin:
        raise HTTPException(status_code=404, detail="User not found")
    return digital_twin
