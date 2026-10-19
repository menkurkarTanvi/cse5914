
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import defer

from agent_chatbot.coach_rules import STOP_WORDS
from agent.state import WorkoutAgentState

if TYPE_CHECKING:
    from models.exercise import Exercise

# AI COACH (chat on the AI Coach page):
#   load_coach_context -> classify_message -> one of
#   ask_follow_up | answer_exercise_question | propose_swap | propose_shorten
#   | propose_adjust | apply_pending_action | decline_pending_action
#   | pending_expired_reply | general_reply
#
# The LLM only classifies the message and writes free-text answers. Whether
# to ask a follow-up, which exercises to offer and what to change in the
# plan are decided by rule-based helpers, so they are testable and every
# change can be explained. Plan changes are only written after the user
# confirms a proposal.
#
# Files:
#   coach.py          state, loading context, free-text answers, name matching
#   coach_intent.py   reading the message: intent, follow-ups, routing
#   coach_swap.py     finding swap options
#   coach_changes.py  shorten/adjust plans, applying confirmed changes
#   agent/coach_rules.py  tunable values


# ============================================================
# State and intent
# ============================================================

class CoachState(WorkoutAgentState, total=False):
    message: str
    history: list[dict]
    # Verified pending action from the previous turn (see sign_pending_action).
    pending: dict | None
    # The client sent a pending action that was expired or invalid.
    pending_expired: bool
    # Set by load_user_context, which the coach reuses.
    recent_workouts: list[dict]

    intent: dict
    follow_up: str | None

    reply: str
    options: list[dict]
    new_pending: dict | None
    plan_changed: bool


IntentName = Literal[
    "exercise_question",
    "swap_exercise",
    "shorten_workout",
    "adjust_difficulty",
    "confirm",
    "decline",
    "other",
]


MODIFY_INTENTS = {"swap_exercise", "shorten_workout", "adjust_difficulty"}

class CoachIntent(BaseModel):
    """What the user wants from the coach in this message."""

    intent: IntentName = Field(
        description=(
            "exercise_question: how to do an exercise, what it works, form, "
            "alternatives in general. swap_exercise: replace an exercise in "
            "today's workout. shorten_workout: make today's workout fit less "
            "time. adjust_difficulty: make today's workout or one exercise "
            "easier or harder. confirm: yes to the coach's proposal, or picking "
            "one of the offered options. decline: no to the proposal. other: "
            "anything else."
        )
    )
    exercise_name: str | None = Field(
        default=None,
        description="The exercise the user means, as they wrote it, if any.",
    )
    minutes_available: int | None = Field(
        default=None,
        description="Minutes the user has for today's workout, if stated.",
    )
    difficulty_direction: Literal["easier", "harder"] | None = Field(
        default=None,
        description="For adjust_difficulty: whether the user wants it easier or harder.",
    )
    reason: str | None = Field(
        default=None,
        description=(
            "Why the user wants the change, in a few words, e.g. 'no barbell', "
            "'knee pain', 'low energy'."
        ),
    )
    selected_option: int | None = Field(
        default=None,
        description="For confirm: the 1-based number of the option the user picked.",
    )


# ============================================================
# Node 1: load context
# ============================================================

async def load_coach_context(state: CoachState) -> dict:
    """Load profile and today's workout with the shared context nodes."""
    from agent.nodes.context import load_user_context
    from agent.nodes.current_program import load_last_workout_plan

    try:
        context = await load_user_context(state)
    except LookupError:
        return {
            "profile": None,
            "reply": "Set up your profile first, then I can coach you through your plan.",
            "intent": {"intent": "other"},
        }

    exercises = await load_last_workout_plan(context)
    return {**context, **exercises}


def has_reply(state: CoachState) -> str:
    return "done" if state.get("reply") else "continue"


# ============================================================
# Exercise questions and general chat (LLM answers)
# ============================================================

