"""
Wait for database to be ready before starting application

Usage: python -m app.core.wait_for_db
"""
import asyncio
import sys
import time
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import settings


async def wait_for_database(max_retries: int = 30, retry_interval: int = 2):
    """
    Wait for database to be ready.

    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries
    """
    print(f"🔍 Checking database connection to {settings.DATABASE_URL.split('@')[1]}...")

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            print(f"✅ Database is ready! (attempt {attempt}/{max_retries})")
            await engine.dispose()
            return True

        except Exception as e:
            if attempt == max_retries:
                print(f"❌ Failed to connect to database after {max_retries} attempts")
                print(f"   Error: {e}")
                await engine.dispose()
                sys.exit(1)

            print(f"⏳ Database not ready (attempt {attempt}/{max_retries}). Retrying in {retry_interval}s...")
            await asyncio.sleep(retry_interval)

    await engine.dispose()
    return False


async def main():
    """Main entry point"""
    start_time = time.time()

    success = await wait_for_database()

    elapsed = time.time() - start_time
    print(f"⏱️  Total wait time: {elapsed:.2f}s")

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
