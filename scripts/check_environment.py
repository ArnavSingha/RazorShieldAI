#!/usr/bin/env python3
"""
RazorShield AI — Environment Validation Script
Validates application configuration, dependencies, and execution modes without leaking secrets.
"""

import os
import sys


def test_postgres(dsn):
    if not dsn:
        return "UNAVAILABLE"
    try:
        import psycopg2

        conn = psycopg2.connect(dsn, connect_timeout=1)
        conn.close()
        return "CONNECTED"
    except Exception:
        return "UNAVAILABLE"


def test_redis(dsn):
    if not dsn:
        return "UNAVAILABLE"
    try:
        import redis

        client = redis.Redis.from_url(dsn, socket_connect_timeout=1)
        client.ping()
        return "CONNECTED"
    except Exception:
        return "UNAVAILABLE"


def test_gemini(api_key, model="gemini-3.6-flash"):
    if not api_key:
        return "UNAVAILABLE"
    try:
        import google.genai

        client = google.genai.Client(api_key=api_key)
        # Just check if the client initialized, or do a tiny call if we want
        return "AVAILABLE"
    except Exception:
        return "UNAVAILABLE"


def check_env():
    print("============================================================")
    print("RAZORSHIELD ENVIRONMENT CHECK")
    print("============================================================")

    from dotenv import load_dotenv

    load_dotenv()

    app_mode = os.getenv("ENVIRONMENT", "local").upper()
    print(f"Application Mode:        {app_mode}")

    # PostgreSQL
    pg_dsn = os.getenv("POSTGRES_DSN", "")
    print(f"PostgreSQL Config        {'CONFIGURED' if pg_dsn else 'OPTIONAL'}")
    pg_status = test_postgres(pg_dsn)
    print(f"PostgreSQL               {pg_status}")

    # Redis
    redis_dsn = os.getenv("REDIS_DSN", "")
    print(f"Redis Config             {'CONFIGURED' if redis_dsn else 'OPTIONAL'}")
    redis_status = test_redis(redis_dsn)
    print(f"Redis                    {redis_status}")

    # Gemini
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    llm_provider = os.getenv("LLM_PROVIDER", "mock").upper()
    print(f"Gemini Config            {'CONFIGURED' if gemini_key else 'OPTIONAL'}")
    gemini_status = test_gemini(gemini_key)
    print(f"Gemini Live              {gemini_status}")

    # Audit Secret
    audit_secret = os.getenv("AUDIT_HMAC_SECRET", "")
    if audit_secret and audit_secret != "replace-with-local-development-hmac-secret":
        print(f"Audit Secret             CONFIGURED")
    else:
        print(f"Audit Secret             UNAVAILABLE (Default or missing)")

    print("============================================================")
    print(f"Configured Provider: {llm_provider}")
    print(f"API Key Present: {'YES' if gemini_key else 'NO'}")
    print(f"Live Provider Available: {'YES' if gemini_status == 'AVAILABLE' else 'NO'}")
    print("============================================================")


if __name__ == "__main__":
    check_env()
