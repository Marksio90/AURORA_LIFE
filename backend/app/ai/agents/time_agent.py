"""
Time Agent - Agent zarządzania czasem i produktywności
"""
from typing import Dict, Any
from app.ai.agents.base_agent import BaseAgent


class TimeAgent(BaseAgent):
    """
    Agent specjalizujący się w zarządzaniu czasem i produktywności.

    Analizuje alokację czasu, efektywność pracy i deep work.
    """

    def __init__(self):
        super().__init__(
            name="TimeAgent",
            specialization="Time management and productivity optimization"
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje wykorzystanie czasu.

        Args:
            user_data: Zawiera 'features', 'scores'

        Returns:
            Analiza zarządzania czasem
        """
        features = user_data.get("features", {})

        # Alokacja czasu
        work_hours = features.get('work_hours_per_week', 40)
        social_hours = features.get('social_time_hours_per_week', 5)
        exercise_hours = features.get('activity_frequency_per_week', 0) * (features.get('activity_avg_duration_minutes', 30) / 60)
        sleep_hours = features.get('sleep_avg_duration_hours', 7) * 7

        time_allocation = {
            "work_hours_per_week": work_hours,
            "social_hours_per_week": social_hours,
            "exercise_hours_per_week": exercise_hours,
            "sleep_hours_per_week": sleep_hours
        }

        # Efektywność
        productivity_avg = features.get('work_productivity_avg', 5)
        efficiency_score = productivity_avg / 10.0

        # Deep work
        deep_work_ratio = features.get('work_deep_work_ratio', 0.3)

        # Identyfikacja problemów
        time_issues = []
        if work_hours > 50:
            time_issues.append("overwork")
        if deep_work_ratio < 0.4:
            time_issues.append("fragmented_work")
        if social_hours < 3:
            time_issues.append("social_isolation")
        if exercise_hours < 2:
            time_issues.append("insufficient_exercise_time")

        # Klasyfikacja efektywności
        efficiency_level = self._classify_efficiency(efficiency_score, deep_work_ratio)

        return {
            "time_allocation": time_allocation,
            "efficiency_score": efficiency_score,
            "efficiency_level": efficiency_level,
            "deep_work_ratio": deep_work_ratio,
            "identified_issues": time_issues,
            "work_life_balance_score": features.get('work_life_balance_ratio', 0.5),
            "confidence": 0.82
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje zarządzania czasem.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Rekomendacje optymalizacji czasu
        """
        issues = analysis_result.get("identified_issues", [])
        deep_work_ratio = analysis_result.get("deep_work_ratio", 0)
        time_alloc = analysis_result.get("time_allocation", {})

        recommendations = []

        # Rekomendacje deep work
        if "fragmented_work" in issues or deep_work_ratio < 0.4:
            recommendations.append({
                "area": "deep_work",
                "action": "Schedule 2-3 hours of uninterrupted deep work daily",
                "priority": "high",
                "expected_benefit": "Significantly improved work quality and efficiency",
                "implementation": "Block calendar time, disable notifications, communicate boundaries"
            })

        # Rekomendacje overwork
        if "overwork" in issues:
            work_hours = time_alloc.get("work_hours_per_week", 0)
            recommendations.append({
                "area": "work_hours",
                "action": f"Reduce work hours from {work_hours:.0f}h to 40-45h per week",
                "priority": "critical",
                "expected_benefit": "Better health, reduced burnout risk, sustained performance",
                "implementation": "Set strict end time, delegate tasks, say no to non-essential work"
            })

        # Rekomendacje social time
        if "social_isolation" in issues:
            recommendations.append({
                "area": "social_time",
                "action": "Schedule regular social activities (min 5h/week)",
                "priority": "medium",
                "expected_benefit": "Improved wellbeing, reduced stress, better relationships",
                "implementation": "Weekly friend meetups, join clubs/groups, family time"
            })

        # Rekomendacje ćwiczeń
        if "insufficient_exercise_time" in issues:
            recommendations.append({
                "area": "exercise_time",
                "action": "Allocate 3-4 hours per week for physical activity",
                "priority": "high",
                "expected_benefit": "Better health, energy, and mental clarity",
                "implementation": "Schedule like important meetings, find accountability partner"
            })

        # Optymalizacja efektywności
        efficiency = analysis_result.get("efficiency_level", "moderate")
        if efficiency in ["low", "moderate"]:
            recommendations.append({
                "area": "productivity_systems",
                "action": "Implement time-blocking and pomodoro technique",
                "priority": "medium",
                "expected_benefit": "Improved focus and task completion",
                "implementation": "Use calendar blocking, 25-min focused sessions with breaks"
            })

        return {
            "time_recommendations": recommendations,
            "optimization_potential": "high" if len(issues) >= 2 else "moderate",
            "priority_focus": recommendations[0]["area"] if recommendations else "maintenance",
            "confidence": 0.82
        }

    def _classify_efficiency(self, efficiency_score: float, deep_work_ratio: float) -> str:
        """Klasyfikuje poziom efektywności."""
        combined_score = (efficiency_score + deep_work_ratio) / 2

        if combined_score > 0.7:
            return "high"
        elif combined_score > 0.5:
            return "moderate"
        else:
            return "low"
