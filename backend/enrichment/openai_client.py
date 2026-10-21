# enrichment/openai_client.py

import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .schemas import ExerciseEnrichment
from .prompts import SYSTEM_PROMPT, build_exercise_prompt


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY was not found. Check your environment variables."
    )

client = AsyncOpenAI(api_key=api_key)

ENRICHMENT_MODEL = "gpt-4o-mini"


async def enrich_with_openai(exercise) -> ExerciseEnrichment:
    """Classify an exercise using OpenAI structured output."""

    prompt = build_exercise_prompt(exercise)

    response = await client.responses.parse(
        model=ENRICHMENT_MODEL,
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=ExerciseEnrichment,
    )

    enrichment = response.output_parsed

    if enrichment is None:
        raise ValueError(
            f"OpenAI did not return structured enrichment for "
            f"exercise {exercise.exercise_id}"
        )

    return enrichment