"""Unit tests for the new-program path. No database needed: these test the
pure helpers that the graph nodes wrap."""

import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from agent.nodes import new_program as npg


def make_exercise(exercise_id, name, primary, equipment, mechanics="compound",
                  difficulty="beginner", category="strength", **enriched):
    fields = dict(
        exercise_id=exercise_id,
        name=name,
        difficulty_level=difficulty,
        mechanics=mechanics,
        category=category,
        primary_muscles=primary,
        secondary_muscles=[],
        equipment_required=equipment,
        exercise_family=None,
        movement_pattern=None,
        training_role=None,
        unilateral=None,
        load_type=None,
        progression_methods=None,
        substitution_group=None,
        goal_suitability=None,
        mobility_requirements=None,
        balance_requirement=None,
        stability_requirement=None,
        fatigue_cost=None,
    )
    fields.update(enriched)
    return SimpleNamespace(**fields)


EXERCISES = [
    make_exercise("squat", "Barbell Squat", ["Quadriceps"], ["Barbell"]),
    make_exercise("goblet", "Goblet Squat", ["Quadriceps"], ["Dumbbell"]),
    make_exercise("bench", "Barbell Bench Press", ["Chest"], ["Barbell"]),
    make_exercise("pushup", "Push Up", ["Chest"], ["Body Only"]),
    make_exercise("rdl", "Romanian Deadlift", ["Hamstrings"], ["Barbell"], difficulty="intermediate"),
    make_exercise("row", "Dumbbell Row", ["Middle Back"], ["Dumbbell"]),
    make_exercise("pullup", "Pullups", ["Lats"], ["Body Only"]),
    make_exercise("press", "Standing Military Press", ["Shoulders"], ["Barbell"]),
    make_exercise("plank", "Plank", ["Abdominals"], ["Body Only"], mechanics="isolation"),
    make_exercise("curl", "Dumbbell Curl", ["Biceps"], ["Dumbbell"], mechanics="isolation"),
    make_exercise("stepup", "Step-up with Knee Raise", ["Glutes"], ["Body Only"]),
    make_exercise("snatch", "Power Snatch", ["Hamstrings"], ["Barbell"], difficulty="expert"),
    make_exercise("weird", "Odd Thing Squat", ["Quadriceps"], ["Other"]),
]


def starting_point(**overrides):
    point = {
        "goal": "hypertrophy",
        "experience_level": "intermediate",
        "available_equipment": sorted(npg.normalize_equipment(["Full gym"])),
        "available_days": ["monday", "wednesday", "friday"],
        "disliked_exercises": [],
        "preferred_exercises": [],
        "limitations": [],
        "recent_exercises": [],
    }
    point.update(overrides)
    return point


def availability(days, minutes=60):
    return [
        {"day_of_week": day, "is_available": True, "max_duration_minutes": minutes}
        for day in days
    ]


def generate(point, minutes=60, recent_performance=(), start=date(2026, 10, 12), exercises=EXERCISES):
    candidates = npg.build_candidates(exercises, {}, point)
    program = npg.build_program(
        starting_point=point,
        candidates=candidates,
        availability=availability(point["available_days"], minutes),
        recent_performance=list(recent_performance),
        start_date=start,  # default is a Monday
    )
    return program, candidates


def program_exercise_ids(program):
    return {
        exercise["exercise_id"]
        for workout in program["workouts"]
        for exercise in workout["exercises"]
    }


# ------------------------------------------------------------
# analyze_starting_point
# ------------------------------------------------------------

def test_analyze_starting_point_orders_days_and_normalizes():
    state = {
        "profile": {
            "user_id": "u",
            "goal": "strength",
            "experience_level": "beginner",
            "available_equipment": ["Dumbbells only"],
            "preferred_exercises": ["Bench Press"],
            "disliked_exercises": [],
            "limitations": ["None"],
        },
        "availability": [
            {"day_of_week": "Friday", "is_available": True, "max_duration_minutes": 30},
            {"day_of_week": "Monday", "is_available": True, "max_duration_minutes": 45},
            {"day_of_week": "Tuesday", "is_available": False, "max_duration_minutes": None},
        ],
        "recent_performance": [{"exercise_id": "bench"}, {"exercise_id": "bench"}],
    }
    point = asyncio.run(npg.analyze_starting_point(state))["starting_point"]

    assert point["available_days"] == ["monday", "friday"]
    assert set(point["available_equipment"]) == {"dumbbell", "body only"}
    assert point["preferred_exercises"] == ["bench press"]
    assert point["limitations"] == []
    assert point["recent_exercises"] == ["bench"]


