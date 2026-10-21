"""AI coach: shorten and adjust plans, applying confirmed changes, signed pending actions.

No API key needed, and no database except where a test says otherwise:
the LLM and the context loader are fakes from coach_fakes.py. The shared
conftest.py needs TEST_DATABASE_URL, so without it run:
    pytest backend/tests/test_coach_*.py --noconftest
"""

import asyncio
import uuid
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy.orm.exc import StaleDataError

from backend.agent_chatbot import coach_rules
from backend.agent_chatbot.nodes import coach_changes
from coach_fakes import USER_ID, WORKOUT_ID, planned, run, workout
from core.auth import create_access_token, get_current_user_id


# ============================================================
# Shorten
# ============================================================

def test_plan_shorten_trims_accessory_sets_before_dropping_exercises():
    exercises = workout()  # about 35 minutes
    changes = coach_changes.plan_shorten(exercises, 30)
    assert all(change["action"] == "update" for change in changes)
    after = coach_changes.apply_changes_preview(exercises, changes)
    assert len(after) == 4
    assert after[0]["sets_planned"] == 4  # main lift untouched
    assert coach_changes.workout_minutes(after) <= 30


def test_plan_shorten_drops_from_the_end_and_keeps_the_main_lift():
    exercises = workout()
    changes = coach_changes.plan_shorten(exercises, 15)
    removed = [change["name"] for change in changes if change["action"] == "remove"]
    assert removed == ["Triceps Pushdown", "Dumbbell Flyes", "Barbell Squat"]
    after = coach_changes.apply_changes_preview(exercises, changes)
    assert [item["exercise"]["name"] for item in after] == ["Barbell Bench Press - Medium Grip"]
    assert coach_changes.workout_minutes(after) <= 15


def test_plan_shorten_trims_sets_when_one_exercise_is_left():
    exercises = workout()
    changes = coach_changes.plan_shorten(exercises, 5)
    after = coach_changes.apply_changes_preview(exercises, changes)
    assert len(after) == 1
    assert after[0]["sets_planned"] == coach_rules.MIN_SETS


def test_shorten_when_it_already_fits():
    result, _ = run({"intent": "shorten_workout", "minutes_available": 120}, "I have 2 hours")
    assert "already fits" in result["reply"]
    assert result.get("new_pending") is None


# ============================================================
# Adjust difficulty
# ============================================================

def test_harder_adds_a_set_raises_rpe_and_weight():
    exercises = workout()
    changes = coach_changes.plan_adjust(exercises, "harder", exercises[0])
    assert len(changes) == 1
    updates = changes[0]["updates"]
    assert updates["sets_planned"] == 5
    assert updates["target_rpe_max"] == 8.5
    assert updates["planned_weight"] == 152.5  # 145 * 1.05, rounded to 2.5


def test_easier_respects_minimums():
    exercises = [planned(1, "Plank", sets=1, rpe=(0.5, 1.0), muscles=("Abdominals",))]
    changes = coach_changes.plan_adjust(exercises, "easier", None)
    assert changes[0]["updates"] == {"target_rpe_min": 0.0, "target_rpe_max": 0.0}


def test_adjust_named_exercise_only_changes_that_exercise():
    result, _ = run(
        {"intent": "adjust_difficulty", "difficulty_direction": "easier", "exercise_name": "squats"},
        "make squats easier",
    )
    changes = result["new_pending"]["changes"]
    assert [change["name"] for change in changes] == ["Barbell Squat"]


def test_harder_never_lowers_sets():
    exercises = [planned(1, "Barbell Squat", sets=8, muscles=("Quadriceps",))]
    changes = coach_changes.plan_adjust(exercises, "harder", None)
    assert "sets_planned" not in changes[0]["updates"]


# ============================================================
# Confirm / decline
# ============================================================

def test_decline_leaves_workout_alone():
    pending = {"type": "changes", "summary": "shorten to 30 minutes", "done": "Done.", "changes": []}
    result, _ = run({"intent": "decline"}, "no thanks", pending=pending)
    assert "left your workout as it is" in result["reply"]
    assert not result.get("plan_changed")


def test_confirm_swap_without_a_pick_asks_again():
    exercises = workout()
    pending = {
        "type": "swap",
        "workout_plan_exercise_id": str(exercises[0]["workout_plan_exercise_id"]),
        "from_name": "Barbell Bench Press - Medium Grip",
        "reason": None,
        "options": [
            {"exercise_id": "a", "name": "A", "equipment_required": [], "reason": "x"},
            {"exercise_id": "b", "name": "B", "equipment_required": [], "reason": "y"},
        ],
    }
    result, _ = run({"intent": "confirm"}, "yes", exercises=exercises, pending=pending)
    assert result["reply"] == "Which option do you want? Reply with 1, 2."
    assert result["new_pending"] == pending


def test_confirm_for_a_workout_that_changed_is_not_applied():
    pending = {
        "type": "changes",
        "summary": "shorten to 30 minutes",
        "done": "Done.",
        "changes": [{"workout_plan_exercise_id": str(uuid.uuid4()), "action": "remove", "name": "X"}],
    }
    result, _ = run({"intent": "confirm"}, "yes", pending=pending)
    assert "didn't apply it" in result["reply"]
    assert not result.get("plan_changed")


# ============================================================
# Applying a confirmed change (fake database session)
# ============================================================

