import uuid

from fastapi import APIRouter, HTTPException

from agent_chatbot.coach_llm import CoachUnavailableError, is_llm_error
from agent_chatbot.nodes.coach_changes import sign_pending_action, verify_pending_action
from dependencies import CurrentUserId
from schemas.coach import CoachChatRequest, CoachChatResponse

# Prefix tag
router = APIRouter(
    prefix="/coach",
    tags=["coach"]
)


@router.post("/chat", response_model=CoachChatResponse)
async def chat(payload: CoachChatRequest, user_id: CurrentUserId):
    """Send one message to the AI coach and get its reply.

    The client keeps the conversation: send the earlier turns in ``history``
    and the previous response's ``pending_action`` back unchanged.
    """
    from backend.agent_chatbot.coach_graph import get_coach_graph

    try:
        graph = get_coach_graph()
    except CoachUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    user_uuid = uuid.UUID(user_id)  # JWT 'sub' is a string; the columns are UUID
    pending = verify_pending_action(payload.pending_action, user_uuid)
    try:
        result = await graph.ainvoke({
            "user_id": user_uuid,
            "message": payload.message,
            "history": [turn.model_dump() for turn in payload.history],
            "pending": pending,
            "pending_expired": payload.pending_action is not None and pending is None,
        })
    except Exception as exc:
        # Gemini failing (often the free tier's rate limit) is temporary, so
        # tell the client to retry instead of returning a bare 500.
        if is_llm_error(exc):
            raise HTTPException(
                status_code=503,
                detail="The AI coach is busy right now. Please try again in a minute.",
            )
        raise

    new_pending = result.get("new_pending")
    return {
        "reply": result["reply"],
        "intent": result["intent"]["intent"],
        "needs_follow_up": new_pending is not None,
        "options": result.get("options") or [],
        "pending_action": sign_pending_action(new_pending, user_uuid) if new_pending else None,
        "plan_changed": result.get("plan_changed", False),
    }
