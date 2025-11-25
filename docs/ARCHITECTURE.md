# Aurora Life Compass - Architektura

## Przegląd

Aurora Life Compass to zaawansowany osobisty "silnik predykcji życia", który buduje cyfrowego bliźniaka użytkownika i wykorzystuje AI do optymalizacji decyzji życiowych.

## Status implementacji

### ✅ Zestaw 1 - Fundamenty (GOTOWE)

Wszystkie podstawowe moduły są zaimplementowane i działają:

1. **Core Identity Layer** - Cyfrowy bliźniak użytkownika
2. **Life Event Stream (LES)** - System rejestracji zdarzeń życiowych
3. **Behavioral Timeline Engine** - Analiza wzorców i cykli
4. **Data Vault** - Bezpieczne przechowywanie danych

### 🔜 Zestaw 2 - Sztuczna Inteligencja Życia (PLANOWANE)

- Aurora Agents (7 agentów AI)
- DataGenius (zaawansowane ML/DS)
- What-If Engine (symulacje scenariuszy)
- Life Reinforcement System (uczenie ze wzmocnieniem)

### 🔜 Zestaw 3 - Orkiestracja (PLANOWANE)

- FlowOS-style Orchestrator
- LLM Integration Hub (OpenAI/Claude)
- External API Integrations
- UI Dashboard

---

## Architektura techniczna

### Stack technologiczny

```
Backend:
├── FastAPI (Python 3.11+)
├── SQLAlchemy (async ORM)
├── PostgreSQL (JSONB dla flexibility)
├── Redis Streams (real-time events)
├── Pydantic (validation)
└── NumPy/Pandas (analityka)

Przyszłość (Zestaw 2-3):
├── scikit-learn, TensorFlow/PyTorch (ML)
├── OpenAI/Anthropic API (LLM)
├── React/Next.js (UI)
└── Docker/K8s (deployment)
```

### Struktura projektu

```
aurora-life-compass/
├── backend/
│   ├── app/
│   │   ├── core/                    # Moduły biznesowe
│   │   │   ├── identity/           # Core Identity Layer
│   │   │   │   └── service.py      # Zarządzanie profilem użytkownika
│   │   │   ├── events/             # Life Event Stream
│   │   │   │   ├── service.py      # CRUD dla zdarzeń
│   │   │   │   └── stream.py       # Redis Streams manager
│   │   │   ├── timeline/           # Behavioral Timeline Engine
│   │   │   │   ├── service.py      # CRUD dla timeline
│   │   │   │   └── analyzer.py     # Pattern detection
│   │   │   └── vault/              # Data Vault
│   │   │       └── service.py      # Export, archiwizacja
│   │   ├── api/                    # REST API endpoints
│   │   │   ├── users.py
│   │   │   ├── events.py
│   │   │   ├── timeline.py
│   │   │   └── vault.py
│   │   ├── models/                 # Database models (SQLAlchemy)
│   │   │   ├── user.py
│   │   │   ├── life_event.py
│   │   │   └── timeline.py
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── database.py             # Database setup
│   │   ├── config.py               # Configuration
│   │   └── main.py                 # FastAPI app
│   └── requirements.txt
├── docs/                           # Dokumentacja
└── docker-compose.yml
```

---

## Moduły podstawowe (Zestaw 1)

### 1. Core Identity Layer

**Cel**: Zarządzanie cyfrowym bliźniakiem użytkownika

**Komponenty**:
- `User` model - podstawowe dane + profile_data (JSONB)
- `IdentityService` - logika biznesowa
- Metryki życiowe: health_score, energy_score, mood_score, productivity_score

**API Endpoints**:
```
POST   /api/users              - Utwórz użytkownika
GET    /api/users/{id}         - Pobierz profil
PUT    /api/users/{id}         - Aktualizuj profil
GET    /api/users/{id}/digital-twin - Pełny cyfrowy bliźniak
```

