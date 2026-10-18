"""AI coach: reading the message, follow-up questions and routing.

No API key needed, and no database except where a test says otherwise:
the LLM and the context loader are fakes from coach_fakes.py. The shared
conftest.py needs TEST_DATABASE_URL, so without it run:
    pytest backend/tests/test_coach_*.py --noconftest
"""

import asyncio

from agent.coach_graph import build_coach_graph
from agent.nodes import coach, coach_intent
from coach_fakes import USER_ID, FakeLLM, fake_context, planned, run, workout


# ============================================================
# Follow-up questions (the planning doc's "shorten" example)
# ============================================================

def test_shorten_without_time_asks_how_much_time():
    result, _ = run({"intent": "shorten_workout"}, "I want to shorten my workout today")
    assert result["reply"].startswith("How much time do you have today?")
    assert result["new_pending"] == {"type": "follow_up", "intent": result["intent"]}


def test_answer_to_follow_up_keeps_the_original_request():
    first, _ = run({"intent": "shorten_workout"}, "I want to shorten my workout today")
    # The model may classify a bare "30" as "other"; the follow-up still wins.
    second, _ = run({"intent": "other"}, "30", pending=first["new_pending"])
    assert second["intent"]["intent"] == "shorten_workout"
    assert second["intent"]["minutes_available"] == 30
    assert second["new_pending"]["type"] == "changes"
    assert "To fit 30 minutes" in second["reply"]


def test_new_topic_after_follow_up_is_not_merged():
    first, _ = run({"intent": "shorten_workout"}, "shorten my workout")
    second, _ = run(
        {"intent": "exercise_question", "exercise_name": "squat"},
        "actually, how deep should I squat?",
        pending=first["new_pending"],
    )
    assert second["intent"]["intent"] == "exercise_question"


def test_unrelated_reply_to_follow_up_starts_fresh():
    first, _ = run({"intent": "shorten_workout"}, "shorten my workout")
    second, _ = run(
        {"intent": "other"}, "thanks, actually how much protein should I eat?",
        pending=first["new_pending"], answer="About 0.7-1 g per lb.",
    )
    assert second["intent"]["intent"] == "other"
    assert second["reply"] == "About 0.7-1 g per lb."
    assert second.get("new_pending") is None


def test_whole_workout_answers_the_adjust_follow_up():
    first, _ = run(
        {"intent": "adjust_difficulty", "difficulty_direction": "harder", "exercise_name": "deadlifts"},
        "make deadlifts harder",
    )
    assert "I couldn't find deadlifts" in first["reply"]
    second, _ = run({"intent": "other"}, "the whole workout", pending=first["new_pending"])
    assert second["new_pending"]["type"] == "changes"
    assert len(second["new_pending"]["changes"]) == len(workout())


def test_whole_workout_does_not_clear_exercise_for_questions():
    intent = coach_intent.resolve_intent(
        {"intent": "exercise_question", "exercise_name": "squat"},
        None, "how do I squat with my whole foot flat?", workout(),
    )
    assert intent["exercise_name"] == "squat"


def test_swap_without_exercise_lists_todays_exercises():
    result, _ = run({"intent": "swap_exercise"}, "swap an exercise")
    assert "Which exercise do you want to swap?" in result["reply"]
    assert "Barbell Squat" in result["reply"]


def test_adjust_without_direction_asks_easier_or_harder():
    result, _ = run({"intent": "adjust_difficulty"}, "adjust difficulty")
    assert result["reply"] == "Do you want today's workout to be easier or harder?"


def test_modify_without_a_workout_does_not_ask_follow_up():
    result, llm = run({"intent": "shorten_workout"}, "shorten my workout", exercises=[])
    assert result.get("new_pending") is None
    assert result["reply"] == "Fake answer."


