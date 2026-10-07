import os

from google import genai
from google.genai import types

from .schemas import ExerciseEnrichment
from .prompts import SYSTEM_PROMPT, build_exercise_prompt


GEMINI_MODEL = "gemini-2.5-flash"


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


def enrich_with_gemini(exercise) -> ExerciseEnrichment:

    prompt = (
        SYSTEM_PROMPT
        + "\n\n"
        + build_exercise_prompt(exercise)
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExerciseEnrichment,
            temperature=0,
        ),
    )

    return ExerciseEnrichment.model_validate_json(response.text)