**Dane przechowywane**:
```json
{
  "goals": ["Zwiększyć produktywność", "Poprawić zdrowie"],
  "values": ["rodzina", "rozwój", "zdrowie"],
  "preferences": {
    "work_hours": "9-17",
    "sleep_target": 8
  },
  "life_state": {
    "health": {},
    "relationships": {},
    "finances": {},
    "career": {},
    "personal_growth": {}
  }
}
```

---

### 2. Life Event Stream (LES)

**Cel**: Rejestracja wszystkich zdarzeń życiowych w czasie rzeczywistym

**Komponenty**:
- `LifeEvent` model - elastyczna struktura (event_data jako JSONB)
- `LifeEventService` - CRUD operacje
- `EventStreamManager` - Redis Streams dla real-time processing

**Typy zdarzeń**:
- `sleep` - sen
- `activity`, `exercise` - aktywność fizyczna
- `emotion` - emocje, nastrój
- `work` - praca, zadania
- `social` - interakcje społeczne
- `health` - zdrowie
- `finance` - finanse

**API Endpoints**:
```
POST   /api/events             - Utwórz zdarzenie
GET    /api/events             - Lista zdarzeń (filtry: type, days)
GET    /api/events/{id}        - Pobierz zdarzenie
PUT    /api/events/{id}        - Aktualizuj zdarzenie
DELETE /api/events/{id}        - Usuń zdarzenie
GET    /api/events/stats/summary - Statystyki
```

**Przykład zdarzenia**:
```json
{
  "event_type": "sleep",
  "title": "Nocny sen",
  "event_time": "2025-11-24T23:00:00Z",
  "duration_minutes": 450,
  "event_data": {
    "quality": 8,
    "deep_sleep_minutes": 120,
    "rem_minutes": 90
  },
  "tags": ["regular", "good_quality"]
}
```

**Redis Streams**:
- Stream name: `aurora:life_events`
- Consumer group: `aurora_processors`
- Real-time publikowanie każdego zdarzenia
- Podstawa do przyszłych agentów AI (Zestaw 2)

---

### 3. Behavioral Timeline Engine

**Cel**: Wykrywanie wzorców, cykli, anomalii i trendów z life events

**Komponenty**:
- `TimelineEntry` model - przetworzone insights
- `TimelineService` - CRUD dla timeline
- `PatternAnalyzer` - algorytmy wykrywania wzorców

**Typy wpisów timeline**:
- `pattern` - wykryty wzorzec (np. regularny sen)
- `cycle` - cykl (rytm życiowy)
- `anomaly` - anomalia (odstępstwo od normy)
- `trend` - trend (wzrost/spadek w czasie)
- `milestone` - kamień milowy
- `insight` - wygenerowany insight

**API Endpoints**:
```
POST   /api/timeline           - Utwórz wpis
GET    /api/timeline           - Lista wpisów
GET    /api/timeline/patterns/detect - Wykryj wzorce
GET    /api/timeline/insights/recent - Ostatnie insights
GET    /api/timeline/summary/period  - Podsumowanie
```

**Algorytmy wykrywania (PatternAnalyzer)**:

1. **Sleep Pattern Detection**
   - Średnia długość snu
   - Regularność (odchylenie standardowe)
   - Preferowana pora snu
   - Confidence score

2. **Activity Pattern Detection**
   - Częstotliwość aktywności
   - Preferowane dni tygodnia
   - Consistency score

3. **Anomaly Detection**
   - Z-score detection (>2σ)
   - Identyfikacja wartości odstających

4. **Trend Detection**
   - Regresja liniowa
   - Kierunek trendu (improving/declining/stable)
   - R² confidence

**Przykład wzorca**:
```json
{
  "type": "sleep_cycle",
  "avg_duration_hours": 7.5,
  "regularity_score": 0.85,
  "avg_bedtime_hour": 23.0,
  "confidence": 0.92
}
```

---

### 4. Data Vault

