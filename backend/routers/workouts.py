from typing import Literal
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.database import get_db
from dependencies import CurrentUserId
from models.exercise import Exercise
from models.profile import Profile
from models.workout_feedback import WorkoutFeedback
from models.workout_plan import WorkoutPlan
from models.workout_plan_exercise import WorkoutPlanExercise
from models.workout_program import WorkoutProgram
from models.workout_set import WorkoutSet
from services.workout_service import Workout_Service

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"],
)


class SwapExerciseRequest(BaseModel):
    exercise_id: str
    apply_to: Literal["this_workout", "rest_of_program"] = "this_workout"


class WorkoutSetRequest(BaseModel):
    set_number: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight: float | None = Field(default=None, ge=0)
    weight_unit: str = "lb"
    rpe: float | None = Field(default=None, ge=0, le=10)


class CompletedExerciseRequest(BaseModel):
    workout_plan_exercise_id: uuid.UUID
    sets: list[WorkoutSetRequest]


class WorkoutFeedbackRequest(BaseModel):
    difficulty: Literal["too_easy", "great", "too_hard"]


class CompleteWorkoutRequest(BaseModel):
    exercises: list[CompletedExerciseRequest]
    feedback: WorkoutFeedbackRequest


class SkipWorkoutRequest(BaseModel):
    reason: str | None = None


async def _get_owned_workout_exercise(
    db: AsyncSession,
    user_uuid: uuid.UUID,
    workout_plan_exercise_id: uuid.UUID,
) -> WorkoutPlanExercise:
    result = await db.execute(
        select(WorkoutPlanExercise)
        .join(
            WorkoutPlan,
            WorkoutPlan.workout_id == WorkoutPlanExercise.workout_id,
        )
        .join(
            WorkoutProgram,
            WorkoutProgram.program_id == WorkoutPlan.program_id,
        )
        .where(
            WorkoutPlanExercise.id == workout_plan_exercise_id,
            WorkoutProgram.user_id == user_uuid,
        )
        .options(selectinload(WorkoutPlanExercise.exercise))
    )

    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Workout exercise not found",
        )

    return item


async def _get_owned_workout(
    db: AsyncSession,
    user_uuid: uuid.UUID,
    workout_id: uuid.UUID,
) -> WorkoutPlan:
    result = await db.execute(
        select(WorkoutPlan)
        .join(
            WorkoutProgram,
            WorkoutProgram.program_id == WorkoutPlan.program_id,
        )
        .where(
            WorkoutPlan.workout_id == workout_id,
            WorkoutProgram.user_id == user_uuid,
        )
        .options(selectinload(WorkoutPlan.exercises))
    )

    workout = result.scalar_one_or_none()

    if workout is None:
        raise HTTPException(
            status_code=404,
            detail="Workout not found",
        )

    return workout


def _exercise_score(
    current: Exercise,
    candidate: Exercise,
) -> int:
    score = 0

    if (
        current.substitution_group
        and candidate.substitution_group
        == current.substitution_group
    ):
        score += 8

    current_primary = set(
        current.primary_muscles or []
    )
    candidate_primary = set(
        candidate.primary_muscles or []
    )

    score += 3 * len(
        current_primary & candidate_primary
    )

    if (
        current.movement_pattern
        and candidate.movement_pattern
        == current.movement_pattern
    ):
        score += 4

    if (
        current.exercise_family
        and candidate.exercise_family
        == current.exercise_family
    ):
        score += 3

    if (
        current.mechanics
        and candidate.mechanics
        == current.mechanics
    ):
        score += 1

    if candidate.category == current.category:
        score += 1

    return score


def _alternative_reason(
    current: Exercise,
    candidate: Exercise,
) -> str:
    if (
        current.substitution_group
        and candidate.substitution_group
        == current.substitution_group
    ):
        return "Same substitution group"

    overlap = sorted(
        set(current.primary_muscles or [])
        & set(candidate.primary_muscles or [])
    )

    if overlap:
        return (
            "Targets similar muscles: "
            + ", ".join(overlap)
        )

    if (
        current.movement_pattern
        and candidate.movement_pattern
        == current.movement_pattern
    ):
        return "Same movement pattern"

    return "Similar exercise"


