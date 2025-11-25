"""
Feature Extractor - Przekształca Life Events w cechy ML
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict

from app.models.life_event import LifeEvent


class FeatureExtractor:
    """
    Feature Extractor - ekstrakcja cech z Life Events do modelowania ML.

    Generuje cechy opisujące:
    - Wzorce snu (duration, quality, regularity)
    - Aktywność fizyczną (frequency, intensity, consistency)
    - Emocje (sentiment, volatility, trends)
    - Produktywność (focus time, task completion)
    - Relacje społeczne (interaction frequency, quality)
    """

    def __init__(self):
        self.feature_names = []

    def extract_features(
        self,
        events: List[LifeEvent],
        window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Ekstraktuje cechy z listy zdarzeń.

        Args:
            events: Lista Life Events
            window_days: Okno czasowe dla cech (dni)

        Returns:
            Słownik z cechami
        """
        if not events:
            return self._empty_features()

        # Konwersja do DataFrame dla łatwiejszej analizy
        df = self._events_to_dataframe(events)

        features = {}

        # Sleep features
        features.update(self._extract_sleep_features(df, window_days))

        # Activity features
        features.update(self._extract_activity_features(df, window_days))

        # Emotion features
        features.update(self._extract_emotion_features(df, window_days))

        # Work/Productivity features
        features.update(self._extract_work_features(df, window_days))

        # Social features
        features.update(self._extract_social_features(df, window_days))

        # Health features
        features.update(self._extract_health_features(df, window_days))

        # Temporal features
        features.update(self._extract_temporal_features(df, window_days))

        # Cross-domain features
        features.update(self._extract_cross_domain_features(df, window_days))

        return features

    def _events_to_dataframe(self, events: List[LifeEvent]) -> pd.DataFrame:
        """Konwertuje Life Events do pandas DataFrame"""
        data = []
        for event in events:
            row = {
                'event_id': event.id,
                'event_type': event.event_type,
                'event_category': event.event_category,
                'event_time': event.event_time,
                'duration_minutes': event.duration_minutes or 0,
                'impact_score': event.impact_score or 0,
                'energy_impact': event.energy_impact or 0,
                'mood_impact': event.mood_impact or 0,
                'tags': ','.join(event.tags) if event.tags else '',
            }
            # Dodaj event_data jako płaskie kolumny
            if event.event_data:
                for key, value in event.event_data.items():
                    if isinstance(value, (int, float, str, bool)):
                        row[f'data_{key}'] = value

            data.append(row)

        df = pd.DataFrame(data)
        df['event_time'] = pd.to_datetime(df['event_time'])
        df = df.sort_values('event_time')

        return df

    def _extract_sleep_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy dotyczące snu"""
        sleep_df = df[df['event_type'] == 'sleep'].copy()

        if len(sleep_df) == 0:
            return {
                'sleep_avg_duration_hours': 0.0,
                'sleep_std_duration': 0.0,
                'sleep_regularity_score': 0.0,
                'sleep_quality_avg': 0.0,
                'sleep_frequency_per_week': 0.0,
            }

        durations = sleep_df['duration_minutes'] / 60.0  # hours

        features = {
            'sleep_avg_duration_hours': durations.mean(),
            'sleep_std_duration': durations.std(),
            'sleep_regularity_score': 1.0 - min(durations.std() / durations.mean(), 1.0) if durations.mean() > 0 else 0.0,
            'sleep_quality_avg': sleep_df['data_quality'].mean() if 'data_quality' in sleep_df.columns else 0.0,
            'sleep_frequency_per_week': len(sleep_df) / (window_days / 7.0),
        }

        return features

    def _extract_activity_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy dotyczące aktywności fizycznej"""
        activity_df = df[df['event_type'].isin(['exercise', 'activity'])].copy()

        if len(activity_df) == 0:
            return {
                'activity_frequency_per_week': 0.0,
                'activity_avg_duration_minutes': 0.0,
                'activity_consistency': 0.0,
                'activity_intensity_avg': 0.0,
            }

        features = {
            'activity_frequency_per_week': len(activity_df) / (window_days / 7.0),
            'activity_avg_duration_minutes': activity_df['duration_minutes'].mean(),
            'activity_consistency': self._calculate_consistency(activity_df['event_time']),
            'activity_intensity_avg': activity_df['impact_score'].mean(),
        }

        return features

    def _extract_emotion_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy dotyczące emocji"""
        emotion_df = df[df['event_type'] == 'emotion'].copy()

        if len(emotion_df) == 0:
            return {
                'emotion_positive_ratio': 0.5,
                'emotion_volatility': 0.0,
                'emotion_avg_intensity': 0.0,
                'mood_trend': 0.0,
            }

        # Sentiment (positive/negative)
        positive_count = emotion_df[emotion_df['mood_impact'] > 0].shape[0]
        total_count = len(emotion_df)

        features = {
            'emotion_positive_ratio': positive_count / total_count if total_count > 0 else 0.5,
            'emotion_volatility': emotion_df['mood_impact'].std(),
            'emotion_avg_intensity': emotion_df['data_intensity'].mean() if 'data_intensity' in emotion_df.columns else 0.0,
            'mood_trend': self._calculate_trend(emotion_df['mood_impact'].values),
        }

        return features

    def _extract_work_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy dotyczące pracy"""
        work_df = df[df['event_type'] == 'work'].copy()

        if len(work_df) == 0:
            return {
                'work_hours_per_week': 0.0,
                'work_focus_level_avg': 0.0,
                'work_productivity_avg': 0.0,
                'work_deep_work_ratio': 0.0,
            }

        total_minutes = work_df['duration_minutes'].sum()
        deep_work_count = work_df[work_df['tags'].str.contains('deep_work', na=False)].shape[0]

        features = {
            'work_hours_per_week': (total_minutes / 60.0) / (window_days / 7.0),
            'work_focus_level_avg': work_df['data_focus_level'].mean() if 'data_focus_level' in work_df.columns else 0.0,
            'work_productivity_avg': work_df['data_productivity_rating'].mean() if 'data_productivity_rating' in work_df.columns else 0.0,
            'work_deep_work_ratio': deep_work_count / len(work_df) if len(work_df) > 0 else 0.0,
        }

        return features

    def _extract_social_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy dotyczące relacji społecznych"""
        social_df = df[df['event_type'] == 'social'].copy()

        if len(social_df) == 0:
            return {
                'social_interactions_per_week': 0.0,
                'social_quality_avg': 0.0,
                'social_time_hours_per_week': 0.0,
            }

        features = {
            'social_interactions_per_week': len(social_df) / (window_days / 7.0),
            'social_quality_avg': social_df['data_quality'].mean() if 'data_quality' in social_df.columns else 0.0,
            'social_time_hours_per_week': (social_df['duration_minutes'].sum() / 60.0) / (window_days / 7.0),
        }

        return features

    def _extract_health_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy dotyczące zdrowia"""
        health_df = df[df['event_type'] == 'health'].copy()

        if len(health_df) == 0:
            return {
                'health_energy_level_avg': 0.0,
                'health_energy_trend': 0.0,
                'health_stress_level_avg': 0.0,
            }

        energy_values = health_df['data_energy_level'].dropna() if 'data_energy_level' in health_df.columns else pd.Series([])
        stress_values = health_df['data_stress_level'].dropna() if 'data_stress_level' in health_df.columns else pd.Series([])

        features = {
            'health_energy_level_avg': energy_values.mean() if len(energy_values) > 0 else 0.0,
            'health_energy_trend': self._calculate_trend(energy_values.values) if len(energy_values) > 0 else 0.0,
            'health_stress_level_avg': stress_values.mean() if len(stress_values) > 0 else 0.0,
        }

        return features

    def _extract_temporal_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy temporalne"""
        if len(df) == 0:
            return {
                'total_events_count': 0,
                'events_per_day_avg': 0.0,
                'weekend_activity_ratio': 0.0,
            }

        df['weekday'] = df['event_time'].dt.weekday
        weekend_count = df[df['weekday'].isin([5, 6])].shape[0]

        features = {
            'total_events_count': len(df),
            'events_per_day_avg': len(df) / window_days,
            'weekend_activity_ratio': weekend_count / len(df) if len(df) > 0 else 0.0,
        }

        return features

    def _extract_cross_domain_features(self, df: pd.DataFrame, window_days: int) -> Dict[str, float]:
        """Cechy cross-domain (relacje między różnymi aspektami życia)"""

        # Work-life balance
        work_minutes = df[df['event_type'] == 'work']['duration_minutes'].sum()
        social_minutes = df[df['event_type'] == 'social']['duration_minutes'].sum()

        work_life_balance = social_minutes / (work_minutes + 1) if work_minutes > 0 else 1.0

        # Overall life balance (diversity of activities)
        event_type_counts = df['event_type'].value_counts()
        diversity_score = len(event_type_counts) / 7.0  # Normalized by max types

        features = {
            'work_life_balance_ratio': work_life_balance,
            'life_diversity_score': diversity_score,
            'overall_impact_avg': df['impact_score'].mean(),
            'overall_energy_impact_avg': df['energy_impact'].mean(),
            'overall_mood_impact_avg': df['mood_impact'].mean(),
        }

        return features

    def _calculate_consistency(self, timestamps: pd.Series) -> float:
        """Oblicza consistency score na podstawie regularności zdarzeń"""
        if len(timestamps) < 2:
            return 0.0

        # Oblicz odstępy między zdarzeniami
        timestamps = timestamps.sort_values()
        deltas = timestamps.diff().dt.total_seconds() / 86400.0  # days
        deltas = deltas.dropna()

        if len(deltas) == 0:
            return 0.0

        # Consistency = 1 - (std / mean), normalized to 0-1
        mean_delta = deltas.mean()
        std_delta = deltas.std()

        if mean_delta == 0:
            return 0.0

        consistency = 1.0 - min(std_delta / mean_delta, 1.0)
        return max(0.0, min(consistency, 1.0))

    def _calculate_trend(self, values: np.ndarray) -> float:
        """Oblicza trend (slope) z wartości"""
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        coeffs = np.polyfit(x, values, 1)
        slope = coeffs[0]

        # Normalizuj slope do rozsądnego zakresu
        return np.clip(slope, -1.0, 1.0)

    def _empty_features(self) -> Dict[str, float]:
        """Zwraca puste cechy (wszystkie 0)"""
        return {
            # Sleep
            'sleep_avg_duration_hours': 0.0,
            'sleep_std_duration': 0.0,
            'sleep_regularity_score': 0.0,
            'sleep_quality_avg': 0.0,
            'sleep_frequency_per_week': 0.0,
            # Activity
            'activity_frequency_per_week': 0.0,
            'activity_avg_duration_minutes': 0.0,
            'activity_consistency': 0.0,
            'activity_intensity_avg': 0.0,
            # Emotion
            'emotion_positive_ratio': 0.5,
            'emotion_volatility': 0.0,
            'emotion_avg_intensity': 0.0,
            'mood_trend': 0.0,
            # Work
            'work_hours_per_week': 0.0,
            'work_focus_level_avg': 0.0,
            'work_productivity_avg': 0.0,
            'work_deep_work_ratio': 0.0,
            # Social
            'social_interactions_per_week': 0.0,
            'social_quality_avg': 0.0,
            'social_time_hours_per_week': 0.0,
            # Health
            'health_energy_level_avg': 0.0,
            'health_energy_trend': 0.0,
            'health_stress_level_avg': 0.0,
            # Temporal
            'total_events_count': 0,
            'events_per_day_avg': 0.0,
            'weekend_activity_ratio': 0.0,
            # Cross-domain
            'work_life_balance_ratio': 1.0,
            'life_diversity_score': 0.0,
            'overall_impact_avg': 0.0,
            'overall_energy_impact_avg': 0.0,
            'overall_mood_impact_avg': 0.0,
        }
