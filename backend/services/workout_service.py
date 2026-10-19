import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.workout_plan import WorkoutPlan
from models.workout_plan_exercise import WorkoutPlanExercise
from models.workout_program import WorkoutProgram


class Workout_Service:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def get_last_week_workout_plans(
        self,
        user_id: uuid.UUID,
        today: date | None = None,
    ) -> list[WorkoutPlan]:
        """Return the user's workout plans from the last 7 days, oldest first.

        The window starts 7 days ago and ends yesterday, so today's workout is
        not included. It always contains last week's workout for today's
        weekday. Workouts from every one of the user's programs are considered,
        except draft programs that were never started.

        Each plan has its exercises loaded (sorted by ``exercise_order``), and
        each exercise has its ``exercise`` details and the logged ``sets``
        loaded (sorted by ``set_number``). Plans the user hasn't done yet
        simply have no sets. Returns an empty list if there are none.

        ``today`` is a parameter so tests can use a fixed date.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        today = today or date.today()
        window_start = today + timedelta(days=7)

        result = await self.db.execute(
            select(WorkoutPlan)
            .join(
                WorkoutProgram,
                WorkoutProgram.program_id == WorkoutPlan.program_id,
            )
            .where(
                WorkoutProgram.user_id == user_id,
                WorkoutPlan.scheduled_date <= window_start,
                WorkoutPlan.scheduled_date >= today,
            )
            .order_by(WorkoutPlan.scheduled_date)
            .options( 
                selectinload(WorkoutPlan.program),
                    selectinload(WorkoutPlan.exercises).options(
                        selectinload(WorkoutPlanExercise.exercise),
                        selectinload(WorkoutPlanExercise.sets),
                    ),
            )
        )
        plans = list(result.scalars().all())

        for plan in plans:
            plan.exercises.sort(key=lambda item: item.exercise_order)
            for item in plan.exercises:
                item.sets.sort(key=lambda workout_set: workout_set.set_number)

        return plans