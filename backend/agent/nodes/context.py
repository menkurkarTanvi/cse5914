from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import selectinload

from agent.state import WorkoutAgentState

if TYPE_CHECKING:
    from models.workout_plan import WorkoutPlan
    from models.workout_plan_exercise import WorkoutPlanExercise
    from models.workout_program import WorkoutProgram


RECENT_WORKOUT_LIMIT = 12


async def load_user_context(state: WorkoutAgentState) -> dict:
    """Load the database-backed context needed by the workout graph.

    The caller must place ``user_id`` in the graph state before this node runs.
    Returning a partial-state dictionary follows LangGraph's node contract and
    avoids mutating the input state in place.
    """
    user_id = state.get("user_id")
    if user_id is None:
        raise ValueError("Workout agent state must include user_id")

    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError as exc:
            raise ValueError("Workout agent user_id must be a valid UUID") from exc

    # Local imports keep graph construction independent of database driver
    # initialization and make this node easier to unit test.
    from database.database import AsyncSessionLocal
    from models.profile import Profile
    from models.user_availability import UserAvailability
    from models.workout_plan import WorkoutPlan
    from models.workout_plan_exercise import WorkoutPlanExercise
    from models.workout_program import WorkoutProgram

    async with AsyncSessionLocal() as session:
        profile = await session.scalar(
            select(Profile).where(Profile.user_id == user_id)
        )
        if profile is None:
            raise LookupError(f"Profile not found for user {user_id}")

        availability = (
            await session.scalars(
                select(UserAvailability)
                .where(UserAvailability.user_id == user_id)
                .order_by(UserAvailability.day_of_week)
            )
        ).all()

        active_program = await session.scalar(
            select(WorkoutProgram)
            .where(
                WorkoutProgram.user_id == user_id,
                WorkoutProgram.status == "active",
            )
            .order_by(WorkoutProgram.start_date.desc())
            .limit(1)
        )

        current_workout = None
        if active_program is not None:
            current_workout = await session.scalar(
                select(WorkoutPlan)
                .where(
                    WorkoutPlan.program_id == active_program.program_id,
                    or_(
                        WorkoutPlan.status == "in_progress",
                        and_(
                            WorkoutPlan.status == "scheduled",
                            WorkoutPlan.scheduled_date >= date.today(),
                        ),
                    ),
                )
                .order_by(
                    case((WorkoutPlan.status == "in_progress", 0), else_=1),
                    WorkoutPlan.scheduled_date,
                )
                .limit(1)
            )

        recent_workouts = (
            await session.scalars(
                select(WorkoutPlan)
                .join(WorkoutProgram)
                .where(
                    WorkoutProgram.user_id == user_id,
                    WorkoutPlan.status.in_(("completed", "skipped")),
                )
                .order_by(WorkoutPlan.scheduled_date.desc())
                .limit(RECENT_WORKOUT_LIMIT)
            )
        ).all()

        recent_workout_ids = [
            workout.workout_id
            for workout in recent_workouts
            if workout.status == "completed"
        ]
        recent_performance: list[WorkoutPlanExercise] = []
        if recent_workout_ids:
            recent_performance = list(
                (
                    await session.scalars(
                        select(WorkoutPlanExercise)
                        .where(WorkoutPlanExercise.workout_id.in_(recent_workout_ids))
                        .options(selectinload(WorkoutPlanExercise.sets))
                        .join(WorkoutPlan)
                        .order_by(
                            WorkoutPlan.scheduled_date.desc(),
                            WorkoutPlanExercise.exercise_order,
                        )
                    )
                ).all()
            )

    return {
        "user_id": user_id,
        "profile": {
            "user_id": profile.user_id,
            "goal": profile.goal,
            "experience_level": profile.experience_level,
            "available_equipment": profile.available_equipment or [],
            "preferred_exercises": profile.preferred_exercises or [],
            "disliked_exercises": profile.disliked_exercises or [],
            "limitations": profile.limitations or [],
        },
        "availability": [
            {
                "day_of_week": item.day_of_week.lower(),
                "is_available": item.is_available,
                "max_duration_minutes": item.max_duration_minutes,
            }
            for item in availability
        ],
        "active_program": _serialize_program(active_program),
        "current_workout": _serialize_workout(current_workout),
        "recent_workouts": [
            {
                "workout_id": workout.workout_id,
                "scheduled_date": workout.scheduled_date,
                "status": workout.status,
            }
            for workout in recent_workouts
        ],
        "recent_performance": [
            _serialize_performance(item) for item in recent_performance
        ],
    }


def _serialize_program(program: WorkoutProgram | None) -> dict | None:
    if program is None:
        return None
    return {
        "program_id": program.program_id,
        "start_date": program.start_date,
        "end_date": program.end_date,
        "goal": program.goal,
        "status": program.status,
    }


def _serialize_workout(workout: WorkoutPlan | None) -> dict | None:
    if workout is None:
        return None
    return {
        "workout_id": workout.workout_id,
        "program_id": workout.program_id,
        "week_number": workout.week_number,
        "day_of_week": workout.day_of_week.lower(),
        "scheduled_date": workout.scheduled_date,
        "status": workout.status,
    }


def _serialize_performance(item: WorkoutPlanExercise) -> dict:
    completed_sets = sorted(
        (workout_set for workout_set in item.sets if workout_set.completed),
        key=lambda workout_set: workout_set.set_number,
    )
    return {
        "workout_plan_exercise_id": item.id,
        "exercise_id": item.exercise_id,
        "planned_sets": item.sets_planned,
        "reps_min": item.reps_min,
        "reps_max": item.reps_max,
        "target_rpe_min": item.target_rpe_min,
        "target_rpe_max": item.target_rpe_max,
        "planned_weight": item.planned_weight,
        "actual_reps": [workout_set.reps for workout_set in completed_sets],
        "actual_weights": [workout_set.weight for workout_set in completed_sets],
        "actual_rpes": [workout_set.rpe for workout_set in completed_sets],
    }


def is_active_four_week_program(state: WorkoutAgentState) -> str:
    """Route to progression when an active program exists, otherwise generate one."""
    if state.get("active_program") is None:
        return "new_program"
    return "current_program"
