import os

from dotenv import load_dotenv


load_dotenv()


MODEL_NAME = "qwen/qwen3.8-27b"


# Groq is an optional LLM provider.
#
# The application must be able to start and use the deterministic
# fallback extractor even when:
#   - the groq package is not installed
#   - GROQ_API_KEY is not configured
#   - the Groq API is unavailable
#
# This import is therefore intentionally guarded.
try:
    from groq import Groq
except ImportError:
    Groq = None


api_key = os.getenv("GROQ_API_KEY")

client = None

if Groq is not None and api_key:
    client = Groq(
        api_key=api_key,
        max_retries=0
    )


def generate_text(prompt: str) -> str:
    """
    Send a prompt to Groq and return the model response.

    Groq is optional. If the provider is unavailable or not configured,
    this function raises a controlled RuntimeError. The extraction
    pipeline is responsible for catching the failure and using the
    deterministic fallback extractor.
    """

    if client is None:
        if Groq is None:
            raise RuntimeError(
                "Groq provider is not installed. "
                "Using deterministic fallback extraction."
            )

        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Using deterministic fallback extraction."
        )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a fact extraction system. "
                    "Always return valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        response_format={
            "type": "json_object"
        },
    )

    return response.choices[0].message.content