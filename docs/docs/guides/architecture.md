# Architecture Overview

AURORA_LIFE is built with modern cloud-native principles, emphasizing scalability, observability, and developer experience.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                            │
│                      (Kubernetes Ingress)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼─────────┐          ┌─────────▼──────────┐
│  Frontend (3x)   │          │   API Server (3x)   │
│   Next.js 14     │          │      FastAPI        │
│  (Auto-scaled)   │          │   (Auto-scaled)     │
└──────────────────┘          └─────────┬───────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
          ┌─────────▼──────┐  ┌────────▼────────┐ ┌───────▼────────┐
          │  PostgreSQL    │  │     Redis       │ │  Celery (2x)   │
          │   (Primary)    │  │  Cache + Queue  │ │    Workers     │
          │                │  │                 │ │                │
          └────────────────┘  └─────────────────┘ └────────────────┘
                    │
          ┌─────────▼──────┐
          │  PostgreSQL    │
          │   (Replica)    │
          │  (Read-only)   │
          └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
│  - OpenAI API (GPT-4)                                           │
│  - Claude API (Opus)                                            │
│  - Prometheus (Metrics)                                         │
│  - Grafana (Dashboards)                                         │
│  - Sentry (Error Tracking)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Server (FastAPI)

**Responsibilities:**
- RESTful API endpoints (versioned: /api/v1/*)
- WebSocket connections for real-time updates
- Request validation with Pydantic V2
- JWT authentication and authorization
- Rate limiting (100 req/min per IP)
- Response caching with Redis

**Key Features:**
- Async/await for I/O operations
- Connection pooling for PostgreSQL
- Automatic API documentation (OpenAPI/Swagger)
- Structured JSON logging
- Prometheus metrics export

**Scaling:**
- Horizontal Pod Autoscaler (HPA): 3-10 replicas
- CPU target: 70%
- Memory target: 80%

### 2. Database Layer (PostgreSQL)

**Configuration:**
- Primary: Write operations
- Replica(s): Read operations (load balanced)
- Connection pool: 20-50 connections per pod
- Async SQLAlchemy 2.0 with asyncpg driver

**Schema Highlights:**
```python
# Users table
- id (UUID)
- email (unique, indexed)
- username (unique, indexed)
- password_hash (bcrypt)
- created_at, updated_at

# Events table
- id (UUID)
- user_id (FK, indexed)
- event_type (indexed)
- event_time (indexed)
- event_data (JSONB)
- created_at

# ML predictions table
- id (UUID)
- user_id (FK)
- model_type (energy|mood)
- prediction
- confidence
- created_at
```

**Migrations:**
- Alembic for schema versioning
- Automatic migrations in CI/CD
- Rollback support

### 3. Caching Layer (Redis)

**Use Cases:**

1. **Response Caching**
   - TTL: 5-60 minutes depending on endpoint
   - Invalidation on data mutations
   - Cache warming for predictions

2. **Rate Limiting**
   - Sliding window algorithm
   - Distributed state across API pods
   - Per-IP and per-user limits

3. **Session Storage**
   - Refresh token blacklist
   - Active WebSocket connections
   - Temporary computation results

4. **Message Queue**
   - Celery task broker
   - Redis Streams for event processing
   - Pub/Sub for real-time notifications

### 4. Background Workers (Celery)

**Task Types:**

1. **ML Model Training**
   - Daily retraining with new data
   - Feature engineering pipeline
   - Model evaluation and versioning
   - Schedule: Daily at 2 AM UTC

2. **Data Processing**
   - Event aggregation for timeline
   - Life score calculations
   - Pattern detection

3. **External Integrations**
   - Email sending (verification, password reset)
   - Webhook deliveries with retries
   - Third-party API syncing (Google Calendar, Fitbit)

4. **Housekeeping**
   - Old data archival
   - Cache cleanup
   - Log rotation

**Configuration:**
- Workers: 2 pods (auto-scaled based on queue length)
- Concurrency: 4 workers per pod
- Beat scheduler: 1 pod (leader election)
- Task timeout: 300 seconds
- Max retries: 3 with exponential backoff

### 5. ML Pipeline

**Architecture:**

```
User Events → Feature Engineering → Model Prediction → Caching → API Response
                      ↓
                ML Retraining (Daily)
                      ↓
                Model Registry
```

**Models:**

1. **Energy Predictor**
   - Algorithm: XGBoost Regressor
   - Features: 25 (sleep, exercise, work, mood, weather, etc.)
   - Target: Energy level (0-10)
   - Training data: Last 90 days per user
   - Metrics: MAE < 1.0, R² > 0.75

2. **Mood Predictor**
   - Algorithm: LightGBM Classifier
   - Features: 23 (similar to energy + social interactions)
   - Target: 5 mood classes (very_negative, negative, neutral, positive, very_positive)
   - Training data: Last 90 days per user
   - Metrics: Accuracy > 70%, F1 > 0.68

**Feature Engineering:**
```python
# Time-based features
- hour_of_day, day_of_week, is_weekend
- time_since_last_sleep, time_since_last_meal

# Aggregated features
- avg_sleep_last_7d, avg_exercise_last_7d
- social_events_count_last_3d

# Rolling statistics
- energy_rolling_mean_7d, energy_rolling_std_7d
- mood_trend_last_14d
```

### 6. AI Integration

**OpenAI (GPT-4):**
- Insight generation
- Mood analysis from text
- Personalized recommendations
- Natural language queries

**Claude (Opus):**
- Complex decision analysis
- What-if scenario modeling
- Long-form explanations
- Multi-step reasoning

**Rate Limiting & Costs:**
- Max 100 AI requests per user per day
- Response caching (24h for identical queries)
- Fallback to simpler models on quota exceeded

### 7. Real-time Layer

**WebSocket Architecture:**

```python
# Connection flow
Client connects → Authentication → Subscribe to topics → Receive updates

# Topics
- user:{user_id}:events (new events)
- user:{user_id}:predictions (new predictions)
- user:{user_id}:insights (new insights)
- system:announcements (platform updates)
```

**Implementation:**
- FastAPI WebSocket endpoints
- Redis Pub/Sub for message broadcasting
- Connection manager tracks active connections
- Heartbeat every 30 seconds
- Automatic reconnection on client

## Data Flow

### 1. Event Creation Flow

```
User → API → Validation → DB Write → Cache Invalidation →
  → WebSocket Broadcast → Celery Task (Async Processing) →
  → Timeline Update → ML Feature Update
```

### 2. Prediction Request Flow

```
User → API → Check Cache → (if miss) → Feature Engineering →
  → Model Prediction → Cache Result → Return Response
```

### 3. Insight Generation Flow

```
User → API → Fetch Events (last N days) → GPT-4 API →
  → Parse Response → Save to DB → Cache → WebSocket Broadcast
```

## Security Architecture

### Authentication Flow

```
1. Login: username/password → JWT access token (30min) + refresh token (7d)
2. API Request: Bearer token in Authorization header
3. Token Validation: Signature + expiry check
4. User Context: Injected into request state
5. Authorization: Role/permission check
```

### Security Layers

1. **Network Security**
   - TLS 1.3 for all connections
   - Network policies in Kubernetes
   - Private subnets for databases

2. **Application Security**
   - CORS with allowed origins
   - CSP headers
   - XSS protection headers
   - SQL injection prevention (parameterized queries)
   - Rate limiting per IP and user

3. **Data Security**
   - Passwords: bcrypt (cost factor 12)
   - Sensitive fields: AES-256 encryption
   - API keys: Hashed in database
   - Audit logging for all mutations

4. **Infrastructure Security**
   - Secrets in Kubernetes Secrets or Vault
   - Pod security policies
   - Non-root containers
   - Read-only root filesystem
   - Network segmentation

## Observability

### Metrics (Prometheus)

**Application Metrics:**
- `http_requests_total{method, endpoint, status}`
- `http_request_duration_seconds{method, endpoint}`
- `ml_prediction_duration_seconds{model_type}`
- `celery_task_duration_seconds{task_name}`
- `active_websocket_connections`

**System Metrics:**
- CPU, memory, disk usage per pod
- Database connection pool stats
- Redis memory usage
- Queue length

### Logging (Structured JSON)

```json
{
  "timestamp": "2024-01-16T10:30:45Z",
  "level": "INFO",
  "service": "api",
  "pod": "api-deployment-7f8d9c-x7k2m",
  "trace_id": "abc123...",
  "user_id": "user_456",
  "endpoint": "/api/v1/events",
  "method": "POST",
  "status_code": 201,
  "duration_ms": 45,
  "message": "Event created successfully"
}
```

**Log Aggregation:**
- ELK Stack (Elasticsearch, Logstash, Kibana) or Loki
- 30-day retention
- Full-text search
- Correlation with trace IDs

### Error Tracking (Sentry)

- Automatic error capture
- Stack traces with source code
- User context and breadcrumbs
- Release tracking
- Performance monitoring (10% sampling)

### Distributed Tracing (OpenTelemetry)

- Request tracing across services
- Database query tracing
- External API call tracing
- Spans for critical operations
- Jaeger or Tempo backend

## Deployment

### Kubernetes Resources

**Deployments:**
- `api-deployment`: 3 replicas (HPA 3-10)
- `celery-worker-deployment`: 2 replicas (HPA 2-5)
- `celery-beat-deployment`: 1 replica (no scaling)
- `frontend-deployment`: 3 replicas (HPA 3-10)

**Services:**
- `api-service`: ClusterIP for internal access
- `frontend-service`: ClusterIP
- `postgres-service`: ClusterIP
- `redis-service`: ClusterIP

**Ingress:**
- TLS termination
- Path-based routing
- Rate limiting (global)

**ConfigMaps & Secrets:**
- `api-config`: Non-sensitive configuration
- `api-secrets`: Database credentials, API keys, JWT secret

### CI/CD Pipeline

**GitHub Actions Workflow:**

```yaml
1. Code Quality
   - black, isort formatting check
   - flake8 linting
   - mypy type checking
   - bandit security scan

2. Testing
   - pytest unit tests (80% coverage required)
   - Integration tests
   - E2E tests

3. Build
   - Docker image build
   - Tag with commit SHA and branch
   - Push to container registry

4. Deploy (on main branch)
   - kubectl apply manifests
   - Rolling update strategy
   - Health check verification
   - Rollback on failure
```

## Scalability Considerations

### Current Limits
- **Users**: 100K active users
- **Events**: 10M events/day
- **API Requests**: 1000 req/s
- **WebSocket Connections**: 10K concurrent

### Scaling Strategies

1. **Horizontal Scaling**
   - API pods: 3 → 50 (based on load)
   - Worker pods: 2 → 20 (based on queue length)
   - Database: Read replicas (1 → 5)

2. **Caching**
   - Response caching (60% hit rate target)
   - Prediction caching (24h TTL)
   - CDN for static assets

3. **Database Optimization**
   - Partitioning events table by month
   - Archival of old data (> 2 years)
   - Connection pooling per pod

4. **Async Processing**
   - Non-critical operations in Celery
   - Webhook deliveries async
   - Email sending async

## Performance Targets

- **API Response Time**: P95 < 200ms
- **Prediction Latency**: P95 < 500ms
- **WebSocket Latency**: P95 < 100ms
- **Database Queries**: P95 < 50ms
- **Availability**: 99.9% uptime
- **Error Rate**: < 0.1%

## Future Architecture Enhancements

1. **Event Sourcing**: CQRS pattern for complex aggregations
2. **GraphQL**: Alternative to REST for flexible queries
3. **gRPC**: Service-to-service communication
4. **Kafka**: Replace Redis Streams for high-volume events
5. **Microservices**: Split monolith into domain services
6. **Multi-region**: Geographic distribution for low latency
7. **A/B Testing**: Feature flags and experimentation framework
