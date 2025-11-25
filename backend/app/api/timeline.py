"""
Timeline API - Endpoints dla Behavioral Timeline Engine
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.core.timeline import TimelineService, PatternAnalyzer
from app.core.events import LifeEventService
from app.schemas.timeline import TimelineEntryCreate, TimelineEntryResponse

router = APIRouter(prefix="/api/timeline", tags=["Timeline"])


@router.post("/", response_model=TimelineEntryResponse, status_code=201)
async def create_timeline_entry(
    user_id: int,
    entry_data: TimelineEntryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Tworzy nowy wpis na timeline"""
    service = TimelineService(db)
    entry = await service.create_entry(user_id, entry_data)
    return entry


@router.get("/{entry_id}", response_model=TimelineEntryResponse)
async def get_timeline_entry(
    entry_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Pobiera wpis timeline po ID"""
    service = TimelineService(db)
    entry = await service.get_entry(entry_id, user_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timeline entry not found")
    return entry


@router.get("/", response_model=List[TimelineEntryResponse])
async def get_timeline_entries(
    user_id: int,
    entry_type: Optional[str] = None,
    days: Optional[int] = Query(30, description="Number of days to look back"),
    significant_only: bool = False,
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Pobiera wpisy timeline"""
    service = TimelineService(db)

    start_time = None
    if days:
        start_time = datetime.utcnow() - timedelta(days=days)

    entries = await service.get_entries(
        user_id=user_id,
        entry_type=entry_type,
        start_time=start_time,
        significant_only=significant_only,
        limit=limit
    )
    return entries


@router.get("/patterns/detect")
async def detect_patterns(
    user_id: int,
    days: int = Query(30, description="Period to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Wykrywa wzorce życiowe użytkownika.
    Analizuje Life Events i generuje insights.
    """
    event_service = LifeEventService(db)
    timeline_service = TimelineService(db)
    analyzer = PatternAnalyzer()

    # Pobierz zdarzenia z ostatnich N dni
    recent_events = await event_service.get_recent_events(user_id, days)

    if not recent_events:
        return {"message": "No events to analyze", "patterns": []}

    patterns = []

    # Wykryj wzorzec snu
    sleep_events = [e for e in recent_events if e.event_type == "sleep"]
    if sleep_events:
        sleep_pattern = analyzer.detect_sleep_pattern(sleep_events)
        if sleep_pattern:
            patterns.append(sleep_pattern)

    # Wykryj wzorzec aktywności
    activity_events = [e for e in recent_events if e.event_type in ["activity", "exercise"]]
    if activity_events:
        activity_pattern = analyzer.detect_activity_pattern(activity_events)
        if activity_pattern:
            patterns.append(activity_pattern)

    # Wykryj anomalie w śnie
    if sleep_events:
        anomalies = analyzer.detect_anomalies(sleep_events, "duration_minutes")
        if anomalies:
            patterns.append({
                "type": "sleep_anomalies",
                "count": len(anomalies),
                "anomalies": anomalies[:5]  # Top 5
            })

    # Wykryj trend w energii (jeśli są dane)
    energy_events = [e for e in recent_events if "energy_level" in e.event_data]
    if energy_events:
        energy_trend = analyzer.detect_trend(energy_events, "energy_level")
        if energy_trend:
            patterns.append(energy_trend)

    return {
        "user_id": user_id,
        "analysis_period_days": days,
        "events_analyzed": len(recent_events),
        "patterns_found": len(patterns),
        "patterns": patterns
    }


@router.get("/insights/recent")
async def get_recent_insights(
    user_id: int,
    days: int = Query(7, description="Number of days"),
    db: AsyncSession = Depends(get_db)
):
    """Pobiera ostatnie insights"""
    service = TimelineService(db)
    insights = await service.get_insights(user_id, days)
    return insights


@router.get("/summary/period")
async def get_timeline_summary(
    user_id: int,
    days: int = Query(30, description="Period in days"),
    db: AsyncSession = Depends(get_db)
):
    """Generuje podsumowanie timeline dla okresu"""
    service = TimelineService(db)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    summary = await service.get_timeline_summary(user_id, start_time, end_time)
    return summary
