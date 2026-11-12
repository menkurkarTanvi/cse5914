# agent/graph.py
"""LangGraph wiring for the FitStack workout agent.

    START -> load_user_context -> [active 4-week program?]
        no  -> analyze_starting_point -> retrieve_candidate_exercises
               -> generate_4_week_program -> validate_program
               -> [errors?] yes: END   no: save_program -> END
        yes -> current-program path (placeholder until those nodes exist)

Run from the project root:  python -m agent.graph <user_id>
"""

from __future__ import annotations

import uuid
from typing import Literal

from langgraph.graph import END, START, StateGraph

from agent.nodes.context import is_active_four_week_program, load_user_context
from agent.nodes.new_program import (
    analyze_starting_point,
    generate_4_week_program,
    retrieve_candidate_exercises,
    save_program,
    validate_program,
)
from agent.state import WorkoutAgentState

# Node names. LangGraph rejects a node whose name matches a state key
# (e.g. a node called "profile_changed" or "starting_point" would fail),
# so keep these as verbs / step names.
LOAD_CONTEXT = "load_user_context"
ANALYZE_START = "analyze_starting_point"
RETRIEVE = "retrieve_candidate_exercises"
GENERATE = "generate_4_week_program"
VALIDATE = "validate_program"
SAVE = "save_program"
CURRENT_PROGRAM = "current_program_path"


# ------------------------------------------------------------
# Routing
# ------------------------------------------------------------

def route_after_validation(state: WorkoutAgentState) -> Literal["save", "stop"]:
    """Only a program with no validation errors may be saved.

    Generation is rule-based and deterministic, so re-running it with the same
    inputs would give the same errors. Stop and surface them instead of looping.
    """
    return "stop" if state.get("validation_errors") else "save"


# ------------------------------------------------------------
# Placeholder for the part of the graph that is not written yet
# ------------------------------------------------------------

async def current_program_path(state: WorkoutAgentState) -> dict:
    """Replace with the real chain:

    load_upcoming_workout -> load_recent_performance -> analyze_progression
    -> apply_progression -> [profile changed?] -> check_existing_exercises
    -> [any invalid?] -> retrieve_replacement -> swap_exercises
    -> validate_upcoming_workout
    """
    raise NotImplementedError("The current-program path has not been built yet")


# ------------------------------------------------------------
# Graph
# ------------------------------------------------------------

def build_graph():
    builder = StateGraph(WorkoutAgentState)

    builder.add_node(LOAD_CONTEXT, load_user_context)

    # New program path
    builder.add_node(ANALYZE_START, analyze_starting_point)
    builder.add_node(RETRIEVE, retrieve_candidate_exercises)
    builder.add_node(GENERATE, generate_4_week_program)
    builder.add_node(VALIDATE, validate_program)
    builder.add_node(SAVE, save_program)

    # Current program path (placeholder)
    builder.add_node(CURRENT_PROGRAM, current_program_path)

    builder.add_edge(START, LOAD_CONTEXT)

    # is_active_four_week_program returns "new_program" or "current_program".
    builder.add_conditional_edges(
        LOAD_CONTEXT,
        is_active_four_week_program,
        {
            "new_program": ANALYZE_START,
            "current_program": CURRENT_PROGRAM,
        },
    )

    builder.add_edge(ANALYZE_START, RETRIEVE)
    builder.add_edge(RETRIEVE, GENERATE)
    builder.add_edge(GENERATE, VALIDATE)
    builder.add_conditional_edges(
        VALIDATE,
        route_after_validation,
        {"save": SAVE, "stop": END},
    )

    # Later, both paths should converge on validate_upcoming_workout:
    #   SAVE -> validate_upcoming_workout -> END
    builder.add_edge(SAVE, END)
    builder.add_edge(CURRENT_PROGRAM, END)

    return builder.compile()


# Module-level compiled graph (also what LangGraph Studio / langgraph.json expects).
graph = build_graph()


async def run_workout_agent(user_id: uuid.UUID | str) -> dict:
    """Run the agent for one user and return the final state.

    On success ``upcoming_workout`` is set. If validation failed, the program
    was not saved and ``validation_errors`` lists why.
    """
    return await graph.ainvoke({"user_id": user_id})


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m agent.graph <user_id>")

    final_state = asyncio.run(run_workout_agent(sys.argv[1]))

    if final_state.get("validation_errors"):
        print("Program NOT saved. Validation errors:")
        for error in final_state["validation_errors"]:
            print(f"  - {error}")
    else:
        print("Upcoming workout:", final_state.get("upcoming_workout"))

