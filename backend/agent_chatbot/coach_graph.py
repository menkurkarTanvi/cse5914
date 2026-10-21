from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from agent_chatbot.nodes import coach
from agent_chatbot.nodes.coach import CoachState
from agent_chatbot.nodes import coach_changes, coach_intent, coach_swap

# AI coach graph. Each request runs it once: the chat history and any
# pending proposal come in with the request, so no state is kept between
# turns on the server.

RESPONSE_NODES = (
    "ask_follow_up",
    "answer_exercise_question",
    "propose_swap",
    "propose_shorten",
    "propose_adjust",
    "apply_pending_action",
    "decline_pending_action",
    "pending_expired_reply",
    "general_reply",
)


def build_coach_graph(llm, load_context=coach.load_coach_context):
    """``load_context`` is swappable so tests can run without a database."""

    async def classify_message(state: CoachState) -> dict:
        return await coach_intent.classify_message(state, llm)

    async def answer_exercise_question(state: CoachState) -> dict:
        return await coach.answer_exercise_question(state, llm)

    async def general_reply(state: CoachState) -> dict:
        return await coach.general_reply(state, llm)

    graph = StateGraph(CoachState)
    graph.add_node("load_coach_context", load_context)
    graph.add_node("classify_message", classify_message)
    graph.add_node("ask_follow_up", coach_intent.ask_follow_up)
    graph.add_node("answer_exercise_question", answer_exercise_question)
    graph.add_node("propose_swap", coach_swap.propose_swap)
    graph.add_node("propose_shorten", coach_changes.propose_shorten)
    graph.add_node("propose_adjust", coach_changes.propose_adjust)
    graph.add_node("apply_pending_action", coach_changes.apply_pending_action)
    graph.add_node("decline_pending_action", coach_changes.decline_pending_action)
    graph.add_node("pending_expired_reply", coach_intent.pending_expired_reply)
    graph.add_node("general_reply", general_reply)

    graph.add_edge(START, "load_coach_context")
    graph.add_conditional_edges(
        "load_coach_context",
        coach.has_reply,
        {"done": END, "continue": "classify_message"},
    )
    graph.add_conditional_edges("classify_message", coach_intent.route_after_classify, list(RESPONSE_NODES))
    for node in RESPONSE_NODES:
        graph.add_edge(node, END)

    return graph.compile()


@lru_cache(maxsize=1)
def get_coach_graph():
    from backend.agent_chatbot.coach_llm import get_coach_llm

    return build_coach_graph(get_coach_llm())
