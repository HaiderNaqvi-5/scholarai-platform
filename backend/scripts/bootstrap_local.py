import asyncio
import sys
import time
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.exc import OperationalError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.demo.seed import seed_demo_data_if_enabled


def run_migrations() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    last_error: Exception | None = None

    for attempt in range(1, 16):
        try:
            command.upgrade(config, "head")
            return
        except OperationalError as exc:
            last_error = exc
            if attempt == 15:
                break
            print(f"Database not ready for migrations yet. Retry {attempt}/15...")
            time.sleep(2)

    if last_error is not None:
        raise last_error


async def main() -> None:
    run_migrations()
    await seed_demo_data_if_enabled()
    print("ScholarAI local bootstrap completed with Alembic migrations.")


if __name__ == "__main__":
    asyncio.run(main())
