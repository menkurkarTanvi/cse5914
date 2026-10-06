from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_service import User_Service
from schemas.profile import ProfileRequest
from database.database import get_db
from models.profile import Profile
from sqlalchemy import select
from dependencies import CurrentUserId

# Prefix tag
router = APIRouter(
    prefix="/profiles",
    tags=["profiles"]
)

@router.post("/createProfile")
async def create_profile(profile_request: ProfileRequest, db: AsyncSession = Depends(get_db)):
    #Get the user_id from the JWT token using the get_current_user_id function from the User_Service class.
    user_id = await User_Service.get_current_user_id()
    #Check if the user already has a profile in the database, if it does, return an HTTPException with a 400 status code and a message indicating that the profile already exists.
    existing_profile = await db.execute(select(Profile).where(Profile.user_id == user_id))
    existing_profile = existing_profile.scalar_one_or_none()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    #Create a new profile object and add it to the database. The profile should be associated with the user_id obtained from the JWT token.
    new_profile = Profile(user_id=user_id, **profile_request.dict())
    db.add(new_profile)
    await db.commit()
    return new_profile

@router.get("/profile")
async def get_profile( user_id: CurrentUserId, db: AsyncSession = Depends(get_db)):
    #Retrieve the profile from the database based on the user_id obtained from the JWT token. If no profile is found, return an HTTPException with a 404 status code and a message indicating that the profile was not found.
    profile = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = profile.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile