"""
API v1 - Main API version
"""
from fastapi import APIRouter
from app.api.v1 import users, events, timeline, vault, ai, auth, analytics, notifications

router = APIRouter(prefix="/v1")

# Include all v1 routers
router.include_router(auth.router, tags=["auth"])
router.include_router(users.router, tags=["users"])
router.include_router(events.router, tags=["events"])
router.include_router(timeline.router, tags=["timeline"])
router.include_router(vault.router, tags=["vault"])
router.include_router(ai.router, tags=["ai"])
router.include_router(analytics.router, tags=["analytics"])
router.include_router(notifications.router, tags=["notifications"])
