import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env first. Variables in .env only reach os.environ after this call.
load_dotenv()

# These must be set BEFORE importing anything that reads DATABASE_URL
# (database.database, main). load_dotenv() does not override variables
# that are already set, so the whole app, including code that opens its
# own sessions with AsyncSessionLocal, ends up on the test database.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is not set. Add it to your .env file or set it "
        "in your shell before running the tests."
    )

# Safety guard: the teardown downgrades to base, which drops every table.
# Refuse to run against anything that isn't clearly a test database.
_db_name = TEST_DATABASE_URL.rsplit("/", 1)[-1].split("?")[0]
if "test" not in _db_name:
    raise RuntimeError(
        f"Refusing to run tests against '{_db_name}'. "
        "The test database name must contain 'test'."
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["TESTING"] = "1"

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from database.database import get_db
from main import app

# NullPool: every connection is created and closed within the test's own
# event loop, which avoids "attached to a different loop" errors.
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)


def _find_alembic_ini() -> str:
    """Look for alembic.ini in this folder and its parents."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "alembic.ini"
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError("alembic.ini not found")


@pytest.fixture(scope="session", autouse=True)
def run_migrations():
    """Run alembic upgrade head on the test database once per test session."""
    alembic_cfg = Config(_find_alembic_ini())
    command.upgrade(alembic_cfg, "head")

    yield


@pytest_asyncio.fixture
async def db_session():
    """A session wrapped in an outer transaction that always rolls back."""
    async with engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            # Match the app's AsyncSessionLocal. With the default (True),
            # reading an attribute after a commit raises MissingGreenlet.
            expire_on_commit=False,
            # session.commit() releases a SAVEPOINT instead of committing
            # the outer transaction, and session.rollback() (for example
            # after an IntegrityError in a route) only rolls back to the
            # savepoint instead of wiping everything the test set up.
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """HTTP client whose get_db dependency uses the rollback-only session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()