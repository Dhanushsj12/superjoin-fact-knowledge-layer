import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured in the .env file.")

client = genai.Client(api_key=api_key)


def generate_text(prompt: str) -> str:
    """Send a prompt to Gemini and return the generated text."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text