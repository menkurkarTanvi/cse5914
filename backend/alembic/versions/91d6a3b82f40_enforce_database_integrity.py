"""Align the profile key and enforce database validation.

Revision ID: 91d6a3b82f40
Revises: f635c7b390ac
"""
from alembic import op
import sqlalchemy as sa

revision = "91d6a3b82f40"
down_revision = "f635c7b390ac"
branch_labels = None
depends_on = None

# Frozen migration definitions: do not import the evolving ORM models here.
GOALS = "('strength','hypertrophy','muscular_endurance','power','general_fitness')"
DAYS = "('monday','tuesday','wednesday','thursday','friday','saturday','sunday')"
CHECKS = {
    "profiles": {
        "ck_profile_goal": f"goal IN {GOALS}",
        "ck_profile_experience": "experience_level IN ('beginner','intermediate','advanced')",
    },
    "exercises": {
        "ck_exercise_difficulty": "difficulty_level IN ('beginner','intermediate','expert','unknown')",
    },
    "exercise_prescriptions": {
        "ck_prescription_goal": f"goal IN {GOALS}",
        "ck_valid_sets": "sets_min > 0 AND sets_max >= sets_min",
        "ck_valid_reps": "reps_min > 0 AND reps_max >= reps_min",
        "ck_valid_rest": "rest_seconds >= 0",
        "ck_valid_rpe": "target_rpe_min >= 0 AND target_rpe_max <= 10 AND target_rpe_max >= target_rpe_min",
    },
    "user_availability": {
        "ck_availability_day": f"lower(day_of_week) IN {DAYS}",
        "ck_availability_duration": "max_duration_minutes IS NULL OR max_duration_minutes BETWEEN 1 AND 300",
    },
    "workout_programs": {
        "ck_program_dates": "end_date >= start_date",
        "ck_program_status": "status IN ('draft','active','completed')",
        "ck_program_goal": f"goal IN {GOALS}",
    },
    "workout_plans": {
        "ck_week_number": "week_number BETWEEN 1 AND 4",
        "ck_workout_status": "status IN ('scheduled','in_progress','completed','skipped')",
        "ck_workout_day": f"lower(day_of_week) IN {DAYS}",
    },
    "workout_plan_exercises": {
        "ck_exercise_order": "exercise_order > 0",
        "ck_sets_planned": "sets_planned > 0",
        "ck_reps_range": "reps_min > 0 AND reps_max >= reps_min",
        "ck_rest_seconds": "rest_seconds >= 0",
        "ck_target_rpe_min": "target_rpe_min IS NULL OR (target_rpe_min >= 0 AND target_rpe_min <= 10)",
        "ck_target_rpe_max": "target_rpe_max IS NULL OR (target_rpe_max >= 0 AND target_rpe_max <= 10)",
        "ck_target_rpe_range": "target_rpe_min <= target_rpe_max",
        "ck_planned_weight": "planned_weight IS NULL OR planned_weight >= 0",
        "ck_planned_weight_unit": "weight_unit IN ('lb','kg')",
    },
    "workout_sets": {
        "ck_set_number": "set_number > 0",
        "ck_reps": "reps > 0",
        "ck_weight": "weight IS NULL OR weight >= 0",
        "ck_rpe": "rpe IS NULL OR (rpe >= 0 AND rpe <= 10)",
        "ck_set_weight_unit": "weight_unit IN ('lb','kg')",
    },
    "workout_feedback": {
        "ck_overall_rating": "overall_rating IS NULL OR (overall_rating >= 1 AND overall_rating <= 5)",
    },
}


def upgrade() -> None:
    # The old skip endpoint wrote this value. Preserve its meaning while
    # moving existing records onto the vocabulary used by the application.
    op.execute("UPDATE workout_plans SET status = 'skipped' WHERE status = 'incompleted'")

    # Fail atomically with a useful error for unexpected historical data.
    # Do not clamp reps/weights or discard rows to force a successful upgrade.
    for table, checks in CHECKS.items():
        for name, condition in checks.items():
            op.execute(sa.text(f"""
                DO $$
                DECLARE invalid_count bigint;
                BEGIN
                    SELECT count(*) INTO invalid_count FROM {table}
                    WHERE NOT ({condition});
                    IF invalid_count > 0 THEN
                        RAISE EXCEPTION 'Cannot add {name}: % invalid rows in {table}. Correct the data and retry.', invalid_count;
                    END IF;
                END $$;
            """))
            op.create_check_constraint(name, table, condition)

    # user_id remains UNIQUE, preserving the one-profile-per-user rule.
    # Existing id values are retained; duplicate ids abort the transaction.
    op.drop_constraint("profiles_pkey", "profiles", type_="primary")
    op.create_primary_key("profiles_pkey", "profiles", ["id"])


def downgrade() -> None:
    op.drop_constraint("profiles_pkey", "profiles", type_="primary")
    op.create_primary_key("profiles_pkey", "profiles", ["user_id"])
    for table, checks in reversed(list(CHECKS.items())):
        for name in checks:
            op.drop_constraint(name, table, type_="check")
    # Keep skipped statuses: this is valid application data, not schema state.
