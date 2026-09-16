from typing import TypedDict
from backend.agent.exercise import Exercise

class UserProfile(TypedDict):
    user_id: str
    name: str
    email: str
    password: str #encrypted password
    gender: str
    experience_level: str
    goal: str
    days_per_week: int
    days_of_week_available: list
    session_duration: int
    equipment_available: list
    preferred_exercises: list
    excluded_exercises: list
    injuries: list
    health_conditions: list

class WorkoutState(TypedDict):
    user_id: str

    current_program: dict | None
    previous_program: dict | None

    current_week: int

    user_profile: dict
    profile_changes: dict

    workout_history: list
    user_feedback: list

    exercise_candidates: list
    selected_exercises: list

    progression_analysis: list

    generated_plan: dict | None

    validation_errors: list

    plan_status: str
    user_satisfied: bool


class WorkoutPlan(TypedDict):
    user_id: str
    week_number: int
    start_date: str
    end_date: str
    monday: list[Exercise] | None
    tuesday: list[Exercise] | None
    wednesday: list[Exercise] | None
    thursday: list[Exercise] | None
    friday: list[Exercise] | None
    Saturday: list[Exercise] | None
    Sunday: list[Exercise] | None

class Performance(TypedDict):
    exercise_id: str
    target_reps: int
    actual_reps: int
    weight: float | None
    difficulty_level: str

class WorkoutHistory(TypedDict):
    workout_id: str
    user_id: str
    start_date: str
    end_date: str
    weeks: list[WorkoutPlan]
