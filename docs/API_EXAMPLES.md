# Aurora Life Compass - API Examples

Kompletna kolekcja przykładów użycia API.

## Spis treści

1. [Users (Core Identity Layer)](#users)
2. [Life Events](#life-events)
3. [Timeline & Patterns](#timeline--patterns)
4. [Data Vault](#data-vault)

---

## Users

### Utwórz nowego użytkownika

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "anna@example.com",
    "username": "anna",
    "password": "secure_password_123",
    "full_name": "Anna Nowak",
    "timezone": "Europe/Warsaw"
  }'
```

### Pobierz profil użytkownika

```bash
curl http://localhost:8000/api/users/1
```

### Aktualizuj profil

```bash
curl -X PUT http://localhost:8000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Anna Nowak-Kowalska",
    "profile_data": {
      "goals": [
        "Zwiększyć energię o 20%",
        "Regularnie ćwiczyć 4x w tygodniu",
        "Poprawić jakość snu"
      ],
      "values": [
        "zdrowie",
        "rozwój osobisty",
        "work-life balance"
      ],
      "preferences": {
        "work_hours": "9-17",
        "sleep_target_hours": 8,
        "exercise_days": ["wtorek", "czwartek", "sobota", "niedziela"]
      }
    }
  }'
```

### Pobierz Digital Twin

```bash
curl http://localhost:8000/api/users/1/digital-twin
```

---

## Life Events

### Sen (Sleep)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "sleep",
    "event_category": "wellness",
    "title": "Nocny sen",
    "description": "Głęboki sen bez przerwań",
    "event_time": "2025-11-24T23:00:00Z",
    "duration_minutes": 480,
    "event_data": {
      "quality": 9,
      "deep_sleep_minutes": 140,
      "rem_minutes": 95,
      "light_sleep_minutes": 245,
      "interruptions": 0,
      "went_to_bed": "22:45",
      "woke_up": "07:00",
      "feeling_after": "refreshed"
    },
    "tags": ["good_quality", "regular", "weekday"],
    "context": {
      "temperature_celsius": 19,
      "room_dark": true,
      "quiet": true
    }
  }'
```

### Aktywność fizyczna (Exercise)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "exercise",
    "event_category": "wellness",
    "title": "Bieganie w parku",
    "event_time": "2025-11-25T06:30:00Z",
    "duration_minutes": 45,
    "event_data": {
      "type": "running",
      "distance_km": 7.5,
      "avg_pace_min_per_km": 6.0,
      "avg_heart_rate": 145,
      "max_heart_rate": 168,
      "calories": 450,
      "elevation_gain_m": 50,
      "feeling": "energized"
    },
    "tags": ["morning", "outdoor", "cardio"],
    "source": "wearable",
    "context": {
      "weather": "sunny",
      "temperature_celsius": 12,
      "location": "City Park"
    }
  }'
```

### Yoga/Stretching

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "exercise",
    "event_category": "wellness",
    "title": "Poranna yoga",
    "event_time": "2025-11-25T07:00:00Z",
    "duration_minutes": 30,
    "event_data": {
      "type": "yoga",
      "intensity": "moderate",
      "style": "hatha",
      "feeling_after": "relaxed and energized"
    },
    "tags": ["morning", "indoor", "flexibility", "mindfulness"]
  }'
```

### Emocje (Emotions)

```bash
# Pozytywna emocja
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "emotion",
    "event_category": "personal",
    "title": "Ekscytacja po awansie",
    "event_time": "2025-11-25T14:30:00Z",
    "event_data": {
      "type": "excited",
      "intensity": 9,
      "valence": "positive",
      "arousal": "high",
      "trigger": "Otrzymałem awans w pracy",
      "physical_sensations": ["energia", "motywacja", "focus"]
    },
    "tags": ["positive", "work", "achievement"]
  }'

# Negatywna emocja
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "emotion",
    "event_category": "personal",
    "title": "Stres przed prezentacją",
    "event_time": "2025-11-25T09:00:00Z",
    "event_data": {
      "type": "anxious",
      "intensity": 7,
      "valence": "negative",
      "arousal": "high",
      "trigger": "Ważna prezentacja dla klientów",
      "coping_strategy": "Głębokie oddychanie"
    },
    "tags": ["negative", "work", "temporary"]
  }'
```

### Praca (Work)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "work",
    "event_category": "productivity",
    "title": "Deep work session - coding",
    "event_time": "2025-11-25T09:00:00Z",
    "duration_minutes": 120,
    "event_data": {
      "task_type": "coding",
      "project": "Aurora Life Compass",
      "focus_level": 9,
      "productivity_rating": 8,
      "interruptions": 1,
      "lines_of_code": 450,
      "tasks_completed": 3
    },
    "tags": ["deep_work", "high_focus", "morning"],
    "context": {
      "location": "home_office",
      "noise_level": "quiet",
      "energy_before": 8
    }
  }'