**Cel**: Bezpieczne przechowywanie i zarządzanie pełną historią życia

**Komponenty**:
- `DataVaultService` - eksport, statystyki, usuwanie danych

**Funkcje**:
1. **Export użytkownika** (GDPR compliance)
   - Pełny eksport profilu + events + timeline
   - Format JSON
   - Filtry czasowe

2. **Statystyki**
   - Liczba zdarzeń, wpisów timeline
   - Rozkład typów zdarzeń
   - Okres śledzenia

3. **Usuwanie danych** (GDPR right to erasure)
   - Kasowanie events, timeline
   - Opcjonalne usunięcie konta

4. **Archiwizacja**
   - Identyfikacja starych danych (>365 dni)
   - Placeholder dla cold storage

**API Endpoints**:
```
GET    /api/vault/export/{user_id}   - Eksport danych
GET    /api/vault/summary/{user_id}  - Podsumowanie
DELETE /api/vault/user/{user_id}     - Usuń dane (GDPR)
GET    /api/vault/archive/{user_id}  - Info o archiwizacji
```

---

## Baza danych

### PostgreSQL Schema

**users** - Profile użytkowników
```sql
id              SERIAL PRIMARY KEY
email           VARCHAR UNIQUE NOT NULL
username        VARCHAR UNIQUE NOT NULL
hashed_password VARCHAR NOT NULL
full_name       VARCHAR
date_of_birth   TIMESTAMP
timezone        VARCHAR DEFAULT 'UTC'
profile_data    JSONB DEFAULT '{}'
health_score    FLOAT DEFAULT 0.0
energy_score    FLOAT DEFAULT 0.0
mood_score      FLOAT DEFAULT 0.0
productivity_score FLOAT DEFAULT 0.0
settings        JSONB DEFAULT '{}'
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP
last_active     TIMESTAMP
```

**life_events** - Zdarzenia życiowe
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER NOT NULL REFERENCES users(id)
event_type      VARCHAR NOT NULL
event_category  VARCHAR
title           VARCHAR NOT NULL
description     VARCHAR
event_data      JSONB DEFAULT '{}'
event_time      TIMESTAMP NOT NULL
duration_minutes INTEGER
end_time        TIMESTAMP
impact_score    FLOAT
energy_impact   FLOAT
mood_impact     FLOAT
tags            JSONB DEFAULT '[]'
context         JSONB DEFAULT '{}'
source          VARCHAR DEFAULT 'manual'
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP

INDEX idx_user_event_time (user_id, event_time)
INDEX idx_user_event_type_time (user_id, event_type, event_time)
```

**timeline_entries** - Oś czasu z wzorcami
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER NOT NULL REFERENCES users(id)
entry_type      VARCHAR NOT NULL
start_time      TIMESTAMP NOT NULL
end_time        TIMESTAMP NOT NULL
title           VARCHAR NOT NULL
description     VARCHAR
analysis_data   JSONB DEFAULT '{}'
confidence_score FLOAT
importance_score FLOAT
related_event_ids JSONB DEFAULT '[]'
is_recurring    BOOLEAN DEFAULT FALSE
is_significant  BOOLEAN DEFAULT FALSE
tags            JSONB DEFAULT '[]'
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP

INDEX idx_user_timeline_time (user_id, start_time)
INDEX idx_user_timeline_type (user_id, entry_type)
```

### Redis

**Streams**:
- `aurora:life_events` - Stream zdarzeń życiowych
- Consumer group: `aurora_processors`

**Struktura wiadomości**:
```json
{
  "event_id": "123",
  "user_id": "456",
  "event_type": "sleep",
  "event_time": "2025-11-24T23:00:00Z",
  "data": "{...}",
  "published_at": "2025-11-25T07:00:00Z"
}
```

---

## Przepływ danych

### 1. Rejestracja zdarzenia

