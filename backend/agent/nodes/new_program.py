from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import defer

from backend.agent_chatbot.program_rules import (
    PROGRAM_WEEKS, DEFAULT_WEIGHT_UNIT, DAY_ORDER, MAX_DAYS_BY_EXPERIENCE,
    MAX_EXERCISES_BY_EXPERIENCE, ALLOWED_DIFFICULTY, PREFERRED_DIFFICULTY,
    BASE_CATEGORIES, EXTRA_CATEGORIES_BY_GOAL, ALWAYS_AVAILABLE_EQUIPMENT,
    EQUIPMENT_ALIASES, LIMITATION_RULES,
    EQUIPMENT_PREFERENCE, LOADED_GOALS, STAPLE_KEYWORDS,
    FALLBACK_PRESCRIPTIONS, SECONDS_PER_SET, SETUP_SECONDS_PER_EXERCISE,
    RPE_SHIFT_BY_WEEK, DELOAD_WEEK, DELOAD_SET_FACTOR, DELOAD_RPE_DROP,
    DELOAD_WEIGHT_FACTOR,
    Slot, DAY_TEMPLATES, SPLITS_BY_DAYS,
)
from agent.state import WorkoutAgentState

if TYPE_CHECKING:
    from models.exercise import Exercise
    from models.exercise_prescription import ExercisePrescription

#PLEASE REFER TO THE WORKOUTAGENTSTATE. This state is common amongst all nodes in the graph
#Each function will perform some operations to update the WorkoutAgentState
#
# NEW PROGRAM PATH (see agent/agent.txt):
#   analyze_starting_point -> retrieve_candidate_exercises
#   -> generate_4_week_program -> validate_program -> save_program
# Rule based (no LLM call). Tunable values live in agent/program_rules.py.


# ============================================================
# Node 1: analyze starting point
# ============================================================

async def analyze_starting_point(state: WorkoutAgentState) -> dict:
    """Condense profile, availability and history into starting_point."""
    profile = state.get("profile")
    if profile is None:
        raise ValueError("analyze_starting_point needs state['profile']")

    available_days = sorted(
        {
            item["day_of_week"].lower()
            for item in state.get("availability") or []
            if item["is_available"]
        },
        key=DAY_ORDER.index,
    )
    if not available_days:
        raise ValueError("User has no available training days")

    recent_exercises = list(
        dict.fromkeys(
            item["exercise_id"] for item in state.get("recent_performance") or []
        )
    )

    starting_point = {
        "goal": profile["goal"],
        "experience_level": profile["experience_level"],
        "available_equipment": sorted(
            normalize_equipment(profile.get("available_equipment") or [])
        ),
        "available_days": available_days,
        "disliked_exercises": _clean_terms(profile.get("disliked_exercises")),
        "preferred_exercises": _clean_terms(profile.get("preferred_exercises")),
        "limitations": _clean_terms(profile.get("limitations")),
        "recent_exercises": recent_exercises,
    }
    return {"starting_point": starting_point}


def normalize_equipment(raw: list[str]) -> set[str]:
    equipment = set(ALWAYS_AVAILABLE_EQUIPMENT)
    for item in raw:
        key = " ".join(item.lower().split())
        mapped = EQUIPMENT_ALIASES.get(key, key)
        if isinstance(mapped, set):
            equipment |= mapped
        else:
            equipment.add(mapped)
    return equipment


def _clean_terms(values: list[str] | None) -> list[str]:
    cleaned = (" ".join(value.lower().split()) for value in values or [])
    return [value for value in cleaned if value and value != "none"]


# ============================================================
# Node 2: retrieve candidate exercises
# ============================================================

