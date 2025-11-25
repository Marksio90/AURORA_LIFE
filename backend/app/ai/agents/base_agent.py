"""
Base Agent - Bazowa klasa dla wszystkich agentów Aurora
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class BaseAgent(ABC):
    """
    Bazowa klasa dla wszystkich Aurora Agents.

    Każdy agent specjalizuje się w innym aspekcie życia.
    """

    def __init__(self, name: str, specialization: str):
        self.name = name
        self.specialization = specialization
        self.last_execution = None

    @abstractmethod
    async def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Główna metoda analizy - każdy agent implementuje inaczej.

        Args:
            user_data: Dane użytkownika (features, events, context)

        Returns:
            Wyniki analizy specyficzne dla agenta
        """
        pass

    @abstractmethod
    async def recommend(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generuje rekomendacje na podstawie analizy.

        Args:
            analysis_result: Wynik analizy z analyze()

        Returns:
            Rekomendacje działań
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Zwraca status agenta"""
        return {
            "agent_name": self.name,
            "specialization": self.specialization,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "status": "active"
        }
