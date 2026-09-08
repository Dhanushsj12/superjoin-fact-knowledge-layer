import os

from dotenv import load_dotenv


load_dotenv()


MODEL_NAME = "qwen/qwen3.8-27b"


# Groq is an optional LLM provider.
#
# The application must remain functional even when:
#   - the groq package is not installed
#   - GROQ_API_KEY is not configured
#   - the Groq API is unavailable
#   - the Groq API reaches its rate/quota limit
#
# In these cases, generate_text() raises a controlled RuntimeError.
# The extraction pipeline catches that failure and uses the
# deterministic fallback extractor.
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

    Groq is used when it is available and configured.
    If Groq is unavailable, not configured, or fails during the
    request, the calling extraction pipeline can fall back to
    deterministic extraction.
    """

    if client is None:
        if Groq is None:
            raise RuntimeError(
                "Groq provider is not installed. "
                "Falling back to deterministic extraction."
            )

        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Falling back to deterministic extraction."
        )

    try:
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

    except Exception as exc:
        raise RuntimeError(
            f"Groq LLM request failed: {exc}. "
            "Falling back to deterministic extraction."
        ) from exc