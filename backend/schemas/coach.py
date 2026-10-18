from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

# Stripped first, so a message of only spaces is rejected (422) instead of
# reaching the model as an empty message.
Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
TurnContent = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: TurnContent


class CoachChatRequest(BaseModel):
    message: Message
    # Earlier turns, oldest first. The server keeps no chat state.
    history: list[ChatTurn] = Field(default_factory=list, max_length=50)
    # Echo back the pending_action from the previous response, unchanged.
    pending_action: str | None = None


class SwapOption(BaseModel):
    number: int
    exercise_id: str
    name: str
    equipment_required: list[str]
    reason: str


class CoachChatResponse(BaseModel):
    reply: str
    intent: str
    # True when the coach is waiting for an answer: a question, swap
    # options to pick from, or a change to confirm with yes/no.
    needs_follow_up: bool
    # Numbered swap choices, for rendering as buttons.
    options: list[SwapOption] = Field(default_factory=list)
    # Opaque; send it back with the next message. None when nothing is pending.
    pending_action: str | None = None
    # True when today's workout was changed; the plan page should refetch.
    plan_changed: bool = False
