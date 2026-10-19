
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sqlalchemy import Text, bindparam, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import defer

from agent.coach_rules import PAIN_WORDS, SWAP_OPTION_COUNT, UNAVAILABLE_AFTER, UNAVAILABLE_BEFORE
from agent.nodes.coach import CoachState, find_workout_exercise
from agent.nodes.new_program import _clean_terms, is_exercise_allowed, normalize_equipment, score_exercise
from agent.program_rules import (
    ALWAYS_AVAILABLE_EQUIPMENT, BASE_CATEGORIES, EQUIPMENT_ALIASES,
    EQUIPMENT_PREFERENCE, EXTRA_CATEGORIES_BY_GOAL, STAPLE_KEYWORDS,
)

if TYPE_CHECKING:
    from models.exercise import Exercise

# AI coach: offer replacements for one exercise in today's workout. The
# swap itself is written by apply_pending_action once the user picks one.


# ============================================================
# Swap an exercise
# ============================================================

async def propose_swap(state: CoachState) -> dict:
    from database.database import AsyncSessionLocal
    from models.exercise import Exercise

    intent = state["intent"]
    exercises = state["current_workout_exercises"]
    planned = find_workout_exercise(intent["exercise_name"], exercises)
    original = planned["exercise"]
    starting_point = coach_starting_point(state["profile"])
    goal = starting_point["goal"]
    categories = BASE_CATEGORIES | EXTRA_CATEGORIES_BY_GOAL.get(goal, set())

    async with AsyncSessionLocal() as session:
        candidates = (
            await session.scalars(
                select(Exercise)
                .where(
                    Exercise.category.in_(categories),
                    # Postgres "&&": shares at least one primary muscle. The
                    # column is the generic ARRAY type, which has no .overlap().
                    Exercise.primary_muscles.op("&&")(
                        bindparam("muscles", original["primary_muscles"], type_=postgresql.ARRAY(Text))
                    ),
                )
                .options(defer(Exercise.embedding), defer(Exercise.searchable_text))
            )
        ).all()

    in_workout = {item["exercise"]["exercise_id"] for item in exercises}
    # Filter on the user's own words too, in case the model left out the
    # reason ("Bench Press, no barbell today").
    reason_text = " ".join(part for part in (intent.get("reason"), state["message"]) if part)
    options = rank_alternatives(original, candidates, starting_point, in_workout, reason_text)

    if not options:
        return {
            "reply": (
                f"I couldn't find a safe replacement for {original['name']} with "
                "your equipment and limitations. You could skip it today, or "
                "update your profile if your equipment has changed."
            ),
        }

    lines = [f"Here are {len(options)} swaps for {original['name']}:"]
    for number, option in enumerate(options, start=1):
        lines.append(f"{number}. {option['name']} ({option['reason']})")
    lines.append("Which one do you want? Your sets and reps stay the same.")

    return {
        "reply": "\n".join(lines),
        "options": [{"number": n, **option} for n, option in enumerate(options, start=1)],
        "new_pending": {
            "type": "swap",
            "workout_plan_exercise_id": str(planned["workout_plan_exercise_id"]),
            "from_name": original["name"],
            "reason": intent.get("reason"),
            "options": options,
        },
    }


def coach_starting_point(profile: dict) -> dict:
    """The parts of new_program's starting point that exercise filtering uses."""
    return {
        "goal": profile["goal"],
        "experience_level": profile["experience_level"],
        "available_equipment": sorted(normalize_equipment(profile.get("available_equipment") or [])),
        "disliked_exercises": _clean_terms(profile.get("disliked_exercises")),
        "preferred_exercises": _clean_terms(profile.get("preferred_exercises")),
        "limitations": _clean_terms(profile.get("limitations")),
        "recent_exercises": [],
    }


def rank_alternatives(
    original: dict,
    candidates: list[Exercise],
    starting_point: dict,
    exclude_ids: set[str],
    reason: str | None,
    count: int = SWAP_OPTION_COUNT,
) -> list[dict]:
    """Best replacements for ``original``: same muscles, allowed for this user,
    and respecting the reason for the swap ("no barbell", "knee pain")."""
    point = dict(starting_point)
    unavailable = unavailable_equipment(reason)
    point["available_equipment"] = sorted(
        (set(point["available_equipment"]) - unavailable) | ALWAYS_AVAILABLE_EQUIPMENT
    )
    if is_pain_reason(reason):
        # "Tweaked my knee" becomes a limitation for this swap. Other reasons
        # don't, so "the shoulder press machine is taken" isn't an injury.
        point["limitations"] = [*point["limitations"], reason.lower()]

    original_muscles = {muscle.lower() for muscle in original["primary_muscles"]}
    scored = []
    for exercise in candidates:
        if exercise.exercise_id in exclude_ids or exercise.exercise_id == original["exercise_id"]:
            continue
        if not is_exercise_allowed(exercise, point):
            continue
        score, why = _alternative_score(exercise, original, original_muscles, point)
        scored.append((score, exercise.name, exercise, why))

    # Same tie-break as new_program: shorter name, then alphabetical.
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return [
        {
            "exercise_id": exercise.exercise_id,
            "name": exercise.name,
            "equipment_required": exercise.equipment_required or [],
            "reason": why,
        }
        for _, _, exercise, why in scored[:count]
    ]


def _alternative_score(
    exercise: Exercise,
    original: dict,
    original_muscles: set[str],
    starting_point: dict,
) -> tuple[float, str]:
    muscles = {muscle.lower() for muscle in exercise.primary_muscles or []}
    shared = muscles & original_muscles
    score = 3.0 * len(shared) / max(len(original_muscles), 1)

    if original.get("substitution_group") and exercise.substitution_group == original["substitution_group"]:
        score += 3.0
    if original.get("movement_pattern") and exercise.movement_pattern == original["movement_pattern"]:
        score += 2.0
    if original.get("exercise_family") and exercise.exercise_family == original["exercise_family"]:
        score += 1.0

    score += score_exercise(exercise, starting_point)
    score += min(
        (EQUIPMENT_PREFERENCE.get(item.lower(), 0.0) for item in exercise.equipment_required or []),
        default=0.0,
    ) / 2
    if any(keyword in exercise.name.lower() for keyword in STAPLE_KEYWORDS):
        score += 0.75

    equipment = ", ".join(item.lower() for item in exercise.equipment_required or []) or "no equipment"
    why = f"works {', '.join(sorted(shared)) or 'the same area'}; {equipment}"
    return score, why


def unavailable_equipment(reason: str | None) -> set[str]:
    """Equipment a reason rules out: "no barbell, dumbbells are fine" rules
    out the barbell only."""
    if not reason:
        return set()
    text = reason.lower()

    names = {name: name for name in (
        "barbell", "dumbbell", "cable", "machine", "kettlebells", "bands",
        "medicine ball", "exercise ball", "e-z curl bar",
    )}
    names.update({alias: target for alias, target in EQUIPMENT_ALIASES.items() if isinstance(target, str)})

    found = set()
    for word, target in names.items():
        if target in ALWAYS_AVAILABLE_EQUIPMENT:
            continue
        name = re.escape(word)
        if re.search(rf"{UNAVAILABLE_BEFORE}{name}", text) or re.search(rf"\b{name}{UNAVAILABLE_AFTER}", text):
            found.add(target)
    return found


def is_pain_reason(reason: str | None) -> bool:
    if not reason:
        return False
    text = f"{reason.lower()} "
    return any(word in text for word in PAIN_WORDS)
