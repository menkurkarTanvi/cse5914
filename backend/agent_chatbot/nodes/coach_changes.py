
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import func, select
from sqlalchemy.orm.exc import StaleDataError

from agent_chatbot.coach_rules import (
    ACCESSORY_MIN_SETS, EASIER_RPE_SHIFT, EASIER_WEIGHT_FACTOR, HARDER_RPE_SHIFT,
    HARDER_WEIGHT_FACTOR, MAX_SETS, MIN_SETS, PENDING_ACTION_AUDIENCE, PENDING_ACTION_MINUTES,
)
from agent_chatbot.nodes.coach import CoachState, find_workout_exercise
from agent.nodes.new_program import _estimate_seconds

# AI coach: propose changes to today's workout (shorten, easier/harder),
# then write a proposal once the user confirms it.


# ============================================================
# Shorten the workout
# ============================================================

async def propose_shorten(state: CoachState) -> dict:
    exercises = state["current_workout_exercises"]
    minutes = state["intent"]["minutes_available"]
    planned_minutes = workout_minutes(exercises)

    if planned_minutes <= minutes:
        return {
            "reply": (
                f"Good news: today's workout is about {planned_minutes} minutes, "
                f"so it already fits in {minutes}. No changes needed."
            ),
        }

    changes = plan_shorten(exercises, minutes)
    new_minutes = workout_minutes(apply_changes_preview(exercises, changes))
    lines = [f"To fit {minutes} minutes (from about {planned_minutes}), I'd:"]
    lines += [f"- {describe_change(change)}" for change in changes]
    lines.append(f"That brings it to about {new_minutes} minutes.")
    if new_minutes > minutes:
        lines.append("It's still a bit over, but cutting more would leave very little work.")
    lines.append("I kept your first exercises, since they're the main lifts. Want me to make this change?")

    return {
        "reply": "\n".join(lines),
        "new_pending": {
            "type": "changes",
            "summary": f"shorten today's workout to {minutes} minutes",
            "done": f"Done. Today's workout now takes about {new_minutes} minutes.",
            "changes": changes,
        },
    }


def workout_minutes(exercises: list[dict]) -> int:
    seconds = sum(
        _estimate_seconds(item["sets_planned"], {"rest_seconds": item["rest_seconds"]})
        for item in exercises
    )
    return round(seconds / 60)


def plan_shorten(exercises: list[dict], minutes: int) -> list[dict]:
    """Cut the workout down until it fits, in three steps, stopping as soon
    as it fits:
    1. trim accessory exercises (everything after the first) to 2 sets,
    2. drop exercises from the end,
    3. trim the remaining sets down to 1.
    The first exercise (the main lift) is never dropped."""
    target = minutes * 60
    remaining = sorted(exercises, key=lambda item: item["exercise_order"])
    sets = {str(item["workout_plan_exercise_id"]): item["sets_planned"] for item in remaining}
    changes = []

    def total() -> int:
        return sum(
            _estimate_seconds(sets[str(item["workout_plan_exercise_id"])], {"rest_seconds": item["rest_seconds"]})
            for item in remaining
        )

    def trim(items: list[dict], floor: int) -> None:
        trimmed = True
        while total() > target and trimmed:
            trimmed = False
            for item in reversed(items):
                key = str(item["workout_plan_exercise_id"])
                if sets[key] > floor and total() > target:
                    sets[key] -= 1
                    trimmed = True

    trim(remaining[1:], ACCESSORY_MIN_SETS)

    while total() > target and len(remaining) > 1:
        dropped = remaining.pop()
        sets[str(dropped["workout_plan_exercise_id"])] = dropped["sets_planned"]
        changes.append(_change(dropped, action="remove"))

    trim(remaining, MIN_SETS)

    for item in remaining:
        key = str(item["workout_plan_exercise_id"])
        if sets[key] != item["sets_planned"]:
            changes.append(_change(item, action="update", sets_planned=sets[key]))
    return changes


# ============================================================
# Adjust difficulty
# ============================================================

