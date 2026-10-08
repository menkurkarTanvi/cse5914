from __future__ import annotations

from agent.state import WorkoutAgentState
from models.profile import Profile
from models.user_availability import UserAvailability

#PLEASE REFER TO THE WORKOUTAGENTSTATE. This state is common amongst all nodes in the graph
#Each function will perform some operations to update the WorkoutAgentState

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