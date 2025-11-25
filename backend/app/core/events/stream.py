"""
Event Stream Manager - Redis Streams dla real-time event processing
"""
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.config import settings


class EventStreamManager:
    """
    Event Stream Manager - zarządza strumieniem zdarzeń w Redis Streams.

    Odpowiedzialności:
    - Publikowanie zdarzeń do strumienia
    - Subskrypcja i konsumpcja zdarzeń
    - Zarządzanie consumer groups
    - Real-time processing pipeline
    """

    STREAM_NAME = "aurora:life_events"
    CONSUMER_GROUP = "aurora_processors"

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None

    async def connect(self):
        """Połącz się z Redis"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Utwórz consumer group jeśli nie istnieje
            try:
                await self.redis_client.xgroup_create(
                    self.STREAM_NAME,
                    self.CONSUMER_GROUP,
                    id="0",
                    mkstream=True
                )
            except redis.ResponseError as e:
                # Group już istnieje
                if "BUSYGROUP" not in str(e):
                    raise

    async def disconnect(self):
        """Rozłącz się z Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def publish_event(
        self,
        event_id: int,
        user_id: int,
        event_type: str,
        event_time: datetime,
        data: Dict[str, Any]
    ) -> str:
        """
        Publikuje zdarzenie do strumienia Redis.

        Returns:
            Stream message ID
        """
        if not self.redis_client:
            await self.connect()

        message = {
            "event_id": str(event_id),
            "user_id": str(user_id),
            "event_type": event_type,
            "event_time": event_time.isoformat(),
            "data": json.dumps(data),
            "published_at": datetime.utcnow().isoformat()
        }

        message_id = await self.redis_client.xadd(
            self.STREAM_NAME,
            message
        )

        return message_id

    async def consume_events(
        self,
        consumer_name: str,
        count: int = 10,
        block: int = 5000
    ) -> List[Dict[str, Any]]:
        """
        Konsumuje zdarzenia ze strumienia (Consumer Group pattern).

        Args:
            consumer_name: Nazwa konsumenta
            count: Liczba zdarzeń do pobrania
            block: Czas blokowania w ms

        Returns:
            Lista zdarzeń
        """
        if not self.redis_client:
            await self.connect()

        # Czytaj nowe wiadomości
        messages = await self.redis_client.xreadgroup(
            self.CONSUMER_GROUP,
            consumer_name,
            {self.STREAM_NAME: ">"},
            count=count,
            block=block
        )

        events = []
        if messages:
            for stream_name, stream_messages in messages:
                for message_id, message_data in stream_messages:
                    event = {
                        "message_id": message_id,
                        "event_id": int(message_data["event_id"]),
                        "user_id": int(message_data["user_id"]),
                        "event_type": message_data["event_type"],
                        "event_time": datetime.fromisoformat(message_data["event_time"]),
                        "data": json.loads(message_data["data"]),
                        "published_at": datetime.fromisoformat(message_data["published_at"])
                    }
                    events.append(event)

        return events

    async def acknowledge_event(self, message_id: str):
        """Potwierdź przetworzenie zdarzenia (ACK)"""
        if not self.redis_client:
            await self.connect()

        await self.redis_client.xack(
            self.STREAM_NAME,
            self.CONSUMER_GROUP,
            message_id
        )

    async def get_pending_events(
        self,
        consumer_name: str
    ) -> List[Dict[str, Any]]:
        """Pobierz oczekujące zdarzenia dla konsumenta"""
        if not self.redis_client:
            await self.connect()

        pending = await self.redis_client.xpending_range(
            self.STREAM_NAME,
            self.CONSUMER_GROUP,
            min="-",
            max="+",
            count=100,
            consumername=consumer_name
        )

        return pending

    async def get_stream_info(self) -> Dict[str, Any]:
        """Pobierz informacje o strumieniu"""
        if not self.redis_client:
            await self.connect()

        info = await self.redis_client.xinfo_stream(self.STREAM_NAME)
        return info


# Singleton instance
event_stream = EventStreamManager()
