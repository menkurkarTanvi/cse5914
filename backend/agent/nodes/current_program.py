from agent.state import WorkoutAgentState

async def load_last_workout_plan(state: WorkoutAgentState) -> None:
    """
    Load the last workout plan from the database and store it in the state.
    """
    #FILL IN THE REST: GET THE LAST WORKOUT PLAN FROM THE DATABASE AND STORE IT IN THE STATE
    pass

async def load_recent_performance(state: WorkoutAgentState) -> None:
    """
    Load the recent performance from the database and store it in the state.
    """
    #USE WorkoutSet TO GET THE RECENT PERFORMANCE FROM THE DATABASE AND STORE IT IN THE STATE

    #Ex of information we want
    #Exercise:
    #    Bench Press
    #
    #    Planned:
    #    3 × 8–10 @ RPE 8

    #    Actual:
    #    Set 1: 135 × 10 @ RPE 7
    #    Set 2: 135 × 10 @ RPE 7
    #    Set 3: 135 × 10 @ RPE 8
    pass
