import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import text

# Ensure project root (/app) is on sys.path when invoked from ./scripts
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    # Reuse the app engine and settings
    from app.db.base_class import engine
except Exception as e:
    print(f"Failed to import database engine: {e}", file=sys.stderr)
    sys.exit(1)


async def wait_for_db() -> None:
    retries = int(os.getenv("DB_WAIT_RETRIES", "60"))
    delay = float(os.getenv("DB_WAIT_DELAY", "1"))

    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"Database connection established on attempt {attempt}")
            return
        except Exception as e:
            if attempt == retries:
                print(
                    f"Database not ready after {retries} attempts: {e}", file=sys.stderr
                )
                raise
            await asyncio.sleep(delay)


if __name__ == "__main__":
    try:
        asyncio.run(wait_for_db())
    except Exception:
        sys.exit(1)
