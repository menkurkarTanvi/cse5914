# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

#Database URL for PostgreSQL with asyncpg driver
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/exercises"

# Create the async engine and sessionmaker
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

#This is the dependency function that will be used in FastAPI routes to get a database session. It ensures that the session is properly closed after use.
#Ensures we only use a single session per request and that the session is properly closed after the request is completed.
async def get_db():
    async with async_session() as session:
        yield session

