# Quick Start

Get up and running with AURORA_LIFE in under 5 minutes.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

## Installation

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/Marksio90/AURORA_LIFE.git
cd AURORA_LIFE

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Create your first user
docker-compose exec api python -m app.scripts.create_user \
  --email your@email.com \
  --username yourusername \
  --password YourSecurePassword123!
```

The API will be available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.core.celery_app worker -l info

# In another terminal, start Celery beat
celery -A app.core.celery_app beat -l info
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

## First Steps

### 1. Get Your API Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourusername",
    "password": "YourSecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Create Your First Event

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "sleep",
    "title": "Good night sleep",
    "event_time": "2024-01-15T23:00:00Z",
    "event_data": {
      "duration_hours": 8,
      "quality": "excellent"
    }
  }'
```

### 3. Get ML Predictions

```bash
# Get energy prediction
curl -X GET http://localhost:8000/api/v1/predictions/energy \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get mood prediction
curl -X GET http://localhost:8000/api/v1/predictions/mood \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Get AI Insights

```bash
curl -X POST http://localhost:8000/api/v1/insights/generate \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "health",
    "time_range_days": 7
  }'
```

## Using the Python SDK

```python
from aurora_life_sdk import AuroraLifeClient

# Initialize client
client = AuroraLifeClient(
    api_key="YOUR_ACCESS_TOKEN",
    base_url="http://localhost:8000/api"
)

# Create an event
event = client.events.create(
    event_type="exercise",
    title="Morning run",
    event_time="2024-01-16T07:00:00Z",
    event_data={
        "duration_minutes": 30,
        "distance_km": 5.2,
        "calories": 320
    }
)

# Get predictions
energy = client.predictions.energy()
mood = client.predictions.mood()

print(f"Predicted energy: {energy.prediction}/10")
print(f"Predicted mood: {mood.prediction}")

# Get insights
insights = client.insights.generate(context="fitness")
for insight in insights.insights:
    print(f"- {insight.title}: {insight.description}")
```

## Next Steps

- 📖 Read the [Architecture Guide](../guides/architecture.md)
- 🔐 Set up [OAuth2 authentication](../api/authentication.md)
- 🚀 Deploy to [Kubernetes](../deployment/kubernetes.md)
- 🧪 Learn about [testing](../guides/testing.md)
- 🤖 Explore [ML models](../guides/ml-models.md)

## Troubleshooting

### Database Connection Error

Make sure PostgreSQL is running and the connection string in `.env` is correct:

```bash
# Check PostgreSQL status
systemctl status postgresql  # Linux
brew services list  # macOS

# Test connection
psql -h localhost -U postgres -d aurora_life
```

### Redis Connection Error

Ensure Redis is running:

```bash
# Check Redis status
redis-cli ping  # Should return "PONG"

# Start Redis
redis-server  # Or use your system's service manager
```

### Celery Worker Not Processing Jobs

Check worker logs:

```bash
# If using Docker
docker-compose logs -f celery-worker

# If running locally
# Check the terminal where celery worker is running
```

## Getting Help

If you encounter any issues:

1. Check the [FAQ](../guides/faq.md)
2. Search [GitHub Issues](https://github.com/Marksio90/AURORA_LIFE/issues)
3. Ask in [GitHub Discussions](https://github.com/Marksio90/AURORA_LIFE/discussions)
