"""AI coach: choosing the model provider from .env settings.

No API calls and no database: these only build the client objects. Run
without TEST_DATABASE_URL with:
    pytest backend/tests/test_coach_llm.py --noconftest
"""

import openai
import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from agent_chatbot.coach_llm import CoachUnavailableError, coach_provider, get_coach_llm, is_llm_error


@pytest.fixture
def env(monkeypatch):
    for name in ("COACH_PROVIDER", "COACH_MODEL", "OPENAI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_openai_is_preferred_when_both_keys_are_set(env):
    env.setenv("OPENAI_API_KEY", "sk-test")
    env.setenv("GOOGLE_API_KEY", "google-test")
    assert coach_provider() == "openai"
    llm = get_coach_llm()
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "gpt-4o-mini"


def test_gemini_is_used_without_an_openai_key(env):
    env.setenv("GOOGLE_API_KEY", "google-test")
    assert coach_provider() == "gemini"
    assert isinstance(get_coach_llm(), ChatGoogleGenerativeAI)


def test_coach_provider_forces_gemini(env):
    env.setenv("OPENAI_API_KEY", "sk-test")
    env.setenv("GOOGLE_API_KEY", "google-test")
    env.setenv("COACH_PROVIDER", "gemini")
    assert isinstance(get_coach_llm(), ChatGoogleGenerativeAI)


def test_coach_model_overrides_the_default(env):
    env.setenv("OPENAI_API_KEY", "sk-test")
    env.setenv("COACH_MODEL", "gpt-test")
    assert get_coach_llm().model_name == "gpt-test"


def test_no_key_is_reported_clearly(env):
    with pytest.raises(CoachUnavailableError, match="OPENAI_API_KEY or GOOGLE_API_KEY"):
        get_coach_llm()


def test_forced_provider_without_its_key(env):
    env.setenv("GOOGLE_API_KEY", "google-test")
    env.setenv("COACH_PROVIDER", "openai")
    with pytest.raises(CoachUnavailableError, match="OPENAI_API_KEY is not set"):
        get_coach_llm()


def test_key_with_lookalike_letters_is_reported(env):
    # "К" is Cyrillic; it would otherwise crash every request.
    env.setenv("OPENAI_API_KEY", "sk-proj-abcКdef")
    with pytest.raises(CoachUnavailableError, match="non-ASCII"):
        get_coach_llm()


def test_unknown_provider(env):
    env.setenv("COACH_PROVIDER", "claude")
    with pytest.raises(CoachUnavailableError, match="must be 'openai' or 'gemini'"):
        get_coach_llm()


def test_openai_failures_count_as_llm_errors():
    assert is_llm_error(openai.APITimeoutError(request=None))
    assert not is_llm_error(KeyError("bug in our code"))
