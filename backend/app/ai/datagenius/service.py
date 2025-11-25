"""
DataGenius Service - Serce AI platformy

Odpowiedzialności:
- Feature engineering z Life Events
- Trenowanie modeli predykcyjnych
- Predykcja energii, nastroju, produktywności
- Systemy rekomendacji
- Klasyfikatory decyzji
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.life_event import LifeEvent
from app.core.events import LifeEventService
from app.ml.features import FeatureExtractor


class DataGeniusService:
    """
    DataGenius Service - główny silnik ML/AI.

    Wykorzystuje Feature Extractor do przetwarzania danych
    i trenuje modele predykcyjne.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_extractor = FeatureExtractor()
        self.event_service = LifeEventService(db)

    async def analyze_user_patterns(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analizuje wzorce użytkownika i generuje insights.

        Returns:
            Analiza z cechami i insights
        """
        # Pobierz ostatnie zdarzenia
        events = await self.event_service.get_recent_events(user_id, days)

        if not events:
            return {
                "message": "No data available for analysis",
                "user_id": user_id,
                "period_days": days
            }

        # Ekstraktuj cechy
        features = self.feature_extractor.extract_features(events, days)

        # Generuj insights
        insights = self._generate_insights(features)

        # Oblicz overall scores
        scores = self._calculate_overall_scores(features)

        return {
            "user_id": user_id,
            "period_days": days,
            "events_analyzed": len(events),
            "features": features,
            "insights": insights,
            "scores": scores,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    async def predict_energy(
        self,
        user_id: int,
        time_of_day: str = "morning"
    ) -> Dict[str, Any]:
        """
        Przewiduje poziom energii użytkownika.

        Args:
            user_id: ID użytkownika
            time_of_day: Pora dnia (morning, afternoon, evening)

        Returns:
            Predykcja energii z confidence
        """
        # Pobierz historyczne dane
        events = await self.event_service.get_recent_events(user_id, days=30)
        features = self.feature_extractor.extract_features(events, 30)

        # Prosty model predykcyjny (bazujący na historycznych wzorcach)
        energy_prediction = self._predict_energy_simple(features, time_of_day)

        return {
            "user_id": user_id,
            "time_of_day": time_of_day,
            "predicted_energy": energy_prediction["energy"],
            "confidence": energy_prediction["confidence"],
            "factors": energy_prediction["factors"],
            "recommendations": energy_prediction["recommendations"]
        }

    async def predict_mood(
        self,
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Przewiduje nastrój użytkownika.

        Args:
            user_id: ID użytkownika
            context: Dodatkowy kontekst (np. dzień tygodnia, pogoda)

        Returns:
            Predykcja nastroju
        """
        events = await self.event_service.get_recent_events(user_id, days=30)
        features = self.feature_extractor.extract_features(events, 30)

        mood_prediction = self._predict_mood_simple(features, context)

        return {
            "user_id": user_id,
            "predicted_mood_score": mood_prediction["mood_score"],
            "sentiment": mood_prediction["sentiment"],
            "confidence": mood_prediction["confidence"],
            "influencing_factors": mood_prediction["factors"]
        }

    async def recommend_activities(
        self,
        user_id: int,
        goal: str = "energy"
    ) -> Dict[str, Any]:
        """
        Rekomenduje aktywności dla użytkownika.

        Args:
            user_id: ID użytkownika
            goal: Cel (energy, mood, productivity, balance)

        Returns:
            Lista rekomendacji
        """
        events = await self.event_service.get_recent_events(user_id, days=30)
        features = self.feature_extractor.extract_features(events, 30)

        recommendations = self._generate_recommendations(features, goal)

        return {
            "user_id": user_id,
            "goal": goal,
            "recommendations": recommendations,
            "personalization_confidence": recommendations["confidence"]
        }

    def _generate_insights(self, features: Dict[str, float]) -> List[str]:
        """Generuje insights na podstawie cech"""
        insights = []

        # Sleep insights
        if features['sleep_avg_duration_hours'] < 7.0:
            insights.append(f"⚠️ Średnia długość snu ({features['sleep_avg_duration_hours']:.1f}h) jest poniżej zalecanej (7-9h)")
        elif features['sleep_avg_duration_hours'] > 9.0:
            insights.append(f"⚠️ Średnia długość snu ({features['sleep_avg_duration_hours']:.1f}h) jest powyżej normalnej")
        else:
            insights.append(f"✅ Dobra średnia długość snu: {features['sleep_avg_duration_hours']:.1f}h")

        if features['sleep_regularity_score'] > 0.8:
            insights.append(f"✅ Wysoka regularność snu (score: {features['sleep_regularity_score']:.2f})")
        elif features['sleep_regularity_score'] < 0.5:
            insights.append(f"⚠️ Niska regularność snu - rozważ stałą porę snu")

        # Activity insights
        if features['activity_frequency_per_week'] < 2:
            insights.append(f"⚠️ Niska aktywność fizyczna ({features['activity_frequency_per_week']:.1f}x/tydzień) - zalecane minimum 3x")
        elif features['activity_frequency_per_week'] >= 4:
            insights.append(f"✅ Dobra aktywność fizyczna: {features['activity_frequency_per_week']:.1f}x/tydzień")

        # Emotion insights
        if features['emotion_positive_ratio'] > 0.7:
            insights.append(f"✅ Wysoki poziom pozytywnych emocji ({features['emotion_positive_ratio']:.0%})")
        elif features['emotion_positive_ratio'] < 0.4:
            insights.append(f"⚠️ Niska proporcja pozytywnych emocji - może warto porozmawiać z kimś lub rozważyć wsparcie")

        if features['mood_trend'] > 0.1:
            insights.append(f"📈 Trend nastroju wzrostowy - świetnie!")
        elif features['mood_trend'] < -0.1:
            insights.append(f"📉 Trend nastroju spadkowy - zwróć uwagę na well-being")

        # Work-life balance
        if features['work_life_balance_ratio'] < 0.3:
            insights.append(f"⚠️ Niska równowaga work-life - poświęć więcej czasu na relacje i odpoczynek")
        elif features['work_life_balance_ratio'] > 0.7:
            insights.append(f"✅ Dobra równowaga work-life")

        # Energy trends
        if features['health_energy_trend'] > 0.1:
            insights.append(f"⚡ Poziom energii rośnie - coś robisz dobrze!")
        elif features['health_energy_trend'] < -0.1:
            insights.append(f"⚠️ Poziom energii spada - sprawdź sen, dietę i aktywność")

        return insights

    def _calculate_overall_scores(self, features: Dict[str, float]) -> Dict[str, float]:
        """Oblicza overall scores na podstawie cech"""

        # Health score (0-1)
        health_score = np.mean([
            min(features['sleep_avg_duration_hours'] / 8.0, 1.0),
            features['sleep_regularity_score'],
            min(features['activity_frequency_per_week'] / 5.0, 1.0),
            features['health_energy_level_avg'] / 10.0 if features['health_energy_level_avg'] > 0 else 0.5,
        ])

        # Mood score (0-1)
        mood_score = np.mean([
            features['emotion_positive_ratio'],
            (features['mood_trend'] + 1.0) / 2.0,  # Normalize from [-1,1] to [0,1]
            1.0 - (features['health_stress_level_avg'] / 10.0) if features['health_stress_level_avg'] > 0 else 0.5,
        ])

        # Productivity score (0-1)
        productivity_score = np.mean([
            features['work_focus_level_avg'] / 10.0 if features['work_focus_level_avg'] > 0 else 0.5,
            features['work_productivity_avg'] / 10.0 if features['work_productivity_avg'] > 0 else 0.5,
            features['work_deep_work_ratio'],
        ])

        # Energy score (0-1)
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

    def _predict_energy_simple(
        self,
        features: Dict[str, float],
        time_of_day: str
    ) -> Dict[str, Any]:
        """Prosta predykcja energii (heurystyczna)"""

        base_energy = features['health_energy_level_avg']

        # Modyfikatory na podstawie pory dnia
        time_modifiers = {
            "morning": 1.1,
            "afternoon": 0.9,
            "evening": 0.7,
            "night": 0.5
        }

        modifier = time_modifiers.get(time_of_day, 1.0)

        # Wpływ snu
        sleep_factor = min(features['sleep_avg_duration_hours'] / 8.0, 1.2)

        # Wpływ aktywności
        activity_factor = 1.0 + (features['activity_frequency_per_week'] / 10.0)

        # Oblicz predykcję
        predicted_energy = base_energy * modifier * sleep_factor * activity_factor
        predicted_energy = np.clip(predicted_energy, 0, 10)

        # Confidence na podstawie ilości danych
        confidence = min(features['total_events_count'] / 100.0, 0.95)

        factors = []
        if features['sleep_avg_duration_hours'] < 7:
            factors.append("Niedostateczny sen może obniżać energię")
        if features['activity_frequency_per_week'] < 2:
            factors.append("Niska aktywność fizyczna może ograniczać energię")
        if time_of_day == "evening":
            factors.append("Naturalne obniżenie energii wieczorem")

        recommendations = []
        if predicted_energy < 5:
            recommendations.append("Rozważ krótką drzemkę (20-30 min)")
            recommendations.append("Wypij wodę i zjedz zdrową przekąskę")
            recommendations.append("Krótki spacer na świeżym powietrzu")

        return {
            "energy": round(float(predicted_energy), 2),
            "confidence": round(confidence, 2),
            "factors": factors,
            "recommendations": recommendations
        }

    def _predict_mood_simple(
        self,
        features: Dict[str, float],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prosta predykcja nastroju"""

        # Base mood z emotion features
        base_mood = features['emotion_positive_ratio'] * 10.0

        # Modyfikatory
        if features['mood_trend'] > 0:
            base_mood += 1.0
        elif features['mood_trend'] < 0:
            base_mood -= 1.0

        # Work-life balance wpływa na nastrój
        if features['work_life_balance_ratio'] < 0.3:
            base_mood -= 1.5

        # Stress level
        if features['health_stress_level_avg'] > 7:
            base_mood -= 2.0

        mood_score = np.clip(base_mood, 0, 10)

        sentiment = "positive" if mood_score > 6 else "neutral" if mood_score > 4 else "negative"
        confidence = min(features['total_events_count'] / 100.0, 0.90)

        factors = []
        if features['emotion_positive_ratio'] < 0.4:
            factors.append("Niska proporcja pozytywnych emocji w ostatnim czasie")
        if features['work_life_balance_ratio'] < 0.3:
            factors.append("Brak równowagi work-life")
        if features['social_interactions_per_week'] < 2:
            factors.append("Niski poziom interakcji społecznych")

        return {
            "mood_score": round(float(mood_score), 2),
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "factors": factors
        }

    def _generate_recommendations(
        self,
        features: Dict[str, float],
        goal: str
    ) -> Dict[str, Any]:
        """Generuje rekomendacje aktywności"""

        recommendations = []
        confidence = min(features['total_events_count'] / 100.0, 0.85)

        if goal == "energy":
            if features['sleep_avg_duration_hours'] < 7:
                recommendations.append({
                    "activity": "Poprawa higieny snu",
                    "reason": "Niedostateczna długość snu",
                    "expected_impact": "+2 punkty energii",
                    "priority": "high"
                })

            if features['activity_frequency_per_week'] < 3:
                recommendations.append({
                    "activity": "Zwiększ aktywność fizyczną do 3-4x/tydzień",
                    "reason": "Aktywność fizyczna zwiększa energię",
                    "expected_impact": "+1.5 punkty energii",
                    "priority": "medium"
                })

            recommendations.append({
                "activity": "Krótkie przerwy co godzinę (stretching, spacer)",
                "reason": "Regularne przerwy poprawiają krążenie i energię",
                "expected_impact": "+0.5 punkty energii",
                "priority": "low"
            })

        elif goal == "mood":
            if features['social_interactions_per_week'] < 2:
                recommendations.append({
                    "activity": "Zaplanuj spotkanie z przyjaciółmi",
                    "reason": "Interakcje społeczne poprawiają nastrój",
                    "expected_impact": "+2 punkty nastroju",
                    "priority": "high"
                })

            if features['activity_frequency_per_week'] < 2:
                recommendations.append({
                    "activity": "Aktywność na świeżym powietrzu (spacer, jogging)",
                    "reason": "Ruch i światło słoneczne poprawiają nastrój",
                    "expected_impact": "+1.5 punkty nastroju",
                    "priority": "medium"
                })

            recommendations.append({
                "activity": "Praktyka mindfulness lub medytacji (10-15 min/dzień)",
                "reason": "Mindfulness redukuje stres i poprawia well-being",
                "expected_impact": "+1 punkt nastroju",
                "priority": "medium"
            })

        elif goal == "productivity":
            if features['work_deep_work_ratio'] < 0.5:
                recommendations.append({
                    "activity": "Zaplanuj 2-3h deep work każdego dnia rano",
                    "reason": "Rano energia i focus są najwyższe",
                    "expected_impact": "+30% produktywności",
                    "priority": "high"
                })

            recommendations.append({
                "activity": "Technika Pomodoro (25 min pracy + 5 min przerwy)",
                "reason": "Strukturyzacja czasu zwiększa focus",
                "expected_impact": "+20% produktywności",
                "priority": "medium"
            })

            if features['sleep_avg_duration_hours'] < 7:
                recommendations.append({
                    "activity": "Zwiększ czas snu do 7-8h",
                    "reason": "Sen wpływa bezpośrednio na cognitive performance",
                    "expected_impact": "+25% produktywności",
                    "priority": "high"
                })

        elif goal == "balance":
            if features['work_life_balance_ratio'] < 0.4:
                recommendations.append({
                    "activity": "Zwiększ czas na hobby i relacje o 2-3h/tydzień",
                    "reason": "Work-life balance jest kluczowy dla well-being",
                    "expected_impact": "Znaczna poprawa równowagi",
                    "priority": "high"
                })

            if features['life_diversity_score'] < 0.5:
                recommendations.append({
                    "activity": "Wprowadź nowe aktywności (np. hobby, sport, kursy)",
                    "reason": "Różnorodność aktywności zwiększa satysfakcję życiową",
                    "expected_impact": "Poprawa ogólnego well-being",
                    "priority": "medium"
                })

        return {
            "items": recommendations,
            "confidence": round(confidence, 2),
            "goal": goal
        }
