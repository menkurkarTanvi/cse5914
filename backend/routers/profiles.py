from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import User_Service
from schemas.profile import CreateProfileRequest, ProfileWithAvailabilityResponse
from database.database import get_db
from models.profile import Profile
from models.user_availability import UserAvailability
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
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
 
@router.post(
    "/createProfile",
    status_code=201,
    response_model=ProfileWithAvailabilityResponse,
)
async def create_profile(
    payload: CreateProfileRequest,
    response: Response,
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    """Create the user's profile, or replace it if one already exists.
 
    Returns 201 when a profile is created and 200 when an existing one is
    replaced.
    """
    user_uuid = uuid.UUID(user_id)  # JWT 'sub' is a string; the columns are UUID
 
    profile = await db.scalar(select(Profile).where(Profile.user_id == user_uuid))
 
    if profile is None:
        profile = Profile(user_id=user_uuid, **payload.profile.model_dump())
        db.add(profile)
    else:
        # exclude_unset: only overwrite fields the client actually sent, so
        # optional lists the form doesn't have (preferred_exercises,
        # disliked_exercises) are kept. Use model_dump() instead for a full
        # overwrite that resets every omitted field to its default.
        for field, value in payload.profile.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        response.status_code = 200
 
    # The weekly availability is always replaced as a whole: delete the old
    # rows, then insert all 7 days, Monday to Sunday. Days the client didn't
    # send are saved as unavailable, so GET /profile returns a full week.
    await db.execute(
        delete(UserAvailability).where(UserAvailability.user_id == user_uuid)
    )
 
    submitted = {entry.day_of_week: entry for entry in payload.availability}
    availability = []
    for day in DAY_ORDER:
        entry = submitted.get(day)
        is_available = entry.is_available if entry else False
        availability.append(
            UserAvailability(
                user_id=user_uuid,
                day_of_week=day,
                is_available=is_available,
                # A duration only means something on an available day.
                max_duration_minutes=(
                    entry.max_duration_minutes if entry and is_available else None
                ),
            )
        )
    db.add_all(availability)
 
    # Profile and availability are saved in one transaction: either all of
    # it is saved or none of it is.
    try:
        await db.commit()
    except IntegrityError:
        # Two first-time requests for the same user raced each other.
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Profile was changed by another request. Please try again.",
        )
 
    return {"profile": profile, "availability": availability}
    

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