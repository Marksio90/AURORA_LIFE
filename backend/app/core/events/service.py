"""
Life Event Service - Logika biznesowa dla zdarzeń życiowych
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.life_event import LifeEvent
from app.schemas.life_event import LifeEventCreate, LifeEventUpdate


class LifeEventService:
    """
    Life Event Service - zarządza zdarzeniami życiowymi użytkownika.

    Odpowiedzialności:
    - Tworzenie, aktualizacja, usuwanie zdarzeń
    - Zapytania temporalne (po czasie, typie, kategorii)
    - Obliczanie metryk wpływu (impact, energy, mood)
    - Agregacja danych dla analizy
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(
        self,
        user_id: int,
        event_data: LifeEventCreate
    ) -> LifeEvent:
        """
        Tworzy nowe zdarzenie życiowe.
        """
        # Oblicz end_time jeśli jest duration
        end_time = None
        if event_data.duration_minutes:
            end_time = event_data.event_time + timedelta(minutes=event_data.duration_minutes)

        # Utwórz zdarzenie
        event = LifeEvent(
            user_id=user_id,
            event_type=event_data.event_type,
            event_category=event_data.event_category,
            title=event_data.title,
            description=event_data.description,
            event_data=event_data.event_data,
            event_time=event_data.event_time,
            duration_minutes=event_data.duration_minutes,
            end_time=end_time,
            tags=event_data.tags,
            context=event_data.context,
            source=event_data.source
        )

        # Oblicz podstawowe metryki wpływu
        event = self._calculate_impact_scores(event)

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        return event

    def _calculate_impact_scores(self, event: LifeEvent) -> LifeEvent:
        """
        Oblicza podstawowe metryki wpływu zdarzenia.
        W przyszłości (Zestaw 2) będzie to robione przez DataGenius z ML.
        """
        # Proste heurystyki jako placeholder
        impact_map = {
            "sleep": 0.8,
            "exercise": 0.7,
            "activity": 0.6,
            "emotion": 0.5,
            "work": 0.4,
            "social": 0.5,
            "health": 0.7,
        }

        event.impact_score = impact_map.get(event.event_type, 0.3)

        # Energy impact
        if event.event_type in ["sleep", "exercise", "rest"]:
            event.energy_impact = 0.5
        elif event.event_type in ["work", "stress"]:
            event.energy_impact = -0.3
        else:
            event.energy_impact = 0.0

        # Mood impact
        if event.event_type == "emotion":
            emotion_type = event.event_data.get("type", "")
            if emotion_type in ["happy", "joy", "excited"]:
                event.mood_impact = 0.7
            elif emotion_type in ["sad", "angry", "stressed"]:
                event.mood_impact = -0.5
            else:
                event.mood_impact = 0.0
        else:
            event.mood_impact = 0.0

        return event

    async def get_event(self, event_id: int, user_id: int) -> Optional[LifeEvent]:
        """Pobiera zdarzenie po ID"""
        result = await self.db.execute(
            select(LifeEvent).where(
                and_(LifeEvent.id == event_id, LifeEvent.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_events(
        self,
        user_id: int,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[LifeEvent]:
        """
        Pobiera zdarzenia użytkownika z filtrami.
        """
        query = select(LifeEvent).where(LifeEvent.user_id == user_id)

        if event_type:
            query = query.where(LifeEvent.event_type == event_type)
        if start_time:
            query = query.where(LifeEvent.event_time >= start_time)
        if end_time:
            query = query.where(LifeEvent.event_time <= end_time)

        query = query.order_by(desc(LifeEvent.event_time)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_events(
        self,
        user_id: int,
        days: int = 7,
        event_type: Optional[str] = None
    ) -> List[LifeEvent]:
        """Pobiera ostatnie zdarzenia z N dni"""
        start_time = datetime.utcnow() - timedelta(days=days)
        return await self.get_events(
            user_id=user_id,
            event_type=event_type,
            start_time=start_time
        )

    async def update_event(
        self,
        event_id: int,
        user_id: int,
        event_data: LifeEventUpdate
    ) -> Optional[LifeEvent]:
        """Aktualizuje zdarzenie"""
        event = await self.get_event(event_id, user_id)
        if not event:
            return None

        if event_data.title is not None:
            event.title = event_data.title
        if event_data.description is not None:
            event.description = event_data.description
        if event_data.event_data is not None:
            event.event_data = event_data.event_data
        if event_data.tags is not None:
            event.tags = event_data.tags
        if event_data.context is not None:
            event.context = event_data.context

        event.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(event)

        return event

    async def delete_event(self, event_id: int, user_id: int) -> bool:
        """Usuwa zdarzenie"""
        event = await self.get_event(event_id, user_id)
        if not event:
            return False

        await self.db.delete(event)
        await self.db.commit()

        return True

    async def get_event_stats(
        self,
        user_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Generuje statystyki zdarzeń dla danego okresu.
        """
        events = await self.get_events(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        # Agregacja
        type_counts = {}
        total_impact = 0.0
        total_energy = 0.0
        total_mood = 0.0

        for event in events:
            # Zlicz typy
            type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1

            # Suma metryk
            if event.impact_score:
                total_impact += event.impact_score
            if event.energy_impact:
                total_energy += event.energy_impact
            if event.mood_impact:
                total_mood += event.mood_impact

        count = len(events)
        return {
            "total_events": count,
            "event_types": type_counts,
            "avg_impact": total_impact / count if count > 0 else 0.0,
            "total_energy_change": total_energy,
            "total_mood_change": total_mood,
            "period": {
                "start": start_time,
                "end": end_time
            }
        }
