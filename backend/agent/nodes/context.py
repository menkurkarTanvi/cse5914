from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import contains_eager, selectinload

from agent.state import WorkoutAgentState

if TYPE_CHECKING:
    from models.workout_plan import WorkoutPlan
    from models.workout_plan_exercise import WorkoutPlanExercise
    from models.workout_program import WorkoutProgram


WEEKDAY_ORDER = {
    day: index
    for index, day in enumerate(
        [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
    )
}


def _today() -> date:
    """Today's date. A separate function so tests can replace it with a fixed date."""
    return date.today()


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

    today = _today()

    async with AsyncSessionLocal() as session:
        profile = await session.scalar(
            select(Profile).where(Profile.user_id == user_id)
        )
        if profile is None:
            raise LookupError(f"Profile not found for user {user_id}")

        availability = (
            await session.scalars(
                select(UserAvailability).where(UserAvailability.user_id == user_id)
            )
        ).all()
        # Monday to Sunday. Sorting in the database would be alphabetical.
        availability = sorted(
            availability,
            key=lambda item: WEEKDAY_ORDER.get(item.day_of_week.lower(), 7),
        )

        # One week's worth of completed workouts: one per available day.
        recent_limit = max(1, sum(1 for item in availability if item.is_available))

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
                            WorkoutPlan.scheduled_date >= today,
                        ),
                    ),
                )
                .order_by(
                    case((WorkoutPlan.status == "in_progress", 0), else_=1),
                    WorkoutPlan.scheduled_date,
                )
                .limit(1)
            )

            # Nothing left to do in this program, so it is finished. Close it
            # so the graph routes to new-program generation instead of
            # getting stuck on an "active" program with no upcoming workout.
            # Note: this is the one place this node writes to the database.
            if current_workout is None:
                active_program.status = "completed"
                await session.commit()
                active_program = None

        # Most recent completed workouts, across all of the user's programs.
        recent_workout_ids = (
            await session.scalars(
                select(WorkoutPlan.workout_id)
                .join(
                    WorkoutProgram,
                    WorkoutProgram.program_id == WorkoutPlan.program_id,
                )
                .where(
                    WorkoutProgram.user_id == user_id,
                    WorkoutPlan.status == "completed",
                )
                .order_by(WorkoutPlan.scheduled_date.desc())
                .limit(recent_limit)
            )
        ).all()

        recent_performance: list[WorkoutPlanExercise] = []
        if recent_workout_ids:
            recent_performance = list(
                (
                    await session.scalars(
                        select(WorkoutPlanExercise)
                        .join(
                            WorkoutPlan,
                            WorkoutPlan.workout_id == WorkoutPlanExercise.workout_id,
                        )
                        .where(WorkoutPlanExercise.workout_id.in_(recent_workout_ids))
                        .options(
                            # Fills item.workout from the join above. A lazy
                            # load would raise MissingGreenlet in async code.
                            contains_eager(WorkoutPlanExercise.workout),
                            selectinload(WorkoutPlanExercise.sets),
                        )
                        .order_by(
                            WorkoutPlan.scheduled_date.desc(),
                            WorkoutPlanExercise.exercise_order,
                        )
                    )
                ).all()
            )

        # Serialize while the session is open and everything is loaded.
        profile_state = {
            "user_id": profile.user_id,
            "goal": profile.goal,
            "experience_level": profile.experience_level,
            "available_equipment": profile.available_equipment or [],
            "preferred_exercises": profile.preferred_exercises or [],
            "disliked_exercises": profile.disliked_exercises or [],
            "limitations": profile.limitations or [],
        }
        availability_state = [
            {
                "day_of_week": item.day_of_week.lower(),
                "is_available": item.is_available,
                "max_duration_minutes": item.max_duration_minutes,
            }
            for item in availability
        ]
        program_state = _serialize_program(active_program)
        workout_state = _serialize_workout(current_workout)
        performance_state = [_serialize_performance(item) for item in recent_performance]

    return {
        "user_id": user_id,
        "profile": profile_state,
        "availability": availability_state,
        "active_program": program_state,
        "current_workout": workout_state,
        "recent_performance": performance_state,
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
        "description": workout.description,
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
        "workout_id": item.workout_id,
        "scheduled_date": item.workout.scheduled_date,
        "workout_plan_exercise_id": item.id,
        "exercise_id": item.exercise_id,
        "planned_sets": item.sets_planned,
        "reps_min": item.reps_min,
        "reps_max": item.reps_max,
        "target_rpe_min": item.target_rpe_min,
        "target_rpe_max": item.target_rpe_max,
        "planned_weight": item.planned_weight,
        # Actual weights are assumed to be logged in the plan's unit.
        "weight_unit": item.weight_unit,
        "actual_reps": [workout_set.reps for workout_set in completed_sets],
        "actual_weights": [workout_set.weight for workout_set in completed_sets],
        "actual_rpes": [workout_set.rpe for workout_set in completed_sets],
    }


def is_active_four_week_program(state: WorkoutAgentState) -> str:
    """Route to progression when an active program exists, otherwise generate one."""
    if state.get("active_program") is None:
        return "new_program"
    return "current_program"