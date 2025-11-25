"""
AI API - Endpoints dla Zestawu 2 (DataGenius, Agents, What-If)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.ai.datagenius import DataGeniusService
from app.ai.agents import AgentOrchestrator
from app.ai.whatif import WhatIfSimulator

router = APIRouter(prefix="/api/ai", tags=["AI & ML"])


# DataGenius Endpoints

@router.get("/analyze/{user_id}")
async def analyze_user_patterns(
    user_id: int,
    days: int = Query(30, description="Period to analyze (days)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Analizuje wzorce użytkownika i generuje insights AI.
    Wykorzystuje DataGenius do feature engineering i analizy.
    """
    service = DataGeniusService(db)
    analysis = await service.analyze_user_patterns(user_id, days)
    return analysis


@router.get("/predict/energy/{user_id}")
async def predict_energy(
    user_id: int,
    time_of_day: str = Query("morning", description="Time of day: morning, afternoon, evening, night"),
    db: AsyncSession = Depends(get_db)
):
    """Przewiduje poziom energii użytkownika"""
    service = DataGeniusService(db)
    prediction = await service.predict_energy(user_id, time_of_day)
    return prediction


@router.get("/predict/mood/{user_id}")
async def predict_mood(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Przewiduje nastrój użytkownika"""
    service = DataGeniusService(db)
    prediction = await service.predict_mood(user_id)
    return prediction


@router.get("/recommend/{user_id}")
async def recommend_activities(
    user_id: int,
    goal: str = Query("energy", description="Goal: energy, mood, productivity, balance"),
    db: AsyncSession = Depends(get_db)
):
    """Generuje rekomendacje aktywności dla użytkownika"""
    service = DataGeniusService(db)
    recommendations = await service.recommend_activities(user_id, goal)
    return recommendations


# Aurora Agents Endpoints

@router.get("/agents/run-all/{user_id}")
async def run_all_agents(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Uruchamia wszystkich 7 Aurora Agents równolegle.

    Agents:
    - DecisionAgent - analiza decyzji
    - PredictionAgent - predykcje przyszłości
    - MoodAgent - analiza nastroju
    - HealthAgent - zdrowie i energia
    - TimeAgent - zarządzanie czasem
    - RelationshipsAgent - relacje społeczne
    - GrowthAgent - rozwój osobisty
    """
    orchestrator = AgentOrchestrator(db)
    results = await orchestrator.run_all_agents(user_id)
    return results


# What-If Engine Endpoints

@router.post("/whatif/simulate/{user_id}")
async def simulate_whatif_scenario(
    user_id: int,
    scenario: Dict[str, Any],
    simulation_days: int = Query(30, description="Days to simulate"),
    db: AsyncSession = Depends(get_db)
):
    """
    Symuluje scenariusz "co jeśli".

    Przykładowe scenariusze:
    ```json
    {
      "type": "increase_sleep",
      "value": 1.5,
      "description": "Co jeśli będę spać 1.5h dłużej?"
    }
    ```

    Dostępne typy scenariuszy:
    - increase_sleep: Zwiększ czas snu (value = godziny)
    - increase_activity: Zwiększ aktywność (value = razy/tydzień)
    - improve_work_life_balance: Popraw równowagę (value = zmiana ratio)
    - reduce_work_hours: Zmniejsz godziny pracy (value = godziny/tydzień)
    - increase_social: Zwiększ interakcje (value = razy/tydzień)
    """
    simulator = WhatIfSimulator(db)
    simulation = await simulator.simulate_scenario(user_id, scenario, simulation_days)
    return simulation


@router.get("/whatif/templates")
async def get_whatif_templates():
    """Zwraca gotowe szablony scenariuszy "co jeśli"""""
    return {
        "templates": [
            {
                "name": "Zwiększ czas snu o 1 godzinę",
                "scenario": {
                    "type": "increase_sleep",
                    "value": 1.0,
                    "description": "Co jeśli będę spać godzinę dłużej każdej nocy?"
                }
            },
            {
                "name": "Ćwicz 3 razy w tygodniu",
                "scenario": {
                    "type": "increase_activity",
                    "value": 3.0,
                    "description": "Co jeśli zacznę ćwiczyć regularnie 3x w tygodniu?"
                }
            },
            {
                "name": "Zredukuj pracę o 10h/tydzień",
                "scenario": {
                    "type": "reduce_work_hours",
                    "value": 10.0,
                    "description": "Co jeśli zmniejszę godziny pracy o 10h tygodniowo?"
                }
            },
            {
                "name": "Zwiększ czas z przyjaciółmi",
                "scenario": {
                    "type": "increase_social",
                    "value": 2.0,
                    "description": "Co jeśli będę spotykać się z przyjaciółmi 2x więcej?"
                }
            },
            {
                "name": "Popraw work-life balance",
                "scenario": {
                    "type": "improve_work_life_balance",
                    "value": 0.3,
                    "description": "Co jeśli poświęcę więcej czasu na życie prywatne?"
                }
            }
        ]
    }