async def propose_adjust(state: CoachState) -> dict:
    intent = state["intent"]
    exercises = state["current_workout_exercises"]
    direction = intent["difficulty_direction"]
    target = find_workout_exercise(intent.get("exercise_name"), exercises)

    changes = plan_adjust(exercises, direction, target)
    scope = target["exercise"]["name"] if target else "today's workout"
    if not changes:
        return {
            "reply": (
                f"I can't make {scope} any {direction} without changing "
                "exercises. Want to swap an exercise instead?"
            ),
        }

    lines = [f"To make {scope} {direction}, I'd:"]
    lines += [f"- {describe_change(change)}" for change in changes]
    lines.append("Want me to make this change?")
    return {
        "reply": "\n".join(lines),
        "new_pending": {
            "type": "changes",
            "summary": f"make {scope} {direction}",
            "done": f"Done. I made {scope} {direction}.",
            "changes": changes,
        },
    }


def plan_adjust(exercises: list[dict], direction: str, target: dict | None) -> list[dict]:
    """Harder: one more set, +0.5 RPE, +5% weight. Easier: one fewer set,
    -1 RPE, -10% weight. Applies to one exercise or the whole workout."""
    harder = direction == "harder"
    selected = [target] if target else exercises
    changes = []
    for item in sorted(selected, key=lambda entry: entry["exercise_order"]):
        # Never move sets the wrong way: "harder" on 8 planned sets keeps 8.
        if harder:
            sets = item["sets_planned"] + 1 if item["sets_planned"] < MAX_SETS else item["sets_planned"]
        else:
            sets = max(MIN_SETS, item["sets_planned"] - 1)

        shift = HARDER_RPE_SHIFT if harder else EASIER_RPE_SHIFT
        rpe_min = _shift_rpe(item["target_rpe_min"], shift)
        rpe_max = _shift_rpe(item["target_rpe_max"], shift)

        weight = item["planned_weight"]
        if weight:
            weight = _round_weight(weight * (HARDER_WEIGHT_FACTOR if harder else EASIER_WEIGHT_FACTOR))

        updates = {}
        if sets != item["sets_planned"]:
            updates["sets_planned"] = sets
        if rpe_min != item["target_rpe_min"] or rpe_max != item["target_rpe_max"]:
            updates["target_rpe_min"] = rpe_min
            updates["target_rpe_max"] = rpe_max
        if weight != item["planned_weight"]:
            updates["planned_weight"] = weight
        if updates:
            changes.append(_change(item, action="update", **updates))
    return changes


def _shift_rpe(value: float | None, shift: float) -> float | None:
    if value is None:
        return None
    return max(0.0, min(10.0, value + shift))


def _round_weight(weight: float) -> float:
    # Nearest 2.5, the smallest common plate jump.
    return round(weight / 2.5) * 2.5


# ============================================================
# Proposals: apply or decline
# ============================================================

def _change(item: dict, action: str, **updates) -> dict:
    return {
        "workout_plan_exercise_id": str(item["workout_plan_exercise_id"]),
        "name": item["exercise"]["name"],
        "action": action,
        "before": {key: item[key] for key in updates},
        "updates": updates,
    }


def describe_change(change: dict) -> str:
    if change["action"] == "remove":
        return f"skip {change['name']}"
    parts = []
    updates, before = change["updates"], change["before"]
    if "sets_planned" in updates:
        parts.append(f"{before['sets_planned']} → {updates['sets_planned']} sets")
    if "target_rpe_max" in updates and updates["target_rpe_max"] is not None:
        parts.append(f"target RPE {_fmt(updates['target_rpe_min'])}-{_fmt(updates['target_rpe_max'])}")
    if "planned_weight" in updates:
        parts.append(f"weight {_fmt(before['planned_weight'])} → {_fmt(updates['planned_weight'])}")
    return f"{change['name']}: {', '.join(parts)}"


def _fmt(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:g}"


def apply_changes_preview(exercises: list[dict], changes: list[dict]) -> list[dict]:
    by_id = {change["workout_plan_exercise_id"]: change for change in changes}
    preview = []
    for item in exercises:
        change = by_id.get(str(item["workout_plan_exercise_id"]))
        if change is None:
            preview.append(item)
        elif change["action"] != "remove":
            preview.append({**item, **change["updates"]})
    return preview


