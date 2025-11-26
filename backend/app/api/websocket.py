"""
WebSocket endpoints for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.core.websocket import manager
from app.core.auth.jwt import verify_token


router = APIRouter()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str = None):
    """
    WebSocket endpoint for real-time updates.

    Usage:
        ws://localhost:8000/ws/{user_id}?token={jwt_token}

    Messages sent to clients:
    - event_created: New life event created
    - insight_generated: New AI insight available
    - pattern_detected: New pattern detected
    - prediction_updated: New prediction available
    - notification: General notification

    Client can send:
    - ping: Keep-alive message
    - subscribe: Subscribe to specific channels
    """
    # Verify token from query params
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    payload = verify_token(token)
    if not payload or int(payload.get("sub")) != user_id:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    # Connect user
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()

            # Handle client messages
            message_type = data.get("type")

            if message_type == "ping":
                # Respond to ping
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")},
                    websocket
                )

            elif message_type == "subscribe":
                # Handle channel subscription
                channels = data.get("channels", [])
                await manager.send_personal_message(
                    {"type": "subscribed", "channels": channels},
                    websocket
                )

            else:
                # Echo unknown messages
                await manager.send_personal_message(
                    {"type": "echo", "data": data},
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")

    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)
        await websocket.close(code=1011, reason="Internal error")


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": manager.get_total_connections(),
        "users_connected": len(manager.active_connections),
    }
