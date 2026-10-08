"""Seed a complete, repeatable user context for manual agent testing."""

import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import select

from database.database import AsyncSessionLocal
from models import (
    Exercise,
    Profile,
    User,
    UserAvailability,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutProgram,
    WorkoutSet,
)


USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000101")
PROGRAM_ID = uuid.UUID("00000000-0000-0000-0000-000000000201")
COMPLETED_WORKOUT_ID = uuid.UUID("00000000-0000-0000-0000-000000000301")
UPCOMING_WORKOUT_ID = uuid.UUID("00000000-0000-0000-0000-000000000302")
PLAN_EXERCISE_ID = uuid.UUID("00000000-0000-0000-0000-000000000401")
EXERCISE_ID = "context-test-bench-press"


async def main() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(User).where(User.id == USER_ID))
        if existing is not None:
            print(USER_ID)
            return

        today = date.today()
        session.add(
            User(
                id=USER_ID,
                email="context-test@fitstack.local",
                hashed_password="not-for-login",
            )
        )
        session.add(
            Profile(
                id=uuid.UUID("00000000-0000-0000-0000-000000000102"),
                user_id=USER_ID,
                goal="strength",
                experience_level="intermediate",
                available_equipment=["barbell", "bench"],
                preferred_exercises=["bench press"],
                disliked_exercises=[],
                limitations=[],
            )
        )
        session.add_all(
            [
                UserAvailability(
                    availability_id=uuid.UUID("00000000-0000-0000-0000-000000000111"),
                    user_id=USER_ID,
                    day_of_week="monday",
                    is_available=True,
                    max_duration_minutes=60,
                ),
                UserAvailability(
                    availability_id=uuid.UUID("00000000-0000-0000-0000-000000000112"),
                    user_id=USER_ID,
                    day_of_week="wednesday",
                    is_available=True,
                    max_duration_minutes=45,
                ),
            ]
        )
        session.add(
            Exercise(
                exercise_id=EXERCISE_ID,
                name="Bench Press",
                type="strength",
                difficulty_level="intermediate",
                force_type="push",
                mechanics="compound",
                category="strength",
                instructions="Lower the bar under control and press it upward.",
                primary_muscles=["chest"],
                secondary_muscles=["triceps"],
                tertiary_muscles=["shoulders"],
                equipment_required=["barbell", "bench"],
            )
        )
        session.add(
            WorkoutProgram(
                program_id=PROGRAM_ID,
                user_id=USER_ID,
                start_date=today - timedelta(days=7),
                end_date=today + timedelta(days=20),
                goal="strength",
                status="active",
            )
        )
        session.add_all(
            [
                WorkoutPlan(
                    workout_id=COMPLETED_WORKOUT_ID,
                    program_id=PROGRAM_ID,
                    week_number=1,
                    day_of_week="monday",
                    scheduled_date=today - timedelta(days=7),
                    status="completed",
                ),
                WorkoutPlan(
                    workout_id=UPCOMING_WORKOUT_ID,
                    program_id=PROGRAM_ID,
                    week_number=2,
                    day_of_week="wednesday",
                    scheduled_date=today + timedelta(days=1),
                    status="scheduled",
                ),
            ]
        )
        session.add(
            WorkoutPlanExercise(
                id=PLAN_EXERCISE_ID,
                workout_id=COMPLETED_WORKOUT_ID,
                exercise_id=EXERCISE_ID,
                exercise_order=1,
                sets_planned=3,
                reps_min=8,
                reps_max=10,
                target_rpe_min=7.0,
                target_rpe_max=8.0,
                rest_seconds=120,
                planned_weight=135.0,
                weight_unit="lb",
                progression_method="increase_weight",
            )
        )
        session.add_all(
            [
                WorkoutSet(
                    set_id=uuid.UUID(
                        f"00000000-0000-0000-0000-{500 + index:012d}"
                    ),
                    workout_plan_exercise_id=PLAN_EXERCISE_ID,
                    set_number=index,
                    weight=135.0,
                    weight_unit="lb",
                    reps=reps,
                    rpe=rpe,
                    completed=True,
                )
                for index, (reps, rpe) in enumerate(
                    [(10, 7.0), (9, 7.5), (8, 8.0)], start=1
                )
            ]
        )

        await session.commit()
        print(USER_ID)


if __name__ == "__main__":
    asyncio.run(main())
