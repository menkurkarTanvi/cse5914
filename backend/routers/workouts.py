from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.dependencies import CurrentUserId
from services.user_service import User_Service
from schemas.user import LoginRequest, SignUpRequest
from database.database import get_db
from models.profile import Profile
from sqlalchemy import select
from schemas.profile import WorkoutPlanResponse

# Prefix tag
router = APIRouter(
    prefix="/workouts",
    tags=["workouts"]
)

@router.get("/workoutPlan")
async def get_workout_plan(user_id: CurrentUserId, db: AsyncSession = Depends(get_db)) -> WorkoutPlanResponse:
    #Check if the user has a profile in the database. If not, return no workout plan and a message indicating that the user needs to create a profile first.
    profile = await db.execute(select(Profile).where(Profile.user_id == user_id))
    profile = profile.scalar_one_or_none()
    if not profile:
        return None
    #Get the current date and time in UTC timezone
    #If the current date is NOT Monday, return the users last workout plan from the database.
    #If the current date, is Monday, invoke the function to generate a new workout plan for the user and return it. 
    pass
