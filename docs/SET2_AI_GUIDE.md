# Aurora Life Compass - Zestaw 2: AI & ML Guide

## Przegląd

Zestaw 2 wprowadza zaawansowaną sztuczną inteligencję do platformy Aurora Life Compass:

1. **DataGenius** - Feature engineering i modele ML
2. **Aurora Agents** - 7 wyspecjalizowanych agentów AI
3. **What-If Engine** - Symulacje scenariuszy przyszłości

---

## 1. DataGenius

### Czym jest DataGenius?

DataGenius to serce AI platformy - przekształca surowe Life Events w cechy ML i generuje predykcje.

### Feature Engineering

**30+ cech** wyekstraktowanych z Life Events:
- **Sleep**: avg duration, regularity, quality, frequency
- **Activity**: frequency, duration, consistency, intensity
- **Emotion**: positive ratio, volatility, intensity, trend
- **Work**: hours/week, focus level, productivity, deep work ratio
- **Social**: interactions/week, quality, time spent
- **Health**: energy level, energy trend, stress level
- **Temporal**: events count, events/day, weekend ratio
- **Cross-domain**: work-life balance, life diversity, overall impacts

### API Endpoints

#### Analiza wzorców
```bash
GET /api/ai/analyze/{user_id}?days=30
```

Zwraca:
- Wszystkie wyekstraktowane cechy (features)
- Insights (spostrzeżenia tekstowe)
- Scores (health, mood, productivity, energy, overall_wellbeing)

#### Predykcja energii
```bash
GET /api/ai/predict/energy/{user_id}?time_of_day=morning
```

Przewiduje poziom energii dla danej pory dnia.

#### Predykcja nastroju
```bash
GET /api/ai/predict/mood/{user_id}
```

Przewiduje nastrój na podstawie historii emocji.

#### Rekomendacje
```bash
GET /api/ai/recommend/{user_id}?goal=energy
```

Goals: `energy`, `mood`, `productivity`, `balance`

---

## 2. Aurora Agents

### 7 Wyspecjalizowanych Agentów

#### 1. **Decision Agent**
- **Rola**: Wybiera najlepsze ścieżki działania
- **Analiza**: Ocenia decyzje (sen, aktywność, work-life balance)
- **Output**: Lista decyzji z priorytetem i oczekiwaną korzyścią

#### 2. **Prediction Agent**
- **Rola**: Modele prognostyczne
- **Analiza**: Przewiduje energię, nastrój, produktywność
- **Output**: Predykcje na przyszłość z confidence

#### 3. **Mood Agent**
- **Rola**: Analiza emocji i nastroju
- **Analiza**: Sentiment, influencing factors
- **Output**: Mood score + rekomendacje poprawy nastroju

#### 4. **Health Agent**
- **Rola**: Energia i regeneracja
- **Analiza**: Health score, sleep quality, stress level
- **Output**: Health status + zdrowotne rekomendacje

#### 5. **Time Agent**
- **Rola**: Harmonogram i produktywność
- **Analiza**: Alokacja czasu, efficiency score, deep work ratio
- **Output**: Time management recommendations

#### 6. **Relationships Agent**
- **Rola**: Interakcje społeczne
- **Analiza**: Social health, interaction frequency/quality
- **Output**: Social recommendations

#### 7. **Growth Agent**
- **Rola**: Postęp celów i rozwój osobisty
- **Analiza**: Progress areas (health, productivity, mood, energy)
- **Output**: Obszary do rozwoju + strengths

### Orchestrator

**Agent Orchestrator** uruchamia wszystkich 7 agentów **równolegle** (async):

```bash
GET /api/ai/agents/run-all/{user_id}
```

Zwraca:
- Wyniki każdego agenta
- Zagregowane insights
- Priority actions (top 5)
- Overall recommendation

---

## 3. What-If Engine

### Symulacje scenariuszy "Co jeśli"

What-If Engine pozwala testować wpływ zmian stylu życia **przed** ich wprowadzeniem.

### Dostępne scenariusze

#### 1. Increase Sleep
```json
{
  "type": "increase_sleep",
  "value": 1.5,
  "description": "Co jeśli będę spać 1.5h dłużej?"
}
```

#### 2. Increase Activity
```json
{
  "type": "increase_activity",
  "value": 3.0,
  "description": "Co jeśli zacznę ćwiczyć 3x w tygodniu?"
}
```

#### 3. Reduce Work Hours
```json
{
  "type": "reduce_work_hours",
  "value": 10.0,
  "description": "Co jeśli zmniejszę godziny pracy o 10h/tydzień?"
}
```

