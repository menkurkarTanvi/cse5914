"""Shared fakes for the AI coach tests: a fake LLM that returns a fixed
classification, an in-memory workout, and a helper that runs the graph."""

import asyncio
import uuid
from types import SimpleNamespace

from langchain_core.messages import AIMessage

from backend.agent_chatbot.coach_graph import build_coach_graph
from backend.agent_chatbot.nodes.coach import CoachIntent


USER_ID = uuid.uuid4()

WORKOUT_ID = uuid.uuid4()

class FakeLLM:
    def __init__(self, intent: dict, answer: str = "Fake answer."):
        self.intent = CoachIntent(**intent)
        self.answer = answer
        self.calls = []

    def with_structured_output(self, schema):
        return SimpleNamespace(ainvoke=self._classify)

    async def _classify(self, messages):
        self.calls.append(messages)
        return self.intent

    async def ainvoke(self, messages):
        self.calls.append(messages)
        return AIMessage(self.answer)


def planned(order, name, sets=3, rest=90, weight=None, rpe=(7.0, 8.0), muscles=("Chest",)):
    return {
        "workout_plan_exercise_id": uuid.uuid4(),
        "exercise_order": order,
        "sets_planned": sets,
        "reps_min": 8,
        "reps_max": 12,
        "target_rpe_min": rpe[0],
        "target_rpe_max": rpe[1],
        "rest_seconds": rest,
        "planned_weight": weight,
        "weight_unit": "lb",
        "progression_method": None,
        "notes": None,
        "exercise": {
            "exercise_id": name.lower().replace(" ", "_"),
            "name": name,
            "primary_muscles": list(muscles),
            "equipment_required": ["Barbell"],
            "substitution_group": None,
            "movement_pattern": None,
            "exercise_family": None,
        },
    }


def workout():
    return [
        planned(1, "Barbell Bench Press - Medium Grip", sets=4, rest=120, weight=145.0),
        planned(2, "Barbell Squat", sets=4, rest=120, weight=185.0, muscles=("Quadriceps",)),
        planned(3, "Dumbbell Flyes", sets=3, rest=60),
        planned(4, "Triceps Pushdown", sets=3, rest=60, muscles=("Triceps",)),
    ]


PROFILE = {
    "user_id": USER_ID,
    "goal": "hypertrophy",
    "experience_level": "intermediate",
    "available_equipment": ["Full gym"],
    "preferred_exercises": [],
    "disliked_exercises": [],
    "limitations": [],
}

def fake_context(exercises):
    async def load(state):
        return {
            "profile": PROFILE,
            "current_workout": {"workout_id": WORKOUT_ID, "day_of_week": "monday", "scheduled_date": "2026-10-19"},
            "current_workout_exercises": exercises,
        }
    return load


def run(intent, message, exercises=None, pending=None, answer="Fake answer."):
    llm = FakeLLM(intent, answer)
    graph = build_coach_graph(llm, load_context=fake_context(workout() if exercises is None else exercises))
    state = {"user_id": USER_ID, "message": message, "history": [], "pending": pending}
    return asyncio.run(graph.ainvoke(state)), llm


def make_exercise(exercise_id, name, primary, equipment, difficulty="beginner", category="strength"):
    return SimpleNamespace(
        exercise_id=exercise_id, name=name, difficulty_level=difficulty, category=category,
        mechanics="compound", primary_muscles=primary, secondary_muscles=[],
        equipment_required=equipment, exercise_family=None, movement_pattern=None,
        training_role=None, unilateral=None, load_type=None, progression_methods=None,
        substitution_group=None, goal_suitability=None, mobility_requirements=None,
        balance_requirement=None, stability_requirement=None, fatigue_cost=None,
    )
