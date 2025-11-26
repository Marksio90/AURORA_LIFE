"""
Natural Language Interface for querying life data.

Allows users to ask questions in natural language:
- "How much sleep did I get last week?"
- "Show me my energy levels for January"
- "What were my top activities this month?"
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import re

from app.integrations.openai_client import OpenAIClient
from app.integrations.claude_client import ClaudeClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

import logging

logger = logging.getLogger(__name__)


class NaturalLanguageInterface:
    """Service for natural language queries."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_client = OpenAIClient()
        self.claude_client = ClaudeClient()

    async def process_query(
        self,
        user_id: UUID,
        query: str,
        use_claude: bool = False
    ) -> Dict[str, Any]:
        """
        Process a natural language query.

        Args:
            user_id: User UUID
            query: Natural language question
            use_claude: Whether to use Claude instead of GPT-4

        Returns:
            Response with answer and data
        """
        # Extract intent and parameters from query
        intent = await self._extract_intent(query, use_claude)

        # Execute query based on intent
        if intent["type"] == "aggregation":
            data = await self._handle_aggregation_query(user_id, intent)
        elif intent["type"] == "comparison":
            data = await self._handle_comparison_query(user_id, intent)
        elif intent["type"] == "trend":
            data = await self._handle_trend_query(user_id, intent)
        elif intent["type"] == "recommendation":
            data = await self._handle_recommendation_query(user_id, intent)
        else:
            data = await self._handle_general_query(user_id, query, use_claude)

        # Generate natural language response
        response = await self._generate_response(query, data, use_claude)

        return {
            "query": query,
            "intent": intent,
            "data": data,
            "response": response
        }

    async def _extract_intent(
        self,
        query: str,
        use_claude: bool = False
    ) -> Dict[str, Any]:
        """Extract intent and parameters from query using LLM."""
        prompt = f"""
Analyze this life data query and extract:
1. Query type: aggregation, comparison, trend, recommendation, or general
2. Metric: sleep, exercise, work, mood, energy, social, or general
3. Time range: specific dates or relative (last week, this month, etc.)
4. Aggregation: sum, average, count, min, max

Query: "{query}"

Respond in JSON format:
{{
    "type": "aggregation|comparison|trend|recommendation|general",
    "metric": "sleep|exercise|work|mood|energy|social|general",
    "time_range": "last_week|last_month|this_year|...",
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "aggregation": "sum|average|count|min|max|null"
}}
"""

        if use_claude:
            response = await self.claude_client.generate(prompt, max_tokens=500)
        else:
            response = await self.openai_client.generate(prompt, max_tokens=500)

        # Parse JSON from response
        import json
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                intent = json.loads(json_match.group())
            else:
                intent = {"type": "general", "metric": "general"}
        except json.JSONDecodeError:
            intent = {"type": "general", "metric": "general"}

        # Parse relative time ranges
        if intent.get("time_range"):
            intent.update(self._parse_time_range(intent["time_range"]))

        return intent

    def _parse_time_range(self, time_range: str) -> Dict[str, Any]:
        """Parse relative time ranges into dates."""
        now = datetime.utcnow()

        mappings = {
            "today": (now.replace(hour=0, minute=0, second=0), now),
            "yesterday": (
                (now - timedelta(days=1)).replace(hour=0, minute=0, second=0),
                (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            ),
            "last_week": (now - timedelta(days=7), now),
            "last_month": (now - timedelta(days=30), now),
            "last_year": (now - timedelta(days=365), now),
            "this_week": (
                now - timedelta(days=now.weekday()),
                now
            ),
            "this_month": (
                now.replace(day=1, hour=0, minute=0, second=0),
                now
            ),
            "this_year": (
                now.replace(month=1, day=1, hour=0, minute=0, second=0),
                now
            ),
        }

        dates = mappings.get(time_range, (now - timedelta(days=30), now))

        return {
            "start_date": dates[0].isoformat(),
            "end_date": dates[1].isoformat()
        }

    async def _handle_aggregation_query(
        self,
        user_id: UUID,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle aggregation queries (sum, average, count)."""
        from app.models.event import Event

        metric = intent.get("metric")
        start_date = datetime.fromisoformat(intent["start_date"])
        end_date = datetime.fromisoformat(intent["end_date"])

        # Query events
        result = await self.db.execute(
            select(Event).where(
                and_(
                    Event.user_id == user_id,
                    Event.event_type == metric,
                    Event.event_time >= start_date,
                    Event.event_time <= end_date
                )
            )
        )

        events = result.scalars().all()

        # Compute aggregation
        agg_func = intent.get("aggregation", "count")

        if agg_func == "count":
            value = len(events)
        elif agg_func == "sum":
            value = sum(
                e.event_data.get("duration_hours", 0) or
                e.event_data.get("duration_minutes", 0) / 60
                for e in events
            )
        elif agg_func == "average":
            values = [
                e.event_data.get("duration_hours", 0) or
                e.event_data.get("duration_minutes", 0) / 60
                for e in events
            ]
            value = sum(values) / len(values) if values else 0
        else:
            value = len(events)

        return {
            "metric": metric,
            "aggregation": agg_func,
            "value": value,
            "count": len(events),
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    async def _handle_comparison_query(
        self,
        user_id: UUID,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle comparison queries."""
        # Compare two time periods
        metric = intent.get("metric")

        # Period 1: Last week
        end1 = datetime.utcnow()
        start1 = end1 - timedelta(days=7)

        # Period 2: Week before that
        end2 = start1
        start2 = end2 - timedelta(days=7)

        period1_data = await self._get_metric_summary(user_id, metric, start1, end1)
        period2_data = await self._get_metric_summary(user_id, metric, start2, end2)

        return {
            "metric": metric,
            "period1": period1_data,
            "period2": period2_data,
            "change_percent": (
                ((period1_data["value"] - period2_data["value"]) / period2_data["value"] * 100)
                if period2_data["value"] > 0 else 0
            )
        }

    async def _get_metric_summary(
        self,
        user_id: UUID,
        metric: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        from app.models.event import Event

        result = await self.db.execute(
            select(Event).where(
                and_(
                    Event.user_id == user_id,
                    Event.event_type == metric,
                    Event.event_time >= start_date,
                    Event.event_time <= end_date
                )
            )
        )

        events = result.scalars().all()

        total = sum(
            e.event_data.get("duration_hours", 0) or
            e.event_data.get("duration_minutes", 0) / 60
            for e in events
        )

        return {
            "count": len(events),
            "value": total,
            "average": total / len(events) if events else 0,
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }

    async def _handle_trend_query(
        self,
        user_id: UUID,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle trend analysis queries."""
        # Get daily values for the metric
        metric = intent.get("metric")
        start_date = datetime.fromisoformat(intent["start_date"])
        end_date = datetime.fromisoformat(intent["end_date"])

        from app.models.event import Event

        result = await self.db.execute(
            select(
                func.date(Event.event_time).label("date"),
                func.count(Event.id).label("count"),
                func.sum(
                    func.coalesce(
                        Event.event_data["duration_hours"].astext.cast(Float),
                        Event.event_data["duration_minutes"].astext.cast(Float) / 60,
                        0
                    )
                ).label("total")
            )
            .where(
                and_(
                    Event.user_id == user_id,
                    Event.event_type == metric,
                    Event.event_time >= start_date,
                    Event.event_time <= end_date
                )
            )
            .group_by(func.date(Event.event_time))
            .order_by(func.date(Event.event_time))
        )

        daily_values = [
            {
                "date": row[0].isoformat(),
                "count": row[1],
                "value": float(row[2]) if row[2] else 0
            }
            for row in result.fetchall()
        ]

        # Calculate trend (simple linear regression slope)
        if len(daily_values) > 1:
            values = [d["value"] for d in daily_values]
            x = list(range(len(values)))
            import numpy as np
            slope = np.polyfit(x, values, 1)[0]
            trend = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        else:
            trend = "insufficient_data"

        return {
            "metric": metric,
            "daily_values": daily_values,
            "trend": trend,
            "average": sum(d["value"] for d in daily_values) / len(daily_values) if daily_values else 0
        }

    async def _handle_recommendation_query(
        self,
        user_id: UUID,
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle recommendation queries."""
        # Use AI to generate recommendations based on user data
        metric = intent.get("metric", "general")

        # Get recent data summary
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        data_summary = await self._get_metric_summary(user_id, metric, start_date, end_date)

        prompt = f"""
Based on this user's {metric} data from the last 30 days:
- Count: {data_summary['count']} events
- Total: {data_summary['value']:.1f} hours
- Average: {data_summary['average']:.1f} hours per event

Provide 3-5 actionable recommendations to improve their {metric}.
Be specific, practical, and encouraging.
"""

        recommendations = await self.openai_client.generate(prompt)

        return {
            "metric": metric,
            "data_summary": data_summary,
            "recommendations": recommendations
        }

    async def _handle_general_query(
        self,
        user_id: UUID,
        query: str,
        use_claude: bool = False
    ) -> Dict[str, Any]:
        """Handle general queries that don't fit specific patterns."""
        # Get user context
        from app.models.event import Event

        result = await self.db.execute(
            select(Event).where(Event.user_id == user_id)
            .order_by(Event.event_time.desc())
            .limit(50)
        )

        recent_events = result.scalars().all()

        context = f"User's recent activities:\n"
        for event in recent_events[:10]:
            context += f"- {event.event_type}: {event.title} ({event.event_time.date()})\n"

        prompt = f"{context}\n\nUser question: {query}\n\nProvide a helpful answer based on their activity data."

        if use_claude:
            answer = await self.claude_client.generate(prompt)
        else:
            answer = await self.openai_client.generate(prompt)

        return {
            "context_events": len(recent_events),
            "answer": answer
        }

    async def _generate_response(
        self,
        query: str,
        data: Dict[str, Any],
        use_claude: bool = False
    ) -> str:
        """Generate natural language response."""
        prompt = f"""
User asked: "{query}"

Data retrieved:
{json.dumps(data, indent=2)}

Generate a natural, conversational response that answers their question clearly and concisely.
Include relevant numbers and insights. Be friendly and encouraging.
"""

        if use_claude:
            return await self.claude_client.generate(prompt, max_tokens=500)
        else:
            return await self.openai_client.generate(prompt, max_tokens=500)


# Example usage:
"""
from app.ml.natural_language import NaturalLanguageInterface

nli = NaturalLanguageInterface(db)

result = await nli.process_query(
    user_id=user.id,
    query="How much sleep did I get last week?"
)

print(result["response"])
# "You got an average of 7.2 hours of sleep per night last week,
#  with a total of 50.4 hours across 7 nights. That's pretty good!"
"""

from sqlalchemy import Float
import json
