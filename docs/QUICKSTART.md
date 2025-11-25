# Aurora Life Compass - Quick Start Guide

Przewodnik szybkiego startu dla Aurora Life Compass.

## Wymagania

- Docker & Docker Compose
- Python 3.11+ (jeśli uruchamiasz lokalnie)
- Porty: 8000 (API), 5432 (PostgreSQL), 6379 (Redis)

---

## Uruchomienie z Docker Compose (ZALECANE)

### 1. Sklonuj repozytorium
```bash
cd AURORA_LIFE
```

### 2. Utwórz plik .env
```bash
cp .env.example .env
# Edytuj .env jeśli potrzeba (domyślne wartości są OK dla dev)
```

### 3. Uruchom wszystko
```bash
docker-compose up -d
```

To uruchomi:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Aurora Backend API (port 8000)

### 4. Sprawdź status
```bash
# Logi
docker-compose logs -f backend

# Health check
curl http://localhost:8000/health
```

### 5. Otwórz dokumentację API
Przejdź do: http://localhost:8000/docs

Interaktywna dokumentacja Swagger UI.

---

## Uruchomienie lokalne (bez Dockera)

### 1. Uruchom PostgreSQL i Redis

```bash
# PostgreSQL
docker run -d \
  --name aurora_postgres \
  -e POSTGRES_DB=aurora_life \
  -e POSTGRES_USER=aurora \
  -e POSTGRES_PASSWORD=aurora_dev_password \
  -p 5432:5432 \
  postgres:15-alpine

# Redis
docker run -d \
  --name aurora_redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 2. Zainstaluj zależności Python

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Uruchom serwer

```bash
python app/main.py
# lub
uvicorn app.main:app --reload
```

### 4. Sprawdź
```bash
curl http://localhost:8000/health
```

---

## Pierwsze kroki z API

### 1. Utwórz użytkownika

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123",
    "full_name": "Test User",
    "timezone": "Europe/Warsaw"
  }'
```

Odpowiedź:
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "timezone": "Europe/Warsaw",
  "profile_data": {
    "goals": [],
    "values": [],
    "preferences": {},
    "life_state": {...}
  },
  "health_score": 0.0,
  "energy_score": 0.0,
  "mood_score": 0.0,
  "productivity_score": 0.0,
  "created_at": "2025-11-25T10:00:00Z",
  "last_active": "2025-11-25T10:00:00Z"
}
```

### 2. Dodaj zdarzenie życiowe (sen)

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "sleep",
    "event_category": "wellness",
    "title": "Nocny sen",
    "description": "Dobry sen, bez przerwań",
    "event_time": "2025-11-24T23:00:00Z",
    "duration_minutes": 480,
    "event_data": {
      "quality": 8,
      "deep_sleep_minutes": 120,
      "rem_minutes": 90,
      "interruptions": 0
    },
    "tags": ["good_quality", "regular"]
  }'
```

### 3. Dodaj aktywność fizyczną

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "exercise",
    "event_category": "wellness",
    "title": "Bieganie",
    "event_time": "2025-11-25T06:30:00Z",
    "duration_minutes": 45,
    "event_data": {
      "type": "running",
      "distance_km": 7.5,
      "avg_heart_rate": 145,
      "calories": 450
    },
    "tags": ["morning", "outdoor"]
  }'
```

### 4. Dodaj emocję

```bash
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "emotion",
    "event_category": "personal",
    "title": "Bardzo dobry nastrój",
    "event_time": "2025-11-25T12:00:00Z",
    "event_data": {
      "type": "happy",
      "intensity": 9,
      "trigger": "Ukończenie ważnego projektu"
    },
    "tags": ["positive", "work_related"]
  }'
