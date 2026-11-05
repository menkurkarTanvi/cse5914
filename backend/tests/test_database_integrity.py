"""Exercise the migrated PostgreSQL schema, not just Pydantic validation."""
import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import CheckConstraint, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.database import Base
from models import (
    Exercise, ExercisePrescription, Profile, User, UserAvailability,
    WorkoutFeedback, WorkoutPlan, WorkoutPlanExercise, WorkoutProgram, WorkoutSet,
)
from services.workout_service import Workout_Service

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def records(db_session):
    user = User(email="integrity@example.com", hashed_password="test")
    exercise = Exercise(
        exercise_id=str(uuid.uuid4()), name="Barbell Squat", type="reps",
        difficulty_level="beginner", force_type="push", mechanics="compound",
        category="strength", instructions="Squat.", primary_muscles=["quadriceps"],
        secondary_muscles=[], tertiary_muscles=[], equipment_required=["barbell"],
    )
    db_session.add_all([user, exercise])
    await db_session.flush()
    profile = Profile(user_id=user.id, goal="strength", experience_level="beginner")
    program = WorkoutProgram(user_id=user.id, start_date=date.today(),
                             end_date=date.today() + timedelta(days=27),
                             goal="strength", status="active")
    db_session.add_all([profile, program])
    await db_session.flush()
    workout = WorkoutPlan(program_id=program.program_id, description="Full Body",
                          week_number=1, day_of_week="Monday",
                          scheduled_date=date.today(), status="scheduled")
    db_session.add(workout)
    await db_session.flush()
    planned = WorkoutPlanExercise(workout_id=workout.workout_id,
        exercise_id=exercise.exercise_id, exercise_order=1, sets_planned=3,
        reps_min=8, reps_max=12, target_rpe_min=6, target_rpe_max=8,
        rest_seconds=90, planned_weight=50)
    db_session.add(planned)
    await db_session.flush()
    db_session.add_all([
        WorkoutSet(workout_plan_exercise_id=planned.id, set_number=1, reps=8, weight=50, rpe=7),
        WorkoutFeedback(workout_id=workout.workout_id, user_id=user.id, overall_rating=4),
        UserAvailability(user_id=user.id, day_of_week="Monday", max_duration_minutes=60),
        ExercisePrescription(exercise_id=exercise.exercise_id, goal="strength",
            sets_min=3, sets_max=5, reps_min=3, reps_max=6, rest_seconds=180,
            target_rpe_min=7, target_rpe_max=9),
    ])
    await db_session.flush()
    return user, profile, program, workout, exercise


@pytest.mark.parametrize("table,updates", [
    ("profiles", "goal='typo'"),
    ("profiles", "experience_level='expert'"),
    ("exercises", "difficulty_level='typo'"),
    ("exercise_prescriptions", "goal='typo'"),
    ("exercise_prescriptions", "sets_min=0"),
    ("exercise_prescriptions", "sets_max=1"),
    ("exercise_prescriptions", "reps_max=1"),
    ("exercise_prescriptions", "rest_seconds=-1"),
    ("exercise_prescriptions", "target_rpe_min=10,target_rpe_max=7"),
    ("user_availability", "day_of_week='Funday'"),
    ("user_availability", "max_duration_minutes=0"),
    ("workout_programs", "end_date=start_date-1"),
    ("workout_programs", "status='typo'"),
    ("workout_programs", "goal='typo'"),
    ("workout_plans", "week_number=5"),
    ("workout_plans", "status='typo'"),
    ("workout_plans", "day_of_week='Funday'"),
    ("workout_plan_exercises", "exercise_order=0"),
    ("workout_plan_exercises", "sets_planned=0"),
    ("workout_plan_exercises", "reps_min=0"),
    ("workout_plan_exercises", "reps_min=13"),
    ("workout_plan_exercises", "target_rpe_min=-1"),
    ("workout_plan_exercises", "target_rpe_max=11"),
    ("workout_plan_exercises", "target_rpe_min=9,target_rpe_max=8"),
    ("workout_plan_exercises", "rest_seconds=-1"),
    ("workout_plan_exercises", "planned_weight=-1"),
    ("workout_plan_exercises", "weight_unit='oz'"),
    ("workout_sets", "set_number=0"),
    ("workout_sets", "reps=0"),
    ("workout_sets", "weight=-1"),
    ("workout_sets", "rpe=11"),
    ("workout_sets", "weight_unit='oz'"),
    ("workout_feedback", "overall_rating=6"),
])
async def test_postgres_rejects_invalid_data(db_session, records, table, updates):
    with pytest.raises(IntegrityError) as error:
        async with db_session.begin_nested():
            await db_session.execute(text(f"UPDATE {table} SET {updates}"))
    assert error.value.orig.sqlstate == "23514"  # check_violation


async def test_all_model_checks_exist_in_migrated_database(db_session):
    connection = await db_session.connection()
    def verify(sync_connection):
        inspector = inspect(sync_connection)
        for table in Base.metadata.sorted_tables:
            actual = {c["name"] for c in inspector.get_check_constraints(table.name)}
            expected = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
            assert actual == expected, table.name
        assert inspector.get_pk_constraint("profiles")["constrained_columns"] == ["id"]
        assert any(c["column_names"] == ["user_id"]
                   for c in inspector.get_unique_constraints("profiles"))
    await connection.run_sync(verify)


