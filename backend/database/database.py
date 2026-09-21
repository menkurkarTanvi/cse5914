# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

#Database URL for PostgreSQL with asyncpg driver
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/exercises"

# Create the async engine and sessionmaker
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


