# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()
#Database URL for PostgreSQL with asyncpg driver
# Falls back to the local Docker database if DATABASE_URL isn't set
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in {"1", "true", "yes"}

# Create the async engine and sessionmaker
engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO, pool_pre_ping=True)

# Base class that all your models inherit from
Base = declarative_base()

# Creates a new database session for each request
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# FastAPI dependency: gives each endpoint a session, then closes it
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


