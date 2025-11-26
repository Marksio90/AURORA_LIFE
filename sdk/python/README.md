# AURORA_LIFE Python SDK

Official Python SDK for the AURORA_LIFE API.

## Installation

```bash
pip install aurora-life-sdk
```

## Quick Start

```python
from aurora_life_sdk import AuroraLifeClient

# Initialize client
client = AuroraLifeClient(api_key="your-api-key")

# Create a life event
event = client.events.create(
    event_type="sleep",
    title="Good night sleep",
    event_time="2024-01-01T23:00:00Z",
    event_data={"duration_hours": 8, "quality": "excellent"}
)

# Get predictions
energy_prediction = client.predictions.energy(user_id=1)
mood_prediction = client.predictions.mood(user_id=1)

# Get AI insights
insights = client.insights.generate(
    user_id=1,
    context="health"
)
```

## Features

- 🔐 Authentication (JWT tokens)
- 📊 Event management
- 🤖 AI predictions (energy, mood)
- 💡 Personalized insights
- 📈 Timeline analysis
- 🔄 Real-time WebSocket support
- ⚡ Async support

## Documentation

Full documentation: https://docs.auroralife.example.com

## License

MIT
