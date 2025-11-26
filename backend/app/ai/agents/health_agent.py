"""
Health Agent - Agent zdrowia i energii
"""
from typing import Dict, Any, List
from app.ai.agents.base_agent import BaseAgent


class HealthAgent(BaseAgent):
    """
    Agent specjalizujący się w analizie zdrowia fizycznego i poziomu energii.

    Monitoruje sen, aktywność fizyczną, stres i poziom energii.
    """

    def __init__(self):
        super().__init__(
            name="HealthAgent",
            specialization="Physical health and energy management"
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje wskaźniki zdrowia.

        Args:
            user_data: Zawiera 'features', 'scores'

        Returns:
            Kompleksowa analiza zdrowia
        """
        features = user_data.get("features", {})
        scores = user_data.get("scores", {})

        health_score = scores.get("health_score", 0.5)

        # Klasyfikacja stanu zdrowia
        health_status = self._classify_health_status(health_score)

        # Analiza komponentów
        sleep_analysis = self._analyze_sleep(features)
        activity_analysis = self._analyze_activity(features)
        stress_analysis = self._analyze_stress(features)
        energy_analysis = self._analyze_energy(features)

        # Identyfikacja problemów
        health_issues = []
        if sleep_analysis["status"] == "insufficient":
            health_issues.append("sleep_deprivation")
        if activity_analysis["status"] == "low":
            health_issues.append("sedentary_lifestyle")
        if stress_analysis["level"] == "high":
            health_issues.append("chronic_stress")
        if energy_analysis["level"] == "low":
            health_issues.append("low_energy")

        return {
            "health_status": health_status,
            "health_score": health_score,
            "sleep_analysis": sleep_analysis,
            "activity_analysis": activity_analysis,
            "stress_analysis": stress_analysis,
            "energy_analysis": energy_analysis,
            "identified_issues": health_issues,
            "confidence": 0.88
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje zdrowotne.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Priorytetyzowane rekomendacje zdrowotne
        """
        issues = analysis_result.get("identified_issues", [])
        sleep_analysis = analysis_result.get("sleep_analysis", {})
        activity_analysis = analysis_result.get("activity_analysis", {})
        stress_analysis = analysis_result.get("stress_analysis", {})

        recommendations = []

        # Rekomendacje snu
        if "sleep_deprivation" in issues:
            recommendations.append({
                "area": "sleep",
                "action": f"Increase sleep to 7-8 hours (currently {sleep_analysis.get('avg_hours', 0):.1f}h)",
                "priority": "critical",
                "expected_benefit": "Improved energy, mood, and cognitive function",
                "implementation": "Set consistent bedtime, avoid screens 1h before sleep"
            })

        # Rekomendacje aktywności
        if "sedentary_lifestyle" in issues:
            recommendations.append({
                "area": "physical_activity",
                "action": f"Add {3 - activity_analysis.get('frequency', 0)} more exercise sessions per week",
                "priority": "high",
                "expected_benefit": "Better cardiovascular health, energy, and mood",
                "implementation": "Start with 3x30min walks/week, build up gradually"
            })

        # Rekomendacje stresu
        if "chronic_stress" in issues:
            recommendations.append({
                "area": "stress_management",
                "action": "Implement daily stress reduction practice",
                "priority": "high",
                "expected_benefit": "Lower cortisol, better sleep, improved health",
                "implementation": "10-15min meditation, yoga, or deep breathing daily"
            })

        # Rekomendacje energii
        if "low_energy" in issues:
            recommendations.append({
                "area": "energy",
                "action": "Address sleep and nutrition to boost energy",
                "priority": "high",
                "expected_benefit": "Sustained energy throughout the day",
                "implementation": "Regular meal times, hydration, and quality sleep"
            })

        return {
            "health_recommendations": recommendations,
            "critical_actions": len([r for r in recommendations if r["priority"] == "critical"]),
            "overall_health_trajectory": analysis_result.get("health_status", "unknown"),
            "confidence": 0.88
        }

    def _classify_health_status(self, score: float) -> str:
        """Klasyfikuje ogólny stan zdrowia."""
        if score > 0.8:
            return "excellent"
        elif score > 0.6:
            return "good"
        elif score > 0.4:
            return "fair"
        else:
            return "needs_attention"

    def _analyze_sleep(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuje sen."""
        avg_hours = features.get('sleep_avg_duration_hours', 7)
        quality = features.get('sleep_quality_avg', 5)

        status = "optimal" if avg_hours >= 7 and avg_hours <= 9 else "insufficient" if avg_hours < 7 else "excessive"

        return {
            "avg_hours": avg_hours,
            "quality_score": quality,
            "status": status
        }

    def _analyze_activity(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuje aktywność fizyczną."""
        frequency = features.get('activity_frequency_per_week', 0)
        intensity = features.get('activity_avg_intensity', 5)

        status = "optimal" if frequency >= 3 else "low" if frequency < 2 else "moderate"

        return {
            "frequency": frequency,
            "intensity": intensity,
            "status": status
        }

    def _analyze_stress(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuje poziom stresu."""
        stress_level = features.get('health_stress_level_avg', 5)

        level = "low" if stress_level < 4 else "moderate" if stress_level < 7 else "high"

        return {
            "stress_score": stress_level,
            "level": level
        }

    def _analyze_energy(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuje poziom energii."""
        energy_level = features.get('health_energy_level_avg', 5)

        level = "high" if energy_level > 7 else "moderate" if energy_level > 4 else "low"

        return {
            "energy_score": energy_level,
            "level": level
        }