async def test_profile_id_and_user_id_remain_unique(db_session, records):
    user, profile, *_ = records
    other = User(email="other@example.com", hashed_password="test")
    db_session.add(other)
    await db_session.flush()
    for profile_id, user_id in [(profile.id, other.id), (uuid.uuid4(), user.id)]:
        with pytest.raises(IntegrityError) as error:
            async with db_session.begin_nested():
                await db_session.execute(text("""
                    INSERT INTO profiles (id,user_id,goal,experience_level,
                        available_equipment,preferred_exercises,disliked_exercises,limitations)
                    VALUES (:id,:user_id,'strength','beginner','{}','{}','{}','{}')
                """), {"id":profile_id, "user_id":user_id})
        assert error.value.orig.sqlstate == "23505"


def load_integrity_migration():
    # The local alembic directory is not the installed alembic package.
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "alembic/versions/91d6a3b82f40_enforce_database_integrity.py"
    spec = spec_from_file_location("integrity_migration", path)
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


async def test_migration_preserves_populated_profiles_and_legacy_skips(db_session, records):
    _, profile, *_ = records
    profile_id, user_id = profile.id, profile.user_id
    connection = await db_session.connection()
    migration = load_integrity_migration()

    def run(sync_connection, direction):
        with Operations.context(MigrationContext.configure(sync_connection)):
            getattr(migration, direction)()

    await connection.run_sync(run, "downgrade")
    await db_session.execute(text("UPDATE workout_plans SET status='incompleted'"))
    await connection.run_sync(run, "upgrade")
    row = (await db_session.execute(text("SELECT id,user_id,goal FROM profiles"))).one()
    assert tuple(row) == (profile_id, user_id, "strength")
    assert await db_session.scalar(text("SELECT status FROM workout_plans")) == "skipped"


async def test_migration_rejects_invalid_history_atomically(db_session, records):
    from sqlalchemy.exc import DBAPIError

    migration = load_integrity_migration()
    connection = await db_session.connection()

    def run(sync_connection, direction):
        with Operations.context(MigrationContext.configure(sync_connection)):
            getattr(migration, direction)()

    await connection.run_sync(run, "downgrade")
    await db_session.execute(text("UPDATE workout_plans SET status='incompleted'"))
    await db_session.execute(text("UPDATE workout_sets SET reps=-1"))
    with pytest.raises(DBAPIError, match="ck_reps: 1 invalid rows in workout_sets"):
        async with connection.begin_nested():
            await connection.run_sync(run, "upgrade")
    # Neither the status normalization nor the new key/checks survive failure.
    assert await db_session.scalar(text("SELECT status FROM workout_plans")) == "incompleted"
    assert await connection.run_sync(
        lambda conn: inspect(conn).get_pk_constraint("profiles")["constrained_columns"]
    ) == ["user_id"]
    assert await connection.run_sync(
        lambda conn: inspect(conn).get_check_constraints("profiles")
    ) == []


async def test_upcoming_query_boundaries_and_program_filter(db_session, records):
    user, _, program, *_ = records
    today = date.today()
    for offset, day in zip([-1, 1, 7, 8], ["Monday", "Tuesday", "Wednesday", "Thursday"]):
        db_session.add(WorkoutPlan(program_id=program.program_id, description="Boundary",
            week_number=2 if offset < 7 else 3, day_of_week=day,
            scheduled_date=today+timedelta(days=offset), status="scheduled"))
    draft = WorkoutProgram(user_id=user.id, start_date=today, end_date=today,
                           goal="strength", status="draft")
    other_user = User(email="someone@example.com", hashed_password="test")
    db_session.add_all([draft, other_user])
    await db_session.flush()
    other_program = WorkoutProgram(user_id=other_user.id, start_date=today,
        end_date=today, goal="strength", status="active")
    db_session.add(other_program)
    await db_session.flush()
    for p in [draft, other_program]:
        db_session.add(WorkoutPlan(program_id=p.program_id, description="Excluded",
            week_number=1, day_of_week="Monday", scheduled_date=today, status="scheduled"))
    await db_session.flush()
    plans = await Workout_Service(db_session).get_upcoming_workout_plans(user.id, today)
    assert [p.scheduled_date for p in plans] == [today, today+timedelta(days=1), today+timedelta(days=7)]
    assert all(p.program_id == program.program_id for p in plans)


async def test_generate_save_and_retrieve_four_week_program(db_session, client, monkeypatch, records):
    from agent.nodes import new_program
    from core.auth import create_access_token
    from database import database

    user, _, _, _, exercise = records
    point = {"goal":"strength", "experience_level":"beginner",
        "available_equipment":["barbell", "body only"], "available_days":["monday"],
        "disliked_exercises":[], "preferred_exercises":[], "limitations":[], "recent_exercises":[]}
    candidates = new_program.build_candidates([exercise], {}, point)
    program = new_program.build_program(point, candidates,
        [{"day_of_week":"monday", "is_available":True, "max_duration_minutes":60}],
        [], date.today())
    factory = async_sessionmaker(bind=db_session.bind, expire_on_commit=False,
                                join_transaction_mode="create_savepoint")
    monkeypatch.setattr(database, "AsyncSessionLocal", factory)
    result = await new_program.save_program({"user_id":user.id, "generated_program":program})
    program_id = result["active_program"]["program_id"]
    saved = (await db_session.scalars(select(WorkoutPlan).where(WorkoutPlan.program_id == program_id))).all()
    assert len(saved) == 4
    assert all(w.description == "Full Body" for w in saved)
    token = await create_access_token({"sub":str(user.id)})
    response = await client.get("/workouts/workoutPlan", headers={"Authorization":f"Bearer {token}"})
    assert response.status_code == 200
    returned = [w for w in response.json()["workouts"] if w["workout_id"] in {str(w.workout_id) for w in saved}]
    assert returned and all(w["description"] == "Full Body" and w["exercises"] for w in returned)