def test_wrong_exercise_is_not_adjusted():
    result, _ = run(
        {"intent": "adjust_difficulty", "difficulty_direction": "harder", "exercise_name": "dumbbell curls"},
        "make dumbbell curls harder",
    )
    assert "I couldn't find dumbbell curls" in result["reply"]
    assert result["new_pending"]["type"] == "follow_up"


# ============================================================
# Confirm / decline routing
# ============================================================

def test_confirm_with_nothing_pending_is_a_general_reply():
    result, _ = run({"intent": "confirm"}, "yes", answer="What can I help with?")
    assert result["reply"] == "What can I help with?"


def test_yes_after_an_expired_proposal_does_not_reach_the_llm():
    llm = FakeLLM({"intent": "confirm"}, answer="Sure, done!")
    graph = build_coach_graph(llm, load_context=fake_context(workout()))
    state = {"user_id": USER_ID, "message": "yes", "history": [], "pending": None, "pending_expired": True}
    result = asyncio.run(graph.ainvoke(state))
    assert result["reply"].startswith("That suggestion expired")


# ============================================================
# Matching exercise names
# ============================================================

def test_find_workout_exercise():
    exercises = workout()
    assert coach.find_workout_exercise("bench", exercises)["exercise"]["name"].startswith("Barbell Bench")
    assert coach.find_workout_exercise("squats", exercises)["exercise"]["name"] == "Barbell Squat"
    # "barbell" matches two exercises equally: ambiguous.
    assert coach.find_workout_exercise("barbell", exercises) is None
    assert coach.find_workout_exercise("deadlift", exercises) is None


def test_find_workout_exercise_needs_every_word():
    exercises = [
        *workout(),
        planned(5, "Zottman Preacher Curl", muscles=("Biceps",)),
        planned(6, "Rope Crunch", muscles=("Abdominals",)),
        planned(7, "Pushups"),
        planned(8, "Lying Leg Curls", muscles=("Hamstrings",)),
    ]
    assert coach.find_workout_exercise("dumbbell curl", exercises) is None
    assert coach.find_workout_exercise("overhead press", exercises) is None
    assert coach.find_workout_exercise("leg extensions", exercises) is None
    assert coach.find_workout_exercise("front squat", exercises) is None
    assert coach.find_workout_exercise("crunches", exercises)["exercise"]["name"] == "Rope Crunch"
    assert coach.find_workout_exercise("push-ups", exercises)["exercise"]["name"] == "Pushups"
    assert coach.find_workout_exercise("today's flyes", exercises)["exercise"]["name"] == "Dumbbell Flyes"


# ============================================================
# Minutes
# ============================================================

def test_parse_minutes():
    assert coach_intent.parse_minutes("about 40 min") == 40
    assert coach_intent.parse_minutes("1.5 hours") == 90
    assert coach_intent.parse_minutes("half an hour") == 30
    assert coach_intent.parse_minutes("an hour and a half") == 90
    assert coach_intent.parse_minutes("1 hour 15 minutes") == 75
    assert coach_intent.parse_minutes("1h30") == 90
    assert coach_intent.parse_minutes("I only have 20 minutes before work today because of a meeting") == 20
    assert coach_intent.parse_minutes("swap exercise 2 for something without a barbell please") is None


def test_parse_minutes_bare_numbers_only_when_expected():
    assert coach_intent.parse_minutes("30") is None
    assert coach_intent.parse_minutes("30", allow_bare=True) == 30
    assert coach_intent.parse_minutes("about 40", allow_bare=True) == 40
    # Counts, not minutes, even when a time is expected.
    assert coach_intent.parse_minutes("shorten it to 3 exercises", allow_bare=True) is None
    assert coach_intent.parse_minutes("I only have 2 dumbbells", allow_bare=True) is None
    assert coach_intent.parse_minutes("do 5 sets", allow_bare=True) is None


def test_count_is_not_read_as_minutes():
    result, _ = run({"intent": "shorten_workout"}, "shorten it to 3 exercises")
    assert result["reply"].startswith("How much time do you have today?")
