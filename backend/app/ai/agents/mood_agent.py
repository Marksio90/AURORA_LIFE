"""
Mood Agent - Agent analizy nastroju i emocji
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.agents.base_agent import BaseAgent
from app.ai.datagenius import DataGeniusService


class MoodAgent(BaseAgent):
    """
    Agent specjalizujący się w analizie nastroju i dobrostanu emocjonalnego.

    Monitoruje trendy emocjonalne i identyfikuje czynniki wpływające na nastrój.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(
            name="MoodAgent",
            specialization="Emotional wellbeing and mood analysis"
        )
        self.db = db
        self.datagenius = DataGeniusService(db)

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje nastrój i czynniki wpływające.

        Args:
            user_data: Zawiera 'user_id', 'features', 'scores'

        Returns:
            Szczegółowa analiza nastroju
        """
        user_id = user_data.get("user_id")
        features = user_data.get("features", {})

        # Predykcja nastroju z ML
        mood_analysis = await self.datagenius.predict_mood(user_id)

        current_mood = mood_analysis.get("predicted_mood_score", 5.0)
        sentiment = mood_analysis.get("sentiment", "neutral")
        influencing_factors = mood_analysis.get("influencing_factors", [])

        # Analiza trendów
        mood_trend = features.get("mood_trend", 0)
        trend_direction = "improving" if mood_trend > 0.1 else "declining" if mood_trend < -0.1 else "stable"

        # Identyfikacja stanów emocjonalnych
        emotional_state = self._classify_emotional_state(current_mood, sentiment)

        return {
            "current_mood_score": current_mood,
            "sentiment": sentiment,
            "emotional_state": emotional_state,
            "trend_direction": trend_direction,
            "trend_value": mood_trend,
            "influencing_factors": influencing_factors,
            "confidence": mood_analysis.get("confidence", 0.75)
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje dla poprawy nastroju.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Personalizowane rekomendacje poprawy nastroju
        """
        mood_score = analysis_result.get("current_mood_score", 5.0)
        sentiment = analysis_result.get("sentiment", "neutral")
        trend = analysis_result.get("trend_direction", "stable")

        recommendations = []

        # Dla niskiego nastroju
        if mood_score < 5:
            recommendations.extend([
                {
                    "action": "Spend quality time with close friends or family",
                    "category": "social_connection",
                    "priority": "high",
                    "expected_impact": "high"
                },
                {
                    "action": "30-minute outdoor walk or exercise",
                    "category": "physical_activity",
                    "priority": "high",
                    "expected_impact": "medium"
                },
                {
                    "action": "10-minute mindfulness or meditation session",
                    "category": "mental_health",
                    "priority": "medium",
                    "expected_impact": "medium"
                }
            ])

        # Dla spadającego trendu
        if trend == "declining":
            recommendations.append({
                "action": "Review recent life changes - identify stress sources",
                "category": "self_reflection",
                "priority": "high",
                "expected_impact": "high"
            })

        # Dla negatywnego sentymentu
        if sentiment in ["negative", "very_negative"]:
            recommendations.append({
                "action": "Consider talking to a friend or professional",
                "category": "emotional_support",
                "priority": "high",
                "expected_impact": "very_high"
            })

        # Dla stabilnego dobrego nastroju
        if mood_score >= 7 and trend == "stable":
            recommendations.append({
                "action": "Maintain current positive habits and routines",
                "category": "maintenance",
                "priority": "medium",
                "expected_impact": "medium"
            })

        return {
            "mood_recommendations": recommendations,
            "intervention_urgency": "high" if mood_score < 4 else "medium" if mood_score < 6 else "low",
            "confidence": analysis_result.get("confidence", 0.75)
        }

    def _classify_emotional_state(self, mood_score: float, sentiment: str) -> str:
        """Klasyfikuje stan emocjonalny na podstawie score i sentymentu."""
        if mood_score >= 8:
            return "thriving"
        elif mood_score >= 6:
            return "content"
        elif mood_score >= 4:
            return "neutral"
        elif mood_score >= 3:
            return "struggling"
        else:
            return "needs_support"
