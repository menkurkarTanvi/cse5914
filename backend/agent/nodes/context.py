from agent.state import WorkoutState
import uuid

#Get the user id, the profile, the current program (if they have one), and the current workout(if they have one) and return it as a dictionary
def load_user_context(state: WorkoutState, id: uuid.UUID) -> None:
    #Look at the WorkoutState class in state.py to see what information needs to be stored in the state (this will be passed amongst the nodes in the graph)
    pass

#We need to check if the last week was week number 4, if not the user is still in the current workout plan
def is_active_four_week_program(state: WorkoutState) -> str:
    """
    Check if the current program is an active four-week program.
    """
    if state.get("active_program") is None:
        return "new_program"

    return "current_program"
    
