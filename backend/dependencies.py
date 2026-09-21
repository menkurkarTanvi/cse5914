from backend.database.database import async_session
#DATABASE DEPENDECY
#This is the dependency function that will be used in FastAPI routes to get a database session. It ensures that the session is properly closed after use.
#Ensures we only use a single session per request and that the session is properly closed after the request is completed.
async def get_db():
    async with async_session() as session:
        yield session