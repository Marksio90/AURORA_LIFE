"""
Decision Agent - Agent wspomagający podejmowanie decyzji
"""
from typing import Dict, Any
from app.ai.agents.base_agent import BaseAgent


class DecisionAgent(BaseAgent):
    """
    Agent specjalizujący się w analizie decyzji życiowych.

    Pomaga użytkownikowi identyfikować najważniejsze decyzje
    i priorytetyzować działania w oparciu o dane.
    """

    def __init__(self):
        super().__init__(
            name="DecisionAgent",
            specialization="Life decisions and prioritization"
        )

    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizuje dane użytkownika i identyfikuje obszary wymagające decyzji.

        Args:
            user_data: Zawiera 'features', 'scores', 'events'

        Returns:
            Analiza z zidentyfikowanymi obszarami decyzyjnymi
        """
        features = user_data.get("features", {})
        scores = user_data.get("scores", {})

        decision_points = []

        # Analiza snu
        sleep_hours = features.get('sleep_avg_duration_hours', 7)
        if sleep_hours < 7:
            decision_points.append({
                "area": "sleep",
                "current_state": f"{sleep_hours:.1f} hours/night",
                "issue": "Insufficient sleep duration",
                "impact": "high",
                "urgency": "high"
            })

        # Analiza aktywności fizycznej
        activity_freq = features.get('activity_frequency_per_week', 0)
        if activity_freq < 3:
            decision_points.append({
                "area": "physical_activity",
                "current_state": f"{activity_freq} sessions/week",
                "issue": "Below recommended activity level",
                "impact": "high",
                "urgency": "medium"
            })

        # Analiza work-life balance
        wlb_ratio = features.get('work_life_balance_ratio', 0.5)
        if wlb_ratio < 0.4:
            decision_points.append({
                "area": "work_life_balance",
                "current_state": f"ratio {wlb_ratio:.2f}",
                "issue": "Work dominating life balance",
                "impact": "very_high",
                "urgency": "high"
            })

        # Analiza stresu
        stress_level = features.get('health_stress_level_avg', 5)
        if stress_level > 7:
            decision_points.append({
                "area": "stress_management",
                "current_state": f"stress level {stress_level:.1f}/10",
                "issue": "High stress levels",
                "impact": "high",
                "urgency": "high"
            })

        return {
            "decision_points": decision_points,
            "overall_decision_pressure": len(decision_points),
            "confidence": 0.85
        }

    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje konkretne rekomendacje decyzyjne.

        Args:
            analysis_result: Wynik z metody analyze()

        Returns:
            Priorytetyzowane rekomendacje decyzyjne
        """
        decision_points = analysis_result.get("decision_points", [])

        # Sortuj według wpływu i pilności
        impact_scores = {"very_high": 4, "high": 3, "medium": 2, "low": 1}
        urgency_scores = {"high": 3, "medium": 2, "low": 1}

        prioritized = sorted(
            decision_points,
            key=lambda x: (
                impact_scores.get(x["impact"], 0) +
                urgency_scores.get(x["urgency"], 0)
            ),
            reverse=True
        )

        recommendations = []
        for point in prioritized:
            area = point["area"]

            if area == "sleep":
                recommendations.append({
                    "decision": "prioritize_sleep",
                    "action": "Establish a consistent sleep schedule with 7-8 hours per night",
                    "reason": "Insufficient sleep impacts health, mood, and productivity",
                    "expected_benefit": "high",
                    "effort_required": "medium",
                    "timeline": "Start tonight"
                })
            elif area == "physical_activity":
                recommendations.append({
                    "decision": "increase_physical_activity",
                    "action": "Schedule 3-4 exercise sessions per week (30+ min each)",
                    "reason": "Regular activity improves energy, mood, and long-term health",
                    "expected_benefit": "high",
                    "effort_required": "medium",
                    "timeline": "This week"
                })
            elif area == "work_life_balance":
                recommendations.append({
                    "decision": "improve_work_life_balance",
                    "action": "Set strict work hours and protect personal time",
                    "reason": "Poor balance leads to burnout and reduced life satisfaction",
                    "expected_benefit": "very_high",
                    "effort_required": "high",
                    "timeline": "Next week"
                })
            elif area == "stress_management":
                recommendations.append({
                    "decision": "implement_stress_reduction",
                    "action": "Add daily mindfulness practice (10-15 min meditation)",
                    "reason": "High stress damages health and decision-making quality",
                    "expected_benefit": "high",
                    "effort_required": "low",
                    "timeline": "Tomorrow"
                })

        return {
            "recommendations": recommendations[:5],  # Top 5 priorities
            "total_decisions_needed": len(decision_points),
            "immediate_actions": len([r for r in recommendations if r.get("timeline") in ["Tonight", "Tomorrow"]]),
            "confidence": 0.85
        }
