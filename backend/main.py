import os
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from database.database import get_db
from database.models import Availability, Equipment, Limitation, Profile
from schemas import ProfileCreate, ProfileRead

app = FastAPI(title="FitStack API", version="0.1.0")

origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.post("/api/v1/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)) -> Profile:
    if len({item.day_of_week for item in payload.availability}) != len(payload.availability):
        raise HTTPException(status_code=422, detail="Availability days must be unique")

    profile = Profile(
        display_name=payload.display_name,
        goal=payload.goal,
        experience_level=payload.experience_level,
        training_block_weeks=payload.training_block_weeks,
        equipment=[
            Equipment(name=name)
            for name in dict.fromkeys(item.strip().lower() for item in payload.equipment if item.strip())
        ],
        availability=[Availability(**item.model_dump()) for item in payload.availability],
        limitations=[Limitation(**item.model_dump()) for item in payload.limitations],
    )
    db.add(profile)
    db.commit()
    return get_profile(profile.id, db)


@app.get("/api/v1/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID, db: Session = Depends(get_db)) -> Profile:
    profile = db.scalar(
        select(Profile)
        .where(Profile.id == profile_id)
        .options(selectinload(Profile.equipment), selectinload(Profile.availability), selectinload(Profile.limitations))
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
