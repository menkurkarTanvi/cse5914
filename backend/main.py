import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import users, profiles, workouts, coach


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic (run `alembic upgrade head` before starting)
    yield

#Instance of the app
app = FastAPI(title="FitStack API", version="0.1.0", lifespan=lifespan)
#Register the APIRouter into main application
app.include_router(users.router)
app.include_router(profiles.router)
app.include_router(workouts.router)
app.include_router(coach.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}

origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
