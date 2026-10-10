from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import User_Service
from schemas.profile import CreateProfileRequest, ProfileWithAvailabilityResponse
from database.database import get_db
from models.profile import Profile
from models.user_availability import UserAvailability
from sqlalchemy import select
from dependencies import CurrentUserId
import uuid

# Prefix tag
router = APIRouter(
    prefix="/profiles",
    tags=["profiles"]
)

DAY_ORDER = {
    day: i
    for i, day in enumerate(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
}

@router.post("/createProfile", status_code=201)
async def create_profile(
    payload: CreateProfileRequest,
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    user_uuid = uuid.UUID(user_id)  # JWT 'sub' is a string; the columns are UUID
    

@router.get("/profile", response_model=ProfileWithAvailabilityResponse)
async def get_profile(user_id: CurrentUserId, db: AsyncSession = Depends(get_db)):
    user_uuid = uuid.UUID(user_id)

    result = await db.execute(select(Profile).where(Profile.user_id == user_uuid))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    #Get the users availiability from monday - sunday
    result = await db.execute(
        select(UserAvailability).where(UserAvailability.user_id == user_uuid)
    )
    availability = sorted(
        result.scalars().all(),
        key=lambda a: DAY_ORDER.get(a.day_of_week, len(DAY_ORDER)),
    )

    return {"profile": profile, "availability": availability}