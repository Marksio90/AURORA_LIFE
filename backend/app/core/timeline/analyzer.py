"""
Pattern Analyzer - Wykrywanie wzorców, cykli, anomalii i trendów
"""
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.models.life_event import LifeEvent


class PatternAnalyzer:
    """
    Pattern Analyzer - analizuje Life Events i wykrywa:
    - Wzorce (patterns): powtarzające się sekwencje
    - Cykle (cycles): rytmy życiowe (snu, produktywności)
    - Anomalie (anomalies): odstępstwa od normy
    - Trendy (trends): zmiany w czasie

    W Zestawie 2 zostanie wzbogacony o ML models z DataGenius.
    """

    def __init__(self):
        self.min_pattern_occurrences = 3
        self.anomaly_threshold = 2.0  # Odchylenia standardowe

    def detect_sleep_pattern(
        self,
        sleep_events: List[LifeEvent]
    ) -> Optional[Dict[str, Any]]:
        """
        Wykrywa wzorzec snu użytkownika.
        """
        if len(sleep_events) < 3:
            return None

        durations = []
        sleep_times = []  # Godzina zaśnięcia

        for event in sleep_events:
            if event.duration_minutes:
                durations.append(event.duration_minutes / 60.0)  # Godziny
            sleep_times.append(event.event_time.hour + event.event_time.minute / 60.0)

        if not durations:
            return None

        avg_duration = np.mean(durations)
        std_duration = np.std(durations)
        avg_sleep_time = np.mean(sleep_times)
        regularity = 1.0 - min(std_duration / avg_duration, 1.0)  # 0-1

        return {
            "type": "sleep_cycle",
            "avg_duration_hours": round(avg_duration, 2),
            "std_duration_hours": round(std_duration, 2),
            "avg_bedtime_hour": round(avg_sleep_time, 2),
            "regularity_score": round(regularity, 2),
            "sample_size": len(durations),
            "confidence": min(len(durations) / 30.0, 1.0)  # Confidence rośnie z ilością danych
        }

    def detect_activity_pattern(
        self,
        activity_events: List[LifeEvent]
    ) -> Optional[Dict[str, Any]]:
        """Wykrywa wzorzec aktywności fizycznej"""
        if len(activity_events) < 3:
            return None

        # Grupuj po dniach tygodnia
        day_counts = defaultdict(int)
        total_activities = 0

        for event in activity_events:
            day_of_week = event.event_time.weekday()
            day_counts[day_of_week] += 1
            total_activities += 1

        # Znajdź preferowane dni
        preferred_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        day_names = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]

        avg_per_week = total_activities / max(len(activity_events) / 7.0, 1)

        return {
            "type": "activity_pattern",
            "avg_activities_per_week": round(avg_per_week, 2),
            "preferred_days": [
                {"day": day_names[day], "count": count}
                for day, count in preferred_days
            ],
            "total_activities": total_activities,
            "consistency": round(min(avg_per_week / 7.0, 1.0), 2),
            "confidence": min(len(activity_events) / 20.0, 1.0)
        }

    def detect_anomalies(
        self,
        events: List[LifeEvent],
        metric_key: str = "duration_minutes"
    ) -> List[Dict[str, Any]]:
        """
        Wykrywa anomalie w zdarzeniach (wartości odstające).
        """
        if len(events) < 5:
            return []

        values = []
        event_map = {}

        for event in events:
            if metric_key == "duration_minutes" and event.duration_minutes:
                values.append(event.duration_minutes)
                event_map[len(values) - 1] = event
            elif metric_key in event.event_data:
                val = event.event_data[metric_key]
                if isinstance(val, (int, float)):
                    values.append(val)
                    event_map[len(values) - 1] = event

        if len(values) < 5:
            return []

        mean = np.mean(values)
        std = np.std(values)

        anomalies = []
        for idx, value in enumerate(values):
            z_score = abs((value - mean) / std) if std > 0 else 0
            if z_score > self.anomaly_threshold:
                event = event_map[idx]
                anomalies.append({
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "event_time": event.event_time,
                    "value": value,
                    "expected_mean": round(mean, 2),
                    "deviation": round(z_score, 2),
                    "description": f"Wartość {value} odbiega o {z_score:.1f} odchyleń standardowych od średniej {mean:.1f}"
                })

        return anomalies

    def detect_trend(
        self,
        events: List[LifeEvent],
        metric_key: str = "duration_minutes"
    ) -> Optional[Dict[str, Any]]:
        """
        Wykrywa trend w czasie (wzrost/spadek).
        """
        if len(events) < 5:
            return None

        values = []
        times = []

        for event in events:
            val = None
            if metric_key == "duration_minutes" and event.duration_minutes:
                val = event.duration_minutes
            elif metric_key in event.event_data:
                val = event.event_data.get(metric_key)

            if val is not None and isinstance(val, (int, float)):
                values.append(val)
                times.append(event.event_time.timestamp())

        if len(values) < 5:
            return None

        # Prosta regresja liniowa
        times_norm = np.array(times) - times[0]  # Normalizuj czas
        values_arr = np.array(values)

        # y = ax + b
        A = np.vstack([times_norm, np.ones(len(times_norm))]).T
        slope, intercept = np.linalg.lstsq(A, values_arr, rcond=None)[0]

        # Kierunek trendu
        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "improving"
        else:
            direction = "declining"

        # R² dla confidence
        y_pred = slope * times_norm + intercept
        ss_res = np.sum((values_arr - y_pred) ** 2)
        ss_tot = np.sum((values_arr - np.mean(values_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        return {
            "type": "trend",
            "metric": metric_key,
            "direction": direction,
            "slope": round(slope, 4),
            "confidence": round(max(0, min(r_squared, 1.0)), 2),
            "sample_size": len(values),
            "time_span_days": round((times[-1] - times[0]) / 86400, 1)
        }

    def generate_insight(
        self,
        user_id: int,
        events: List[LifeEvent],
        patterns: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Generuje insight na podstawie wykrytych wzorców.
        """
        if not patterns:
            return None

        # Przykładowy insight: podsumowanie wzorców
        insights = []

        for pattern in patterns:
            if pattern["type"] == "sleep_cycle":
                if pattern["regularity_score"] > 0.8:
                    insights.append(f"Regularny wzorzec snu: średnio {pattern['avg_duration_hours']}h")
                else:
                    insights.append(f"Nieregularny sen - rozważ ustalenie stałej pory snu")

            elif pattern["type"] == "activity_pattern":
                insights.append(f"Aktywność fizyczna: średnio {pattern['avg_activities_per_week']} razy/tydzień")

        if insights:
            return {
                "title": "Podsumowanie wzorców życiowych",
                "insights": insights,
                "confidence": np.mean([p.get("confidence", 0.5) for p in patterns])
            }

        return None
