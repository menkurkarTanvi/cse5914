"""AI coach: the POST /coach/chat route.

No API key needed, and no database except where a test says otherwise:
the LLM and the context loader are fakes from coach_fakes.py. The shared
conftest.py needs TEST_DATABASE_URL, so without it run:
    pytest backend/tests/test_coach_*.py --noconftest
"""

import asyncio

from httpx import ASGITransport, AsyncClient
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

from backend.agent_chatbot.coach_graph import build_coach_graph
from coach_fakes import USER_ID, FakeLLM, fake_context, workout
from core.auth import create_access_token


def call_route(monkeypatch, llm, body):
    import backend.agent_chatbot.coach_graph as coach_graph
    from main import app

    graph = build_coach_graph(llm, load_context=fake_context(workout()))
    monkeypatch.setattr(coach_graph, "get_coach_graph", lambda: graph)
    token = asyncio.run(create_access_token({"sub": str(USER_ID)}))

    async def post():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/coach/chat", json=body, headers={"Authorization": f"Bearer {token}"})

    return asyncio.run(post())


def test_route_whitespace_message_is_rejected(monkeypatch):
    response = call_route(monkeypatch, FakeLLM({"intent": "other"}), {"message": "   "})
    assert response.status_code == 422


def test_route_llm_failure_is_503(monkeypatch):
    class FailingLLM(FakeLLM):
        async def _classify(self, messages):
            raise ChatGoogleGenerativeAIError("429 RESOURCE_EXHAUSTED")

    response = call_route(monkeypatch, FailingLLM({"intent": "other"}), {"message": "hi"})
    assert response.status_code == 503
    assert "busy" in response.json()["detail"]


def test_route_proposal_needs_follow_up(monkeypatch):
    llm = FakeLLM({"intent": "shorten_workout", "minutes_available": 20})
    response = call_route(monkeypatch, llm, {"message": "I have 20 minutes"})
    body = response.json()
    assert response.status_code == 200
    assert body["needs_follow_up"] and body["pending_action"]
    assert not body["plan_changed"]


def test_route_expired_pending_action(monkeypatch):
    response = call_route(monkeypatch, FakeLLM({"intent": "confirm"}), {"message": "yes", "pending_action": "expired.token.x"})
    assert response.json()["reply"].startswith("That suggestion expired")
