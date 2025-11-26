"""
Aurora Life Compass - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.core.events.stream import event_stream
from app.middleware.rate_limit import RateLimitMiddleware

# Import routers
from app.api import users, events, timeline, vault, ai, auth

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Aurora Life Compass...")
    await init_db()
    logger.info("✅ Database initialized")

    # Connect to Redis
    await event_stream.connect()
    logger.info("✅ Redis Stream connected")

    yield

    # Shutdown
    await event_stream.disconnect()
    logger.info("👋 Aurora Life Compass shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Zaawansowana platforma AI do zarządzania życiem - osobisty silnik predykcji życia",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting for expensive ML endpoints
app.add_middleware(
    RateLimitMiddleware,
    rate_limit=10,  # Default: 10 requests per window
    window_seconds=60  # 1 minute window
)

# Include routers
app.include_router(auth.router, prefix="/api")  # Authentication
app.include_router(users.router)
app.include_router(events.router)
app.include_router(timeline.router)
app.include_router(vault.router)
app.include_router(ai.router)  # Zestaw 2: AI/ML


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "description": "Aurora Life Compass - Future Self OS",
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users",
            "events": "/api/events",
            "timeline": "/api/timeline",
            "vault": "/api/vault",
            "ai": "/api/ai",  # Zestaw 2
            "docs": "/docs"
        },
        "set_2_ai": {
            "datagenius": "/api/ai/analyze, /api/ai/predict, /api/ai/recommend",
            "aurora_agents": "/api/ai/agents/run-all",
            "whatif_engine": "/api/ai/whatif/simulate"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "database": "connected",
        "redis": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=settings.APP_DEBUG
    )