class FakeSession:
    def __init__(self, rows, logged_sets=0, stale=False):
        self.rows = rows
        self.logged_sets = logged_sets
        self.stale = stale
        self.deleted = []
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, model, key):
        return self.rows.get(key)

    async def scalar(self, query):
        return self.logged_sets

    async def delete(self, row):
        self.deleted.append(row)

    async def commit(self):
        if self.stale:
            raise StaleDataError("0 rows matched")
        self.committed = True

    async def rollback(self):
        pass


def fake_rows(exercises, workout_id=WORKOUT_ID):
    return {
        item["workout_plan_exercise_id"]: SimpleNamespace(
            id=item["workout_plan_exercise_id"], workout_id=workout_id,
            exercise_id=item["exercise"]["exercise_id"], sets_planned=item["sets_planned"],
            planned_weight=item["planned_weight"], notes=None,
        )
        for item in exercises
    }


def confirm_with(session, monkeypatch, exercises, pending, intent=None):
    monkeypatch.setattr("database.database.AsyncSessionLocal", lambda: session)
    result, _ = run(intent or {"intent": "confirm"}, "yes", exercises=exercises, pending=pending)
    return result


def shorten_pending(exercises, minutes=15):
    changes = coach_changes.plan_shorten(exercises, minutes)
    return {"type": "changes", "summary": "shorten", "done": "Done.", "changes": changes}


def test_confirm_shorten_writes_the_changes(monkeypatch):
    exercises = workout()
    session = FakeSession(fake_rows(exercises))
    result = confirm_with(session, monkeypatch, exercises, shorten_pending(exercises))
    assert result["plan_changed"] and session.committed
    assert len(session.deleted) == 3


def test_confirm_swap_writes_the_new_exercise(monkeypatch):
    exercises = workout()
    rows = fake_rows(exercises)
    pending = {
        "type": "swap",
        "workout_plan_exercise_id": str(exercises[0]["workout_plan_exercise_id"]),
        "from_name": "Barbell Bench Press - Medium Grip",
        "reason": "no barbell",
        "options": [
            {"exercise_id": "db_bench", "name": "Dumbbell Bench Press", "equipment_required": [], "reason": "x"},
            {"exercise_id": "pushup", "name": "Pushups", "equipment_required": [], "reason": "y"},
        ],
    }
    session = FakeSession(rows)
    result = confirm_with(session, monkeypatch, exercises, pending, {"intent": "confirm", "selected_option": 2})
    row = rows[exercises[0]["workout_plan_exercise_id"]]
    assert result["plan_changed"]
    assert row.exercise_id == "pushup"
    assert row.planned_weight is None
    assert row.notes == "Swapped from Barbell Bench Press - Medium Grip by AI coach: no barbell"


def test_second_confirm_after_rows_are_gone_is_not_a_crash(monkeypatch):
    exercises = workout()
    session = FakeSession({})  # the first "yes" already removed them
    result = confirm_with(session, monkeypatch, exercises, shorten_pending(exercises))
    assert result["reply"] == coach_changes.WORKOUT_CHANGED_REPLY
    assert not session.committed


def test_concurrent_confirm_is_not_a_crash(monkeypatch):
    exercises = workout()
    session = FakeSession(fake_rows(exercises), stale=True)
    result = confirm_with(session, monkeypatch, exercises, shorten_pending(exercises))
    assert result["reply"] == coach_changes.WORKOUT_CHANGED_REPLY
    assert not result.get("plan_changed")


def test_rows_from_another_workout_are_not_changed(monkeypatch):
    exercises = workout()
    session = FakeSession(fake_rows(exercises, workout_id=uuid.uuid4()))
    result = confirm_with(session, monkeypatch, exercises, shorten_pending(exercises))
    assert result["reply"] == coach_changes.WORKOUT_CHANGED_REPLY
    assert not session.deleted


def test_exercises_with_logged_sets_are_left_alone(monkeypatch):
    exercises = workout()
    session = FakeSession(fake_rows(exercises), logged_sets=2)
    result = confirm_with(session, monkeypatch, exercises, shorten_pending(exercises))
    assert "already logged sets" in result["reply"]
    assert not session.deleted and not session.committed


# ============================================================
# Signed pending actions
# ============================================================

def test_pending_action_is_signed_per_user():
    pending = {"type": "follow_up", "intent": {"intent": "shorten_workout"}}
    token = coach_changes.sign_pending_action(pending, USER_ID)
    assert coach_changes.verify_pending_action(token, USER_ID) == pending
    assert coach_changes.verify_pending_action(token, uuid.uuid4()) is None
    assert coach_changes.verify_pending_action(token[:-2] + "xx", USER_ID) is None
    assert coach_changes.verify_pending_action(None, USER_ID) is None


def test_pending_action_payload_cannot_be_edited():
    token = coach_changes.sign_pending_action({"type": "follow_up", "intent": {"intent": "other"}}, USER_ID)
    header, payload, signature = token.split(".")
    forged = jwt.encode({"sub": str(USER_ID), "aud": coach_rules.PENDING_ACTION_AUDIENCE, "pending": {}}, "wrong-key")
    assert coach_changes.verify_pending_action(f"{header}.{forged.split('.')[1]}.{signature}", USER_ID) is None


def test_pending_action_is_not_a_login_token():
    token = coach_changes.sign_pending_action({"type": "follow_up", "intent": {"intent": "other"}}, USER_ID)
    with pytest.raises(HTTPException) as error:
        asyncio.run(get_current_user_id(token))
    assert error.value.status_code == 401


def test_login_token_is_not_a_pending_action():
    login = asyncio.run(create_access_token({"sub": str(USER_ID)}))
    assert coach_changes.verify_pending_action(login, USER_ID) is None
