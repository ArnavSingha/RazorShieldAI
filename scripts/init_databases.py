#!/usr/bin/env python3
"""
RazorShield AI — Database Connection & Creation Checker
Validates connections to PostgreSQL, Redis, and SQLite, and ensures tables are created.
"""

import sys
import os
import psycopg2
from psycopg2 import sql
import redis
import sqlite3

# Import application settings directly if possible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.config import settings
from backend.app.infrastructure.storage_contracts import (
    SQLiteIdempotencyStore,
    SQLiteAuditRepository,
    PostgreSQLAuditRepository,
    RedisIdempotencyStore,
)


def check_and_init():
    print("============================================================")
    print("RAZORSHIELD DATABASE CONNECTION & CREATION CHECK")
    print("============================================================")

    # 1. Check SQLite (Always works locally, creates tables)
    try:
        print(f"Checking SQLite at {settings.sqlite_db_path}...")
        sqlite_idemp = SQLiteIdempotencyStore()
        sqlite_audit = SQLiteAuditRepository()
        print(
            "[SUCCESS] SQLite tables (idempotency_records, audit_ledger) verified/created successfully."
        )
    except Exception as e:
        print(f"[FAIL] SQLite initialization failed: {e}")

    # 2. Check Redis
    redis_dsn = settings.redis_dsn
    print(f"\nChecking Redis at {redis_dsn}...")
    try:
        r = redis.from_url(redis_dsn)
        if r.ping():
            print("[SUCCESS] Redis connection successful.")
            # Redis doesn't need schema creation
        else:
            print("[FAIL] Redis ping failed.")
    except Exception as e:
        print(f"[WARN] Redis is offline or unreachable: {e}")

    # 3. Check PostgreSQL
    pg_dsn = settings.postgres_dsn
    print(f"\nChecking PostgreSQL at {pg_dsn}...")
    try:
        # We attempt to connect and create tables using the app's adapter
        pg_audit = PostgreSQLAuditRepository()
        print("[SUCCESS] PostgreSQL connection successful.")

        # Verify table exists
        with psycopg2.connect(pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'audit_ledger');"
                )
                row = cur.fetchone()
                exists = row[0] if row else False
                if exists:
                    print(
                        "[SUCCESS] PostgreSQL 'audit_ledger' table verified/created successfully."
                    )
                else:
                    print(
                        "[FAIL] PostgreSQL table creation might have failed silently."
                    )

    except Exception as e:
        print(f"[WARN] PostgreSQL is offline or unreachable: {e}")
        print(
            "   If you need Postgres, make sure your local Postgres server is running and the database 'razorshield' exists."
        )

    print("\n============================================================")
    print("CHECK COMPLETE")
    print("============================================================")


if __name__ == "__main__":
    check_and_init()
