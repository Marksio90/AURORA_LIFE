"""
Comprehensive health check endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from typing import Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """
    Basic health check - returns 200 if service is running.

    Use for: Kubernetes liveness probe
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "aurora-life-api"
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check - verifies dependencies are available.

    Use for: Kubernetes readiness probe

    Checks:
    - Database connectivity
    - Redis connectivity
    """
    checks = {}

    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Redis check
    try:
        from app.core.events.stream import event_stream
        if event_stream.redis:
            await event_stream.redis.ping()
            checks["redis"] = {"status": "healthy"}
        else:
            checks["redis"] = {"status": "not_connected"}
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Determine overall status
    all_healthy = all(
        check.get("status") == "healthy"
        for check in checks.values()
    )

    return {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check - service is alive and not deadlocked.

    Use for: Kubernetes liveness probe
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/detailed")
async def detailed_health(db: AsyncSession = Depends(get_db)):
    """
    Detailed health information with all system components.

    Includes:
    - Application info
    - Database status
    - Redis status
    - Disk usage
    - Memory usage
    """
    import psutil

    checks = {}

    # Application info
    checks["application"] = {
        "name": getattr(settings, 'APP_NAME', 'AURORA_LIFE'),
        "version": getattr(settings, 'APP_VERSION', '1.0.0'),
        "environment": getattr(settings, 'APP_ENV', 'development'),
        "uptime_seconds": psutil.Process().create_time()
    }

    # Database
    try:
        result = await db.execute("SELECT version()")
        version = result.scalar()
        checks["database"] = {
            "status": "healthy",
            "type": "PostgreSQL",
            "version": version
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Redis
    try:
        from app.core.events.stream import event_stream
        if event_stream.redis:
            info = await event_stream.redis.info()
            checks["redis"] = {
                "status": "healthy",
                "version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # System resources
    checks["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
