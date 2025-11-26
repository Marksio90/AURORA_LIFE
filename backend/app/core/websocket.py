"""
WebSocket support for real-time updates
"""
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manage WebSocket connections for real-time updates.

    Features:
    - User-specific connections
    - Broadcast to all users
    - Broadcast to specific user
    - Connection pooling
    """

    def __init__(self):
        # Map of user_id -> set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # All connections for broadcast
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept new WebSocket connection."""
        await websocket.accept()

        # Add to user-specific connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

        # Add to all connections
        self.all_connections.add(websocket)

        # Send welcome message
        await self.send_personal_message(
            {"type": "connected", "message": "Welcome to AURORA_LIFE real-time updates"},
            websocket
        )

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection."""
        # Remove from user-specific connections
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        # Remove from all connections
        self.all_connections.discard(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}", exc_info=True)

    async def send_to_user(self, message: dict, user_id: int):
        """Send message to all connections of a specific user."""
        if user_id in self.active_connections:
            # Send to all user's connections
            tasks = [
                self.send_personal_message(message, ws)
                for ws in self.active_connections[user_id]
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        tasks = [
            self.send_personal_message(message, ws)
            for ws in self.all_connections
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a user."""
        return len(self.active_connections.get(user_id, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self.all_connections)


# Global connection manager instance
manager = ConnectionManager()


# Message types for real-time updates
class WSMessageType:
    """WebSocket message types."""
    # Events
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_DELETED = "event_deleted"

    # Insights
    INSIGHT_GENERATED = "insight_generated"
    PATTERN_DETECTED = "pattern_detected"

    # Predictions
    PREDICTION_UPDATED = "prediction_updated"

    # Notifications
    NOTIFICATION = "notification"

    # System
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