def test_analyze_starting_point_requires_a_day():
    state = {
        "profile": {"goal": "strength", "experience_level": "beginner"},
        "availability": [],
    }
    with pytest.raises(ValueError):
        asyncio.run(npg.analyze_starting_point(state))


# ------------------------------------------------------------
# Candidate filtering
# ------------------------------------------------------------

def test_equipment_is_a_hard_filter():
    point = starting_point(available_equipment=sorted(npg.normalize_equipment(["Bodyweight"])))
    ids = {c["exercise"]["exercise_id"] for c in npg.build_candidates(EXERCISES, {}, point)}
    assert "pushup" in ids and "pullup" in ids
    assert "bench" not in ids and "row" not in ids


def test_knee_limitation_excludes_knee_exercises():
    point = starting_point(limitations=["tweaked my knee"])
    ids = {c["exercise"]["exercise_id"] for c in npg.build_candidates(EXERCISES, {}, point)}
    assert not ids & {"squat", "goblet", "stepup", "weird"}
    assert "bench" in ids


def test_disliked_exercises_are_excluded():
    point = starting_point(disliked_exercises=["bench press"])
    ids = {c["exercise"]["exercise_id"] for c in npg.build_candidates(EXERCISES, {}, point)}
    assert "bench" not in ids


def test_beginners_skip_expert_exercises():
    point = starting_point(experience_level="beginner")
    ids = {c["exercise"]["exercise_id"] for c in npg.build_candidates(EXERCISES, {}, point)}
    assert "snatch" not in ids
    assert "rdl" in ids  # Kinetic labels it intermediate, still fine for beginners


def test_prescription_row_wins_over_fallback():
    row = SimpleNamespace(sets_min=5, sets_max=5, reps_min=5, reps_max=5,
                          rest_seconds=200, target_rpe_min=8.0, target_rpe_max=9.0)
    candidates = npg.build_candidates(EXERCISES, {"squat": row}, starting_point())
    squat = next(c for c in candidates if c["exercise"]["exercise_id"] == "squat")
    assert squat["prescription"]["rest_seconds"] == 200


# ------------------------------------------------------------
# Program generation
# ------------------------------------------------------------

def test_program_covers_four_weeks_on_available_days():
    point = starting_point()
    program, candidates = generate(point)

    assert program["start_date"] == date(2026, 10, 12)
    assert program["end_date"] == date(2026, 11, 8)
    assert len(program["workouts"]) == 4 * 3
    assert {w["day_of_week"] for w in program["workouts"]} == {"monday", "wednesday", "friday"}
    assert npg.find_program_errors(program, candidates, availability(point["available_days"])) == []


def test_same_exercises_each_week_and_week_four_deloads():
    program, _ = generate(starting_point())
    mondays = {w["week_number"]: w for w in program["workouts"] if w["day_of_week"] == "monday"}

    ids = [[e["exercise_id"] for e in mondays[week]["exercises"]] for week in (1, 2, 3, 4)]
    assert ids[0] == ids[1] == ids[2] == ids[3]

    week1, week3, week4 = (mondays[n]["exercises"][0] for n in (1, 3, 4))
    assert week3["target_rpe_min"] > week1["target_rpe_min"]
    assert week4["sets_planned"] < week1["sets_planned"]
    assert week4["notes"].startswith("Deload")


def test_sessions_fit_time_limit():
    point = starting_point(goal="strength")
    program, candidates = generate(point, minutes=20)
    assert all(w["exercises"] for w in program["workouts"])
    assert npg.find_program_errors(program, candidates, availability(point["available_days"], 20)) == []


