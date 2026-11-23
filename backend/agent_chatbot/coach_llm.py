from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

load_dotenv()

# The AI coach's model. OpenAI is used when OPENAI_API_KEY is set (paid, no
# free-tier rate limits); otherwise Gemini (free tier) with GOOGLE_API_KEY.
# COACH_PROVIDER forces one ("openai" or "gemini"), and COACH_MODEL overrides
# the model. Any LangChain chat model with structured output works.
DEFAULT_COACH_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-3.5-flash",
}

API_KEY_SETTINGS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}

# How many earlier chat turns the model sees.
HISTORY_TURNS = 10


class CoachUnavailableError(RuntimeError):
    pass


def coach_provider() -> str:
    """Which provider the coach uses: COACH_PROVIDER if set, else the first
    one with an API key, preferring OpenAI."""
    provider = os.getenv("COACH_PROVIDER", "").strip().lower()
    if provider:
        if provider not in API_KEY_SETTINGS:
            raise CoachUnavailableError(
                f"COACH_PROVIDER must be 'openai' or 'gemini', not {provider!r}."
            )
        return provider
    for provider, setting in API_KEY_SETTINGS.items():
        if os.getenv(setting):
            return provider
    raise CoachUnavailableError(
        "The AI coach needs OPENAI_API_KEY or GOOGLE_API_KEY in .env "
        "(a free Gemini key: https://aistudio.google.com/apikey)."
    )


def get_coach_llm():
    provider = coach_provider()
    api_key = os.getenv(API_KEY_SETTINGS[provider])
    if not api_key:
        raise CoachUnavailableError(
            f"COACH_PROVIDER is {provider!r}, but {API_KEY_SETTINGS[provider]} is not set in .env."
        )
    if not api_key.isascii():
        # Otherwise every request fails with a bare 500 while building headers.
        raise CoachUnavailableError(
            f"{API_KEY_SETTINGS[provider]} in .env contains non-ASCII characters, often "
            "lookalike letters from copying the key. Paste the key again."
        )
    model = os.getenv("COACH_MODEL") or DEFAULT_COACH_MODELS[provider]

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        chat_model = ChatOpenAI
    else:
        from langchain_google_genai import ChatGoogleGenerativeAI

        chat_model = ChatGoogleGenerativeAI

    return chat_model(
        model=model,
        api_key=api_key,
        max_retries=2,
        # Seconds. Without this, a hung call holds the request open forever.
        timeout=LLM_TIMEOUT_SECONDS,
    )


LLM_TIMEOUT_SECONDS = 30


def is_llm_error(exc: BaseException) -> bool:
    """True for failures of the model call itself (rate limit, outage,
    timeout, unusable output), as opposed to bugs in our code."""
    import asyncio

    import httpx
    import openai
    from google.genai.errors import APIError
    from langchain_core.exceptions import OutputParserException
    from langchain_google_genai._common import GoogleGenerativeAIError

    return isinstance(
        exc,
        (
            GoogleGenerativeAIError,
            APIError,
            # Rate limits, timeouts, connection failures and 5xx from OpenAI.
            openai.APIError,
            OutputParserException,
            httpx.TimeoutException,
            asyncio.TimeoutError,
        ),
    )


# ============================================================
# Prompts
# ============================================================

CLASSIFIER_PROMPT = """You route messages for FitStack's AI fitness coach.
Read the conversation and the user's latest message, and fill in the intent and any details the user gave.
Only fill in details the user actually said or clearly implied; leave the rest empty.

How to read short replies:
- If the coach just asked the user a question, the latest message is most likely the answer to it. Keep the intent of the original request and fill in the detail it answers.
- If the coach offered numbered options, a pick ("2", "the second one", "dumbbell bench") is intent "confirm" with selected_option set to that number.
- If the coach proposed a change and asked whether to make it, "yes"/"sure"/"do it" is "confirm" and "no"/"never mind" is "decline".

{context}"""

ANSWER_PROMPT = """You are FitStack's AI fitness coach. You are talking to the user inside the FitStack app.

Rules:
- Be brief and practical: at most about 120 words, plain sentences or a short list.
- Respect the user's limitations. Never suggest a movement that loads an injured area. For sharp or lasting pain, tell them to stop and see a professional.
- Base exercise facts on the exercise details below when they are given.
- You can't change the plan in this reply. If they want changes, tell them you can swap an exercise, shorten today's workout, or make it easier or harder, and they just need to ask.
- Stay on fitness and training. Politely steer anything else back.

{context}"""


