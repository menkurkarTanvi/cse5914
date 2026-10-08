import os
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
#from schemas import UserLogin
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from database.database import get_db
from routers import users, profiles
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic (run `alembic upgrade head` before starting)
    yield

#Instance of the app
app = FastAPI(title="FitStack API", version="0.1.0", lifespan=lifespan)
#Register the APIRouter into main application
app.include_router(users.router)
app.include_router(profiles.router)


origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
