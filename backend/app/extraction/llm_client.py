import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is not configured in the .env file."
    )


client = Groq(
    api_key=api_key,
    max_retries=0
)


MODEL_NAME = "qwen/qwen3.8-27b"


def generate_text(prompt: str) -> str:
    """
    Send a prompt to Groq and return the model response.

    The LLM provider is isolated behind this function so the
    extraction pipeline remains provider-independent.
    """

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