from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import contains_eager, selectinload

from agent.state import WorkoutAgentState
from database.database import AsyncSessionLocal
from models.workout_plan import WorkoutPlan
from models.workout_plan_exercise import WorkoutPlanExercise
from models.workout_program import WorkoutProgram
from models.workout_set import WorkoutSet

if TYPE_CHECKING:
    from models.exercise import Exercise
    from models.workout_plan_exercise import WorkoutPlanExercise


# How far back "recent" goes when looking up how the user performed.
LOOKBACK_DAYS = 7


async def load_last_workout_plan(state: WorkoutAgentState) -> dict:
    """
    Load the exercises (with their prescriptions) for the workout the user
    does next, and store them in the state.

    The workout header (workout_id, week, day, date, status) is already in
    state["current_workout"] from load_user_context. What progression needs
    on top of that is the planned exercises, because those are the rows
    apply_progression will update, and the exercise details are needed for
    the compatibility check and for finding replacements.

    Returns a partial state update, following LangGraph's node contract.
    """
    current_workout = state.get("current_workout")
    if current_workout is None:
        # Active program but nothing left to do. Nothing to load.
        return {"current_workout_exercises": []}

    workout_id = current_workout["workout_id"]

    # Local imports keep graph construction independent of database
    # driver initialization (same pattern as context.py).
    from database.database import AsyncSessionLocal
    from models.workout_plan_exercise import WorkoutPlanExercise

    async with AsyncSessionLocal() as session:
        plan_exercises = (
            await session.scalars(
                select(WorkoutPlanExercise)
                .where(WorkoutPlanExercise.workout_id == workout_id)
                .options(selectinload(WorkoutPlanExercise.exercise))
                .order_by(WorkoutPlanExercise.exercise_order)
            )
        ).all()

        serialized = [_serialize_plan_exercise(item) for item in plan_exercises]

    return {"current_workout_exercises": serialized}

#Goal: for each upcoming exercise, find the last time the user did it and return what was planned next to what actually happened
async def load_recent_performance(state: WorkoutAgentState) -> dict:
    """
    For each exercise in the upcoming workout, load the last time the user
    completed it (within LOOKBACK_DAYS): what was planned and what they
    actually did, set by set.

    Example of one entry:
        Exercise: Bench Press
        Planned:  3 x 8-10 @ RPE 8
        Actual:   Set 1: 135 x 10 @ RPE 7
                  Set 2: 135 x 10 @ RPE 7
                  Set 3: 135 x 10 @ RPE 8

    Needs state["current_workout_exercises"] (from load_last_workout_plan).
    Exercises with no completed sets in the window are left out, so
    analyze_progression should treat "no entry" as "no history, keep the
    plan as written".

    This replaces the broader recent_performance list that load_user_context
    sets, so the progression nodes only see what they need.
    """
    #Reac currnet_workout_exericses from the state
    upcoming = state.get("current_workout_exercises") or []
    if not upcoming:
        return {"recent_performance": []}

    user_id = state["user_id"]
    exercise_ids = list(
        dict.fromkeys(item["exercise"]["exercise_id"] for item in upcoming)
    )
    cutoff = date.today() - timedelta(days=LOOKBACK_DAYS)

    # Only count a past occurrence if at least one set was actually logged
    # as completed, so a workout where the exercise was skipped doesn't hide
    # an earlier real performance.
    has_completed_set = (
        select(WorkoutSet.set_id)
        .where(
            WorkoutSet.workout_plan_exercise_id == WorkoutPlanExercise.id,
            WorkoutSet.completed.is_(True),
        )
        .exists()
    )

    async with AsyncSessionLocal() as session:
        rows = (
            await session.scalars(
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
                    WorkoutProgram.user_id == user_id,
                    WorkoutPlan.status == "completed",
                    WorkoutPlan.scheduled_date >= cutoff,
                    WorkoutPlanExercise.exercise_id.in_(exercise_ids),
                    has_completed_set,
                )
                # PostgreSQL DISTINCT ON: one row per exercise, the most
                # recent one (the ORDER BY must start with the DISTINCT ON
                # column).
                .distinct(WorkoutPlanExercise.exercise_id)
                .order_by(
                    WorkoutPlanExercise.exercise_id,
                    WorkoutPlan.scheduled_date.desc(),
                )
                .options(
                    # Populate item.workout from the join above. A lazy load
                    # here would raise MissingGreenlet in async SQLAlchemy.
                    contains_eager(WorkoutPlanExercise.workout),
                    selectinload(WorkoutPlanExercise.sets),
                )
            )
        ).all()

        latest_by_exercise = {
            row.exercise_id: _serialize_performance(row) for row in rows
        }

    # Same order as the upcoming workout; exercises with no history are skipped.
    performance = [
        latest_by_exercise[exercise_id]
        for exercise_id in exercise_ids
        if exercise_id in latest_by_exercise
    ]
    return {"recent_performance": performance}


def _serialize_plan_exercise(item: WorkoutPlanExercise) -> dict:
    return {
        "workout_plan_exercise_id": item.id,
        "exercise_order": item.exercise_order,
        "sets_planned": item.sets_planned,
        "reps_min": item.reps_min,
        "reps_max": item.reps_max,
        "target_rpe_min": item.target_rpe_min,
        "target_rpe_max": item.target_rpe_max,
        "rest_seconds": item.rest_seconds,
        "planned_weight": item.planned_weight,
        "weight_unit": item.weight_unit,
        "progression_method": item.progression_method,
        "notes": item.notes,
        "exercise": _serialize_exercise(item.exercise),
    }


def _serialize_exercise(exercise: Exercise) -> dict:
    # Enrichment fields are passed through as-is: None means "not enriched
    # yet", which downstream nodes may want to distinguish from empty.
    return {
        "exercise_id": exercise.exercise_id,
        "name": exercise.name,
        "difficulty_level": exercise.difficulty_level,
        "primary_muscles": exercise.primary_muscles or [],
        "secondary_muscles": exercise.secondary_muscles or [],
        "equipment_required": exercise.equipment_required or [],
        "exercise_family": exercise.exercise_family,
        "movement_pattern": exercise.movement_pattern,
        "training_role": exercise.training_role,
        "unilateral": exercise.unilateral,
        "load_type": exercise.load_type,
        "progression_methods": exercise.progression_methods,
        "substitution_group": exercise.substitution_group,
        "goal_suitability": exercise.goal_suitability,
        "mobility_requirements": exercise.mobility_requirements,
        "balance_requirement": exercise.balance_requirement,
        "stability_requirement": exercise.stability_requirement,
        "fatigue_cost": exercise.fatigue_cost,
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


async def analyze_progression(state: WorkoutAgentState) -> None:
    pass

async def apply_progression(state: WorkoutAgentState) -> None:
    pass
