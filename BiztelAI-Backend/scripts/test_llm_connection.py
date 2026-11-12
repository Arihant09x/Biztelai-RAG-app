#!/usr/bin/env python3
"""Dynamic LLM Connection Test Script.

Performs an authenticated chat-completion request using the configured
base URL, API key, and model from .env without hardcoding provider details.
Exits with 0 on success, 1 on failure.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

from app.utils.security import mask_secret
from openai import OpenAI, AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError


def run_llm_connection_test() -> int:
    base_url = os.getenv("LLM_API_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    print("=" * 70)
    print("BIZTELAI MANUFACTURING SOP COPILOT - DYNAMIC LLM CONNECTION TEST")
    print("=" * 70)

    # 1. Validation of environment variables
    missing = []
    if not base_url:
        missing.append("LLM_API_BASE_URL")
    if not api_key:
        missing.append("LLM_API_KEY")
    if not model:
        missing.append("LLM_MODEL")

    if missing:
        print(f"\n[FAIL] Missing required configuration in .env:\n  - " + "\n  - ".join(missing))
        print("Please configure .env before executing the live connection test.")
        return 1

    print(f"Target Base URL: {base_url}")
    print(f"Target Model:    {model}")
    print(f"API Key:         {mask_secret(api_key)}")
    print("-" * 70)
    print("Initiating authenticated chat-completion request...")

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=30.0)

    test_messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant.",
    },
    {
        "role": "user",
        "content": "Reply with the word 'OK'.",
    },
    ]
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=test_messages,
            max_tokens=2048,
            temperature=0.0,
        )
        latency_ms = round((time.time() - start_time) * 1000, 2)
        message = response.choices[0].message
        
        # 1. Try to get standard content
        reply = message.content or ""
        
        # 2. Fallback to reasoning if content is empty (Crucial for gpt-oss models)
        if not reply.strip():
            reasoning_text = getattr(message, "reasoning", None) or ""
            if reasoning_text.strip():
                reply = reasoning_text.strip()

        # 3. If BOTH content and reasoning are empty, THEN fail
        if not reply.strip():
            finish_reason = response.choices[0].finish_reason if response.choices else "unknown"
            print(f"\n[FAIL] LLM returned an empty response.")
            print(f"Finish Reason: {finish_reason}")
            if finish_reason == "length":
                print("The token budget was likely exhausted during reasoning. Try increasing max_tokens further.")
            return 1  # <--- NOW PROPERLY INDENTED

        print("\n[SUCCESS] Connection established successfully!")
        print(f"Response Latency: {latency_ms} ms")
        print(f"Response Content: {reply.strip()}")
        print("=" * 70)
        return 0

    except AuthenticationError as e:
        print(f"\n[FAIL] Authentication Error: Invalid API key for endpoint {base_url}.")
        print(f"Details: {str(e)}")
        return 1
    except RateLimitError as e:
        print(f"\n[FAIL] Rate Limit Exceeded: Provider quota exhausted or rate limit hit.")
        print(f"Details: {str(e)}")
        return 1
    except APITimeoutError as e:
        print(f"\n[FAIL] Request Timeout: Endpoint failed to respond within 30 seconds.")
        print(f"Details: {str(e)}")
        return 1
    except APIConnectionError as e:
        print(f"\n[FAIL] Connection Error: Could not connect to {base_url}.")
        print(f"Details: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n[FAIL] Unexpected Error: {type(e).__name__}: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_llm_connection_test())

