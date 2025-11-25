"""
Data Vault API - Endpoints dla Data Vault
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.core.vault import DataVaultService

router = APIRouter(prefix="/api/vault", tags=["Data Vault"])


@router.get("/export/{user_id}")
async def export_user_data(
    user_id: int,
    include_events: bool = Query(True),
    include_timeline: bool = Query(True),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Eksportuje pełne dane użytkownika (GDPR compliance).
    Pobiera wszystkie dane w formacie JSON.
    """
    service = DataVaultService(db)
    export_data = await service.export_user_data(
        user_id=user_id,
        include_events=include_events,
        include_timeline=include_timeline,
        start_date=start_date,
        end_date=end_date
    )

    if not export_data:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(content=export_data)


@router.get("/summary/{user_id}")
async def get_data_summary(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pobiera podsumowanie danych użytkownika"""
    service = DataVaultService(db)
    summary = await service.get_data_summary(user_id)

    if not summary:
        raise HTTPException(status_code=404, detail="User not found")

    return summary


@router.delete("/user/{user_id}")
async def delete_user_data(
    user_id: int,
    delete_user: bool = Query(False, description="Also delete user account"),
    db: AsyncSession = Depends(get_db)
):
    """
    Usuwa dane użytkownika (GDPR right to erasure).
    Opcjonalnie usuwa też konto użytkownika.
    """
    service = DataVaultService(db)
    result = await service.delete_user_data(user_id, delete_user)

    return {
        "message": "User data deleted successfully",
        "details": result
    }


@router.get("/archive/{user_id}")
async def archive_old_data(
    user_id: int,
    older_than_days: int = Query(365, description="Archive data older than N days"),
    db: AsyncSession = Depends(get_db)
):
    """Informuje o danych do archiwizacji"""
    service = DataVaultService(db)
    result = await service.archive_old_data(user_id, older_than_days)

    return result