def test_preferred_exercise_is_chosen():
    point = starting_point(preferred_exercises=["goblet"])
    program, _ = generate(point)
    first_day = program["workouts"][0]["exercises"]
    assert first_day[0]["exercise_id"] == "goblet"


def test_recent_weight_seeds_planned_weight():
    performance = [{"exercise_id": "bench", "actual_weights": [135.0, 145.0, None]}]
    program, _ = generate(starting_point(), recent_performance=performance)
    bench = [
        e for w in program["workouts"] if w["week_number"] < npg.DELOAD_WEEK
        for e in w["exercises"] if e["exercise_id"] == "bench"
    ]
    assert bench and all(e["planned_weight"] == 145.0 for e in bench)


@pytest.mark.parametrize(
    "available, max_days, expected",
    [
        (npg.DAY_ORDER[:5], 4, ["monday", "tuesday", "thursday", "friday"]),
        (npg.DAY_ORDER, 4, ["monday", "wednesday", "friday", "sunday"]),
        (npg.DAY_ORDER[:6], 5, ["monday", "tuesday", "thursday", "friday", "saturday"]),
        (["monday", "friday"], 4, ["monday", "friday"]),
    ],
)
def test_training_days_capped_and_spread(available, max_days, expected):
    assert npg.choose_training_days(available, max_days) == expected


@pytest.mark.parametrize(
    "days, experience, split",
    [
        (npg.DAY_ORDER[:4], "intermediate", ["upper", "lower", "upper", "lower"]),
        (npg.DAY_ORDER[:5], "intermediate", ["upper", "lower", "push", "pull", "legs"]),
        (npg.DAY_ORDER[:6], "advanced", ["push", "pull", "legs"] * 2),
    ],
)
def test_split_matches_number_of_days(days, experience, split):
    point = starting_point(available_days=days, experience_level=experience)
    program, candidates = generate(point)
    assert npg.SPLITS_BY_DAYS[len(days)] == split
    assert len(program["workouts"]) == 4 * len(days)
    assert npg.find_program_errors(program, candidates, availability(days)) == []


def test_non_monday_start_keeps_dates_in_range():
    start = date(2026, 10, 14)  # a Wednesday
    point = starting_point()
    program, candidates = generate(point, start=start)

    assert program["end_date"] == date(2026, 11, 10)
    for workout in program["workouts"]:
        assert start <= workout["scheduled_date"] <= program["end_date"]
        assert npg.DAY_ORDER[workout["scheduled_date"].weekday()] == workout["day_of_week"]
    assert npg.find_program_errors(program, candidates, availability(point["available_days"])) == []


def test_deload_week_lowers_weight():
    performance = [{"exercise_id": "bench", "actual_weights": [200.0]}]
    program, _ = generate(starting_point(), recent_performance=performance)
    bench = {
        w["week_number"]: e
        for w in program["workouts"] for e in w["exercises"] if e["exercise_id"] == "bench"
    }
    assert bench[3]["planned_weight"] == 200.0
    assert bench[4]["planned_weight"] == 170.0


def test_tiny_time_limit_still_gets_one_exercise():
    point = starting_point()
    program, candidates = generate(point, minutes=2)
    for workout in program["workouts"]:
        assert len(workout["exercises"]) == 1
        assert workout["exercises"][0]["sets_planned"] == 1
    assert npg.find_program_errors(program, candidates, availability(point["available_days"], 2)) == []


def test_validation_reports_empty_workouts_when_nothing_fits():
    # Only a biceps curl is available: full-body days have no slot it can fill
    # except "arms", so drop it too and every day ends up empty.
    point = starting_point(disliked_exercises=["curl"])
    only_curl = [e for e in EXERCISES if e.exercise_id == "curl"]
    program, candidates = generate(point, exercises=only_curl)
    errors = npg.find_program_errors(program, candidates, availability(point["available_days"]))
    assert errors and all("no exercises" in error for error in errors)


def test_validation_flags_disallowed_exercise():
    point = starting_point(limitations=["knee"])
    program, candidates = generate(point)
    program["workouts"][0]["exercises"][0]["exercise_id"] = "squat"
    errors = npg.find_program_errors(program, candidates, availability(point["available_days"]))
    assert any("not an allowed exercise" in error for error in errors)
