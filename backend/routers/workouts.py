from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import CurrentUserId
from services.user_service import User_Service
from schemas.user import LoginRequest, SignUpRequest
from database.database import get_db
from models.profile import Profile
from sqlalchemy import select
from services.workout_service import Workout_Service
from datetime import date
import uuid

# Prefix tag
router = APIRouter(
    prefix="/workouts",
    tags=["workouts"]
)

#ADD THE CODE TO RETURN 3 SIMILAR EXERCISES
@router.get("/swapExercise")
async def swap_exercise(user_id: CurrentUserId, db: AsyncSession = Depends(get_db)):
    pass

@router.post("/saveUserWorkoutInfo")
async def save_workout_info(user_id: CurrentUserId, db: AsyncSession = Depends(get_db)):
    #METHOD EXPLANATION: this method is the save the the users actual completed sets, reps, weight, etc for a workout
    pass

@router.get("/workoutPlan")
async def get_workout_plan(user_id: CurrentUserId, db: AsyncSession = Depends(get_db)) -> dict:
    # Check if the user has a profile in the database. If not, return no workout plan
    # and a message indicating that the user needs to create a profile first.
    user_uuid = uuid.UUID(user_id)
    profile = await db.execute(select(Profile).where(Profile.user_id == user_uuid))
    profile = profile.scalar_one_or_none()
    if not profile:
        return {
            "program": None,
            "workouts": [],
            "message": "Please create a profile before requesting a workout plan.",
        }

    # Until agent is working, just return last week's workout plans
    workout_service = Workout_Service(db)
    plans = await workout_service.get_last_week_workout_plans(user_uuid, date.today())
    if not plans:
        return {"program": None, "workouts": [], "message": "No workouts found."}

    program = plans[0].program
    return {
        "program": {
            "program_id": str(program.program_id),
            "goal": program.goal,
            "status": program.status,
            "start_date": program.start_date.isoformat(),
            "end_date": program.end_date.isoformat(),
        },
        "workouts": [
            {
                "workout_id": str(plan.workout_id),
                "day_of_week": plan.day_of_week,
                "description": plan.description,
                "week_number": plan.week_number,
                "scheduled_date": plan.scheduled_date.isoformat(),
                "status": plan.status,
                "exercises": [
                    {
                        "id": str(item.id),
                        "exercise_id": item.exercise_id,
                        "name": item.exercise.name,
                        "exercise_order": item.exercise_order,
                        "sets_planned": item.sets_planned,
                        "reps_min": item.reps_min,
                        "reps_max": item.reps_max,
                        "target_rpe_min": item.target_rpe_min,
                        "target_rpe_max": item.target_rpe_max,
                        "rest_seconds": item.rest_seconds,
                        "planned_weight": item.planned_weight,
                        "weight_unit": item.weight_unit,
                    }
                    for item in plan.exercises
                ],
            }
            for plan in plans
        ],
        "message": None,
    }