#Candidate exercises for the next 4 week workout plan
async def retrieve_candidate_exercises(state: WorkoutAgentState) -> dict:
    """Load allowed exercises, each with a 0-1 similarity_score and a
    goal-specific prescription."""
    starting_point = state.get("starting_point")
    if starting_point is None:
        raise ValueError("retrieve_candidate_exercises needs state['starting_point']")

    # Local imports keep graph construction independent of database
    # driver initialization (same pattern as context.py).
    from database.database import AsyncSessionLocal
    from models.exercise import Exercise
    from models.exercise_prescription import ExercisePrescription

    goal = starting_point["goal"]
    categories = BASE_CATEGORIES | EXTRA_CATEGORIES_BY_GOAL.get(goal, set())

    async with AsyncSessionLocal() as session:
        exercises = (
            await session.scalars(
                select(Exercise)
                .where(Exercise.category.in_(categories))
                .order_by(Exercise.name)
                # Generation never reads these, and embeddings are large.
                .options(defer(Exercise.embedding), defer(Exercise.searchable_text))
            )
        ).all()

        prescriptions = {
            row.exercise_id: row
            for row in (
                await session.scalars(
                    select(ExercisePrescription).where(
                        ExercisePrescription.goal == goal
                    )
                )
            ).all()
        }

    candidates = build_candidates(exercises, prescriptions, starting_point)
    return {"candidate_exercises": candidates}


def build_candidates(
    exercises: list[Exercise],
    prescriptions: dict[str, ExercisePrescription],
    starting_point: dict,
) -> list[dict]:
    candidates = []
    for exercise in exercises:
        if not is_exercise_allowed(exercise, starting_point):
            continue

        is_compound = _is_compound(exercise)
        candidates.append(
            {
                "exercise": _serialize_exercise(exercise),
                "similarity_score": score_exercise(exercise, starting_point),
                "prescription": _prescription_for(
                    prescriptions.get(exercise.exercise_id),
                    starting_point["goal"],
                    is_compound,
                ),
                "is_compound": is_compound,
                "category": exercise.category,
            }
        )

    candidates.sort(key=lambda item: item["similarity_score"], reverse=True)
    return candidates


def is_exercise_allowed(exercise: Exercise, starting_point: dict) -> bool:
    experience = starting_point["experience_level"]
    if exercise.difficulty_level not in ALLOWED_DIFFICULTY.get(experience, set()):
        return False

    available = set(starting_point["available_equipment"]) | ALWAYS_AVAILABLE_EQUIPMENT
    required = {item.lower() for item in exercise.equipment_required or []}
    if not required <= available:
        return False

    if _matches_any(exercise, starting_point["disliked_exercises"]):
        return False

    return not violates_limitations(exercise, starting_point["limitations"])


def violates_limitations(exercise: Exercise, limitations: list[str]) -> bool:
    primary_muscles = {muscle.lower() for muscle in exercise.primary_muscles or []}
    mobility = set(exercise.mobility_requirements or [])
    name = exercise.name.lower()

    for limitation in limitations:
        for keyword, rule in LIMITATION_RULES.items():
            if keyword not in limitation:
                continue
            if exercise.exercise_family in rule.get("families", set()):
                return True
            if primary_muscles & rule.get("muscles", set()):
                return True
            if mobility & rule.get("mobility", set()):
                return True
            if exercise.category in rule.get("categories", set()):
                return True
            if any(word in name for word in rule.get("names", set())):
                return True
    return False


def score_exercise(exercise: Exercise, starting_point: dict) -> float:
    score = 0.0

    goal_suitability = exercise.goal_suitability
    if goal_suitability is None:
        # Not enriched yet: neutral.
        score += 0.2
    elif starting_point["goal"] in goal_suitability:
        score += 0.4

    if _matches_any(exercise, starting_point["preferred_exercises"]):
        score += 0.4

    preferred_levels = PREFERRED_DIFFICULTY.get(starting_point["experience_level"], set())
    if exercise.difficulty_level in preferred_levels:
        score += 0.2

    # Mild bonus for exercises the user already trains: we know their
    # working weight, so week 1 can start with a real number.
    if exercise.exercise_id in starting_point["recent_exercises"]:
        score += 0.1

    return min(score, 1.0)


