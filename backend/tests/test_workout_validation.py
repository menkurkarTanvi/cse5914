import uuid

import pytest
from pydantic import ValidationError

from routers.workouts import CompleteWorkoutRequest


def _set(set_number: int = 1, weight_unit: str = "lb") -> dict:
    return {
        "set_number": set_number,
        "reps": 8,
        "weight": 100,
        "weight_unit": weight_unit,
    }


def _exercise(exercise_id: uuid.UUID, sets: list[dict]) -> dict:
    return {
        "workout_plan_exercise_id": exercise_id,
        "sets": sets,
    }


def test_completion_rejects_duplicate_set_numbers():
    with pytest.raises(ValidationError, match="set_number must be unique"):
        CompleteWorkoutRequest.model_validate(
            {
                "exercises": [_exercise(uuid.uuid4(), [_set(1), _set(1)])],
                "feedback": {"difficulty": "great"},
            }
        )


def test_completion_rejects_duplicate_exercises():
    exercise_id = uuid.uuid4()
    with pytest.raises(ValidationError, match="workout_plan_exercise_id must be unique"):
        CompleteWorkoutRequest.model_validate(
            {
                "exercises": [
                    _exercise(exercise_id, [_set()]),
                    _exercise(exercise_id, [_set()]),
                ],
                "feedback": {"difficulty": "great"},
            }
        )


def test_completion_rejects_unknown_weight_unit():
    with pytest.raises(ValidationError):
        CompleteWorkoutRequest.model_validate(
            {
                "exercises": [_exercise(uuid.uuid4(), [_set(weight_unit="stone")])],
                "feedback": {"difficulty": "great"},
            }
        )
