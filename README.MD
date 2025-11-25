# Aurora Life Compass

Zaawansowana platforma AI do zarządzania życiem - osobisty silnik predykcji życia.

## Architektura

Aurora Life Compass składa się z wyspecjalizowanych modułów:

### Zestaw 1 - Fundamenty (w trakcie)
- **Core Identity Layer** - Profil użytkownika i cyfrowy bliźniak
- **Life Event Stream (LES)** - Strumień zdarzeń życiowych w czasie rzeczywistym
- **Behavioral Timeline Engine** - Analiza wzorców i cykli życiowych
- **Data Vault** - Bezpieczne przechowywanie danych użytkownika

### Zestaw 2 - Sztuczna Inteligencja Życia (✅ GOTOWE)
- **DataGenius** - Feature engineering i modele ML
- **Aurora Agents** - 7 wyspecjalizowanych agentów AI (Decision, Prediction, Mood, Health, Time, Relationships, Growth)
- **What-If Engine** - Symulacje scenariuszy "co jeśli"
- **Agent Orchestrator** - Równoległa koordynacja agentów

### Zestaw 3 - Orkiestracja (planowane)
- FlowOS-style Orchestrator
- LLM Integration Hub
- External API Integrations
- UI Dashboard

## Stack technologiczny

- **Backend**: Python 3.11+ z FastAPI
- **Database**: PostgreSQL (JSONB) + Redis Streams
- **ML/AI**: scikit-learn, pandas, numpy
- **Event Processing**: Redis Streams
- **API**: REST + WebSocket

## Struktura projektu

```
aurora-life-compass/
├── backend/          # Backend API i logika biznesowa
│   ├── app/
│   │   ├── core/     # Moduły podstawowe (Identity, Events, Timeline, Vault)
│   │   ├── api/      # Endpoints REST API
│   │   └── models/   # Modele danych
├── docs/             # Dokumentacja
└── docker-compose.yml
```

## Rozpoczęcie pracy

```bash
# Uruchomienie środowiska
docker-compose up -d

# Instalacja zależności
cd backend
pip install -r requirements.txt

# Uruchomienie serwera
python main.py
```

## Status

✅ **Zestaw 1 (Fundamenty) - GOTOWE**
✅ **Zestaw 2 (AI & ML) - GOTOWE**
🚧 **Zestaw 3 (Orkiestracja) - Planowane**
