"""
Main SDK client
"""
from typing import Optional
import httpx

from .resources.events import EventsResource
from .resources.users import UsersResource
from .resources.predictions import PredictionsResource
from .resources.insights import InsightsResource


class AuroraLifeClient:
    """
    Main client for AURORA_LIFE API.

    Args:
        api_key: API key for authentication (or JWT token)
        base_url: API base URL (default: https://api.auroralife.example.com)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.auroralife.example.com",
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Initialize HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"aurora-life-sdk-python/0.1.0"
            },
            timeout=timeout
        )

        # Initialize resource clients
        self.events = EventsResource(self._client)
        self.users = UsersResource(self._client)
        self.predictions = PredictionsResource(self._client)
        self.insights = InsightsResource(self._client)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close HTTP client."""
        self._client.close()
