"""
Notification API Endpoints

API routes for notifications, preferences, and real-time updates.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.notifications.service import NotificationService
from app.notifications.websocket import websocket_manager
from app.notifications.schemas import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationList, NotificationType, BulkNotificationAction,
    BulkActionResponse, NotificationStats,
    NotificationPreferencesUpdate, NotificationPreferencesResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ==================== NOTIFICATION ENDPOINTS ====================

@router.get("", response_model=NotificationList)
async def get_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    notification_type: Optional[NotificationType] = Query(default=None),
    include_dismissed: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user notifications with pagination.

    Query parameters:
    - page: Page number (1-indexed)
    - page_size: Items per page (max 100)
    - unread_only: Return only unread notifications
    - notification_type: Filter by type
    - include_dismissed: Include dismissed notifications
    """
    service = NotificationService(db)

    return service.get_user_notifications(
        user_id=str(current_user.id),
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        notification_type=notification_type,
        include_dismissed=include_dismissed,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get single notification by ID"""
    service = NotificationService(db)

    notification = service.get_notification(
        notification_id=notification_id,
        user_id=str(current_user.id),
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse.model_validate(notification)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark notification as read"""
    service = NotificationService(db)

    notification = service.mark_as_read(
        notification_id=notification_id,
        user_id=str(current_user.id),
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse.model_validate(notification)


@router.post("/read-all")
async def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read"""
    service = NotificationService(db)

    affected = service.mark_all_as_read(user_id=str(current_user.id))

    return {
        "success": True,
        "affected_count": affected,
        "message": f"Marked {affected} notifications as read",
    }


@router.post("/{notification_id}/dismiss", response_model=NotificationResponse)
async def dismiss_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss notification"""
    service = NotificationService(db)

    notification = service.dismiss_notification(
        notification_id=notification_id,
        user_id=str(current_user.id),
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse.model_validate(notification)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete notification"""
    service = NotificationService(db)

    success = service.delete_notification(
        notification_id=notification_id,
        user_id=str(current_user.id),
    )

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {
        "success": True,
        "message": "Notification deleted",
    }


@router.post("/bulk", response_model=BulkActionResponse)
async def bulk_notification_action(
    action: BulkNotificationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Perform bulk action on notifications.

    Actions:
    - mark_read: Mark as read
    - mark_unread: Mark as unread
    - dismiss: Dismiss notifications
    - delete: Delete notifications
    """
    service = NotificationService(db)

    affected = service.bulk_action(
        action=action,
        user_id=str(current_user.id),
    )

    return BulkActionResponse(
        success=True,
        affected_count=affected,
        message=f"Action '{action.action}' completed on {affected} notifications",
    )


@router.get("/stats/summary", response_model=NotificationStats)
async def get_notification_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get notification statistics.

    Returns:
    - Total notifications
    - Unread count
    - Breakdown by type and priority
    - Recent activity (7d, 30d)
    """
    service = NotificationService(db)

    return service.get_statistics(user_id=str(current_user.id))


# ==================== PREFERENCES ENDPOINTS ====================

@router.get("/preferences/me", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user notification preferences"""
    service = NotificationService(db)

    preferences = service.get_or_create_preferences(user_id=str(current_user.id))

    return NotificationPreferencesResponse.model_validate(preferences)


@router.put("/preferences/me", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update notification preferences.

    Controls:
    - Email/Push/In-app channels
    - Per-type channel preferences
    - Quiet hours
    - Daily digest
    - Weekly summary
    """
    service = NotificationService(db)

    preferences = service.update_preferences(
        user_id=str(current_user.id),
        preferences_data=preferences_update.model_dump(exclude_unset=True),
    )

    return NotificationPreferencesResponse.model_validate(preferences)


# ==================== WEBSOCKET ENDPOINT ====================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time notifications.

    Connect with authentication token as query parameter:
    ws://localhost:8000/api/v1/notifications/ws?token=YOUR_TOKEN

    Message types:
    - notification: New notification event
    - ping/pong: Connection health check
    - connected: Connection established
    """
    # TODO: Verify token and get user
    # For now, extract user_id from token (implement proper auth)
    try:
        # This is a placeholder - implement proper JWT verification
        user_id = "user-123"  # Extract from token

        # Connect WebSocket
        await websocket_manager.connect(websocket, user_id)

        try:
            while True:
                # Receive message
                data = await websocket.receive_text()

                # Handle message
                await websocket_manager.handle_message(websocket, data)

        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)

    except Exception as e:
        websocket_manager.disconnect(websocket)
        await websocket.close(code=1008, reason=str(e))


# ==================== ADMIN/TESTING ENDPOINTS ====================

@router.post("/test/create", response_model=NotificationResponse, include_in_schema=False)
async def create_test_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create test notification (for development/testing).

    This endpoint is hidden from schema in production.
    """
    # Ensure user can only create notifications for themselves
    if str(notification.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Cannot create notifications for other users")

    service = NotificationService(db)

    notif = service.create_notification(notification_data=notification)

    # Send via WebSocket if user is connected
    await websocket_manager.send_notification(
        user_id=str(current_user.id),
        notification=NotificationResponse.model_validate(notif).model_dump(),
    )

    return NotificationResponse.model_validate(notif)