def _matches_any(exercise: Exercise, terms: list[str]) -> bool:
    """True when a user term names this exercise ("bench press" matches
    "Barbell Bench Press - Medium Grip")."""
    name = exercise.name.lower()
    exercise_id = exercise.exercise_id.lower()
    return any(term == exercise_id or term in name for term in terms)


def _is_compound(exercise: Exercise) -> bool:
    roles = set(exercise.training_role or [])
    if roles:
        return bool(roles & {"primary_compound", "secondary_compound"})
    return exercise.mechanics == "compound"


def _prescription_for(
    row: ExercisePrescription | None,
    goal: str,
    is_compound: bool,
) -> dict:
    if row is not None:
        return {
            "sets_min": row.sets_min,
            "sets_max": row.sets_max,
            "reps_min": row.reps_min,
            "reps_max": row.reps_max,
            "rest_seconds": row.rest_seconds,
            "target_rpe_min": row.target_rpe_min,
            "target_rpe_max": row.target_rpe_max,
        }

    values = FALLBACK_PRESCRIPTIONS.get(
        (goal, is_compound),
        FALLBACK_PRESCRIPTIONS[("general_fitness", is_compound)],
    )
    keys = (
        "sets_min", "sets_max", "reps_min", "reps_max",
        "rest_seconds", "target_rpe_min", "target_rpe_max",
    )
    return dict(zip(keys, values))


def _serialize_exercise(exercise: Exercise) -> dict:
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


# ============================================================
# Node 3: generate the 4-week program
# ============================================================

async def generate_4_week_program(state: WorkoutAgentState) -> dict:
    """Build the program in memory. The same exercises repeat every week,
    with rising target RPE in weeks 1-3 and a deload in week 4."""
    starting_point = state.get("starting_point")
    candidates = state.get("candidate_exercises") or []
    if starting_point is None:
        raise ValueError("generate_4_week_program needs state['starting_point']")

    program = build_program(
        starting_point=starting_point,
        candidates=candidates,
        availability=state.get("availability") or [],
        recent_performance=state.get("recent_performance") or [],
        start_date=date.today(),
    )
    return {"generated_program": program}


def build_program(
    starting_point: dict,
    candidates: list[dict],
    availability: list[dict],
    recent_performance: list[dict],
    start_date: date,
) -> dict:
    experience = starting_point["experience_level"]
    goal = starting_point["goal"]

    max_minutes = {
        item["day_of_week"].lower(): item.get("max_duration_minutes")
        for item in availability
    }
    last_weights = _last_weights(recent_performance)

    training_days = choose_training_days(
        starting_point["available_days"],
        MAX_DAYS_BY_EXPERIENCE.get(experience, 4),
    )
    split = SPLITS_BY_DAYS[len(training_days)]

    weekly_sessions: dict[str, list[dict]] = {}
    variant_counts: dict[str, int] = {}
    for day, day_type in zip(training_days, split):
        variant = variant_counts.get(day_type, 0)
        variant_counts[day_type] = variant + 1
        weekly_sessions[day] = build_session(
            day_type=day_type,
            variant=variant,
            candidates=candidates,
            goal=goal,
            experience=experience,
            max_minutes=max_minutes.get(day),
            last_weights=last_weights,
        )

    workouts = []
    for week in range(1, PROGRAM_WEEKS + 1):
        week_start = start_date + timedelta(days=7 * (week - 1))
        for day in training_days:
            workouts.append(
                {
                    "week_number": week,
                    "day_of_week": day,
                    "scheduled_date": _date_in_week(week_start, day),
                    "exercises": [
                        _apply_week(exercise, week)
                        for exercise in weekly_sessions[day]
                    ],
                }
            )
    workouts.sort(key=lambda item: item["scheduled_date"])

    return {
        "goal": goal,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=7 * PROGRAM_WEEKS - 1),
        "workouts": workouts,
    }


