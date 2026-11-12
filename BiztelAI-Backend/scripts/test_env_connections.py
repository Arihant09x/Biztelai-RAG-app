#!/usr/bin/env python3
"""Diagnostic script to test DB, Redis, and LLM connections from .env."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def test_database():
    print("-" * 60)
    print("TESTING DATABASE (PostgreSQL / Neon)")
    print("-" * 60)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[FAIL] DATABASE_URL is not set.")
        return False

    from sqlalchemy import create_engine, text
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            ver = conn.execute(text("SELECT version();")).scalar()
            print("[PASS] Connected to PostgreSQL!")
            print(f"       Version: {ver[:60]}...")

            # Check pgvector extension
            ext = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchall()
            if ext:
                print(f"[PASS] pgvector extension installed: version {ext[0][1]}")
            else:
                print("[INFO] pgvector not yet created in DB. Attempting 'CREATE EXTENSION IF NOT EXISTS vector;'...")
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    print("[PASS] pgvector extension successfully created!")
                except Exception as ce:
                    print(f"[WARN] Could not create pgvector extension: {ce}")
        return True
    except Exception as e:
        print(f"[FAIL] Database connection error: {type(e).__name__}: {e}")
        return False

def test_redis():
    print("\n" + "-" * 60)
    print("TESTING REDIS (Upstash)")
    print("-" * 60)
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("[FAIL] REDIS_URL is not set.")
        return False

    import redis
    try:
        import ssl
        # Check if Upstash rediss://
        ssl_kwargs = {}
        if redis_url.startswith("rediss://"):
            ssl_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE

        client = redis.from_url(redis_url, **ssl_kwargs)
        pong = client.ping()
        print(f"[PASS] Connected to Redis successfully! PING response: {pong}")
        # Test basic write/read
        client.set("biztelai_test_key", "healthy", ex=60)
        val = client.get("biztelai_test_key")
        print(f"[PASS] Key set & get test: biztelai_test_key = {val.decode() if isinstance(val, bytes) else val}")
        return True
    except Exception as e:
        print(f"[FAIL] Redis connection error: {type(e).__name__}: {e}")
        return False

def test_llm():
    print("\n" + "-" * 60)
    print("TESTING LLM PROVIDER (Groq)")
    print("-" * 60)
    base_url = os.getenv("LLM_API_BASE_URL")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")

    print(f"Target Base URL: {base_url}")
    print(f"Target Model:    {model}")

    if not api_key:
        print("[FAIL] LLM_API_KEY is not set.")
        return False

    from openai import OpenAI
    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Respond strictly with the single word: OK"}],
            max_tokens=10,
            temperature=0.0,
        )
        msg = res.choices[0].message.content.strip()
        print(f"[PASS] LLM response received: '{msg}'")
        return True
    except Exception as e:
        print(f"[FAIL] LLM connection error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    db_ok = test_database()
    redis_ok = test_redis()
    llm_ok = test_llm()
    print("\n" + "=" * 60)
    print(f"SUMMARY: DB={db_ok}, REDIS={redis_ok}, LLM={llm_ok}")
    print("=" * 60)

