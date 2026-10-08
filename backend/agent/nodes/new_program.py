from __future__ import annotations

from agent.state import WorkoutAgentState
from models.profile import Profile
from models.user_availability import UserAvailability


# Days/week thresholds for picking a split. Chosen to match common
# programming conventions — adjust freely if your generation step
# wants different cutoffs.
MIN_DAYS_FOR_UPPER_LOWER = 3
MIN_DAYS_FOR_PPL = 5


async def analyze_starting_point(state: WorkoutAgentState) -> dict:
   pass


#Candidate exercises for the next 4 week workout plan
async def retrieve_candidate_exercises(state: WorkoutAgentState):
    # Find exercises that could be used in the new program
    pass


async def generate_4_week_program(state: WorkoutAgentState):
    pass


async def validate_program(state: WorkoutAgentState):
    pass


async def save_program(state: WorkoutAgentState):
    pass