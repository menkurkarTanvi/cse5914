from google import genai
from google.genai import types

import os


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)


EMBEDDING_MODEL = "gemini-embedding-001"

#Generate embedding for the given text using the Gemini embedding model.
def generate_embedding(text: str) -> list[float]:

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            output_dimensionality=1536,
        ),
    )

    return response.embeddings[0].values