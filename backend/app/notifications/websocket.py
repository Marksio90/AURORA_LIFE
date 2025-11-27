"""
WebSocket Manager

Manages WebSocket connections for real-time notifications.
"""
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Features:
    - Multiple connections per user
    - Broadcast to specific users
    - Ping/pong for connection health
    - Automatic cleanup of disconnected clients
    """

    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> user_id mapping
        self.connection_user_map: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Accept and register new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        # Add to active connections
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_user_map[websocket] = user_id

        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connected",
                "message": "Connected to notification service",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket
        )

    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
        """
        user_id = self.connection_user_map.get(websocket)

        if user_id:
            # Remove from active connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)

                # Remove user entry if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Remove from mapping
            del self.connection_user_map[websocket]

            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to specific WebSocket connection.

        Args:
            message: Message dict
            websocket: Target WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            # Disconnect on error
            self.disconnect(websocket)

    async def send_to_user(self, message: dict, user_id: str):
        """
        Send message to all connections of a specific user.

        Args:
            message: Message dict
            user_id: Target user ID
        """
        if user_id not in self.active_connections:
            logger.debug(f"No active connections for user {user_id}")
            return

        # Get all connections for user
        connections = self.active_connections[user_id].copy()

        # Send to all connections
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_to_all(self, message: dict):
        """
        Broadcast message to all connected users.

        Args:
            message: Message dict
        """
        disconnected = []

        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_notification(self, user_id: str, notification: dict):
        """
        Send new notification event to user.

        Args:
            user_id: User ID
            notification: Notification data
        """
        message = {
            "type": "notification",
            "event": "new_notification",
            "data": notification,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self.send_to_user(message, user_id)

    async def send_ping(self, websocket: WebSocket):
        """
        Send ping to check connection health.

        Args:
            websocket: WebSocket connection
        """
        await self.send_personal_message(
            {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket
        )

    async def handle_message(self, websocket: WebSocket, data: str):
        """
        Handle incoming WebSocket message.

        Args:
            websocket: WebSocket connection
            data: Message data (JSON string)
        """
        try:
            message = json.loads(data)
            message_type = message.get("type")

            if message_type == "pong":
                # Pong received, connection is alive
                logger.debug(f"Pong received from {self.connection_user_map.get(websocket)}")

            elif message_type == "ping":
                # Send pong back
                await self.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket
                )

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    def get_active_users_count(self) -> int:
        """Get count of users with active connections"""
        return len(self.active_connections)

    def get_total_connections_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(connections) for connections in self.active_connections.values())

    def is_user_connected(self, user_id: str) -> bool:
        """Check if user has any active connections"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global WebSocket manager instance
websocket_manager = WebSocketConnectionManager()
