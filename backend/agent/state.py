# agent/state.py

from __future__ import annotations

import uuid
from datetime import date
from typing import Literal, TypedDict


# ============================================================
# Controlled values
# ============================================================

Goal = Literal[
    "strength",
    "hypertrophy",
    "muscular_endurance",
    "power",
    "general_fitness",
]

ExperienceLevel = Literal[
    "beginner",
    "intermediate",
    "advanced",
]

DayOfWeek = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

ProgramStatus = Literal[
    "draft",
    "active",
    "completed",
]

WorkoutStatus = Literal[
    "scheduled",
    "in_progress",
    "completed",
    "skipped",
]

ProgressionAction = Literal[
    "increase_weight",
    "decrease_weight",
    "increase_reps",
    "decrease_reps",
    "increase_sets",
    "decrease_sets",
    "maintain",
]


# ============================================================
# User information
# ============================================================

class ProfileState(TypedDict):
    user_id: uuid.UUID
    goal: Goal
    experience_level: ExperienceLevel
    available_equipment: list[str]
    preferred_exercises: list[str]
    disliked_exercises: list[str]
    limitations: list[str]


class AvailabilityState(TypedDict):
    day_of_week: DayOfWeek
    is_available: bool
    max_duration_minutes: int | None


# ============================================================
# Program / workout information
# ============================================================

class ProgramState(TypedDict):
    program_id: uuid.UUID
    start_date: date
    end_date: date
    goal: Goal
    status: ProgramStatus


class WorkoutState(TypedDict):
    workout_id: uuid.UUID
    program_id: uuid.UUID
    week_number: int
    day_of_week: DayOfWeek
    scheduled_date: date
    status: WorkoutStatus


# ============================================================
# Exercise information
# ============================================================

class ExerciseState(TypedDict):
    exercise_id: str
    name: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    exercise_family: str | None
    movement_pattern: str | None
    training_role: list[str] | None
    unilateral: bool | None
    load_type: str | None
    equipment_required: list[str]
    progression_methods: list[str] | None
    substitution_group: str | None
    goal_suitability: list[str] | None
    mobility_requirements: list[str] | None
    balance_requirement: str | None
    stability_requirement: str | None
    fatigue_cost: str | None
    difficulty_level: str


class ExerciseCandidateState(TypedDict):
    exercise: ExerciseState
    similarity_score: float


# One exercise in the upcoming workout: its prescription (a
# WorkoutPlanExercise row) plus the exercise details.
class PlannedExerciseState(TypedDict):
    workout_plan_exercise_id: uuid.UUID
    exercise_order: int
    sets_planned: int
    reps_min: int
    reps_max: int
    target_rpe_min: float | None
    target_rpe_max: float | None
    rest_seconds: int
    planned_weight: float | None
    weight_unit: str
    progression_method: str | None
    notes: str | None
    exercise: ExerciseState


# ============================================================
# Training history / performance
# ============================================================

class PerformanceState(TypedDict):
    workout_id: uuid.UUID
    scheduled_date: date
    workout_plan_exercise_id: uuid.UUID
    exercise_id: str

    # Planned prescription
    planned_sets: int
    reps_min: int
    reps_max: int
    target_rpe_min: float | None
    target_rpe_max: float | None
    planned_weight: float | None
    weight_unit: str

    # Actual performance (completed sets only, ordered by set_number)
    actual_reps: list[int]
    actual_weights: list[float | None]
    actual_rpes: list[float | None]



# ============================================================
# User feedback
# ============================================================

class FeedbackState(TypedDict):
    workout_id: uuid.UUID
    overall_rating: int | None
    comments: str | None
    exercise_feedback: dict[str, object] | None


# ============================================================
# Starting point for new program
# ============================================================

class StartingPointState(TypedDict):
    goal: Goal
    experience_level: ExperienceLevel
    available_equipment: list[str]
    available_days: list[DayOfWeek]
    disliked_exercises: list[str]
    preferred_exercises: list[str]
    limitations: list[str]
    recent_exercises: list[str]


# ============================================================
# Generated 4-week program
# ============================================================

class GeneratedExerciseState(TypedDict):
    exercise_id: str
    exercise_order: int

    sets_planned: int
    reps_min: int
    reps_max: int

    target_rpe_min: float | None
    target_rpe_max: float | None

    rest_seconds: int

    planned_weight: float | None
    weight_unit: str

    progression_method: str | None
    notes: str | None


class GeneratedWorkoutState(TypedDict):
    week_number: int
    day_of_week: DayOfWeek
    scheduled_date: date
    exercises: list[GeneratedExerciseState]


class GeneratedProgramState(TypedDict):
    goal: Goal
    start_date: date
    end_date: date
    workouts: list[GeneratedWorkoutState]


# ============================================================
# Progression
# ============================================================

class ProgressionUpdateState(TypedDict):
    workout_plan_exercise_id: uuid.UUID
    action: ProgressionAction

    new_weight: float | None

    new_reps_min: int | None
    new_reps_max: int | None

    new_sets_planned: int | None

    new_target_rpe_min: float | None
    new_target_rpe_max: float | None

    new_rest_seconds: int | None


# ============================================================
# LangGraph state
# ============================================================

class WorkoutAgentState(TypedDict, total=False):

    # --------------------------------------------------------
    # User
    # --------------------------------------------------------
    user_id: uuid.UUID
    profile: ProfileState
    availability: list[AvailabilityState]

    # --------------------------------------------------------
    # Active program
    # --------------------------------------------------------
    active_program: ProgramState | None
    current_workout: WorkoutState | None
    current_workout_exercises: list[PlannedExerciseState]

    # --------------------------------------------------------
    # Training history
    # --------------------------------------------------------
    recent_performance: list[PerformanceState]

    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------
    workout_feedback: FeedbackState | None

    # --------------------------------------------------------
    # New program generation
    # --------------------------------------------------------
    starting_point: StartingPointState
    candidate_exercises: list[ExerciseCandidateState]
    generated_program: GeneratedProgramState

    # --------------------------------------------------------
    # Progression
    # --------------------------------------------------------
    progression_updates: list[ProgressionUpdateState]

    # --------------------------------------------------------
    # Profile / compatibility
    # --------------------------------------------------------
    profile_changed: bool
    invalid_exercises: list[ExerciseState]
    replacement_exercises: list[ExerciseCandidateState]

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------
    upcoming_workout: WorkoutState | None
    validation_errors: list[str]