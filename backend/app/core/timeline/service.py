"""
Timeline Service - Zarządzanie osią czasu życia
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.timeline import TimelineEntry
from app.schemas.timeline import TimelineEntryCreate


class TimelineService:
    """
    Timeline Service - zarządza osią czasu życia użytkownika.

    Odpowiedzialności:
    - Tworzenie wpisów timeline (wzorce, cykle, anomalie, trendy)
    - Zapytania temporalne
    - Zarządzanie znaczącymi momentami (milestones)
    - Agregacja insights
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_entry(
        self,
        user_id: int,
        entry_data: TimelineEntryCreate
    ) -> TimelineEntry:
        """Tworzy nowy wpis na timeline"""
        entry = TimelineEntry(
            user_id=user_id,
            entry_type=entry_data.entry_type,
            start_time=entry_data.start_time,
            end_time=entry_data.end_time,
            title=entry_data.title,
            description=entry_data.description,
            analysis_data=entry_data.analysis_data,
            confidence_score=entry_data.confidence_score,
            importance_score=entry_data.importance_score,
            related_event_ids=entry_data.related_event_ids,
            is_recurring=entry_data.is_recurring,
            is_significant=entry_data.is_significant,
            tags=entry_data.tags
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def get_entry(self, entry_id: int, user_id: int) -> Optional[TimelineEntry]:
        """Pobiera wpis po ID"""
        result = await self.db.execute(
            select(TimelineEntry).where(
                and_(TimelineEntry.id == entry_id, TimelineEntry.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_entries(
        self,
        user_id: int,
        entry_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        significant_only: bool = False,
        limit: int = 100
    ) -> List[TimelineEntry]:
        """Pobiera wpisy timeline z filtrami"""
        query = select(TimelineEntry).where(TimelineEntry.user_id == user_id)

        if entry_type:
            query = query.where(TimelineEntry.entry_type == entry_type)
        if start_time:
            query = query.where(TimelineEntry.start_time >= start_time)
        if end_time:
            query = query.where(TimelineEntry.end_time <= end_time)
        if significant_only:
            query = query.where(TimelineEntry.is_significant == True)

        query = query.order_by(desc(TimelineEntry.start_time)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_patterns(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TimelineEntry]:
        """Pobiera wykryte wzorce"""
        return await self.get_entries(
            user_id=user_id,
            entry_type="pattern",
            start_time=start_time,
            end_time=end_time
        )

    async def get_anomalies(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TimelineEntry]:
        """Pobiera wykryte anomalie"""
        return await self.get_entries(
            user_id=user_id,
            entry_type="anomaly",
            start_time=start_time,
            end_time=end_time
        )

    async def get_trends(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[TimelineEntry]:
        """Pobiera wykryte trendy"""
        return await self.get_entries(
            user_id=user_id,
            entry_type="trend",
            start_time=start_time,
            end_time=end_time
        )

    async def get_milestones(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[TimelineEntry]:
        """Pobiera znaczące momenty (milestones)"""
        return await self.get_entries(
            user_id=user_id,
            entry_type="milestone",
            significant_only=True,
            limit=limit
        )

    async def get_insights(
        self,
        user_id: int,
        days: int = 7
    ) -> List[TimelineEntry]:
        """Pobiera ostatnie insights"""
        start_time = datetime.utcnow() - timedelta(days=days)
        return await self.get_entries(
            user_id=user_id,
            entry_type="insight",
            start_time=start_time
        )

    async def delete_entry(self, entry_id: int, user_id: int) -> bool:
        """Usuwa wpis"""
        entry = await self.get_entry(entry_id, user_id)
        if not entry:
            return False

        await self.db.delete(entry)
        await self.db.commit()

        return True

    async def get_timeline_summary(
        self,
        user_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generuje podsumowanie timeline dla okresu"""
        entries = await self.get_entries(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )

        # Agregacja
        type_counts = {}
        significant_entries = []
        avg_confidence = 0.0
        total_confidence = 0.0
        confidence_count = 0

        for entry in entries:
            type_counts[entry.entry_type] = type_counts.get(entry.entry_type, 0) + 1

            if entry.is_significant:
                significant_entries.append({
                    "id": entry.id,
                    "type": entry.entry_type,
                    "title": entry.title,
                    "time": entry.start_time
                })

            if entry.confidence_score is not None:
                total_confidence += entry.confidence_score
                confidence_count += 1

        if confidence_count > 0:
            avg_confidence = total_confidence / confidence_count

        return {
            "total_entries": len(entries),
            "entry_types": type_counts,
            "significant_count": len(significant_entries),
            "significant_entries": significant_entries[:10],  # Top 10
            "avg_confidence": avg_confidence,
            "period": {
                "start": start_time,
                "end": end_time
            }
        }
