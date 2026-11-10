import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.workout_plan import WorkoutPlan
from models.workout_plan_exercise import WorkoutPlanExercise
from models.workout_program import WorkoutProgram
from agent.graph import run_workout_agent

class Workout_Service:
    def __init__(self, db: AsyncSession):
        self.db = db

    #This function calls the agent to generate a new workout program for the user
    async def generate_new_workout_program(self, user_id: uuid.UUID) -> dict:
        return run_workout_agent(user_id=user_id)

    async def determine_user_has_workout_plan(self, user_id: uuid.UUID) -> bool:
        #Get the most recent workout program for the user
        result = await self.db.execute(
            select(WorkoutProgram)
            .where(WorkoutProgram.user_id == user_id)
            .order_by(WorkoutProgram.start_date.desc())
            .limit(1)
        )
        program = result.scalar_one_or_none()

        if not program:
            return False

        #Determine the last week number of the most current workout program
        result = await self.db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.program_id == program.program_id)
            .order_by(WorkoutPlan.scheduled_date.desc())    
            .limit(1)
        )
        plan = result.scalar_one_or_none()

        #If the week number if 4, return false, else return true
        if plan and plan.week_number == 4:
            return False
        return True

    async def get_upcoming_workout_plans(
        self,
        user_id: uuid.UUID,
        today: date | None = None,
    ) -> list[WorkoutPlan]:
        """Return plans from today through seven days ahead, oldest first.

        Both endpoints are included, preserving the My Plan page's existing
        upcoming-workout window. Draft programs are excluded.

        Each plan has its exercises loaded (sorted by ``exercise_order``), and
        each exercise has its ``exercise`` details and the logged ``sets``
        loaded (sorted by ``set_number``). Plans the user hasn't done yet
        simply have no sets. Returns an empty list if there are none.

        ``today`` is a parameter so tests can use a fixed date.
        """
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        today = today or date.today()
        window_end = today + timedelta(days=7)

        result = await self.db.execute(
            select(WorkoutPlan)
            .join(
                WorkoutProgram,
                WorkoutProgram.program_id == WorkoutPlan.program_id,
            )
            .where(
                WorkoutProgram.user_id == user_id,
                WorkoutProgram.status != "draft",
                WorkoutPlan.scheduled_date <= window_end,
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