```
User → POST /api/events
  ↓
LifeEventService.create_event()
  ↓
PostgreSQL: INSERT life_events
  ↓
EventStreamManager.publish_event()
  ↓
Redis Stream: aurora:life_events
  ↓
[Przyszłość: Aurora Agents konsumują stream]
```

### 2. Analiza wzorców

```
User → GET /api/timeline/patterns/detect?days=30
  ↓
LifeEventService.get_recent_events()
  ↓
PatternAnalyzer.detect_*_pattern()
  ↓
Zwróć wykryte wzorce
```

### 3. Eksport danych (GDPR)

```
User → GET /api/vault/export/{user_id}
  ↓
DataVaultService.export_user_data()
  ↓
Query: users + life_events + timeline_entries
  ↓
Zwróć kompletny JSON export
```

---

## Bezpieczeństwo

### Obecnie zaimplementowane:
- Haszowanie haseł (bcrypt via passlib)
- CORS middleware
- Environment variables dla sekretów

### Planowane (Zestaw 3):
- JWT authentication
- Role-based access control
- Rate limiting
- Encryption at rest (sensitive data)
- Audit logging

---

## Skalowanie

### Obecna architektura:
- Async PostgreSQL (asyncpg)
- Redis Streams dla real-time processing
- Horizontally scalable (stateless API)

### Przyszłe optymalizacje:
- Read replicas dla PostgreSQL
- Redis Cluster
- Caching layer (Redis)
- Message queue dla długich zadań (Celery)
- Vector database dla embeddings (Pinecone/FAISS)

---

## Roadmap

### ✅ Faza 1 - Fundamenty (GOTOWE)
- Core Identity Layer
- Life Event Stream
- Behavioral Timeline Engine
- Data Vault
- REST API
- Docker setup

### 🔜 Faza 2 - Sztuczna Inteligencja (Q1 2026)
- **DataGenius**: ML models dla predykcji
- **Aurora Agents**: 7 wyspecjalizowanych agentów AI
- **What-If Engine**: Symulacje scenariuszy
- **Life Reinforcement System**: Deep Q-Learning

### 🔜 Faza 3 - Orkiestracja (Q2 2026)
- **FlowOS Orchestrator**: Multi-agent coordination
- **LLM Integration**: OpenAI/Claude API
- **External APIs**: Google Calendar, Wearables, etc.
- **UI Dashboard**: React/Next.js interface

### 🔜 Faza 4 - Production (Q3 2026)
- Authentication & Authorization
- Advanced security
- Monitoring & Observability
- CI/CD pipeline
- Production deployment

---

## Przykłady użycia

### Scenariusz 1: Nowy użytkownik

```bash
# 1. Utwórz użytkownika
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jan@example.com",
    "username": "jan",
    "password": "secure123",
    "full_name": "Jan Kowalski",
    "timezone": "Europe/Warsaw"
  }'

# 2. Dodaj zdarzenie snu
curl -X POST "http://localhost:8000/api/events?user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "sleep",
    "title": "Nocny sen",
    "event_time": "2025-11-24T23:00:00Z",
    "duration_minutes": 480,
    "event_data": {
      "quality": 9,
      "deep_sleep_minutes": 140
    }
  }'

# 3. Pobierz ostatnie zdarzenia
curl "http://localhost:8000/api/events?user_id=1&days=7"

# 4. Wykryj wzorce (po zebraniu danych)
curl "http://localhost:8000/api/timeline/patterns/detect?user_id=1&days=30"
```

### Scenariusz 2: Analiza wzorców życiowych

Po 30 dniach zbierania danych:
- System automatycznie wykrywa regularny wzorzec snu (23:00-7:00)
- Identyfikuje preferowane dni na aktywność (wtorek, czwartek, sobota)
- Wykrywa anomalie (np. krótki sen w piątek)
- Generuje trend energii (wzrost o 15% w ostatnim miesiącu)

---

## Referencje

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Pydantic](https://docs.pydantic.dev/)
