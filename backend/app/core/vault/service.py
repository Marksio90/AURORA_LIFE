"""
Data Vault Service - Zarządzanie pełną historią życia użytkownika
"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.models.user import User
from app.models.life_event import LifeEvent
from app.models.timeline import TimelineEntry


class DataVaultService:
    """
    Data Vault Service - bezpieczne przechowywanie pełnej historii życia.

    Odpowiedzialności:
    - Eksport pełnego profilu użytkownika
    - Archiwizacja danych
    - Statystyki i agregacje
    - GDPR compliance (prawo do pobrania danych)
    - Backup i restore
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_user_data(
        self,
        user_id: int,
        include_events: bool = True,
        include_timeline: bool = True,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Eksportuje pełne dane użytkownika (GDPR compliance).

        Returns:
            Pełny export w formacie JSON
        """
        # Pobierz użytkownika
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            return {}

        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "timezone": user.timezone,
                "profile_data": user.profile_data,
                "life_metrics": {
                    "health_score": user.health_score,
                    "energy_score": user.energy_score,
                    "mood_score": user.mood_score,
                    "productivity_score": user.productivity_score,
                },
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": user.last_active.isoformat() if user.last_active else None,
            },
            "statistics": await self._get_user_statistics(user_id, start_date, end_date)
        }

        # Life Events
        if include_events:
            events_query = select(LifeEvent).where(LifeEvent.user_id == user_id)
            if start_date:
                events_query = events_query.where(LifeEvent.event_time >= start_date)
            if end_date:
                events_query = events_query.where(LifeEvent.event_time <= end_date)

            events_result = await self.db.execute(events_query)
            events = events_result.scalars().all()

            export_data["life_events"] = [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "event_category": event.event_category,
                    "title": event.title,
                    "description": event.description,
                    "event_data": event.event_data,
                    "event_time": event.event_time.isoformat(),
                    "duration_minutes": event.duration_minutes,
                    "impact_score": event.impact_score,
                    "energy_impact": event.energy_impact,
                    "mood_impact": event.mood_impact,
                    "tags": event.tags,
                    "source": event.source,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in events
            ]

        # Timeline
        if include_timeline:
            timeline_query = select(TimelineEntry).where(TimelineEntry.user_id == user_id)
            if start_date:
                timeline_query = timeline_query.where(TimelineEntry.start_time >= start_date)
            if end_date:
                timeline_query = timeline_query.where(TimelineEntry.end_time <= end_date)

            timeline_result = await self.db.execute(timeline_query)
            timeline = timeline_result.scalars().all()

            export_data["timeline"] = [
                {
                    "id": entry.id,
                    "entry_type": entry.entry_type,
                    "start_time": entry.start_time.isoformat(),
                    "end_time": entry.end_time.isoformat(),
                    "title": entry.title,
                    "description": entry.description,
                    "analysis_data": entry.analysis_data,
                    "confidence_score": entry.confidence_score,
                    "importance_score": entry.importance_score,
                    "is_recurring": entry.is_recurring,
                    "is_significant": entry.is_significant,
                    "tags": entry.tags,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                }
                for entry in timeline
            ]

        return export_data

    async def _get_user_statistics(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generuje statystyki użytkownika"""
        # Events statistics
        events_query = select(func.count(LifeEvent.id)).where(LifeEvent.user_id == user_id)
        if start_date:
            events_query = events_query.where(LifeEvent.event_time >= start_date)
        if end_date:
            events_query = events_query.where(LifeEvent.event_time <= end_date)

        total_events_result = await self.db.execute(events_query)
        total_events = total_events_result.scalar()

        # Timeline statistics
        timeline_query = select(func.count(TimelineEntry.id)).where(TimelineEntry.user_id == user_id)
        if start_date:
            timeline_query = timeline_query.where(TimelineEntry.start_time >= start_date)
        if end_date:
            timeline_query = timeline_query.where(TimelineEntry.end_time <= end_date)

        total_timeline_result = await self.db.execute(timeline_query)
        total_timeline = total_timeline_result.scalar()

        # Event types distribution
        type_query = select(
            LifeEvent.event_type,
            func.count(LifeEvent.id)
        ).where(LifeEvent.user_id == user_id).group_by(LifeEvent.event_type)

        if start_date:
            type_query = type_query.where(LifeEvent.event_time >= start_date)
        if end_date:
            type_query = type_query.where(LifeEvent.event_time <= end_date)

        type_result = await self.db.execute(type_query)
        event_types_dist = {row[0]: row[1] for row in type_result.all()}

        return {
            "total_events": total_events or 0,
            "total_timeline_entries": total_timeline or 0,
            "event_types_distribution": event_types_dist,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            }
        }

    async def get_data_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Pobiera podsumowanie danych użytkownika.
        """
        # User info
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            return {}

        # Counts
        events_count_result = await self.db.execute(
            select(func.count(LifeEvent.id)).where(LifeEvent.user_id == user_id)
        )
        events_count = events_count_result.scalar()

        timeline_count_result = await self.db.execute(
            select(func.count(TimelineEntry.id)).where(TimelineEntry.user_id == user_id)
        )
        timeline_count = timeline_count_result.scalar()

        # First and last event
        first_event_result = await self.db.execute(
            select(LifeEvent.event_time)
            .where(LifeEvent.user_id == user_id)
            .order_by(LifeEvent.event_time)
            .limit(1)
        )
        first_event = first_event_result.scalar_one_or_none()

        last_event_result = await self.db.execute(
            select(LifeEvent.event_time)
            .where(LifeEvent.user_id == user_id)
            .order_by(LifeEvent.event_time.desc())
            .limit(1)
        )
        last_event = last_event_result.scalar_one_or_none()

        return {
            "user_id": user.id,
            "username": user.username,
            "total_life_events": events_count or 0,
            "total_timeline_entries": timeline_count or 0,
            "data_span": {
                "first_event": first_event.isoformat() if first_event else None,
                "last_event": last_event.isoformat() if last_event else None,
                "days_tracked": (
                    (last_event - first_event).days
                    if first_event and last_event
                    else 0
                )
            },
            "life_metrics": {
                "health_score": user.health_score,
                "energy_score": user.energy_score,
                "mood_score": user.mood_score,
                "productivity_score": user.productivity_score,
            },
            "account_age_days": (
                (datetime.utcnow() - user.created_at).days
                if user.created_at
                else 0
            )
        }

    async def delete_user_data(
        self,
        user_id: int,
        delete_user: bool = False
    ) -> Dict[str, int]:
        """
        Usuwa dane użytkownika (GDPR right to erasure).

        Returns:
            Liczba usuniętych rekordów
        """
        # Usuń Life Events
        events_result = await self.db.execute(
            select(func.count(LifeEvent.id)).where(LifeEvent.user_id == user_id)
        )
        events_count = events_result.scalar()

        await self.db.execute(
            LifeEvent.__table__.delete().where(LifeEvent.user_id == user_id)
        )

        # Usuń Timeline
        timeline_result = await self.db.execute(
            select(func.count(TimelineEntry.id)).where(TimelineEntry.user_id == user_id)
        )
        timeline_count = timeline_result.scalar()

        await self.db.execute(
            TimelineEntry.__table__.delete().where(TimelineEntry.user_id == user_id)
        )

        # Opcjonalnie usuń użytkownika
        user_deleted = 0
        if delete_user:
            await self.db.execute(
                User.__table__.delete().where(User.id == user_id)
            )
            user_deleted = 1

        await self.db.commit()

        return {
            "events_deleted": events_count or 0,
            "timeline_deleted": timeline_count or 0,
            "user_deleted": user_deleted
        }

    async def archive_old_data(
        self,
        user_id: int,
        older_than_days: int = 365
    ) -> Dict[str, Any]:
        """
        Archiwizuje stare dane (opcjonalna funkcjonalność).
        W pełnej implementacji przeniosłoby to dane do cold storage.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # Zlicz stare wydarzenia
        old_events_result = await self.db.execute(
            select(func.count(LifeEvent.id)).where(
                and_(
                    LifeEvent.user_id == user_id,
                    LifeEvent.event_time < cutoff_date
                )
            )
        )
        old_events_count = old_events_result.scalar()

        return {
            "archivable_events": old_events_count or 0,
            "cutoff_date": cutoff_date.isoformat(),
            "note": "Archiving not yet implemented - placeholder for cold storage"
        }
