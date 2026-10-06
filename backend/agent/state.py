
from click import UUID
from langchain_protocol import TypedDict

#This is the state of the workout agent. Information is stored here and nodes can access this state
class WorkoutState(TypedDict):
    user_id: UUID

    profile: dict
    availability: list[dict]

    current_program: dict | None
    current_workout: dict | None

    recent_performance: list[dict]
    recent_feedback: list[dict]

    progression_updates: list[dict]

    candidate_exercises: list[dict]

    generated_program: dict | None

    validation_errors: list[str]

    action: str