def choose_training_days(available_days: list[str], max_days: int) -> list[str]:
    """Pick up to max_days days, spread out across the week for recovery."""
    days = sorted(available_days, key=DAY_ORDER.index)
    count = min(len(days), max_days, max(SPLITS_BY_DAYS))
    if count == len(days):
        return days
    # Sample from the middle of each step so picks don't bunch at the start.
    step = len(days) / count
    return [days[int((i + 0.5) * step)] for i in range(count)]


def build_session(
    day_type: str,
    variant: int,
    candidates: list[dict],
    goal: str,
    experience: str,
    max_minutes: int | None,
    last_weights: dict[str, float],
) -> list[dict]:
    budget_seconds = max_minutes * 60 if max_minutes else None
    max_exercises = MAX_EXERCISES_BY_EXPERIENCE.get(experience, 6)

    session: list[dict] = []
    used_ids: set[str] = set()
    used_seconds = 0

    for slot in DAY_TEMPLATES[day_type]:
        if len(session) >= max_exercises:
            break

        candidate = pick_for_slot(slot, candidates, used_ids, variant, goal)
        if candidate is None:
            continue

        prescription = candidate["prescription"]
        sets = _sets_for_experience(prescription, experience)

        # Shrink sets to fit the time limit before giving up on the slot.
        if budget_seconds is not None:
            while sets > 1 and used_seconds + _estimate_seconds(sets, prescription) > budget_seconds:
                sets -= 1
            # A limit too short for anything still gets one exercise.
            too_long = used_seconds + _estimate_seconds(sets, prescription) > budget_seconds
            if too_long and session:
                continue

        used_seconds += _estimate_seconds(sets, prescription)
        used_ids.add(candidate["exercise"]["exercise_id"])
        session.append(
            _planned_exercise(
                candidate, slot, len(session) + 1, sets, last_weights
            )
        )

    return session


def pick_for_slot(
    slot: Slot,
    candidates: list[dict],
    used_ids: set[str],
    variant: int,
    goal: str,
) -> dict | None:
    """``variant`` rotates through the top matches so repeated day types
    (full body A/B/C) don't get identical exercises."""
    scored = []
    for candidate in candidates:
        exercise = candidate["exercise"]
        if exercise["exercise_id"] in used_ids:
            continue
        score = slot_score(slot, candidate, goal)
        if score is not None:
            scored.append((score, exercise["name"], candidate))

    if not scored:
        return None

    # Ties go to the shorter name ("Barbell Squat" over "Barbell Side
    # Split Squat"), then alphabetical, so output is deterministic.
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return scored[min(variant, len(scored) - 1)][2]


def slot_score(slot: Slot, candidate: dict, goal: str) -> float | None:
    """How well a candidate fits a slot, or None if it doesn't fit at all."""
    exercise = candidate["exercise"]
    primary = [muscle.lower() for muscle in exercise["primary_muscles"]]
    if not set(primary) & slot.muscles:
        return None

    score = 2.0 * candidate["similarity_score"]

    # The first-listed primary muscle is the main target.
    if primary and primary[0] in slot.muscles:
        score += 1.0

    if exercise["exercise_family"] is not None:
        if exercise["exercise_family"] in slot.families:
            score += 3.0
    if candidate.get("is_compound") == slot.compound:
        score += 2.0
    if slot.compound and "primary_compound" in (exercise["training_role"] or []):
        score += 1.0

    # Loadable exercises progress more cleanly for strength/size goals.
    preference = min(
        (EQUIPMENT_PREFERENCE.get(item.lower(), 0.0) for item in exercise["equipment_required"]),
        default=0.0,
    )
    if preference > 0 and goal not in LOADED_GOALS:
        preference /= 2
    score += preference

    name = exercise["name"].lower()
    if any(keyword in name for keyword in STAPLE_KEYWORDS):
        score += 0.75

    if candidate.get("category") == "plyometrics" and goal != "power":
        score -= 0.5

    return score


