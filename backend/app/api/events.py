"""
Life Events API - Endpoints dla Life Event Stream
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.core.events import LifeEventService, EventStreamManager
from app.schemas.life_event import LifeEventCreate, LifeEventUpdate, LifeEventResponse

router = APIRouter(prefix="/api/events", tags=["Life Events"])


@router.post("/", response_model=LifeEventResponse, status_code=201)
async def create_event(
    user_id: int,
    event_data: LifeEventCreate,
    publish_to_stream: bool = Query(True, description="Publish to Redis Stream"),
    db: AsyncSession = Depends(get_db)
):
    """Tworzy nowe zdarzenie życiowe"""
    service = LifeEventService(db)
    event = await service.create_event(user_id, event_data)

    # Publikuj do Redis Stream dla real-time processing
    if publish_to_stream:
        stream_manager = EventStreamManager()
        await stream_manager.publish_event(
            event_id=event.id,
            user_id=event.user_id,
            event_type=event.event_type,
            event_time=event.event_time,
            data=event.event_data
        )

    return event


@router.get("/{event_id}", response_model=LifeEventResponse)
async def get_event(
    event_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pobiera zdarzenie po ID"""
    service = LifeEventService(db)
    event = await service.get_event(event_id, user_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/", response_model=List[LifeEventResponse])
async def get_events(
    user_id: int,
    event_type: Optional[str] = None,
    days: Optional[int] = Query(7, description="Number of days to look back"),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Pobiera zdarzenia użytkownika"""
    service = LifeEventService(db)

    if days:
        events = await service.get_recent_events(user_id, days, event_type)
    else:
        events = await service.get_events(user_id, event_type=event_type, limit=limit)

    return events


@router.put("/{event_id}", response_model=LifeEventResponse)
async def update_event(
    event_id: int,
    user_id: int,
    event_data: LifeEventUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Aktualizuje zdarzenie"""
    service = LifeEventService(db)
    event = await service.update_event(event_id, user_id, event_data)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Usuwa zdarzenie"""
    service = LifeEventService(db)
    success = await service.delete_event(event_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")


@router.get("/stats/summary")
async def get_event_stats(
    user_id: int,
    days: int = Query(30, description="Period in days"),
    db: AsyncSession = Depends(get_db)
):
    """Generuje statystyki zdarzeń"""
    service = LifeEventService(db)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    stats = await service.get_event_stats(user_id, start_time, end_time)
    return stats
