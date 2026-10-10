import os
import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from main import app
from database.database import get_db

# Configure your Docker Postgres Test URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5450/test_db"

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def run_migrations():
    """Configures environment flags and runs alembic upgrade head on the test container."""
    # Set the flags so env.py catches them
    os.environ["TESTING"] = "1"
    os.environ["TEST_DATABASE_URL"] = TEST_DATABASE_URL
    
    alembic_cfg = Config("alembic.ini")
    
    # Run the migrations up to head
    command.upgrade(alembic_cfg, "head")
    
    yield
    
    # Optional: Clean up after your entire test suite finishes running
    command.downgrade(alembic_cfg, "base")
    
    # Clean up environment variables
    os.environ.pop("TESTING", None)
    os.environ.pop("TEST_DATABASE_URL", None)


@pytest.fixture(scope="function")
async def db_session():
    """Wraps test execution inside a rolling transaction."""
    async with engine.connect() as connection:
        transaction = await connection.begin()
        
        async with TestingSessionLocal(bind=connection) as session:
            yield session
            
        await transaction.rollback()


@pytest.fixture(scope="function")
async def client(db_session):
    """Overrides the FastAPI database connection dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()