def _planned_exercise(
    candidate: dict,
    slot: Slot,
    order: int,
    sets: int,
    last_weights: dict[str, float],
) -> dict:
    exercise = candidate["exercise"]
    prescription = candidate["prescription"]
    exercise_id = exercise["exercise_id"]

    return {
        "exercise_id": exercise_id,
        "exercise_order": order,
        "sets_planned": sets,
        "reps_min": prescription["reps_min"],
        "reps_max": prescription["reps_max"],
        "target_rpe_min": prescription["target_rpe_min"],
        "target_rpe_max": prescription["target_rpe_max"],
        "rest_seconds": prescription["rest_seconds"],
        "planned_weight": last_weights.get(exercise_id),
        "weight_unit": DEFAULT_WEIGHT_UNIT,
        "progression_method": _progression_method(exercise),
        "notes": _explain(exercise, slot, candidate),
    }


def _apply_week(base: dict, week: int) -> dict:
    planned = dict(base)
    rpe_min = base["target_rpe_min"]
    rpe_max = base["target_rpe_max"]

    if week == DELOAD_WEEK:
        planned["sets_planned"] = max(1, round(base["sets_planned"] * DELOAD_SET_FACTOR))
        if base["planned_weight"] is not None:
            planned["planned_weight"] = round(base["planned_weight"] * DELOAD_WEIGHT_FACTOR, 1)
        if rpe_min is not None:
            planned["target_rpe_min"] = max(0.0, rpe_min - DELOAD_RPE_DROP)
            planned["target_rpe_max"] = max(0.0, rpe_min - DELOAD_RPE_DROP + 1.0)
        planned["notes"] = f"Deload week: lighter volume to recover. {base['notes']}"
        return planned

    if rpe_min is not None and rpe_max is not None:
        # One-point-wide target band that climbs toward rpe_max.
        low = min(rpe_min + RPE_SHIFT_BY_WEEK[week], max(rpe_max - 1.0, rpe_min))
        planned["target_rpe_min"] = low
        planned["target_rpe_max"] = min(low + 1.0, rpe_max)
    return planned


def _sets_for_experience(prescription: dict, experience: str) -> int:
    if experience == "beginner":
        return prescription["sets_min"]
    if experience == "advanced":
        return prescription["sets_max"]
    return (prescription["sets_min"] + prescription["sets_max"]) // 2


def _estimate_seconds(sets: int, prescription: dict) -> int:
    return SETUP_SECONDS_PER_EXERCISE + sets * (
        SECONDS_PER_SET + prescription["rest_seconds"]
    )


def _progression_method(exercise: dict) -> str:
    methods = exercise.get("progression_methods") or []
    if methods:
        return methods[0]
    equipment = {item.lower() for item in exercise["equipment_required"]}
    return "increase_weight" if equipment - {"body only"} else "increase_reps"


def _explain(exercise: dict, slot: Slot, candidate: dict) -> str:
    kind = "compound" if candidate.get("is_compound") else "isolation"
    muscles = ", ".join(exercise["primary_muscles"]) or "full body"
    reason = f"Chosen for the {slot.label} slot: {kind} exercise for {muscles}."
    if candidate["similarity_score"] >= 0.5:
        reason += " Matches your goal and preferences."
    return reason


def _last_weights(recent_performance: list[dict]) -> dict[str, float]:
    """Heaviest logged weight per exercise (input is newest first)."""
    weights: dict[str, float] = {}
    for item in recent_performance:
        exercise_id = item["exercise_id"]
        if exercise_id in weights:
            continue
        logged = [w for w in item.get("actual_weights") or [] if w is not None]
        if logged:
            weights[exercise_id] = max(logged)
    return weights


def _date_in_week(week_start: date, day: str) -> date:
    offset = (DAY_ORDER.index(day) - week_start.weekday()) % 7
    return week_start + timedelta(days=offset)


# ============================================================
# Node 4: validate
# ============================================================

