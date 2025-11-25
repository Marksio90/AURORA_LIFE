"""
Behavioral Timeline Engine - Timeline Model
Oś czasu życia z wykrytymi wzorami
"""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Float, ForeignKey, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base


class TimelineEntry(Base):
    """
    Timeline Entry - reprezentuje przetworzone dane na osi czasu.

    Timeline Engine analizuje Life Events i tworzy:
    - Wzorce (patterns)
    - Cykle (cycles)
    - Anomalie (anomalies)
    - Trendy (trends)
    """
    __tablename__ = "timeline_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Entry Type
    entry_type = Column(String, nullable=False, index=True)
    # Types: pattern, cycle, anomaly, trend, milestone, insight

    # Temporal Range
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Title and Description
    title = Column(String, nullable=False)
    description = Column(String)

    # Pattern/Analysis Data
    analysis_data = Column(JSON, default=dict)
    # Przykłady:
    # - pattern: {type: "sleep_cycle", avg_duration: 7.5, regularity: 0.85}
    # - anomaly: {deviation: 2.5, expected: 8.0, actual: 5.5}
    # - trend: {direction: "improving", change_rate: 0.15, confidence: 0.92}

    # Metrics
    confidence_score = Column(Float)  # 0.0 - 1.0
    importance_score = Column(Float)  # 0.0 - 1.0

    # Related Events
    related_event_ids = Column(JSON, default=list)  # Lista ID powiązanych Life Events

    # Flags
    is_recurring = Column(Boolean, default=False)
    is_significant = Column(Boolean, default=False)

    # Tags
    tags = Column(JSON, default=list)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TimelineEntry(id={self.id}, type={self.entry_type}, start={self.start_time})>"


# Indeksy dla wydajnych zapytań
Index("idx_user_timeline_time", TimelineEntry.user_id, TimelineEntry.start_time)
Index("idx_user_timeline_type", TimelineEntry.user_id, TimelineEntry.entry_type)
