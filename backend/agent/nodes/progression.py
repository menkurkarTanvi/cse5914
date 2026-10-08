from agent.state import WorkoutAgentState

async def analyze_progression(state: WorkoutAgentState):
    #Example output
    [
        {
            "workout_plan_exercise_id": "...",
            "action": "increase_weight",
            "amount": 5
        },
        ...
    ]

async def apply_progression(state: WorkoutAgentState):
    pass