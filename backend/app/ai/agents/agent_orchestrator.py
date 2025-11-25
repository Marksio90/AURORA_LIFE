"""
Agent Orchestrator - Koordynator wszystkich Aurora Agents

Zarządza wykonaniem wszystkich 7 agentów równolegle i agreguje wyniki.
"""
import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.datagenius import DataGeniusService


class AgentOrchestrator:
    """
    Agent Orchestrator - główny koordynator agentów.

    Zarządza równoległym wykonaniem 7 Aurora Agents:
    1. Decision Agent - wybór najlepszych ścieżek
    2. Prediction Agent - modele prognostyczne
    3. Mood Agent - analiza emocji
    4. Health Agent - energia i regeneracja
    5. Time Agent - harmonogram i produktywność
    6. Relationships Agent - interakcje społeczne
    7. Growth Agent - postęp celów

    Każdy agent działa niezależnie, a Orchestrator agreguje wyniki.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.datagenius = DataGeniusService(db)
        self.agents = []

    async def run_all_agents(
        self,
        user_id: int,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Uruchamia wszystkich agentów równolegle.

        Args:
            user_id: ID użytkownika
            context: Dodatkowy kontekst

        Returns:
            Zagregowane wyniki wszystkich agentów
        """
        # Pobierz dane z DataGenius
        analysis = await self.datagenius.analyze_user_patterns(user_id, days=30)

        if analysis.get("message") == "No data available for analysis":
            return {
                "user_id": user_id,
                "message": "Insufficient data for agent analysis",
                "recommendation": "Add more life events to enable AI insights"
            }

        # Równoległe wykonanie wszystkich analiz
        results = await asyncio.gather(
            self._run_decision_agent(analysis),
            self._run_prediction_agent(user_id, analysis),
            self._run_mood_agent(user_id, analysis),
            self._run_health_agent(analysis),
            self._run_time_agent(analysis),
            self._run_relationships_agent(analysis),
            self._run_growth_agent(analysis),
            return_exceptions=True
        )

        agent_names = [
            "decision_agent",
            "prediction_agent",
            "mood_agent",
            "health_agent",
            "time_agent",
            "relationships_agent",
            "growth_agent"
        ]

        agent_results = {}
        for name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                agent_results[name] = {"error": str(result)}
            else:
                agent_results[name] = result

        # Agregacja wyników
        aggregated = self._aggregate_results(agent_results, analysis)

        return {
            "user_id": user_id,
            "orchestration_timestamp": analysis["analyzed_at"],
            "agent_results": agent_results,
            "aggregated_insights": aggregated["insights"],
            "priority_actions": aggregated["priority_actions"],
            "overall_recommendation": aggregated["overall_recommendation"]
        }

    async def _run_decision_agent(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Decision Agent - analiza decyzji"""
        features = analysis["features"]
        scores = analysis["scores"]

        decisions = []

        # Decyzja: czy poprawić sen?
        if features['sleep_avg_duration_hours'] < 7:
            decisions.append({
                "decision": "prioritize_sleep",
                "reason": "Niedostateczny czas snu wpływa na zdrowie i produktywność",
                "expected_benefit": "high",
                "effort_required": "medium"
            })

        # Decyzja: czy zwiększyć aktywność?
        if features['activity_frequency_per_week'] < 3:
            decisions.append({
                "decision": "increase_physical_activity",
                "reason": "Aktywność fizyczna poniżej zalecanego minimum",
                "expected_benefit": "high",
                "effort_required": "medium"
            })

        # Decyzja: work-life balance
        if features['work_life_balance_ratio'] < 0.4:
            decisions.append({
                "decision": "improve_work_life_balance",
                "reason": "Nierównowaga między pracą a życiem prywatnym",
                "expected_benefit": "very_high",
                "effort_required": "high"
            })

        return {
            "agent": "DecisionAgent",
            "decisions": decisions,
            "confidence": 0.85
        }

    async def _run_prediction_agent(self, user_id: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prediction Agent - predykcje przyszłości"""
        # Użyj DataGenius do predykcji
        energy_pred = await self.datagenius.predict_energy(user_id, "morning")
        mood_pred = await self.datagenius.predict_mood(user_id)

        predictions = {
            "energy_tomorrow_morning": energy_pred["predicted_energy"],
            "mood_today": mood_pred["predicted_mood_score"],
            "productivity_potential": analysis["scores"]["productivity_score"] * 10,
            "wellbeing_trend": "improving" if analysis["features"]["mood_trend"] > 0 else "stable"
        }

        return {
            "agent": "PredictionAgent",
            "predictions": predictions,
            "confidence": 0.78
        }

    async def _run_mood_agent(self, user_id: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Mood Agent - analiza nastroju"""
        mood_analysis = await self.datagenius.predict_mood(user_id)

        recommendations = []
        if mood_analysis["predicted_mood_score"] < 5:
            recommendations.extend([
                "Spędź czas z bliskimi osobami",
                "Aktywność fizyczna na świeżym powietrzu",
                "Rozważ medytację lub mindfulness"
            ])

        return {
            "agent": "MoodAgent",
            "current_mood": mood_analysis["predicted_mood_score"],
            "sentiment": mood_analysis["sentiment"],
            "influencing_factors": mood_analysis["influencing_factors"],
            "mood_recommendations": recommendations,
            "confidence": mood_analysis["confidence"]
        }

    async def _run_health_agent(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Health Agent - zdrowie i energia"""
        features = analysis["features"]
        health_score = analysis["scores"]["health_score"]

        health_status = "excellent" if health_score > 0.8 else "good" if health_score > 0.6 else "needs_attention"

        recommendations = []
        if features['sleep_avg_duration_hours'] < 7:
            recommendations.append("Zwiększ czas snu do 7-8 godzin")
        if features['activity_frequency_per_week'] < 3:
            recommendations.append("Dodaj minimum 3 sesje aktywności fizycznej tygodniowo")
        if features['health_stress_level_avg'] > 6:
            recommendations.append("Zastosuj techniki redukcji stresu (medytacja, yoga)")

        return {
            "agent": "HealthAgent",
            "health_status": health_status,
            "health_score": health_score,
            "energy_level": features['health_energy_level_avg'],
            "sleep_quality": features['sleep_quality_avg'],
            "recommendations": recommendations,
            "confidence": 0.88
        }

    async def _run_time_agent(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Time Agent - zarządzanie czasem"""
        features = analysis["features"]

        time_allocation = {
            "work_hours_per_week": features['work_hours_per_week'],
            "social_hours_per_week": features['social_time_hours_per_week'],
            "exercise_hours_per_week": features['activity_frequency_per_week'] * (features['activity_avg_duration_minutes'] / 60),
            "sleep_hours_per_week": features['sleep_avg_duration_hours'] * 7
        }

        efficiency_score = features['work_productivity_avg'] / 10.0 if features['work_productivity_avg'] > 0 else 0.5

        recommendations = []
        if features['work_deep_work_ratio'] < 0.5:
            recommendations.append("Zaplanuj codziennie 2-3h nieprzerwanego deep work")
        if time_allocation["work_hours_per_week"] > 50:
            recommendations.append("Rozważ redukcję godzin pracy - >50h/tydzień szkodzi zdrowiu")

        return {
            "agent": "TimeAgent",
            "time_allocation": time_allocation,
            "efficiency_score": efficiency_score,
            "deep_work_ratio": features['work_deep_work_ratio'],
            "recommendations": recommendations,
            "confidence": 0.82
        }

    async def _run_relationships_agent(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Relationships Agent - relacje społeczne"""
        features = analysis["features"]

        social_health = "strong" if features['social_interactions_per_week'] > 3 else "moderate" if features['social_interactions_per_week'] > 1 else "weak"

        recommendations = []
        if features['social_interactions_per_week'] < 2:
            recommendations.extend([
                "Zaplanuj regularne spotkania z przyjaciółmi (min 2x/tydzień)",
                "Rozważ dołączenie do grupy/klubu zainteresowań"
            ])

        return {
            "agent": "RelationshipsAgent",
            "social_health": social_health,
            "interactions_per_week": features['social_interactions_per_week'],
            "social_quality": features['social_quality_avg'],
            "recommendations": recommendations,
            "confidence": 0.75
        }

    async def _run_growth_agent(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Growth Agent - rozwój osobisty"""
        features = analysis["features"]
        scores = analysis["scores"]

        progress_areas = {
            "health": scores["health_score"],
            "productivity": scores["productivity_score"],
            "mood": scores["mood_score"],
            "energy": scores["energy_score"]
        }

        # Znajdź obszar do rozwoju
        weakest_area = min(progress_areas, key=progress_areas.get)
        strongest_area = max(progress_areas, key=progress_areas.get)

        growth_recommendations = [
            f"Priorytet rozwoju: {weakest_area} (obecny score: {progress_areas[weakest_area]:.2f})",
            f"Kontynuuj sukces w obszarze: {strongest_area}"
        ]

        return {
            "agent": "GrowthAgent",
            "progress_areas": progress_areas,
            "weakest_area": weakest_area,
            "strongest_area": strongest_area,
            "overall_growth_trend": "positive" if features["mood_trend"] > 0 else "stable",
            "recommendations": growth_recommendations,
            "confidence": 0.80
        }

    def _aggregate_results(
        self,
        agent_results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agreguje wyniki wszystkich agentów"""

        # Zbierz wszystkie insights
        all_insights = analysis.get("insights", [])

        # Zbierz priority actions
        priority_actions = []

        # Z Decision Agent
        if "decisions" in agent_results.get("decision_agent", {}):
            for decision in agent_results["decision_agent"]["decisions"]:
                if decision["expected_benefit"] in ["high", "very_high"]:
                    priority_actions.append({
                        "action": decision["decision"],
                        "source": "DecisionAgent",
                        "priority": decision["expected_benefit"]
                    })

        # Z Health Agent
        if "recommendations" in agent_results.get("health_agent", {}):
            for rec in agent_results["health_agent"]["recommendations"][:2]:
                priority_actions.append({
                    "action": rec,
                    "source": "HealthAgent",
                    "priority": "high"
                })

        # Overall recommendation
        overall_wellbeing = analysis["scores"]["overall_wellbeing"]

        if overall_wellbeing > 0.8:
            overall_rec = "Kontynuuj obecny tryb życia - wszystko wygląda świetnie! 🌟"
        elif overall_wellbeing > 0.6:
            overall_rec = "Ogólnie dobrze, ale są obszary do poprawy. Skup się na priorytetowych działaniach poniżej."
        else:
            overall_rec = "Czas na zmiany! Zaimplementuj rekomendacje z high priority - to znacząco poprawi Twoje well-being."

        return {
            "insights": all_insights,
            "priority_actions": priority_actions[:5],  # Top 5
            "overall_recommendation": overall_rec
        }
