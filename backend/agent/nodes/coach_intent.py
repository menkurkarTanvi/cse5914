
from __future__ import annotations

import re

from agent.coach_rules import FOLLOW_UP_FIELDS, NOT_MINUTES, WHOLE_WORKOUT
from agent.nodes.coach import (
    MODIFY_INTENTS, CoachIntent, CoachState, find_workout_exercise,
    find_workout_exercise_in_text,
)
from agent.nodes.coach_changes import workout_minutes

# AI coach, step 2: what does the user want, is anything missing, and which
# node answers. See agent/nodes/coach.py for the whole flow.


# ============================================================
# Node 2: classify the message
# ============================================================

async def classify_message(state: CoachState, llm) -> dict:
    """Ask the LLM for intent and details, then decide on a follow-up."""
    from agent.coach_llm import build_classifier_messages

    structured = llm.with_structured_output(CoachIntent)
    result = await structured.ainvoke(build_classifier_messages(state))
    if result is None:
        # The model returned nothing usable; answer as plain chat.
        result = CoachIntent(intent="other")

    exercises = state.get("current_workout_exercises") or []
    intent = resolve_intent(result.model_dump(), state.get("pending"), state["message"], exercises)

    # If the model missed which exercise was meant, look for one by name in
    # the message itself ("Barbell Lunge, no barbell today").
    if (
        intent["intent"] in MODIFY_INTENTS
        and not intent.get("whole_workout")
        and find_workout_exercise(intent.get("exercise_name"), exercises) is None
    ):
        match = find_workout_exercise_in_text(state["message"], exercises)
        if match is not None:
            intent["exercise_name"] = match["exercise"]["name"]

    return {
        "intent": intent,
        "follow_up": follow_up_question(intent, state),
    }


def resolve_intent(intent: dict, pending: dict | None, message: str, exercises: list[dict]) -> dict:
    """Combine this turn's classification with an open follow-up question.

    After "How much time do you have?", a reply like "30" can come back as
    `other`; it still answers the earlier question, so the earlier intent is
    kept and the new detail is filled in. A reply that answers nothing
    ("how much protein should I eat?") starts fresh instead.
    """
    intent = dict(intent)
    earlier = pending["intent"] if pending and pending.get("type") == "follow_up" else None

    # "Make the whole workout harder": only difficulty changes apply to the
    # whole workout, so don't clear exercise names for other requests.
    about_difficulty = "adjust_difficulty" in (intent["intent"], earlier and earlier["intent"])
    named_whole = WHOLE_WORKOUT.search((intent.get("exercise_name") or "").lower())
    if about_difficulty and (named_whole or WHOLE_WORKOUT.search(message.lower())):
        intent["whole_workout"] = True
        intent["exercise_name"] = None

    if intent.get("minutes_available") is None:
        # A bare "30" only means minutes when that's what we just asked.
        expecting_minutes = earlier is not None and earlier["intent"] == "shorten_workout"
        intent["minutes_available"] = parse_minutes(message, allow_bare=expecting_minutes)

    if earlier is None:
        return intent
    if intent["intent"] == earlier["intent"]:
        return _merge_intent(earlier, intent)
    if intent["intent"] in ("other", "confirm"):
        fields = FOLLOW_UP_FIELDS.get(earlier["intent"], ())
        if "exercise_name" in fields and not intent.get("exercise_name"):
            match = find_workout_exercise_in_text(message, exercises)
            if match is not None:
                intent["exercise_name"] = match["exercise"]["name"]
        if any(intent.get(field) for field in fields):
            return _merge_intent(earlier, intent)
    # The user moved on to something else.
    return intent


def _merge_intent(earlier: dict, intent: dict) -> dict:
    merged = dict(earlier)
    for key, value in intent.items():
        if key != "intent" and value is not None:
            merged[key] = value
    if intent.get("whole_workout"):
        merged["exercise_name"] = None
    return merged


