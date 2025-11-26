"""
Agent Orchestrator - Koordynator wszystkich Aurora Agents

Zarządza wykonaniem wszystkich 7 agentów równolegle i agreguje wyniki.
"""
import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.ai.datagenius import DataGeniusService
from app.ai.agents.decision_agent import DecisionAgent
from app.ai.agents.prediction_agent import PredictionAgent
from app.ai.agents.mood_agent import MoodAgent
from app.ai.agents.health_agent import HealthAgent
from app.ai.agents.time_agent import TimeAgent
from app.ai.agents.relationships_agent import RelationshipsAgent
from app.ai.agents.growth_agent import GrowthAgent

logger = logging.getLogger(__name__)


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

        # Initialize all agents
        self.decision_agent = DecisionAgent()
        self.prediction_agent = PredictionAgent(db)
        self.mood_agent = MoodAgent(db)
        self.health_agent = HealthAgent()
        self.time_agent = TimeAgent()
        self.relationships_agent = RelationshipsAgent()
        self.growth_agent = GrowthAgent()

        self.agents = [
            self.decision_agent,
            self.prediction_agent,
            self.mood_agent,
            self.health_agent,
            self.time_agent,
            self.relationships_agent,
            self.growth_agent
        ]

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

        # Prepare user data for agents
        user_data = {
            "user_id": user_id,
            "features": analysis.get("features", {}),
            "scores": analysis.get("scores", {}),
            "events": analysis.get("events", [])
        }

        # Równoległe wykonanie wszystkich analiz i rekomendacji
        logger.info(f"Running all agents for user {user_id}")

        results = await asyncio.gather(
            self._run_agent_full_cycle(self.decision_agent, user_data),
            self._run_agent_full_cycle(self.prediction_agent, user_data),
            self._run_agent_full_cycle(self.mood_agent, user_data),
            self._run_agent_full_cycle(self.health_agent, user_data),
            self._run_agent_full_cycle(self.time_agent, user_data),
            self._run_agent_full_cycle(self.relationships_agent, user_data),
            self._run_agent_full_cycle(self.growth_agent, user_data),
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
                logger.error(f"Agent {name} failed: {str(result)}")
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

    async def _run_agent_full_cycle(self, agent, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs full agent cycle: analyze -> recommend.

        Args:
            agent: Agent instance (BaseAgent subclass)
            user_data: User data for analysis

        Returns:
            Combined analysis and recommendations
        """
        from datetime import datetime

        # Run analysis
        analysis_result = await agent.analyze(user_data)

        # Run recommendations based on analysis
        recommendations = await agent.recommend(analysis_result)

        # Update agent's last execution time
        agent.last_execution = datetime.utcnow()

        # Combine results
        return {
            "agent": agent.name,
            "specialization": agent.specialization,
            "analysis": analysis_result,
            "recommendations": recommendations,
            "status": agent.get_status()
        }


    def _aggregate_results(
        self,
        agent_results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Agreguje wyniki wszystkich agentów"""

        # Zbierz wszystkie insights
        all_insights = analysis.get("insights", [])

        # Zbierz priority actions z wszystkich agentów
        priority_actions = []

        # Z Decision Agent
        decision_agent_data = agent_results.get("decision_agent", {})
        if "recommendations" in decision_agent_data:
            recs = decision_agent_data["recommendations"].get("recommendations", [])
            for rec in recs[:3]:  # Top 3
                priority_actions.append({
                    "action": rec.get("action", rec.get("decision", "Unknown")),
                    "source": "DecisionAgent",
                    "priority": rec.get("expected_benefit", "medium")
                })

        # Z Health Agent
        health_agent_data = agent_results.get("health_agent", {})
        if "recommendations" in health_agent_data:
            health_recs = health_agent_data["recommendations"].get("health_recommendations", [])
            for rec in health_recs[:2]:  # Top 2
                priority_actions.append({
                    "action": rec.get("action", "Unknown"),
                    "source": "HealthAgent",
                    "priority": rec.get("priority", "medium")
                })

        # Z Growth Agent
        growth_agent_data = agent_results.get("growth_agent", {})
        if "recommendations" in growth_agent_data:
            growth_recs = growth_agent_data["recommendations"].get("growth_recommendations", [])
            if growth_recs:
                priority_actions.append({
                    "action": growth_recs[0].get("action", "Focus on weakest area"),
                    "source": "GrowthAgent",
                    "priority": "high"
                })

        # Overall recommendation based on wellbeing
        overall_wellbeing = analysis["scores"].get("overall_wellbeing", 0.5)

        if overall_wellbeing > 0.8:
            overall_rec = "Continue your current lifestyle - everything looks great!"
        elif overall_wellbeing > 0.6:
            overall_rec = "Generally good, but there are areas to improve. Focus on priority actions below."
        else:
            overall_rec = "Time for changes! Implement high priority recommendations - this will significantly improve your well-being."

        return {
            "insights": all_insights,
            "priority_actions": priority_actions[:5],  # Top 5
            "overall_recommendation": overall_rec
        }
