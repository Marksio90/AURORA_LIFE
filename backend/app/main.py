"""
Aurora Life Compass - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.core.events.stream import event_stream

# Import routers
from app.api import users, events, timeline, vault, ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Aurora Life Compass...")
    await init_db()
    print("✅ Database initialized")

    # Connect to Redis
    await event_stream.connect()
    print("✅ Redis Stream connected")

    yield

    # Shutdown
    await event_stream.disconnect()
    print("👋 Aurora Life Compass shutdown complete")


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

# Include routers
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