def build_classifier_messages(state: dict) -> list[BaseMessage]:
    context = [_profile_context(state), _workout_context(state), _pending_context(state.get("pending"))]
    system = CLASSIFIER_PROMPT.format(context="\n\n".join(part for part in context if part))
    return [SystemMessage(system), *_history(state), HumanMessage(state["message"])]


def build_answer_messages(state: dict, details: dict | None, planned: dict | None) -> list[BaseMessage]:
    context = [_profile_context(state), _workout_context(state)]
    if details is not None:
        context.append(_exercise_context(details, planned))
    elif (
        state.get("intent", {}).get("intent") == "exercise_question"
        and state["intent"].get("exercise_name")
    ):
        context.append(
            f"The user asked about \"{state['intent'].get('exercise_name')}\", which isn't in the "
            "FitStack exercise library. Answer from general knowledge and say so briefly."
        )
    system = ANSWER_PROMPT.format(context="\n\n".join(part for part in context if part))
    return [SystemMessage(system), *_history(state), HumanMessage(state["message"])]


def _history(state: dict) -> list[BaseMessage]:
    messages = []
    for turn in (state.get("history") or [])[-HISTORY_TURNS:]:
        if turn["role"] == "user":
            messages.append(HumanMessage(turn["content"]))
        else:
            messages.append(AIMessage(turn["content"]))
    return messages


def _profile_context(state: dict) -> str:
    profile = state.get("profile")
    if not profile:
        return ""
    limitations = ", ".join(profile.get("limitations") or []) or "none"
    equipment = ", ".join(profile.get("available_equipment") or []) or "bodyweight only"
    return (
        "User profile:\n"
        f"- Goal: {profile['goal']}\n"
        f"- Experience: {profile['experience_level']}\n"
        f"- Equipment: {equipment}\n"
        f"- Limitations: {limitations}"
    )


def _workout_context(state: dict) -> str:
    exercises = state.get("current_workout_exercises") or []
    workout = state.get("current_workout")
    if not exercises or not workout:
        return "The user has no upcoming workout right now."

    lines = [f"Today's workout ({workout['day_of_week'].title()}, {workout['scheduled_date']}):"]
    for item in sorted(exercises, key=lambda entry: entry["exercise_order"]):
        line = f"{item['exercise_order']}. {item['exercise']['name']}: {item['sets_planned']} x {item['reps_min']}-{item['reps_max']}"
        if item.get("planned_weight"):
            line += f" @ {item['planned_weight']:g} {item['weight_unit']}"
        lines.append(line)
    return "\n".join(lines)


def _pending_context(pending: dict | None) -> str:
    if not pending:
        return ""
    if pending["type"] == "follow_up":
        return (
            f"The coach just asked a follow-up question about a \"{pending['intent']['intent']}\" "
            "request. The latest message probably answers it."
        )
    if pending["type"] == "swap":
        options = "\n".join(
            f"{number}. {option['name']}" for number, option in enumerate(pending["options"], start=1)
        )
        return f"The coach offered these replacements for {pending['from_name']}:\n{options}"
    return f"The coach proposed to {pending['summary']} and asked whether to make the change."


def _exercise_context(details: dict, planned: dict | None) -> str:
    lines = [
        f"Exercise details for {details['name']}:",
        f"- Difficulty: {details['difficulty_level']}, {details['mechanics']}",
        f"- Primary muscles: {', '.join(details['primary_muscles']) or 'n/a'}",
        f"- Secondary muscles: {', '.join(details['secondary_muscles']) or 'n/a'}",
        f"- Equipment: {', '.join(details['equipment_required']) or 'none'}",
        f"- Instructions: {details['instructions']}",
    ]
    if planned is not None:
        lines.append(
            f"- In today's workout: {planned['sets_planned']} sets of {planned['reps_min']}-{planned['reps_max']} reps, "
            f"{planned['rest_seconds']}s rest"
        )
    return "\n".join(lines)
