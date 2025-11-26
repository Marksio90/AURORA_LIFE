"""
Relationships Agent - Agent relacji społecznych
"""
from typing import Dict, Any
from app.ai.agents.base_agent import BaseAgent


class RelationshipsAgent(BaseAgent):
    """
    Agent specjalizujący się w analizie relacji społecznych.

    Monitoruje jakość i częstotliwość interakcji społecznych.
    """

    def __init__(self):
        super().__init__(
            name="RelationshipsAgent",
            specialization="Social connections and relationship health"
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje stan relacji społecznych.

        Args:
            user_data: Zawiera 'features'

        Returns:
            Analiza zdrowia społecznego
        """
        features = user_data.get("features", {})

        # Metryki społeczne
        interactions_per_week = features.get('social_interactions_per_week', 0)
        quality_avg = features.get('social_quality_avg', 5)
        time_hours = features.get('social_time_hours_per_week', 0)

        # Klasyfikacja zdrowia społecznego
        social_health = self._classify_social_health(interactions_per_week, quality_avg)

        # Analiza jakości
        quality_level = "high" if quality_avg > 7 else "moderate" if quality_avg > 4 else "low"

        # Identyfikacja problemów
        social_issues = []
        if interactions_per_week < 2:
            social_issues.append("social_isolation")
        if quality_avg < 5:
            social_issues.append("low_quality_interactions")
        if time_hours < 3:
            social_issues.append("insufficient_social_time")

        # Balans społeczny
        work_hours = features.get('work_hours_per_week', 40)
        social_work_ratio = time_hours / work_hours if work_hours > 0 else 0

        return {
            "social_health": social_health,
            "interactions_per_week": interactions_per_week,
            "quality_level": quality_level,
            "quality_score": quality_avg,
            "time_hours_per_week": time_hours,
            "social_work_ratio": social_work_ratio,
            "identified_issues": social_issues,
            "confidence": 0.75
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje dla relacji.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Rekomendacje poprawy relacji
        """
        issues = analysis_result.get("identified_issues", [])
        interactions = analysis_result.get("interactions_per_week", 0)
        quality = analysis_result.get("quality_score", 5)

        recommendations = []

        # Rekomendacje dla izolacji społecznej
        if "social_isolation" in issues:
            recommendations.append({
                "area": "social_frequency",
                "action": "Schedule regular social activities (minimum 2-3 times per week)",
                "priority": "high",
                "expected_benefit": "Improved mood, reduced loneliness, better mental health",
                "implementation": "Weekly friend meetups, join interest groups, family dinners"
            })

        # Rekomendacje dla niskiej jakości
        if "low_quality_interactions" in issues:
            recommendations.append({
                "area": "relationship_quality",
                "action": "Focus on deeper, meaningful conversations with close connections",
                "priority": "high",
                "expected_benefit": "More fulfilling relationships, stronger support network",
                "implementation": "1-on-1 time, active listening, vulnerability and openness"
            })

        # Rekomendacje dla niewystarczającego czasu
        if "insufficient_social_time" in issues:
            recommendations.append({
                "area": "social_time",
                "action": "Allocate 5-10 hours per week for social activities",
                "priority": "medium",
                "expected_benefit": "Stronger relationships, better work-life balance",
                "implementation": "Calendar blocking for social time, treat as important as work"
            })

        # Pozytywne wzmocnienie
        if analysis_result.get("social_health") in ["strong", "very_strong"]:
            recommendations.append({
                "area": "maintenance",
                "action": "Continue nurturing your strong social connections",
                "priority": "low",
                "expected_benefit": "Sustained wellbeing and life satisfaction",
                "implementation": "Maintain current habits, express gratitude to loved ones"
            })

        # Ekspansja sieci
        if interactions >= 3 and quality >= 7:
            recommendations.append({
                "area": "network_expansion",
                "action": "Consider expanding social circle with new connections",
                "priority": "low",
                "expected_benefit": "New perspectives, opportunities, diverse support",
                "implementation": "Join clubs, attend events, professional networking"
            })

        return {
            "relationship_recommendations": recommendations,
            "intervention_priority": "high" if "social_isolation" in issues else "medium" if issues else "low",
            "social_wellbeing_trajectory": analysis_result.get("social_health", "unknown"),
            "confidence": 0.75
        }

    def _classify_social_health(self, interactions: int, quality: float) -> str:
        """Klasyfikuje zdrowie społeczne."""
        # Kombinacja częstotliwości i jakości
        combined_score = (min(interactions / 5, 1.0) + quality / 10) / 2

        if combined_score > 0.7:
            return "very_strong"
        elif combined_score > 0.5:
            return "strong"
        elif combined_score > 0.3:
            return "moderate"
        else:
            return "weak"