async def apply_pending_action(state: CoachState) -> dict:
    """Write the confirmed proposal to the user's current workout."""
    from database.database import AsyncSessionLocal
    from models.workout_plan_exercise import WorkoutPlanExercise
    from models.workout_set import WorkoutSet

    pending = state["pending"]
    current_ids = {
        str(item["workout_plan_exercise_id"]) for item in state.get("current_workout_exercises") or []
    }

    if pending["type"] == "swap":
        options = pending["options"]
        choice = state["intent"].get("selected_option")
        if choice is None and len(options) == 1:
            choice = 1
        if choice is None or not 1 <= choice <= len(options):
            numbers = ", ".join(str(n) for n in range(1, len(options) + 1))
            return {
                "reply": f"Which option do you want? Reply with {numbers}.",
                "new_pending": pending,
                "options": [{"number": n, **option} for n, option in enumerate(options, start=1)],
            }
        changes = [{
            "workout_plan_exercise_id": pending["workout_plan_exercise_id"],
            "action": "swap",
            "exercise_id": options[choice - 1]["exercise_id"],
            "note": f"Swapped from {pending['from_name']} by AI coach"
                    + (f": {pending['reason']}" if pending.get("reason") else ""),
        }]
        done = f"Done. {options[choice - 1]['name']} replaces {pending['from_name']} in today's workout."
    else:
        changes = pending["changes"]
        done = pending["done"]

    if any(change["workout_plan_exercise_id"] not in current_ids for change in changes):
        # The workout moved on (completed, or a new one is up) since the proposal.
        return {"reply": WORKOUT_CHANGED_REPLY}

    workout_id = state["current_workout"]["workout_id"]
    async with AsyncSessionLocal() as session:
        # Re-check inside the write: a second "yes" sent at the same time may
        # already have removed these rows.
        rows = []
        for change in changes:
            row = await session.get(WorkoutPlanExercise, uuid.UUID(change["workout_plan_exercise_id"]))
            if row is None or row.workout_id != workout_id:
                return {"reply": WORKOUT_CHANGED_REPLY}
            rows.append(row)

        # Removing or swapping an exercise would drop or mislabel sets the
        # user already logged, so leave those alone.
        logged = await session.scalar(
            select(func.count(WorkoutSet.set_id)).where(
                WorkoutSet.workout_plan_exercise_id.in_([row.id for row in rows])
            )
        )
        if logged:
            return {
                "reply": (
                    "You've already logged sets for an exercise this would change, "
                    "so I left today's workout as it is."
                ),
            }

        for change, row in zip(changes, rows):
            if change["action"] == "remove":
                await session.delete(row)
            elif change["action"] == "swap":
                row.exercise_id = change["exercise_id"]
                row.notes = change["note"]
                # The old exercise's weight doesn't carry over to a new one.
                row.planned_weight = None
            else:
                for key, value in change["updates"].items():
                    setattr(row, key, value)
        try:
            await session.commit()
        except StaleDataError:
            # Another request changed the same rows first.
            await session.rollback()
            return {"reply": WORKOUT_CHANGED_REPLY}

    return {"reply": done, "plan_changed": True}


WORKOUT_CHANGED_REPLY = "Your workout has changed since I suggested that, so I didn't apply it. Ask me again?"

async def decline_pending_action(state: CoachState) -> dict:
    return {"reply": "No problem, I left your workout as it is. Anything else?"}


# ============================================================
# Pending actions travel through the client, signed
# ============================================================

def sign_pending_action(pending: dict, user_id: uuid.UUID | str) -> str:
    """The client sends this back next turn. Signing it means a user can't
    edit the proposal (another user's workout, an unlisted exercise)."""
    from core.auth import ALGORITHM, SECRET_KEY

    claims = {
        "sub": str(user_id),
        # The audience claim stops this working as a login token: decoding
        # without audience=... (as core/auth does) rejects it.
        "aud": PENDING_ACTION_AUDIENCE,
        "pending": pending,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=PENDING_ACTION_MINUTES),
    }
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def verify_pending_action(token: str | None, user_id: uuid.UUID | str) -> dict | None:
    """The pending action, or None if missing, expired or not this user's."""
    from core.auth import ALGORITHM, SECRET_KEY

    if not token:
        return None
    try:
        claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=PENDING_ACTION_AUDIENCE)
    except jwt.PyJWTError:
        return None
    if claims.get("sub") != str(user_id):
        return None
    return claims["pending"]