```

### Spotkania (Meetings)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "social",
    "event_category": "work",
    "title": "Team standup meeting",
    "event_time": "2025-11-25T10:00:00Z",
    "duration_minutes": 15,
    "event_data": {
      "type": "meeting",
      "format": "video_call",
      "participants": 8,
      "productivity": 7,
      "energy_drain": 2
    },
    "tags": ["work", "recurring", "team"],
    "source": "calendar"
  }'
```

### Posiłki (Meals)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "health",
    "event_category": "nutrition",
    "title": "Śniadanie",
    "event_time": "2025-11-25T07:30:00Z",
    "duration_minutes": 20,
    "event_data": {
      "meal_type": "breakfast",
      "calories": 450,
      "protein_g": 25,
      "carbs_g": 55,
      "fats_g": 15,
      "items": ["oatmeal", "banana", "peanut butter", "coffee"],
      "feeling_after": "energized"
    },
    "tags": ["healthy", "balanced", "home"]
  }'
```

### Interakcje społeczne

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "social",
    "event_category": "relationships",
    "title": "Kolacja z przyjaciółmi",
    "event_time": "2025-11-25T19:00:00Z",
    "duration_minutes": 180,
    "event_data": {
      "type": "friends",
      "people_count": 4,
      "quality": 9,
      "mood_before": 7,
      "mood_after": 9,
      "connection_depth": "deep"
    },
    "tags": ["friends", "evening", "positive", "recharge"],
    "context": {
      "location": "restaurant",
      "atmosphere": "relaxed"
    }
  }'
```

### Poziom energii (samodzielne pomiary)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "health",
    "event_category": "wellness",
    "title": "Check-in energii",
    "event_time": "2025-11-25T14:00:00Z",
    "event_data": {
      "energy_level": 8,
      "mental_clarity": 9,
      "physical_feeling": 7,
      "stress_level": 3,
      "mood": "positive"
    },
    "tags": ["checkin", "afternoon"]
  }'
```

### Pobierz ostatnie zdarzenia

```bash
# Wszystkie z ostatnich 7 dni
curl "http://localhost:8000/api/events?user_id=1&days=7"

# Tylko sen z ostatnich 14 dni
curl "http://localhost:8000/api/events?user_id=1&event_type=sleep&days=14"

# Wszystkie emocje z ostatnich 30 dni
curl "http://localhost:8000/api/events?user_id=1&event_type=emotion&days=30&limit=100"
```

### Aktualizuj zdarzenie

```bash
curl -X PUT "http://localhost:8000/api/events/5?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bardzo dobry sen",
    "description": "Najlepszy sen od tygodnia",
    "tags": ["excellent_quality", "regular", "best_this_week"]
  }'
```

### Usuń zdarzenie

```bash
curl -X DELETE "http://localhost:8000/api/events/10?user_id=1"
```

### Statystyki zdarzeń

```bash
# Ostatnie 30 dni
curl "http://localhost:8000/api/events/stats/summary?user_id=1&days=30"
```

---

## Timeline & Patterns

### Wykryj wzorce życiowe

```bash
# Analiza ostatnich 30 dni
curl "http://localhost:8000/api/timeline/patterns/detect?user_id=1&days=30"