def parse_minutes(message: str, allow_bare: bool = False) -> int | None:
    """Minutes stated in the message ("40 min", "1h30", "an hour and a half").
    A bare number ("30") only counts when ``allow_bare`` is set."""
    text = message.lower()

    hours_and_minutes = re.search(r"(\d+)\s*(?:h|hrs?|hours?)\s*(?:and\s*)?(\d+)\s*(?:m|mins?|minutes?)?\b", text)
    if hours_and_minutes:
        return int(hours_and_minutes.group(1)) * 60 + int(hours_and_minutes.group(2))
    and_a_half = re.search(r"(\d+|an|one|\b)\s*(?:h|hrs?|hours?) and a half\b", text)
    if and_a_half:
        hours = int(and_a_half.group(1)) if and_a_half.group(1).isdigit() else 1
        return hours * 60 + 30
    hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:h|hrs?|hours?)\b", text)
    if hours:
        return round(float(hours.group(1)) * 60)
    if re.search(r"\bhalf an hour\b", text):
        return 30
    if re.search(r"\b(?:an|one) hour\b", text):
        return 60
    minutes = re.search(r"(\d+)\s*(?:m|mins?|minutes?)\b", text)
    if minutes:
        return int(minutes.group(1))
    if allow_bare:
        bare = re.fullmatch(rf"\D{{0,20}}?(\d+)(?!\d|{NOT_MINUTES})\D{{0,20}}", text.strip())
        if bare:
            return int(bare.group(1))
    return None


def follow_up_question(intent: dict, state: CoachState) -> str | None:
    """The question to ask when the request is missing something, else None."""
    name = intent["intent"]
    exercises = state.get("current_workout_exercises") or []

    if name in MODIFY_INTENTS and not exercises:
        # Nothing to modify; handled as a plain reply, not a question.
        return None

    if name == "swap_exercise":
        if find_workout_exercise(intent.get("exercise_name"), exercises) is None:
            return (
                "Which exercise do you want to swap? Today you have: "
                f"{_list_names(exercises)}."
            )

    if name == "shorten_workout":
        minutes = intent.get("minutes_available")
        if minutes is None or minutes <= 0:
            return (
                "How much time do you have today? Your workout is planned "
                f"for about {workout_minutes(exercises)} minutes."
            )

    if name == "adjust_difficulty":
        if intent.get("difficulty_direction") is None:
            return "Do you want today's workout to be easier or harder?"
        named = intent.get("exercise_name")
        if named and find_workout_exercise(named, exercises) is None:
            return (
                f"I couldn't find {named} in today's workout. Which exercise did "
                f"you mean? Today you have: {_list_names(exercises)}. "
                "Or say \"the whole workout\"."
            )

    if name == "exercise_question" and not intent.get("exercise_name"):
        return "Which exercise are you asking about?"

    return None


def route_after_classify(state: CoachState) -> str:
    intent = state["intent"]["intent"]
    pending = state.get("pending")
    proposal = pending if pending and pending.get("type") != "follow_up" else None

    if state.get("follow_up"):
        return "ask_follow_up"
    if intent == "confirm" and proposal:
        return "apply_pending_action"
    if intent == "decline" and proposal:
        return "decline_pending_action"
    if intent in ("confirm", "decline") and state.get("pending_expired"):
        # Don't let the LLM answer "yes" as if something had been applied.
        return "pending_expired_reply"
    if intent in MODIFY_INTENTS and not state.get("current_workout_exercises"):
        return "general_reply"
    return {
        "exercise_question": "answer_exercise_question",
        "swap_exercise": "propose_swap",
        "shorten_workout": "propose_shorten",
        "adjust_difficulty": "propose_adjust",
    }.get(intent, "general_reply")


# ============================================================
# Follow-up
# ============================================================

async def ask_follow_up(state: CoachState) -> dict:
    # Remember what was asked so the answer can be combined next turn.
    return {
        "reply": state["follow_up"],
        "new_pending": {"type": "follow_up", "intent": state["intent"]},
    }


async def pending_expired_reply(state: CoachState) -> dict:
    return {
        "reply": (
            "That suggestion expired, so I didn't change anything. "
            "Ask me again and I'll make a fresh one."
        ),
    }


def _list_names(exercises: list[dict]) -> str:
    return ", ".join(item["exercise"]["name"] for item in sorted(exercises, key=lambda e: e["exercise_order"]))
