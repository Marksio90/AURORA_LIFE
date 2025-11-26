"""
Database configuration with optimized connection pooling.

Features:
- Async SQLAlchemy 2.0 with asyncpg
- Optimized connection pool settings
- Read replica support
- Connection health checks
- Automatic retry on connection loss
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Primary database engine (write operations)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=20,  # Default connections in pool
    max_overflow=10,  # Additional connections when pool is full
    pool_timeout=30,  # Seconds to wait for connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
    connect_args={
        "server_settings": {
            "application_name": "aurora_life_api",
            "jit": "off",  # Disable JIT for better connection performance
        },
        "command_timeout": 60,  # Query timeout in seconds
        "timeout": 10,  # Connection timeout
    },
)

# Read replica engine (optional, for read-heavy operations)
read_engine = None
if settings.DATABASE_READ_REPLICA_URL:
    read_engine = create_async_engine(
        settings.DATABASE_READ_REPLICA_URL,
        echo=settings.DEBUG,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=30,  # Larger pool for read replicas
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={
            "server_settings": {
                "application_name": "aurora_life_api_read",
                "jit": "off",
            },
            "command_timeout": 60,
            "timeout": 10,
        },
    )

# Session factories
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

AsyncReadSessionLocal = None
if read_engine:
    AsyncReadSessionLocal = async_sessionmaker(
        read_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session (write operations).

    Usage:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_read_db() -> AsyncSession:
    """
    Dependency for getting read-only database session.

    Uses read replica if configured, otherwise falls back to primary.

    Usage:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_read_db)):
            # This will use read replica if available
            ...
    """
    session_factory = AsyncReadSessionLocal if AsyncReadSessionLocal else AsyncSessionLocal

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Initialize database (create tables).

    NOTE: In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db():
    """
    Close database connections.

    Call this on application shutdown.
    """
    await engine.dispose()
    if read_engine:
        await read_engine.dispose()
    logger.info("Database connections closed")


async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# Connection pool statistics (for monitoring)
def get_pool_stats() -> dict:
    """
    Get connection pool statistics.

    Returns:
        Dictionary with pool metrics.
    """
    pool = engine.pool

    stats = {
        "pool_size": pool.size(),
        "checked_in_connections": pool.checkedin(),
        "checked_out_connections": pool.checkedout(),
        "overflow_connections": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }

    if read_engine:
        read_pool = read_engine.pool
        stats["read_pool_size"] = read_pool.size()
        stats["read_checked_in"] = read_pool.checkedin()
        stats["read_checked_out"] = read_pool.checkedout()
        stats["read_overflow"] = read_pool.overflow()

    return stats
