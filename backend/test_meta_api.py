"""
Meta Model API Connection Test for DevTeam AI.

Tests connectivity using the OpenAI SDK against the configured
Meta Model API endpoint (Meta Muse Spark).
"""

import os
import sys
import traceback
import json
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env explicitly
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

META_API_KEY = os.getenv("META_API_KEY")
META_BASE_URL = os.getenv("META_BASE_URL")
META_MODEL = os.getenv("META_MODEL")


def sanitize(text: str) -> str:
    """Ensure the API key is never exposed in output or error messages."""
    if not text:
        return text
    if META_API_KEY and len(META_API_KEY) > 4:
        return text.replace(META_API_KEY, "[REDACTED_API_KEY]")
    return text


def test_meta_connection():
    # 1. Configuration Validation
    missing_vars = []
    if not META_API_KEY:
        missing_vars.append("META_API_KEY")
    if not META_BASE_URL:
        missing_vars.append("META_BASE_URL")
    if not META_MODEL:
        missing_vars.append("META_MODEL")

    if missing_vars:
        print("[ERROR] Missing required configuration in backend/.env:")
        for var in missing_vars:
            print(f"  - {var}")
        sys.exit(1)

    print("Connecting to Meta Model API...")
    print(f"  Base URL : {META_BASE_URL}")
    print(f"  Model    : {META_MODEL}")
    print("  API Key  : [CONFIGURED]")

    try:
        from openai import (
            OpenAI,
            APIConnectionError,
            AuthenticationError,
            RateLimitError,
            APIStatusError,
        )

        client = OpenAI(
            api_key=META_API_KEY,
            base_url=META_BASE_URL,
        )

        # Single small Chat Completions request.
        # Meta Muse Spark generates internal reasoning tokens that consume output budget.
        # max_completion_tokens=500 provides sufficient headroom for reasoning tokens + final text.
        request_kwargs = {
            "model": META_MODEL,
            "messages": [
                {"role": "user", "content": "Reply with exactly READY."}
            ],
            "temperature": 0.0,
            "max_completion_tokens": 500,
        }

        try:
            response = client.chat.completions.create(**request_kwargs)
        except Exception as req_err:
            # Fall back to max_tokens=500 if the endpoint strictly expects legacy max_tokens
            if "max_completion_tokens" in str(req_err):
                request_kwargs.pop("max_completion_tokens", None)
                request_kwargs["max_tokens"] = 500
                response = client.chat.completions.create(**request_kwargs)
            else:
                raise req_err

        if not response.choices:
            print("\n[ERROR] API returned an empty choices list.")
            print(f"Raw Response: {sanitize(str(response))}")
            sys.exit(1)

        choice = response.choices[0]
        message = getattr(choice, "message", None)
        finish_reason = getattr(choice, "finish_reason", "unknown")

        # Safely extract message content (may be None if tokens were exhausted or format is non-standard)
        raw_content = getattr(message, "content", None) if message else None
        refusal = getattr(message, "refusal", None) if message else None

        # Inspect any reasoning/thinking fields that reasoning models may include
        model_extra = getattr(message, "model_extra", {}) or {} if message else {}
        reasoning = (
            getattr(message, "reasoning_content", None)
            or model_extra.get("reasoning_content")
            or model_extra.get("reasoning")
            or model_extra.get("thought")
        )

        reply = raw_content.strip() if isinstance(raw_content, str) and raw_content.strip() else None

        if reply:
            print("\n--- Model Response ---")
            print(reply)
            print("----------------------")
            print("\n[SUCCESS] Meta Model API connection verified successfully!")
        else:
            print("\n[WARNING] Request succeeded (HTTP 200), but message.content was None or empty.")
            print(f"  Finish Reason: {finish_reason}")
            if finish_reason == "length":
                print("  Note: finish_reason is 'length'. Internal reasoning tokens may have reached the token limit.")
            if refusal:
                print(f"  Refusal: {refusal}")
            if reasoning:
                print(f"  Reasoning / Thinking: {reasoning}")

            # Print serialized choice for detailed inspection
            try:
                dumped = choice.model_dump()
                print(f"  Choice Data: {sanitize(json.dumps(dumped, indent=2))}")
            except Exception:
                print(f"  Choice Data: {sanitize(str(choice))}")
            print("\n[SUCCESS] Endpoint reachable and authenticated, but response format requires review.")

    except AuthenticationError as e:
        print("\n[ERROR] Authentication failed. Please verify your META_API_KEY.")
        print(f"Details: {sanitize(str(e))}")
        sys.exit(1)
    except APIConnectionError as e:
        print(f"\n[ERROR] Connection failed. Unable to reach {META_BASE_URL}.")
        print(f"Details: {sanitize(str(e))}")
        sys.exit(1)
    except RateLimitError as e:
        print("\n[ERROR] Rate limit reached. Please check your quota or retry later.")
        print(f"Details: {sanitize(str(e))}")
        sys.exit(1)
    except APIStatusError as e:
        print(f"\n[ERROR] API returned error status {e.status_code}: {e.message}")
        print(f"Details: {sanitize(str(e))}")
        sys.exit(1)
    except Exception as e:
        print("\n[ERROR] Unexpected error during API test:")
        tb_str = traceback.format_exc()
        print(sanitize(tb_str))
        sys.exit(1)


if __name__ == "__main__":
    test_meta_connection()
