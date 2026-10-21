"""AI coach: choosing swap options and reading the reason for a swap.

No API key needed, and no database except where a test says otherwise:
the LLM and the context loader are fakes from coach_fakes.py. The shared
conftest.py needs TEST_DATABASE_URL, so without it run:
    pytest backend/tests/test_coach_*.py --noconftest
"""

from backend.agent_chatbot import coach_rules
from backend.agent_chatbot.nodes import coach_swap
from coach_fakes import PROFILE, make_exercise, workout


CHEST = [
    make_exercise("db_bench", "Dumbbell Bench Press", ["Chest"], ["Dumbbell"]),
    make_exercise("incline", "Barbell Incline Bench Press", ["Chest"], ["Barbell"]),
    make_exercise("pushup", "Pushups", ["Chest"], ["Body Only"]),
    make_exercise("cable_fly", "Cable Crossover", ["Chest"], ["Cable"]),
    make_exercise("expert", "Planche Push-Up", ["Chest"], ["Body Only"], difficulty="expert"),
]

# ============================================================
# Ranking
# ============================================================

def test_rank_alternatives_respects_reason_equipment():
    original = workout()[0]["exercise"]
    options = coach_swap.rank_alternatives(original, CHEST, coach_swap.coach_starting_point(PROFILE), set(), "no barbell today")
    names = [option["name"] for option in options]
    assert "Barbell Incline Bench Press" not in names
    assert names[0] == "Dumbbell Bench Press"
    assert len(options) == coach_rules.SWAP_OPTION_COUNT


def test_rank_alternatives_skips_exercises_already_in_workout_and_too_hard():
    original = workout()[0]["exercise"]
    options = coach_swap.rank_alternatives(original, CHEST, coach_swap.coach_starting_point(PROFILE), {"db_bench"}, None)
    names = {option["name"] for option in options}
    assert "Dumbbell Bench Press" not in names
    assert "Planche Push-Up" not in names


def test_rank_alternatives_treats_pain_reason_as_limitation():
    legs = [
        make_exercise("goblet", "Goblet Squat", ["Quadriceps"], ["Dumbbell"]),
        make_exercise("leg_curl", "Lying Leg Curls", ["Hamstrings"], ["Machine"]),
    ]
    original = workout()[1]["exercise"]
    original = {**original, "primary_muscles": ["Quadriceps", "Hamstrings"]}
    options = coach_swap.rank_alternatives(original, legs, coach_swap.coach_starting_point(PROFILE), set(), "my knee hurts")
    assert [option["name"] for option in options] == ["Lying Leg Curls"]


def test_machine_taken_reason_still_offers_shoulder_exercises():
    shoulders = [
        make_exercise("db_press", "Dumbbell Shoulder Press", ["Shoulders"], ["Dumbbell"]),
        make_exercise("machine_press", "Machine Shoulder Press", ["Shoulders"], ["Machine"]),
    ]
    original = {**workout()[0]["exercise"], "exercise_id": "bb_press", "primary_muscles": ["Shoulders"]}
    options = coach_swap.rank_alternatives(
        original, shoulders, coach_swap.coach_starting_point(PROFILE), set(), "the shoulder press machine is taken",
    )
    assert [option["name"] for option in options] == ["Dumbbell Shoulder Press"]


# ============================================================
# Reasons
# ============================================================

def test_unavailable_equipment():
    assert coach_swap.unavailable_equipment("no barbell") == {"barbell"}
    assert coach_swap.unavailable_equipment("the cables are taken and I don't have dumbbells") == {"cable", "dumbbell"}
    assert coach_swap.unavailable_equipment("I love barbells") == set()
    assert coach_swap.unavailable_equipment(None) == set()


def test_unavailable_equipment_needs_the_negation_next_to_it():
    assert coach_swap.unavailable_equipment("no barbell, dumbbells are fine") == {"barbell"}
    assert coach_swap.unavailable_equipment("no machine, I'll use a cable") == {"machine"}
    assert coach_swap.unavailable_equipment("the shoulder press machine is taken") == {"machine"}
    assert coach_swap.unavailable_equipment("without a barbell") == {"barbell"}


def test_only_pain_reasons_become_limitations():
    assert coach_swap.is_pain_reason("my knee hurts")
    assert coach_swap.is_pain_reason("tweaked my shoulder")
    assert not coach_swap.is_pain_reason("the shoulder press machine is taken")
    assert not coach_swap.is_pain_reason("machine is broken, knee is fine")