async def answer_exercise_question(state: CoachState, llm) -> dict:
    from backend.agent_chatbot.coach_llm import build_answer_messages

    name = state["intent"]["exercise_name"]
    planned = find_workout_exercise(name, state.get("current_workout_exercises") or [])
    details = await _find_exercise_details(planned["exercise"]["exercise_id"] if planned else None, name)

    response = await llm.ainvoke(build_answer_messages(state, details, planned))
    return {"reply": _text(response)}


async def general_reply(state: CoachState, llm) -> dict:
    from backend.agent_chatbot.coach_llm import build_answer_messages

    response = await llm.ainvoke(build_answer_messages(state, None, None))
    return {"reply": _text(response)}


async def _find_exercise_details(exercise_id: str | None, name: str) -> dict | None:
    from database.database import AsyncSessionLocal
    from models.exercise import Exercise

    async with AsyncSessionLocal() as session:
        if exercise_id is not None:
            exercise = await session.get(Exercise, exercise_id)
        else:
            exercise = await _search_exercise_by_name(session, name)
        if exercise is None:
            return None
        return {
            "name": exercise.name,
            "difficulty_level": exercise.difficulty_level,
            "mechanics": exercise.mechanics,
            "primary_muscles": exercise.primary_muscles or [],
            "secondary_muscles": exercise.secondary_muscles or [],
            "equipment_required": exercise.equipment_required or [],
            "instructions": exercise.instructions,
        }


async def _search_exercise_by_name(session, name: str) -> Exercise | None:
    from models.exercise import Exercise

    words = _words(name)
    if not words:
        return None
    query = select(Exercise).options(defer(Exercise.embedding))
    for word in words:
        query = query.where(Exercise.name.ilike(f"%{word}%"))
    # Shortest name is usually the plain version ("Barbell Squat").
    query = query.order_by(func.length(Exercise.name), Exercise.name).limit(1)
    return await session.scalar(query)


def _text(response) -> str:
    content = response.content
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return content.strip()


# ============================================================
# Matching exercise names
# ============================================================

def find_workout_exercise(name: str | None, exercises: list[dict]) -> dict | None:
    """The planned exercise the user means by ``name``, or None.

    Every word the user gave has to appear in the exercise's name, so
    "bench" matches "Barbell Bench Press - Medium Grip" but "dumbbell curl"
    doesn't match "Dumbbell Flyes". If several exercises match, an exact
    name wins; otherwise it's ambiguous, so None.
    """
    if not name or not exercises:
        return None
    wanted = _words(name)
    if not wanted:
        return None

    matches = []
    for item in exercises:
        have = _words(item["exercise"]["name"])
        joined_match = _singular("".join(wanted)) == _singular("".join(have))  # "push-ups" vs "Pushups"
        if joined_match or all(_word_matches(word, have) for word in wanted):
            matches.append((set(have) == set(wanted) or joined_match, item))

    if len(matches) == 1:
        return matches[0][1]
    exact = [item for is_exact, item in matches if is_exact]
    return exact[0] if len(exact) == 1 else None


def _word_matches(word: str, have: list[str]) -> bool:
    # Whole words only, except that a longer word may be the start of one
    # ("pull" for "Pullups"). Short words like "row" must match exactly.
    return word in have or (len(word) >= 4 and any(h.startswith(word) for h in have))


def find_workout_exercise_in_text(text: str, exercises: list[dict]) -> dict | None:
    """The one planned exercise whose full name appears in ``text``, if any."""
    words = f" {' '.join(_words(text))} "
    matches = [
        item for item in exercises
        if f" {' '.join(_words(item['exercise']['name']))} " in words
    ]
    return matches[0] if len(matches) == 1 else None


def _words(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    # Single letters are leftovers like the "s" in "today's".
    return [_singular(word) for word in words if word not in STOP_WORDS and len(word) > 1]


def _singular(word: str) -> str:
    # "squats" -> "squat", "crunches" -> "crunch", but "press" stays "press".
    if len(word) <= 3 or word.endswith("ss"):
        return word
    if word.endswith(("ches", "shes", "xes")):
        return word[:-2]
    if word.endswith("s"):
        return word[:-1]
    return word
