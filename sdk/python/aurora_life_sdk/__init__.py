"""
AURORA_LIFE Python SDK

Official Python SDK for interacting with AURORA_LIFE API.

Usage:
    from aurora_life_sdk import AuroraLifeClient

    client = AuroraLifeClient(api_key="your-api-key")

    # Create event
    event = client.events.create(
        event_type="sleep",
        title="Good night sleep",
        event_time="2024-01-01T23:00:00Z",
        event_data={"duration_hours": 8}
    )

    # Get predictions
    energy = client.predictions.energy(user_id=1)
    mood = client.predictions.mood(user_id=1)
"""

__version__ = "0.1.0"

from .client import AuroraLifeClient
from .exceptions import AuroraLifeError, AuthenticationError, ValidationError

__all__ = [
    "AuroraLifeClient",
    "AuroraLifeError",
    "AuthenticationError",
    "ValidationError",
]