# Analiza ostatnich 90 dni (długoterminowe trendy)
curl "http://localhost:8000/api/timeline/patterns/detect?user_id=1&days=90"
```

Przykładowa odpowiedź:
```json
{
  "user_id": 1,
  "analysis_period_days": 30,
  "events_analyzed": 87,
  "patterns_found": 4,
  "patterns": [
    {
      "type": "sleep_cycle",
      "avg_duration_hours": 7.8,
      "std_duration_hours": 0.5,
      "avg_bedtime_hour": 23.2,
      "regularity_score": 0.91,
      "sample_size": 30,
      "confidence": 0.95
    },
    {
      "type": "activity_pattern",
      "avg_activities_per_week": 4.5,
      "preferred_days": [
        {"day": "Wtorek", "count": 8},
        {"day": "Czwartek", "count": 7},
        {"day": "Sobota", "count": 6}
      ],
      "total_activities": 19,
      "consistency": 0.64,
      "confidence": 0.88
    },
    {
      "type": "sleep_anomalies",
      "count": 3,
      "anomalies": [
        {
          "event_id": 45,
          "event_type": "sleep",
          "event_time": "2025-11-15T23:00:00Z",
          "value": 300,
          "expected_mean": 468,
          "deviation": 2.8,
          "description": "Wartość 300 odbiega o 2.8 odchyleń standardowych od średniej 468.0"
        }
      ]
    },
    {
      "type": "trend",
      "metric": "energy_level",
      "direction": "improving",
      "slope": 0.015,
      "confidence": 0.82,
      "sample_size": 15,
      "time_span_days": 29.5
    }
  ]
}
```

### Pobierz wpisy timeline

```bash
# Wszystkie wpisy z ostatnich 30 dni
curl "http://localhost:8000/api/timeline?user_id=1&days=30"

# Tylko wzorce
curl "http://localhost:8000/api/timeline?user_id=1&entry_type=pattern&days=30"

# Tylko znaczące wpisy
curl "http://localhost:8000/api/timeline?user_id=1&significant_only=true&days=60"

# Tylko anomalie
curl "http://localhost:8000/api/timeline?user_id=1&entry_type=anomaly&days=14"
```

### Pobierz ostatnie insights

```bash
curl "http://localhost:8000/api/timeline/insights/recent?user_id=1&days=7"
```

### Podsumowanie timeline

```bash
curl "http://localhost:8000/api/timeline/summary/period?user_id=1&days=30"
```

### Utwórz manualny wpis timeline

```bash
curl -X POST "http://localhost:8000/api/timeline?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "milestone",
    "start_time": "2025-11-25T10:00:00Z",
    "end_time": "2025-11-25T10:00:00Z",
    "title": "Ukończenie projektu Aurora Life Compass v1",
    "description": "Zestaw 1 (Fundamenty) gotowy do użycia",
    "analysis_data": {
      "achievement": "MVP deployed",
      "impact": "high"
    },
    "confidence_score": 1.0,
    "importance_score": 0.95,
    "is_significant": true,
    "tags": ["achievement", "project", "milestone"]
  }'
```

---

## Data Vault

### Eksport pełnych danych użytkownika (GDPR)

```bash
# Pełny eksport
curl "http://localhost:8000/api/vault/export/1" > my_life_data.json

# Tylko ostatnie 30 dni
curl "http://localhost:8000/api/vault/export/1?start_date=2025-10-26T00:00:00Z" > last_30_days.json

# Bez timeline
curl "http://localhost:8000/api/vault/export/1?include_timeline=false" > events_only.json
```

### Podsumowanie danych

```bash
curl "http://localhost:8000/api/vault/summary/1"
```

Przykładowa odpowiedź:
```json
{
  "user_id": 1,
  "username": "anna",
  "total_life_events": 156,
  "total_timeline_entries": 23,
  "data_span": {
    "first_event": "2025-10-01T12:00:00Z",
    "last_event": "2025-11-25T18:30:00Z",
    "days_tracked": 55
  },
  "life_metrics": {
    "health_score": 0.82,
    "energy_score": 0.78,
    "mood_score": 0.85,
    "productivity_score": 0.75
  },
  "account_age_days": 55
}
```

### Informacje o archiwizacji

```bash
# Ile danych starszych niż rok?
curl "http://localhost:8000/api/vault/archive/1?older_than_days=365"

# Ile danych starszych niż 6 miesięcy?
curl "http://localhost:8000/api/vault/archive/1?older_than_days=180"
```

### Usuń dane użytkownika (GDPR Right to Erasure)

```bash
# Usuń tylko dane (events, timeline), zachowaj konto
curl -X DELETE "http://localhost:8000/api/vault/user/1?delete_user=false"

