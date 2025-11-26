"""
Unit tests for Timeline Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from app.schemas.timeline import (
    TimelineEntryCreate,
    TimelineEntryResponse,
    PatternDetectionResult
)


class TestTimelineEntryCreate:
    """Tests for TimelineEntryCreate schema."""

    def test_create_entry_minimum_fields(self):
        """Test creating entry with minimum required fields."""
        entry = TimelineEntryCreate(
            entry_type="pattern",
            start_time=datetime(2024, 1, 1, 0, 0),
            end_time=datetime(2024, 1, 7, 23, 59),
            title="Weekly sleep pattern"
        )
        assert entry.entry_type == "pattern"
        assert entry.title == "Weekly sleep pattern"
        assert entry.is_recurring is False  # default
        assert entry.is_significant is False  # default
        assert entry.analysis_data == {}  # default
        assert entry.tags == []  # default

    def test_create_entry_all_fields(self):
        """Test creating entry with all fields."""
        entry = TimelineEntryCreate(
            entry_type="pattern",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 7),
            title="Sleep pattern",
            description="Consistent 7-8 hours",
            analysis_data={"avg_hours": 7.5, "regularity": 0.9},
            confidence_score=0.95,
            importance_score=0.8,
            related_event_ids=[1, 2, 3],
            is_recurring=True,
            is_significant=True,
            tags=["sleep", "health"]
        )
        assert entry.description == "Consistent 7-8 hours"
        assert entry.confidence_score == 0.95
        assert entry.importance_score == 0.8
        assert entry.related_event_ids == [1, 2, 3]
        assert entry.is_recurring is True
        assert entry.is_significant is True

    def test_create_entry_confidence_score_validation(self):
        """Test confidence score must be between 0 and 1."""
        # Valid scores
        entry = TimelineEntryCreate(
            entry_type="pattern",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            title="Test",
            confidence_score=0.5
        )
        assert entry.confidence_score == 0.5

        # Invalid score > 1
        with pytest.raises(ValidationError) as exc_info:
            TimelineEntryCreate(
                entry_type="pattern",
                start_time=datetime(2024, 1, 1),
                end_time=datetime(2024, 1, 2),
                title="Test",
                confidence_score=1.5
            )
        assert "confidence_score" in str(exc_info.value)

        # Invalid score < 0
        with pytest.raises(ValidationError):
            TimelineEntryCreate(
                entry_type="pattern",
                start_time=datetime(2024, 1, 1),
                end_time=datetime(2024, 1, 2),
                title="Test",
                confidence_score=-0.1
            )

    def test_create_entry_importance_score_validation(self):
        """Test importance score must be between 0 and 1."""
        # Valid
        entry = TimelineEntryCreate(
            entry_type="milestone",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 1),
            title="Achievement",
            importance_score=0.9
        )
        assert entry.importance_score == 0.9

        # Invalid
        with pytest.raises(ValidationError):
            TimelineEntryCreate(
                entry_type="milestone",
                start_time=datetime(2024, 1, 1),
                end_time=datetime(2024, 1, 1),
                title="Achievement",
                importance_score=2.0
            )

    def test_create_entry_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            TimelineEntryCreate(
                entry_type="pattern",
                start_time=datetime(2024, 1, 1)
                # missing end_time and title
            )
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "end_time" in field_names
        assert "title" in field_names


class TestTimelineEntryResponse:
    """Tests for TimelineEntryResponse schema."""

    def test_create_entry_response(self):
        """Test creating timeline entry response."""
        response = TimelineEntryResponse(
            id=1,
            user_id=10,
            entry_type="pattern",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 7),
            title="Sleep pattern",
            description="Good sleep cycle",
            analysis_data={"avg": 7.5},
            confidence_score=0.9,
            importance_score=0.8,
            related_event_ids=[1, 2, 3],
            is_recurring=True,
            is_significant=False,
            tags=["sleep"],
            created_at=datetime(2024, 1, 8)
        )
        assert response.id == 1
        assert response.user_id == 10
        assert response.entry_type == "pattern"
        assert response.confidence_score == 0.9

    def test_entry_response_serialization(self):
        """Test entry response serialization."""
        response = TimelineEntryResponse(
            id=1,
            user_id=10,
            entry_type="anomaly",
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 1),
            title="Unusual activity",
            description=None,
            analysis_data={},
            confidence_score=None,
            importance_score=None,
            related_event_ids=[],
            is_recurring=False,
            is_significant=False,
            tags=[],
            created_at=datetime(2024, 1, 1)
        )
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["entry_type"] == "anomaly"

    def test_entry_response_from_orm(self):
        """Test Config for ORM mode."""
        assert TimelineEntryResponse.model_config.get("from_attributes") is True


class TestPatternDetectionResult:
    """Tests for PatternDetectionResult schema."""

    def test_create_pattern_result(self):
        """Test creating pattern detection result."""
        result = PatternDetectionResult(
            pattern_type="sleep_cycle",
            confidence=0.85,
            description="Consistent bedtime around 23:00",
            data={
                "avg_bedtime": "23:00",
                "regularity_score": 0.9,
                "duration_avg": 7.5
            }
        )
        assert result.pattern_type == "sleep_cycle"
        assert result.confidence == 0.85
        assert result.description == "Consistent bedtime around 23:00"
        assert result.data["avg_bedtime"] == "23:00"

    def test_pattern_result_serialization(self):
        """Test pattern result can be serialized."""
        result = PatternDetectionResult(
            pattern_type="activity_burst",
            confidence=0.7,
            description="Increased activity on weekends",
            data={"days": ["Saturday", "Sunday"]}
        )
        data = result.model_dump()
        assert isinstance(data, dict)
        assert data["pattern_type"] == "activity_burst"
        assert data["confidence"] == 0.7

    def test_pattern_result_missing_required(self):
        """Test validation fails for missing fields."""
        with pytest.raises(ValidationError):
            PatternDetectionResult(
                pattern_type="test"
                # missing confidence, description, data
            )

    def test_pattern_result_with_complex_data(self):
        """Test pattern result with nested complex data."""
        result = PatternDetectionResult(
            pattern_type="multi_dimensional",
            confidence=0.95,
            description="Complex pattern detected",
            data={
                "dimensions": ["sleep", "exercise", "mood"],
                "correlations": {
                    "sleep_exercise": 0.7,
                    "exercise_mood": 0.8
                },
                "insights": [
                    {"type": "positive", "strength": 0.9},
                    {"type": "negative", "strength": 0.3}
                ]
            }
        )
        assert isinstance(result.data["correlations"], dict)
        assert isinstance(result.data["insights"], list)
        assert len(result.data["insights"]) == 2