#### 4. Increase Social
```json
{
  "type": "increase_social",
  "value": 2.0,
  "description": "Co jeśli zwiększę spotkania z przyjaciółmi o 2x/tydzień?"
}
```

#### 5. Improve Work-Life Balance
```json
{
  "type": "improve_work_life_balance",
  "value": 0.3,
  "description": "Co jeśli poświęcę więcej czasu na życie prywatne?"
}
```

### API

```bash
POST /api/ai/whatif/simulate/{user_id}
Content-Type: application/json

{
  "type": "increase_sleep",
  "value": 1.0
}
```

Zwraca:
- **Baseline scores** (obecny stan)
- **Predicted scores** (po zmianach)
- **Improvements** (szczegółowe zmiany)
- **Expected benefits** (korzyści tekstowo)
- **Recommendation** (czy warto)

### Gotowe szablony

```bash
GET /api/ai/whatif/templates
```

Zwraca 5 gotowych szablonów scenariuszy.

---

## Przykłady użycia

### Scenariusz 1: Kompleksowa analiza AI

```bash
# Krok 1: Analiza wzorców
curl http://localhost:8000/api/ai/analyze/1?days=30

# Krok 2: Uruchom wszystkich agentów
curl http://localhost:8000/api/ai/agents/run-all/1

# Krok 3: Sprawdź predykcje
curl http://localhost:8000/api/ai/predict/energy/1?time_of_day=morning
curl http://localhost:8000/api/ai/predict/mood/1

# Krok 4: Otrzymaj rekomendacje
curl http://localhost:8000/api/ai/recommend/1?goal=energy
```

### Scenariusz 2: Testowanie zmian (What-If)

```bash
# Testuję: co jeśli zwiększę aktywność?
curl -X POST http://localhost:8000/api/ai/whatif/simulate/1 \
  -H "Content-Type: application/json" \
  -d '{
    "type": "increase_activity",
    "value": 3.0
  }'

# Odpowiedź pokazuje:
# - Baseline: health_score = 0.65
# - Predicted: health_score = 0.78
# - Improvement: +20%
# - Recommendation: "✅ Zdecydowanie WARTO!"
```

### Scenariusz 3: Porównanie wielu scenariuszy

```bash
# Scenario A: Więcej snu
curl -X POST .../whatif/simulate/1 -d '{"type":"increase_sleep","value":1.5}'

# Scenario B: Więcej aktywności
curl -X POST .../whatif/simulate/1 -d '{"type":"increase_activity","value":3.0}'

# Scenario C: Lepsza równowaga
curl -X POST .../whatif/simulate/1 -d '{"type":"improve_work_life_balance","value":0.3}'

# Porównaj wyniki i wybierz najlepszy!
```

---

## Integracja z Zestawem 1

Zestaw 2 wykorzystuje dane z Zestawu 1:
- **Life Events** → Feature Extraction (DataGenius)
- **Timeline patterns** → Agent insights
- **User profile** → Personalizacja rekomendacji

Pipeline:
```
Life Events → DataGenius → Features → Aurora Agents → Insights
                                   ↓
                            What-If Engine → Simulations
```

---

## Architektura techniczna

### DataGenius
- **FeatureExtractor**: 30+ cech z Life Events
- **Modele predykcyjne**: Energy, Mood (heurystyczne + ML-ready)
- **Recommender**: Goal-based recommendations

### Aurora Agents
- **BaseAgent**: ABC dla wszystkich agentów
- **AgentOrchestrator**: Async parallel execution
- **7 specialized agents**: Każdy z własną specjalizacją

### What-If Simulator
- **Scenario application**: Modyfikacja features
- **Score recalculation**: Nowe metryki
- **Comparison engine**: Baseline vs Predicted

---

## Future enhancements (Zestaw 3)

- **LLM Integration**: GPT-4/Claude dla NLU insights
- **Advanced ML models**: XGBoost, LSTM dla lepszych predykcji
- **Reinforcement Learning**: Deep Q-Network dla optymalizacji decyzji
- **UI Dashboard**: Wizualizacja wszystkich wyników

---

## Podsumowanie

**Zestaw 2** dodaje potężne możliwości AI:

✅ **DataGenius** - Inteligentna analiza i feature engineering
✅ **7 Aurora Agents** - Specjalistyczne insights równolegle
✅ **What-If Engine** - Testowanie zmian przed implementacją

**Platforma jest gotowa do zaawansowanej analizy życia i predykcji!** 🚀