# Usuń wszystko włącznie z kontem
curl -X DELETE "http://localhost:8000/api/vault/user/1?delete_user=true"
```

---

## Zaawansowane scenariusze

### Scenario 1: Tygodniowy tracking życia

```bash
#!/bin/bash
USER_ID=1

# Poniedziałek
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d '{"event_type":"sleep","title":"Nocny sen","event_time":"2025-11-25T23:00:00Z","duration_minutes":450,"event_data":{"quality":7}}'
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d '{"event_type":"exercise","title":"Poranna yoga","event_time":"2025-11-26T07:00:00Z","duration_minutes":30,"event_data":{"type":"yoga"}}'
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d '{"event_type":"work","title":"Deep work","event_time":"2025-11-26T09:00:00Z","duration_minutes":180,"event_data":{"focus_level":8}}'

# ... więcej dni
```

### Scenario 2: Monitorowanie energii przez dzień

```bash
#!/bin/bash
USER_ID=1
DATE="2025-11-25"

# Rano (po przebudzeniu)
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d "{\"event_type\":\"health\",\"title\":\"Energy check\",\"event_time\":\"${DATE}T07:00:00Z\",\"event_data\":{\"energy_level\":6,\"mood\":\"neutral\"}}"

# Przed lunchem
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d "{\"event_type\":\"health\",\"title\":\"Energy check\",\"event_time\":\"${DATE}T12:00:00Z\",\"event_data\":{\"energy_level\":8,\"mood\":\"positive\"}}"

# Po południu
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d "{\"event_type\":\"health\",\"title\":\"Energy check\",\"event_time\":\"${DATE}T15:00:00Z\",\"event_data\":{\"energy_level\":5,\"mood\":\"tired\"}}"

# Wieczorem
curl -X POST "http://localhost:8000/api/events?user_id=$USER_ID" -H "Content-Type: application/json" -d "{\"event_type\":\"health\",\"title\":\"Energy check\",\"event_time\":\"${DATE}T20:00:00Z\",\"event_data\":{\"energy_level\":7,\"mood\":\"relaxed\"}}"
```

### Scenario 3: Analiza wzorców po miesiącu

```bash
#!/bin/bash
USER_ID=1

echo "=== Podsumowanie ostatnich 30 dni ==="
curl -s "http://localhost:8000/api/vault/summary/$USER_ID" | jq .

echo -e "\n=== Statystyki zdarzeń ==="
curl -s "http://localhost:8000/api/events/stats/summary?user_id=$USER_ID&days=30" | jq .

echo -e "\n=== Wykrywanie wzorców ==="
curl -s "http://localhost:8000/api/timeline/patterns/detect?user_id=$USER_ID&days=30" | jq .

echo -e "\n=== Podsumowanie timeline ==="
curl -s "http://localhost:8000/api/timeline/summary/period?user_id=$USER_ID&days=30" | jq .
```

---

## Testing Tips

### Populate test data

```python
import requests
import random
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"
USER_ID = 1

# Generate 30 days of sleep events
for day in range(30):
    event_time = datetime.now() - timedelta(days=day)
    event_time = event_time.replace(hour=23, minute=0, second=0)

    duration = random.randint(400, 520)  # 6.5-8.5 hours
    quality = random.randint(6, 10)

    data = {
        "event_type": "sleep",
        "title": f"Sleep day {day}",
        "event_time": event_time.isoformat() + "Z",
        "duration_minutes": duration,
        "event_data": {
            "quality": quality,
            "deep_sleep_minutes": int(duration * 0.25),
            "rem_minutes": int(duration * 0.20)
        },
        "tags": ["regular"]
    }

    response = requests.post(
        f"{API_URL}/api/events?user_id={USER_ID}",
        json=data
    )
    print(f"Day {day}: {response.status_code}")
```

---

## Podsumowanie

To kompletny zestaw przykładów API dla Aurora Life Compass Zestaw 1 (Fundamenty).

**Kolejne kroki**:
1. Zbieraj dane przez 7-30 dni
2. Użyj pattern detection do analizy
3. Eksportuj dane jeśli potrzebujesz
4. Przygotuj się na Zestaw 2 (AI Agents)!
