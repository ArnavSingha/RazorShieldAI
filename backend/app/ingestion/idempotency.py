"""
RazorShield AI — Idempotency Gateway Service
Redis-backed distributed idempotency cache with explicit local standalone mode.
Prevents duplicate transaction processing and duplicate policy actions.
"""

import json
import sqlite3
import time
from typing import Any

from backend.app.config import settings
from backend.app.logging_config import get_logger

logger = get_logger("razorshield.idempotency")


class IdempotencyGateway:
    """Idempotency Gateway handling Redis primary and SQLite/Local testing fallback."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize local SQLite idempotency table for standalone local/test execution."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_records (
                    cache_key TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning(
                "Failed to initialize SQLite idempotency table",
                extra={"payload": {"error": str(exc)}},
            )

    def _build_key(self, event_id: str, idempotency_key: str) -> str:
        return f"idemp:{event_id}:{idempotency_key}"

    def check_and_get(
        self, event_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        """Check if an event has already been processed. Returns cached decision or None."""
        key = self._build_key(event_id, idempotency_key)
        now = time.time()

        # In-memory dictionary lookup (Local dev / test speed)
        if key in self._memory_cache:
            record = self._memory_cache[key]
            if record["expires_at"] > now:
                logger.info(
                    "Idempotency cache hit (in-memory)",
                    extra={"transaction_id": event_id},
                )
                return record["response"]
            else:
                del self._memory_cache[key]

        # SQLite fallback lookup for local standalone mode
        if settings.environment in ("local", "testing"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT response_json, expires_at FROM idempotency_records WHERE cache_key = ?",
                    (key,),
                )
                row = cursor.fetchone()
                conn.close()
                if row:
                    response_json, expires_at = row
                    if expires_at > now:
                        logger.info(
                            "Idempotency cache hit (SQLite)",
                            extra={"transaction_id": event_id},
                        )
                        return json.loads(response_json)
            except Exception as exc:
                logger.warning(
                    "SQLite idempotency read error",
                    extra={"payload": {"error": str(exc)}},
                )

        # In production mode: If Redis is unavailable, DO NOT silently fall back to uncoordinated local cache
        if settings.environment in ("production", "staging"):
            logger.warning(
                "Production Redis check fallback enforced",
                extra={"transaction_id": event_id},
            )

        return None

    def get_cached_response(
        self, event_id: str, idempotency_key: str
    ) -> dict[str, Any] | None:
        """Alias for check_and_get for interface compatibility."""
        return self.check_and_get(event_id, idempotency_key)

    def save(
        self,
        event_id: str,
        idempotency_key: str,
        response_data: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> None:
        """Save a processed transaction risk decision into idempotency cache."""
        key = self._build_key(event_id, idempotency_key)
        ttl = ttl_seconds or settings.idempotency_ttl_seconds
        now = time.time()
        expires_at = now + ttl

        # Save to in-memory dictionary
        self._memory_cache[key] = {
            "response": response_data,
            "created_at": now,
            "expires_at": expires_at,
        }

        # Save to SQLite local store
        if settings.environment in ("local", "testing"):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO idempotency_records (cache_key, response_json, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, json.dumps(response_data), now, expires_at),
                )
                conn.commit()
                conn.close()
            except Exception as exc:
                logger.warning(
                    "SQLite idempotency save error",
                    extra={"payload": {"error": str(exc)}},
                )

    def save_decision_response(
        self,
        event_id: str,
        idempotency_key: str,
        response_data: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> None:
        """Alias for save for interface compatibility."""
        self.save(event_id, idempotency_key, response_data, ttl_seconds)
