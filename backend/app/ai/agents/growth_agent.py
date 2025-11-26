"""
Growth Agent - Agent rozwoju osobistego
"""
from typing import Dict, Any
from app.ai.agents.base_agent import BaseAgent


class GrowthAgent(BaseAgent):
    """
    Agent specjalizujący się w rozwoju osobistym i postępie w celach.

    Monitoruje postępy w różnych obszarach życia i identyfikuje możliwości rozwoju.
    """

    def __init__(self):
        super().__init__(
            name="GrowthAgent",
            specialization="Personal growth and goal progress tracking"
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje postęp w rozwoju osobistym.

        Args:
            user_data: Zawiera 'features', 'scores'

        Returns:
            Analiza rozwoju w różnych obszarach
        """
        features = user_data.get("features", {})
        scores = user_data.get("scores", {})

        # Obszary rozwoju
        progress_areas = {
            "health": scores.get("health_score", 0.5),
            "productivity": scores.get("productivity_score", 0.5),
            "mood": scores.get("mood_score", 0.5),
            "energy": scores.get("energy_score", 0.5)
        }

        # Identyfikacja najsłabszego i najsilniejszego obszaru
        weakest_area = min(progress_areas, key=progress_areas.get)
        strongest_area = max(progress_areas, key=progress_areas.get)

        weakest_score = progress_areas[weakest_area]
        strongest_score = progress_areas[strongest_area]

        # Trend ogólnego rozwoju
        mood_trend = features.get("mood_trend", 0)
        overall_trend = "positive" if mood_trend > 0.1 else "negative" if mood_trend < -0.1 else "stable"

        # Oblicz ogólny postęp
        avg_progress = sum(progress_areas.values()) / len(progress_areas)
        progress_level = self._classify_progress(avg_progress)

        # Identyfikacja potencjału wzrostu
        growth_potential = self._calculate_growth_potential(progress_areas, features)

        return {
            "progress_areas": progress_areas,
            "weakest_area": weakest_area,
            "weakest_score": weakest_score,
            "strongest_area": strongest_area,
            "strongest_score": strongest_score,
            "overall_progress": avg_progress,
            "progress_level": progress_level,
            "overall_growth_trend": overall_trend,
            "growth_potential": growth_potential,
            "confidence": 0.80
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje rozwoju.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Strategia rozwoju osobistego
        """
        weakest_area = analysis_result.get("weakest_area", "health")
        weakest_score = analysis_result.get("weakest_score", 0.5)
        strongest_area = analysis_result.get("strongest_area", "productivity")
        growth_potential = analysis_result.get("growth_potential", {})

        recommendations = []

        # Priorytet: najsłabszy obszar
        area_actions = {
            "health": "Focus on sleep quality and regular exercise",
            "productivity": "Implement time-blocking and eliminate distractions",
            "mood": "Prioritize social connections and stress management",
            "energy": "Optimize sleep schedule and nutrition habits"
        }

        recommendations.append({
            "type": "priority_development",
            "area": weakest_area,
            "action": area_actions.get(weakest_area, "Focus on improvement"),
            "current_score": weakest_score,
            "target_score": min(weakest_score + 0.2, 1.0),
            "priority": "critical",
            "timeline": "4 weeks"
        })

        # Wzmocnienie mocnych stron
        recommendations.append({
            "type": "strength_leverage",
            "area": strongest_area,
            "action": f"Continue excelling in {strongest_area} and use it to support other areas",
            "priority": "medium",
            "timeline": "Ongoing"
        })

        # Rekomendacje bazujące na potencjale wzrostu
        for area, potential in growth_potential.items():
            if potential == "high":
                recommendations.append({
                    "type": "quick_win",
                    "area": area,
                    "action": f"High growth potential in {area} - implement focused improvements",
                    "priority": "high",
                    "timeline": "2 weeks"
                })

        # Strategia holistyczna
        overall_progress = analysis_result.get("overall_progress", 0.5)
        if overall_progress < 0.5:
            recommendations.append({
                "type": "holistic_strategy",
                "action": "Implement comprehensive life improvements across all areas",
                "priority": "high",
                "focus": "Start with small, sustainable changes in each area"
            })
        elif overall_progress < 0.7:
            recommendations.append({
                "type": "balanced_growth",
                "action": "Balance strengths and weaknesses for well-rounded development",
                "priority": "medium",
                "focus": "Maintain strengths while addressing weak points"
            })
        else:
            recommendations.append({
                "type": "excellence_pursuit",
                "action": "You're doing great! Focus on optimization and new challenges",
                "priority": "low",
                "focus": "Stretch goals and new skill development"
            })

        return {
            "growth_recommendations": recommendations,
            "development_priority": weakest_area,
            "estimated_improvement_timeline": "4-8 weeks with consistent effort",
            "success_probability": "high" if growth_potential else "moderate",
            "confidence": 0.80
        }

    def _classify_progress(self, avg_score: float) -> str:
        """Klasyfikuje ogólny poziom postępu."""
        if avg_score > 0.8:
            return "excellent"
        elif avg_score > 0.6:
            return "good"
        elif avg_score > 0.4:
            return "developing"
        else:
            return "needs_focus"

    def _calculate_growth_potential(self, progress_areas: Dict[str, float], features: Dict[str, Any]) -> Dict[str, str]:
        """Oblicza potencjał wzrostu dla każdego obszaru."""
        potential = {}

        for area, score in progress_areas.items():
            # Obszary z niskim score mają wysoki potencjał wzrostu
            if score < 0.4:
                potential[area] = "very_high"
            elif score < 0.6:
                potential[area] = "high"
            elif score < 0.8:
                potential[area] = "moderate"
            else:
                potential[area] = "maintenance"

        return potential