```

### 5. Pobierz ostatnie zdarzenia

```bash
curl "http://localhost:8000/api/events?user_id=1&days=7"
```

### 6. Pobierz statystyki zdarzeń

```bash
curl "http://localhost:8000/api/events/stats/summary?user_id=1&days=30"
```

Odpowiedź:
```json
{
  "total_events": 15,
  "event_types": {
    "sleep": 7,
    "exercise": 5,
    "emotion": 3
  },
  "avg_impact": 0.65,
  "total_energy_change": 2.3,
  "total_mood_change": 1.8,
  "period": {
    "start": "2025-10-26T10:00:00Z",
    "end": "2025-11-25T10:00:00Z"
  }
}
```

---

## Analiza wzorców

Po zebraniu co najmniej 7-10 dni danych:

### 1. Wykryj wzorce życiowe

```bash
curl "http://localhost:8000/api/timeline/patterns/detect?user_id=1&days=30"
```

Odpowiedź:
```json
{
  "user_id": 1,
  "analysis_period_days": 30,
  "events_analyzed": 45,
  "patterns_found": 3,
  "patterns": [
    {
      "type": "sleep_cycle",
      "avg_duration_hours": 7.8,
      "std_duration_hours": 0.6,
      "avg_bedtime_hour": 23.2,
      "regularity_score": 0.87,
      "sample_size": 15,
      "confidence": 0.92
    },
    {
      "type": "activity_pattern",
      "avg_activities_per_week": 4.2,
      "preferred_days": [
        {"day": "Wtorek", "count": 6},
        {"day": "Czwartek", "count": 5},
        {"day": "Sobota", "count": 4}
      ],
      "total_activities": 18,
      "consistency": 0.6,
      "confidence": 0.85
    },
    {
      "type": "trend",
      "metric": "energy_level",
      "direction": "improving",
      "slope": 0.012,
      "confidence": 0.78,
      "sample_size": 12,
      "time_span_days": 28.5
    }
  ]
}
```

### 2. Pobierz podsumowanie timeline

```bash
curl "http://localhost:8000/api/timeline/summary/period?user_id=1&days=30"
```

---

## Eksport danych (GDPR)

### Pełny eksport użytkownika

```bash
curl "http://localhost:8000/api/vault/export/1" > user_data_export.json
```

### Podsumowanie danych

```bash
curl "http://localhost:8000/api/vault/summary/1"
```

Odpowiedź:
```json
{
  "user_id": 1,
  "username": "testuser",
  "total_life_events": 45,
  "total_timeline_entries": 8,
  "data_span": {
    "first_event": "2025-10-26T12:00:00Z",
    "last_event": "2025-11-25T09:30:00Z",
    "days_tracked": 30
  },
  "life_metrics": {
    "health_score": 0.75,
    "energy_score": 0.82,
    "mood_score": 0.78,
    "productivity_score": 0.68
  },
  "account_age_days": 30
}
```

---

## Testowanie Redis Streams

### Sprawdź strumień Redis

```bash
# Wejdź do kontenera Redis
docker exec -it aurora_redis redis-cli

# Pokaż stream info
XINFO STREAM aurora:life_events

# Pokaż ostatnie wiadomości
XREAD COUNT 10 STREAMS aurora:life_events 0

# Pokaż consumer group
XINFO GROUPS aurora:life_events
```

---

## Przydatne komendy

### Docker Compose

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart tylko backend
docker-compose restart backend

# Logi
docker-compose logs -f backend

# Rebuild
docker-compose up -d --build
```

### PostgreSQL

```bash
# Połącz się z bazą
docker exec -it aurora_postgres psql -U aurora -d aurora_life

# Pokaż tabele
\dt

# Sprawdź użytkowników
SELECT id, username, email FROM users;

# Sprawdź zdarzenia
SELECT id, user_id, event_type, event_time FROM life_events LIMIT 10;
```

### Czyszczenie danych

```bash
# Usuń wszystkie dane użytkownika (GDPR)
curl -X DELETE "http://localhost:8000/api/vault/user/1?delete_user=true"

# Reset całej bazy (DEV ONLY!)
docker-compose down -v
docker-compose up -d
```

---

## Rozwiązywanie problemów

### Port zajęty

```bash
# Zmień port w docker-compose.yml
ports:
  - "8001:8000"  # Zamiast 8000:8000
```

### Baza nie startuje

```bash
# Sprawdź logi
docker-compose logs postgres

# Reset volumenu
docker-compose down -v
docker-compose up -d
```

### Import error w Pythonie

```bash
# Upewnij się że jesteś w katalogu backend/
cd backend

# Reinstall
pip install -r requirements.txt --force-reinstall
```

---

## Następne kroki

1. **Zbierz dane** - Dodaj zdarzenia życiowe przez 7-14 dni
2. **Analizuj wzorce** - Użyj `/api/timeline/patterns/detect`
3. **Eksperymentuj** - Testuj różne typy zdarzeń i kategorii
4. **Przygotuj się na Zestaw 2** - Aurora Agents i ML models (wkrótce!)

---

## Dokumentacja

- **Architektura**: `docs/ARCHITECTURE.md`
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Wsparcie

Jeśli napotkasz problemy:
1. Sprawdź logi: `docker-compose logs -f`
2. Sprawdź health: `curl http://localhost:8000/health`
3. Sprawdź bazę danych: PostgreSQL connection
4. Sprawdź Redis: `docker exec -it aurora_redis redis-cli ping`

Happy tracking your life! 🚀
