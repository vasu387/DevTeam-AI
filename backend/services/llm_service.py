import os
from pathlib import Path

from dotenv import load_dotenv
from crewai import LLM


# Find backend/.env
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


def get_llm():
    """Create and return the shared Meta Muse Spark LLM."""

    api_key = os.getenv("META_API_KEY")
    base_url = os.getenv("META_BASE_URL")
    model = os.getenv("META_MODEL")

    if not api_key:
        raise ValueError("META_API_KEY is missing from backend/.env")

    if not base_url:
        raise ValueError("META_BASE_URL is missing from backend/.env")

    if not model:
        raise ValueError("META_MODEL is missing from backend/.env")

    return LLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
        custom_openai=True,
        timeout=600,
    )
