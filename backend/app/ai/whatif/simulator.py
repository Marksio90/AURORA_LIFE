"""
What-If Simulator - Symulacje scenariuszy "co jeśli"

Pozwala testować wpływ zmian stylu życia na przyszłe wyniki.
"""
import numpy as np
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.datagenius import DataGeniusService


class WhatIfSimulator:
    """
    What-If Simulator - symuluje efekty zmian w stylu życia.

    Przykładowe scenariusze:
    - Co jeśli zwiększę aktywność fizyczną o 30 min/dzień?
    - Co jeśli zmienię dietę?
    - Co jeśli będę spać 8h zamiast 6h?
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.datagenius = DataGeniusService(db)

    async def simulate_scenario(
        self,
        user_id: int,
        scenario: Dict[str, Any],
        simulation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Symuluje scenariusz "co jeśli".

        Args:
            user_id: ID użytkownika
            scenario: Opis scenariusza (zmiany do zastosowania)
            simulation_days: Liczba dni do symulacji

        Returns:
            Wyniki symulacji z predykcjami
        """
        # Pobierz baseline (obecny stan)
        baseline = await self.datagenius.analyze_user_patterns(user_id, days=30)

        if baseline.get("message") == "No data available for analysis":
            return {
                "error": "Insufficient data for simulation",
                "user_id": user_id
            }

        # Zastosuj modyfikacje scenariusza
        modified_features = self._apply_scenario_changes(
            baseline["features"].copy(),
            scenario
        )

        # Oblicz nowe scores
        modified_scores = self._calculate_modified_scores(modified_features)

        # Porównanie
        comparison = self._compare_scenarios(
            baseline["scores"],
            modified_scores,
            scenario
        )

        return {
            "user_id": user_id,
            "scenario": scenario,
            "simulation_days": simulation_days,
            "baseline_scores": baseline["scores"],
            "predicted_scores": modified_scores,
            "improvements": comparison["improvements"],
            "expected_benefits": comparison["benefits"],
            "confidence": comparison["confidence"],
            "recommendation": comparison["recommendation"]
        }

    def _apply_scenario_changes(
        self,
        features: Dict[str, float],
        scenario: Dict[str, Any]
    ) -> Dict[str, float]:
        """Aplikuje zmiany scenariusza na cechy"""

        scenario_type = scenario.get("type")
        change_value = scenario.get("value", 0)

        if scenario_type == "increase_sleep":
            # Zwiększ czas snu
            features['sleep_avg_duration_hours'] += change_value
            features['sleep_regularity_score'] = min(features['sleep_regularity_score'] + 0.1, 1.0)
            features['sleep_quality_avg'] = min(features['sleep_quality_avg'] + 1.0, 10.0)

        elif scenario_type == "increase_activity":
            # Zwiększ aktywność fizyczną
            features['activity_frequency_per_week'] += change_value
            features['activity_consistency'] = min(features['activity_consistency'] + 0.15, 1.0)
            features['health_energy_level_avg'] = min(features['health_energy_level_avg'] + 1.5, 10.0)

        elif scenario_type == "improve_work_life_balance":
            # Popraw równowagę work-life
            features['work_life_balance_ratio'] = min(features['work_life_balance_ratio'] + change_value, 1.5)
            features['social_interactions_per_week'] += 1.0
            features['emotion_positive_ratio'] = min(features['emotion_positive_ratio'] + 0.1, 1.0)

        elif scenario_type == "reduce_work_hours":
            # Zredukuj godziny pracy
            features['work_hours_per_week'] -= change_value
            features['health_stress_level_avg'] = max(features['health_stress_level_avg'] - 1.5, 0.0)
            features['work_life_balance_ratio'] = min(features['work_life_balance_ratio'] + 0.2, 1.5)

        elif scenario_type == "increase_social":
            # Zwiększ interakcje społeczne
            features['social_interactions_per_week'] += change_value
            features['emotion_positive_ratio'] = min(features['emotion_positive_ratio'] + 0.15, 1.0)
            features['mood_trend'] += 0.1

        return features

    def _calculate_modified_scores(self, features: Dict[str, float]) -> Dict[str, float]:
        """Oblicza scores dla zmodyfikowanych cech (podobnie jak DataGenius)"""

        # Health score
        health_score = np.mean([
            min(features['sleep_avg_duration_hours'] / 8.0, 1.0),
            features['sleep_regularity_score'],
            min(features['activity_frequency_per_week'] / 5.0, 1.0),
            features['health_energy_level_avg'] / 10.0 if features['health_energy_level_avg'] > 0 else 0.5,
        ])

        # Mood score
        mood_score = np.mean([
            features['emotion_positive_ratio'],
            (features['mood_trend'] + 1.0) / 2.0,
            1.0 - (features['health_stress_level_avg'] / 10.0) if features['health_stress_level_avg'] > 0 else 0.5,
        ])

        # Productivity score
        productivity_score = np.mean([
            features['work_focus_level_avg'] / 10.0 if features['work_focus_level_avg'] > 0 else 0.5,
            features['work_productivity_avg'] / 10.0 if features['work_productivity_avg'] > 0 else 0.5,
            features['work_deep_work_ratio'],
        ])

        # Energy score
        energy_score = np.mean([
            health_score,
            features['health_energy_level_avg'] / 10.0 if features['health_energy_level_avg'] > 0 else 0.5,
            min(features['activity_frequency_per_week'] / 5.0, 1.0),
        ])

        return {
            "health_score": round(float(health_score), 3),
            "mood_score": round(float(mood_score), 3),
            "productivity_score": round(float(productivity_score), 3),
            "energy_score": round(float(energy_score), 3),
            "overall_wellbeing": round(float(np.mean([health_score, mood_score, productivity_score, energy_score])), 3)
        }

    def _compare_scenarios(
        self,
        baseline: Dict[str, float],
        modified: Dict[str, float],
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Porównuje baseline z modified scenario"""

        improvements = {}
        for key in baseline:
            diff = modified[key] - baseline[key]
            if abs(diff) > 0.01:
                improvements[key] = {
                    "baseline": baseline[key],
                    "predicted": modified[key],
                    "change": round(diff, 3),
                    "change_percent": round((diff / baseline[key] * 100) if baseline[key] > 0 else 0, 1)
                }

        # Expected benefits
        benefits = []
        if improvements.get("health_score", {}).get("change", 0) > 0.05:
            benefits.append(f"Poprawa zdrowia o {improvements['health_score']['change_percent']}%")
        if improvements.get("energy_score", {}).get("change", 0) > 0.05:
            benefits.append(f"Wzrost energii o {improvements['energy_score']['change_percent']}%")
        if improvements.get("mood_score", {}).get("change", 0) > 0.05:
            benefits.append(f"Poprawa nastroju o {improvements['mood_score']['change_percent']}%")
        if improvements.get("productivity_score", {}).get("change", 0) > 0.05:
            benefits.append(f"Wzrost produktywności o {improvements['productivity_score']['change_percent']}%")

        # Overall improvement
        overall_improvement = modified["overall_wellbeing"] - baseline["overall_wellbeing"]

        if overall_improvement > 0.1:
            recommendation = f"✅ Zdecydowanie WARTO! Ten scenariusz może poprawić Twoje well-being o {overall_improvement*100:.1f}%"
        elif overall_improvement > 0.05:
            recommendation = f"👍 Warto spróbować. Potencjalna poprawa o {overall_improvement*100:.1f}%"
        elif overall_improvement > 0:
            recommendation = "🤔 Niewielka poprawa - rozważ inne zmiany"
        else:
            recommendation = "❌ Ten scenariusz może nie przynieść oczekiwanych efektów"

        confidence = 0.75  # Medium confidence dla symulacji

        return {
            "improvements": improvements,
            "benefits": benefits,
            "overall_improvement": round(overall_improvement, 3),
            "confidence": confidence,
            "recommendation": recommendation
        }