@router.get(
    "/exercises/{workout_plan_exercise_id}/alternatives"
)
async def exercise_alternatives(
    workout_plan_exercise_id: uuid.UUID,
    user_id: CurrentUserId,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    user_uuid = uuid.UUID(user_id)

    item = await _get_owned_workout_exercise(
        db,
        user_uuid,
        workout_plan_exercise_id,
    )

    current = item.exercise

    exercise_result = await db.execute(
        select(Exercise).where(
            Exercise.exercise_id
            != current.exercise_id
        )
    )

    candidates = list(
        exercise_result.scalars().all()
    )

    candidates.sort(
        key=lambda exercise: (
            _exercise_score(
                current,
                exercise,
            ),
            exercise.name,
        ),
        reverse=True,
    )

    limit = max(1, min(limit, 10))
    best = candidates[:limit]

    return {
        "current": {
            "exercise_id": current.exercise_id,
            "name": current.name,
        },
        "alternatives": [
            {
                "exercise_id":
                    exercise.exercise_id,
                "name":
                    exercise.name,
                "primary_muscles":
                    exercise.primary_muscles or [],
                "equipment_required":
                    exercise.equipment_required or [],
                "reason":
                    _alternative_reason(
                        current,
                        exercise,
                    ),
            }
            for exercise in best
        ],
    }


@router.post(
    "/exercises/{workout_plan_exercise_id}/swap"
)
async def swap_exercise(
    workout_plan_exercise_id: uuid.UUID,
    body: SwapExerciseRequest,
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    user_uuid = uuid.UUID(user_id)

    item = await _get_owned_workout_exercise(
        db,
        user_uuid,
        workout_plan_exercise_id,
    )

    new_exercise = await db.get(
        Exercise,
        body.exercise_id,
    )

    if new_exercise is None:
        raise HTTPException(
            status_code=404,
            detail="Replacement exercise not found",
        )

    item.exercise_id = new_exercise.exercise_id

    await db.commit()

    return {
        "id": str(item.id),
        "exercise_id":
            new_exercise.exercise_id,
        "name":
            new_exercise.name,
        "exercise_order":
            item.exercise_order,
        "sets_planned":
            item.sets_planned,
        "reps_min":
            item.reps_min,
        "reps_max":
            item.reps_max,
        "target_rpe_min":
            item.target_rpe_min,
        "target_rpe_max":
            item.target_rpe_max,
        "rest_seconds":
            item.rest_seconds,
        "planned_weight":
            item.planned_weight,
        "weight_unit":
            item.weight_unit,
    }


@router.post("/{workout_id}/complete")
async def complete_workout(
    workout_id: uuid.UUID,
    body: CompleteWorkoutRequest,
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    user_uuid = uuid.UUID(user_id)

    workout = await _get_owned_workout(
        db,
        user_uuid,
        workout_id,
    )

    workout_exercises = {
        item.id: item
        for item in workout.exercises
    }

    submitted_ids = {
        item.workout_plan_exercise_id
        for item in body.exercises
    }

    invalid_ids = (
        submitted_ids
        - set(workout_exercises)
    )

    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "One or more exercises "
                "do not belong to this workout"
            ),
        )

    if submitted_ids:
        await db.execute(
            delete(WorkoutSet).where(
                WorkoutSet
                .workout_plan_exercise_id
                .in_(submitted_ids)
            )
        )

    for exercise_entry in body.exercises:
        for set_entry in exercise_entry.sets:
            db.add(
                WorkoutSet(
                    workout_plan_exercise_id=(
                        exercise_entry
                        .workout_plan_exercise_id
                    ),
                    set_number=(
                        set_entry.set_number
                    ),
                    reps=set_entry.reps,
                    weight=set_entry.weight,
                    weight_unit=(
                        set_entry.weight_unit
                    ),
                    rpe=set_entry.rpe,
                    completed=True,
                )
            )

    feedback_result = await db.execute(
        select(WorkoutFeedback).where(
            WorkoutFeedback.workout_id
            == workout_id
        )
    )

    feedback = (
        feedback_result.scalar_one_or_none()
    )

    feedback_data = {
        "difficulty":
            body.feedback.difficulty
    }

    if feedback is None:
        db.add(
            WorkoutFeedback(
                workout_id=workout_id,
                user_id=user_uuid,
                exercise_feedback=(
                    feedback_data
                ),
            )
        )
    else:
        feedback.exercise_feedback = (
            feedback_data
        )

    workout.status = "completed"

    await db.commit()

    return {
        "workout_id": str(workout_id),
        "status": "completed",
    }


@router.post("/{workout_id}/skip")
async def skip_workout(
    workout_id: uuid.UUID,
    body: SkipWorkoutRequest,
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    user_uuid = uuid.UUID(user_id)

    workout = await _get_owned_workout(
        db,
        user_uuid,
        workout_id,
    )

    workout.status = "incompleted"

    await db.commit()

    return {
        "workout_id": str(workout_id),
        "status": "incompleted",
        "reason": body.reason,
    }


@router.get("/workoutPlan")
async def get_workout_plan(
    user_id: CurrentUserId,
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_uuid = uuid.UUID(user_id)

    profile = await db.execute(
        select(Profile).where(
            Profile.user_id == user_uuid
        )
    )

    profile = profile.scalar_one_or_none()

    if not profile:
        return {
            "program": None,
            "workouts": [],
            "message": (
                "Please create a profile "
                "before requesting a workout plan."
            ),
        }

    workout_service = Workout_Service(db)

    plans = (
        await workout_service
        .get_last_week_workout_plans(
            user_uuid,
            date.today(),
        )
    )

    if not plans:
        return {
            "program": None,
            "workouts": [],
            "message": "No workouts found.",
        }

    program = plans[0].program

    return {
        "program": {
            "program_id":
                str(program.program_id),
            "goal":
                program.goal,
            "status":
                program.status,
            "start_date":
                program.start_date.isoformat(),
            "end_date":
                program.end_date.isoformat(),
        },
        "workouts": [
            {
                "workout_id":
                    str(plan.workout_id),
                "day_of_week":
                    plan.day_of_week,
                "description":
                    plan.description,
                "week_number":
                    plan.week_number,
                "scheduled_date":
                    plan.scheduled_date.isoformat(),
                "status":
                    plan.status,
                "exercises": [
                    {
                        "id":
                            str(item.id),
                        "exercise_id":
                            item.exercise_id,
                        "name":
                            item.exercise.name,
                        "exercise_order":
                            item.exercise_order,
                        "sets_planned":
                            item.sets_planned,
                        "reps_min":
                            item.reps_min,
                        "reps_max":
                            item.reps_max,
                        "target_rpe_min":
                            item.target_rpe_min,
                        "target_rpe_max":
                            item.target_rpe_max,
                        "rest_seconds":
                            item.rest_seconds,
                        "planned_weight":
                            item.planned_weight,
                        "weight_unit":
                            item.weight_unit,
                    }
                    for item in plan.exercises
                ],
            }
            for plan in plans
        ],
        "message": None,
    }