async def validate_program(state: WorkoutAgentState) -> dict:
    """The graph should route to save_program only when this is empty."""
    return {
        "validation_errors": find_program_errors(
            state.get("generated_program"),
            state.get("candidate_exercises") or [],
            state.get("availability") or [],
        )
    }


def find_program_errors(
    program: dict | None,
    candidates: list[dict],
    availability: list[dict],
) -> list[str]:
    """Checks that protect the user. Value ranges (sets, reps, RPE, week
    number, unique days/orders) are enforced by the database constraints."""
    if program is None or not program["workouts"]:
        return ["No program was generated"]

    allowed_ids = {item["exercise"]["exercise_id"] for item in candidates}
    day_limits = {
        item["day_of_week"].lower(): item.get("max_duration_minutes")
        for item in availability
        if item["is_available"]
    }

    errors: list[str] = []
    for workout in program["workouts"]:
        day = workout["day_of_week"]
        where = f"Week {workout['week_number']} {day}"
        exercises = workout["exercises"]

        if day not in day_limits:
            errors.append(f"{where}: user is not available on {day}")
        if not exercises:
            errors.append(f"{where}: workout has no exercises")

        for item in exercises:
            if item["exercise_id"] not in allowed_ids:
                errors.append(f"{where}: {item['exercise_id']} is not an allowed exercise")

        total_seconds = sum(
            _estimate_seconds(item["sets_planned"], item) for item in exercises
        )
        limit = day_limits.get(day)
        # A one-exercise session is the minimum, even if it runs over.
        if limit and total_seconds > limit * 60 and len(exercises) > 1:
            errors.append(
                f"{where}: about {total_seconds // 60} min, over the {limit} min limit"
            )

    return errors


# ============================================================
# Node 5: save
# ============================================================

async def save_program(state: WorkoutAgentState) -> dict:
    """Save in one transaction as "active", so the next run takes the
    current-program path."""
    if state.get("validation_errors"):
        raise ValueError(
            "Refusing to save an invalid program: "
            + "; ".join(state["validation_errors"])
        )
    program = state.get("generated_program")
    if program is None:
        raise ValueError("save_program needs state['generated_program']")

    from database.database import AsyncSessionLocal
    from models.workout_plan import WorkoutPlan
    from models.workout_plan_exercise import WorkoutPlanExercise
    from models.workout_program import WorkoutProgram

    user_id = state["user_id"]

    async with AsyncSessionLocal() as session:
        async with session.begin():
            program_row = WorkoutProgram(
                user_id=user_id,
                start_date=program["start_date"],
                end_date=program["end_date"],
                goal=program["goal"],
                status="active",
            )
            session.add(program_row)
            await session.flush()

            workout_rows = []
            for workout in program["workouts"]:
                workout_row = WorkoutPlan(
                    program_id=program_row.program_id,
                    week_number=workout["week_number"],
                    # Capitalized, matching user_availability; context.py
                    # lowercases when it reads it back.
                    day_of_week=workout["day_of_week"].capitalize(),
                    scheduled_date=workout["scheduled_date"],
                    status="scheduled",
                    exercises=[
                        WorkoutPlanExercise(**exercise)
                        for exercise in workout["exercises"]
                    ],
                )
                workout_rows.append(workout_row)
            session.add_all(workout_rows)
            await session.flush()

            first = min(workout_rows, key=lambda row: row.scheduled_date)
            active_program = {
                "program_id": program_row.program_id,
                "start_date": program_row.start_date,
                "end_date": program_row.end_date,
                "goal": program_row.goal,
                "status": program_row.status,
            }
            upcoming_workout = {
                "workout_id": first.workout_id,
                "program_id": first.program_id,
                "week_number": first.week_number,
                "day_of_week": first.day_of_week.lower(),
                "scheduled_date": first.scheduled_date,
                "status": first.status,
            }

    return {
        "active_program": active_program,
        "upcoming_workout": upcoming_workout,
    }
