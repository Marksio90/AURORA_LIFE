"""
Prediction Agent - Agent predykcji przyszłości
"""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.agents.base_agent import BaseAgent
from app.ai.datagenius import DataGeniusService


class PredictionAgent(BaseAgent):
    """
    Agent specjalizujący się w przewidywaniu przyszłych stanów użytkownika.

    Wykorzystuje modele ML do predykcji energii, nastroju, produktywności.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(
            name="PredictionAgent",
            specialization="Future state prediction using ML models"
        )
        self.db = db
        self.datagenius = DataGeniusService(db)

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje dane i generuje predykcje.

        Args:
            user_data: Zawiera 'user_id', 'features', 'scores'

        Returns:
            Predykcje dla różnych aspektów życia
        """
        user_id = user_data.get("user_id")
        features = user_data.get("features", {})
        scores = user_data.get("scores", {})

        # Predykcja energii
        energy_pred = await self.datagenius.predict_energy(user_id, "morning")

        # Predykcja nastroju
        mood_pred = await self.datagenius.predict_mood(user_id)

        # Predykcja produktywności na podstawie trendów
        productivity_score = scores.get("productivity_score", 0.5)
        productivity_potential = productivity_score * 10  # Scale to 0-10

        # Analiza trendu well-being
        mood_trend = features.get("mood_trend", 0)
        wellbeing_trend = "improving" if mood_trend > 0.1 else "declining" if mood_trend < -0.1 else "stable"

        predictions = {
            "energy_tomorrow_morning": {
                "value": energy_pred.get("predicted_energy", 5.0),
                "confidence": energy_pred.get("confidence", 0.75),
                "factors": energy_pred.get("contributing_factors", [])
            },
            "mood_today": {
                "value": mood_pred.get("predicted_mood_score", 5.0),
                "sentiment": mood_pred.get("sentiment", "neutral"),
                "confidence": mood_pred.get("confidence", 0.75)
            },
            "productivity_potential": {
                "value": productivity_potential,
                "confidence": 0.70
            },
            "wellbeing_trend": {
                "direction": wellbeing_trend,
                "confidence": 0.72
            }
        }

        return {
            "predictions": predictions,
            "prediction_horizon": "24-48 hours",
            "overall_confidence": 0.78
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje na podstawie predykcji.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Proaktywne rekomendacje bazujące na predykcjach
        """
        predictions = analysis_result.get("predictions", {})
        recommendations = []

        # Rekomendacje bazujące na energii
        energy_pred = predictions.get("energy_tomorrow_morning", {})
        if energy_pred.get("value", 5) < 4:
            recommendations.append({
                "type": "energy_boost",
                "action": "Go to bed early tonight - low energy predicted for tomorrow",
                "reason": f"Predicted morning energy: {energy_pred.get('value', 0):.1f}/10",
                "timing": "Tonight"
            })

        # Rekomendacje bazujące na nastroju
        mood_pred = predictions.get("mood_today", {})
        if mood_pred.get("value", 5) < 5:
            recommendations.append({
                "type": "mood_support",
                "action": "Schedule social interaction or enjoyable activity",
                "reason": f"Lower mood predicted (sentiment: {mood_pred.get('sentiment', 'unknown')})",
                "timing": "Today"
            })

        # Rekomendacje bazujące na produktywności
        prod_pred = predictions.get("productivity_potential", {})
        if prod_pred.get("value", 5) > 7:
            recommendations.append({
                "type": "productivity_optimization",
                "action": "Schedule important tasks - high productivity potential",
                "reason": f"Productivity score: {prod_pred.get('value', 0):.1f}/10",
                "timing": "Tomorrow morning"
            })

        # Rekomendacje bazujące na trendzie
        trend = predictions.get("wellbeing_trend", {})
        if trend.get("direction") == "declining":
            recommendations.append({
                "type": "trend_intervention",
                "action": "Review recent changes - wellbeing is declining",
                "reason": "Negative trend detected in overall wellbeing",
                "timing": "This week"
            })

        return {
            "proactive_recommendations": recommendations,
            "prediction_reliability": analysis_result.get("overall_confidence", 0.75),
            "next_prediction_update": "Tomorrow"
        }
