"""
RazorShield AI — Storage Abstraction Layer
Explicit interfaces and implementations for Idempotency Stores (Redis / SQLite)
and Audit Repositories (PostgreSQL / SQLite).
Strict fail-closed production mode raises explicit exceptions when Redis/PostgreSQL are unreachable.
"""

import abc
import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from typing import Any

from backend.app.config import settings
from backend.app.domain.models import RiskDecision
from backend.app.logging_config import get_logger

logger = get_logger("razorshield.infrastructure")


# ============================================================================
# IDEMPOTENCY STORE CONTRACT & IMPLEMENTATIONS
# ============================================================================


class IdempotencyStore(abc.ABC):
    """Abstract interface for Idempotency Stores."""

    @abc.abstractmethod
    def claim(
        self, event_id: str, idempotency_key: str, ttl_seconds: int = 86400
    ) -> tuple[str, dict[str, Any] | None]:
        """
        Atomically claims an event for processing.
        Returns (status, cached_response) where status is:
        - "CLAIMED": First request wins atomic lock.
        - "ALREADY_EXISTS": Completed event already has cached response.
        - "IN_PROGRESS": Duplicate concurrent request currently executing.
        """

    @abc.abstractmethod
    def save_result(
        self,
        event_id: str,
        idempotency_key: str,
        response_data: dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> None:
        """Persists completed processing result into idempotency store."""

    @abc.abstractmethod
    def get_mode_name(self) -> str:
        pass


class SQLiteIdempotencyStore(IdempotencyStore):
    """Atomic SQLite Idempotency Store for local standalone execution."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self._init_sqlite()

    def get_mode_name(self) -> str:
        return "sqlite-standalone"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_sqlite(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS idempotency_records (
                        cache_key TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        response_json TEXT,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "Failed to initialize SQLite idempotency table",
                extra={"payload": {"error": str(exc)}},
            )

    def _build_key(self, event_id: str, idempotency_key: str) -> str:
        return f"idemp:{event_id}:{idempotency_key}"

    def claim(
        self, event_id: str, idempotency_key: str, ttl_seconds: int = 86400
    ) -> tuple[str, dict[str, Any] | None]:
        key = self._build_key(event_id, idempotency_key)
        now = time.time()
        expires_at = now + ttl_seconds

        if key in self._memory_cache:
            rec = self._memory_cache[key]
            if rec["expires_at"] > now:
                if rec["status"] == "COMPLETED":
                    return "ALREADY_EXISTS", rec["response"]
                elif rec["status"] == "IN_PROGRESS":
                    return "IN_PROGRESS", None

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT status, response_json, expires_at FROM idempotency_records WHERE cache_key = ?",
                    (key,),
                )
                row = cursor.fetchone()

                if row:
                    status, response_json, exp = row
                    if exp > now:
                        if status == "COMPLETED":
                            resp = json.loads(response_json) if response_json else None
                            return "ALREADY_EXISTS", resp
                        elif status == "IN_PROGRESS":
                            return "IN_PROGRESS", None

                cursor.execute(
                    """
                    INSERT INTO idempotency_records (cache_key, status, response_json, created_at, expires_at)
                    VALUES (?, 'IN_PROGRESS', NULL, ?, ?)
                    """,
                    (key, now, expires_at),
                )
                conn.commit()

                if cursor.rowcount > 0:
                    self._memory_cache[key] = {
                        "status": "IN_PROGRESS",
                        "response": None,
                        "expires_at": expires_at,
                    }
                    return "CLAIMED", None
                else:
                    return "IN_PROGRESS", None
        except Exception as exc:
            logger.warning("SQLite claim error", extra={"payload": {"error": str(exc)}})
            if key not in self._memory_cache:
                self._memory_cache[key] = {
                    "status": "IN_PROGRESS",
                    "response": None,
                    "expires_at": expires_at,
                }
                return "CLAIMED", None
            return "ALREADY_EXISTS", self._memory_cache[key].get("response")

    def save_result(
        self,
        event_id: str,
        idempotency_key: str,
        response_data: dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> None:
        key = self._build_key(event_id, idempotency_key)
        now = time.time()
        expires_at = now + ttl_seconds
        response_json = json.dumps(response_data)

        self._memory_cache[key] = {
            "status": "COMPLETED",
            "response": response_data,
            "expires_at": expires_at,
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO idempotency_records (cache_key, status, response_json, created_at, expires_at)
                    VALUES (?, 'COMPLETED', ?, ?, ?)
                    """,
                    (key, response_json, now, expires_at),
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "SQLite idempotency save_result error",
                extra={"payload": {"error": str(exc)}},
            )


class RedisIdempotencyStore(IdempotencyStore):
    """Production Redis Idempotency Store implementing SET key value NX EX ttl atomic primitives."""

    def __init__(self, redis_dsn: str | None = None, strict_mode: bool | None = None):
        self.redis_dsn = redis_dsn or settings.redis_dsn
        self.strict_mode = (
            strict_mode
            if strict_mode is not None
            else (settings.environment in ("production", "staging"))
        )
        self.client = None

        try:
            import redis

            self.client = redis.Redis.from_url(self.redis_dsn, socket_timeout=2.0)
            self.client.ping()
        except Exception as exc:
            if self.strict_mode:
                raise RuntimeError(
                    f"PRODUCTION REDIS UNREACHABLE ({self.redis_dsn}): {exc}"
                ) from exc
            self.client = None

    def get_mode_name(self) -> str:
        return "redis-production"

    def _build_key(self, event_id: str, idempotency_key: str) -> str:
        return f"idemp:{event_id}:{idempotency_key}"

    def claim(
        self, event_id: str, idempotency_key: str, ttl_seconds: int = 86400
    ) -> tuple[str, dict[str, Any] | None]:
        if not self.client:
            if self.strict_mode:
                raise RuntimeError(
                    "PRODUCTION REDIS STORE UNREACHABLE: Cannot perform distributed atomic idempotency claim."
                )
            return SQLiteIdempotencyStore().claim(
                event_id, idempotency_key, ttl_seconds
            )

        key = self._build_key(event_id, idempotency_key)
        try:
            acquired = self.client.set(key, "IN_PROGRESS", nx=True, ex=ttl_seconds)
            if acquired:
                return "CLAIMED", None

            val = self.client.get(key)
            if val:
                val_str = val.decode("utf-8") if isinstance(val, bytes) else str(val)
                if val_str != "IN_PROGRESS":
                    return "ALREADY_EXISTS", json.loads(val_str)
            return "IN_PROGRESS", None
        except Exception as exc:
            if self.strict_mode:
                raise RuntimeError(f"REDIS ATOMIC CLAIM ERROR: {exc}") from exc
            return SQLiteIdempotencyStore().claim(
                event_id, idempotency_key, ttl_seconds
            )

    def save_result(
        self,
        event_id: str,
        idempotency_key: str,
        response_data: dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> None:
        if not self.client:
            if self.strict_mode:
                raise RuntimeError(
                    "PRODUCTION REDIS STORE UNREACHABLE: Cannot persist completed idempotency result."
                )
            SQLiteIdempotencyStore().save_result(
                event_id, idempotency_key, response_data, ttl_seconds
            )
            return

        key = self._build_key(event_id, idempotency_key)
        try:
            self.client.set(key, json.dumps(response_data), ex=ttl_seconds)
        except Exception as exc:
            if self.strict_mode:
                raise RuntimeError(f"REDIS SAVE RESULT ERROR: {exc}") from exc
            SQLiteIdempotencyStore().save_result(
                event_id, idempotency_key, response_data, ttl_seconds
            )


# ============================================================================
# AUDIT REPOSITORY CONTRACT & IMPLEMENTATIONS
# ============================================================================


class AuditRepository(abc.ABC):
    """Abstract interface for Audit Ledger Repositories."""

    @abc.abstractmethod
    def append_decision_audit(self, decision: RiskDecision) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    def verify_ledger_integrity(self) -> tuple[bool, int]:
        pass

    @abc.abstractmethod
    def get_latest_hash(self) -> str:
        pass

    @abc.abstractmethod
    def get_storage_mode(self) -> str:
        pass


class SQLiteAuditRepository(AuditRepository):
    """Cryptographically tamper-evident SQLite Audit Ledger."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self.secret_key = settings.audit_hmac_secret.encode("utf-8")
        self._init_sqlite()

    def get_storage_mode(self) -> str:
        return "sqlite-standalone"

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_sqlite(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_ledger (
                        sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision_id TEXT UNIQUE NOT NULL,
                        transaction_id TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        previous_hash TEXT NOT NULL,
                        current_hash TEXT NOT NULL,
                        hmac_signature TEXT NOT NULL,
                        timestamp REAL NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(
                "Failed to initialize SQLite audit table",
                extra={"payload": {"error": str(exc)}},
            )

    def get_latest_hash(self) -> str:
        genesis_hash = "0" * 64
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT current_hash FROM audit_ledger ORDER BY sequence_id DESC LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    return row[0]
        except Exception:
            pass
        return genesis_hash

    def append_decision_audit(self, decision: RiskDecision) -> dict[str, Any]:
        prev_hash = self.get_latest_hash()
        payload = decision.to_dict()
        canonical_json = json.dumps(payload, sort_keys=True)
        payload_bytes = canonical_json.encode("utf-8")

        chain_input = payload_bytes + prev_hash.encode("utf-8")
        curr_hash = hashlib.sha256(chain_input).hexdigest()

        hmac_sig = hmac.new(
            self.secret_key, curr_hash.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        audit_entry = {
            "decision_id": decision.decision_id,
            "transaction_id": decision.transaction_id,
            "payload_json": canonical_json,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
            "hmac_signature": hmac_sig,
            "timestamp": time.time(),
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_ledger 
                (decision_id, transaction_id, payload_json, previous_hash, current_hash, hmac_signature, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_entry["decision_id"],
                    audit_entry["transaction_id"],
                    audit_entry["payload_json"],
                    audit_entry["previous_hash"],
                    audit_entry["current_hash"],
                    audit_entry["hmac_signature"],
                    audit_entry["timestamp"],
                ),
            )
            conn.commit()

        return audit_entry

    def verify_ledger_integrity(self) -> tuple[bool, int]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT sequence_id, payload_json, previous_hash, current_hash, hmac_signature FROM audit_ledger ORDER BY sequence_id ASC"
                )
                rows = cursor.fetchall()

            expected_prev_hash = "0" * 64
            verified_count = 0

            for seq_id, payload_json, prev_hash, curr_hash, hmac_sig in rows:
                if prev_hash != expected_prev_hash:
                    logger.error(
                        f"Audit chain broken at seq {seq_id}: prev_hash mismatch"
                    )
                    return False, verified_count

                parsed_payload = json.loads(payload_json)
                canonical_json = json.dumps(parsed_payload, sort_keys=True)
                payload_bytes = canonical_json.encode("utf-8")

                chain_input = payload_bytes + prev_hash.encode("utf-8")
                calc_hash = hashlib.sha256(chain_input).hexdigest()

                if calc_hash != curr_hash:
                    logger.error(
                        f"Audit chain broken at seq {seq_id}: hash tamper detected"
                    )
                    return False, verified_count

                calc_hmac = hmac.new(
                    self.secret_key, curr_hash.encode("utf-8"), hashlib.sha256
                ).hexdigest()
                if calc_hmac != hmac_sig:
                    logger.error(
                        f"Audit chain broken at seq {seq_id}: HMAC signature invalid"
                    )
                    return False, verified_count

                expected_prev_hash = curr_hash
                verified_count += 1

            return True, verified_count
        except Exception as exc:
            logger.error(
                "Ledger verification error", extra={"payload": {"error": str(exc)}}
            )
            return False, 0


class PostgreSQLAuditRepository(AuditRepository):
    """Production PostgreSQL Audit Ledger."""

    def __init__(self, dsn: str | None = None, strict_mode: bool | None = None):
        self.dsn = dsn or settings.postgres_dsn
        self.strict_mode = (
            strict_mode
            if strict_mode is not None
            else (settings.environment in ("production", "staging"))
        )
        self.secret_key = settings.audit_hmac_secret.encode("utf-8")
        self.pg_conn = None
        self.sqlite_fallback = SQLiteAuditRepository()

        # Attempt PostgreSQL connection
        try:
            import psycopg2

            self.pg_conn = psycopg2.connect(self.dsn, connect_timeout=3)
            self._init_pg_schema()
        except Exception as exc:
            if self.strict_mode:
                raise RuntimeError(
                    f"PRODUCTION POSTGRESQL UNREACHABLE ({self.dsn}): {exc}"
                ) from exc
            self.pg_conn = None

    def _init_pg_schema(self) -> None:
        if not self.pg_conn:
            return
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    sequence_id SERIAL PRIMARY KEY,
                    decision_id VARCHAR(64) UNIQUE NOT NULL,
                    transaction_id VARCHAR(64) NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash VARCHAR(64) NOT NULL,
                    current_hash VARCHAR(64) NOT NULL,
                    hmac_signature VARCHAR(64) NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL
                );
                """
            )
            self.pg_conn.commit()

    def get_storage_mode(self) -> str:
        return "postgresql-production"

    def get_latest_hash(self) -> str:
        if not self.pg_conn:
            if self.strict_mode:
                raise RuntimeError("PRODUCTION POSTGRESQL STORE UNREACHABLE")
            return self.sqlite_fallback.get_latest_hash()

        genesis_hash = "0" * 64
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                "SELECT current_hash FROM audit_ledger ORDER BY sequence_id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return row[0]
        return genesis_hash

    def append_decision_audit(self, decision: RiskDecision) -> dict[str, Any]:
        if not self.pg_conn:
            if self.strict_mode:
                raise RuntimeError("PRODUCTION POSTGRESQL STORE UNREACHABLE")
            return self.sqlite_fallback.append_decision_audit(decision)

        prev_hash = self.get_latest_hash()
        payload = decision.to_dict()
        canonical_json = json.dumps(payload, sort_keys=True)
        payload_bytes = canonical_json.encode("utf-8")

        chain_input = payload_bytes + prev_hash.encode("utf-8")
        curr_hash = hashlib.sha256(chain_input).hexdigest()

        hmac_sig = hmac.new(
            self.secret_key, curr_hash.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        audit_entry = {
            "decision_id": decision.decision_id,
            "transaction_id": decision.transaction_id,
            "payload_json": canonical_json,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
            "hmac_signature": hmac_sig,
            "timestamp": time.time(),
        }

        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_ledger 
                (decision_id, transaction_id, payload_json, previous_hash, current_hash, hmac_signature, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    audit_entry["decision_id"],
                    audit_entry["transaction_id"],
                    audit_entry["payload_json"],
                    audit_entry["previous_hash"],
                    audit_entry["current_hash"],
                    audit_entry["hmac_signature"],
                    audit_entry["timestamp"],
                ),
            )
            self.pg_conn.commit()

        return audit_entry

    def verify_ledger_integrity(self) -> tuple[bool, int]:
        if not self.pg_conn:
            if self.strict_mode:
                raise RuntimeError("PRODUCTION POSTGRESQL STORE UNREACHABLE")
            return self.sqlite_fallback.verify_ledger_integrity()

        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                "SELECT sequence_id, payload_json, previous_hash, current_hash, hmac_signature FROM audit_ledger ORDER BY sequence_id ASC"
            )
            rows = cursor.fetchall()

        expected_prev_hash = "0" * 64
        verified_count = 0

        for seq_id, payload_json, prev_hash, curr_hash, hmac_sig in rows:
            if prev_hash != expected_prev_hash:
                return False, verified_count

            parsed_payload = json.loads(payload_json)
            canonical_json = json.dumps(parsed_payload, sort_keys=True)
            payload_bytes = canonical_json.encode("utf-8")

            chain_input = payload_bytes + prev_hash.encode("utf-8")
            calc_hash = hashlib.sha256(chain_input).hexdigest()

            if calc_hash != curr_hash:
                return False, verified_count

            calc_hmac = hmac.new(
                self.secret_key, curr_hash.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            if calc_hmac != hmac_sig:
                return False, verified_count

            expected_prev_hash = curr_hash
            verified_count += 1

        return True, verified_count


# ============================================================================
# DOMAIN REPOSITORIES (TRANSACTIONS, INCIDENTS, ACTIONS, TIMELINE)
# ============================================================================


class SQLiteTransactionRepository:
    """Persistent SQLite repository for Transaction Events and Risk Decisions."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_sqlite(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transaction_records (
                        transaction_id TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL,
                        customer_id TEXT NOT NULL,
                        account_id TEXT,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL,
                        device_id TEXT,
                        ip_address TEXT,
                        risk_score INTEGER NOT NULL,
                        severity TEXT NOT NULL,
                        action TEXT NOT NULL,
                        decision_json TEXT NOT NULL,
                        event_json TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tx_created ON transaction_records(created_at DESC)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tx_cust ON transaction_records(customer_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tx_risk ON transaction_records(risk_score DESC)"
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to initialize transaction_records table: {exc}")

    def save_transaction(
        self, event_dict: dict[str, Any], decision_dict: dict[str, Any]
    ) -> None:
        tx_id = event_dict.get("transaction_id") or decision_dict.get("transaction_id")
        now = time.time()
        raw_ts = event_dict.get("timestamp") or decision_dict.get("created_at")
        if raw_ts and float(raw_ts) > (now - 30 * 86400):
            created_at = float(raw_ts)
        else:
            created_at = now

        amt = float(event_dict.get("amount") or decision_dict.get("amount", 0.0))
        risk_score = int(decision_dict.get("risk_score") or 0)
        sev = (
            decision_dict.get("severity")
            or decision_dict.get("risk_level")
            or (
                "CRITICAL"
                if risk_score >= 85
                else ("HIGH" if risk_score >= 60 else "LOW")
            )
        )
        action = (
            decision_dict.get("final_action")
            or decision_dict.get("decision")
            or (
                "BLOCK"
                if risk_score >= 85
                else ("HOLD" if risk_score >= 60 else "ALLOW")
            )
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO transaction_records (
                    transaction_id, event_id, customer_id, account_id, amount, currency,
                    device_id, ip_address, risk_score, severity, action, decision_json, event_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx_id,
                    event_dict.get("event_id", ""),
                    event_dict.get("customer_id", "")
                    or decision_dict.get("customer_id", ""),
                    event_dict.get("account_id", ""),
                    amt,
                    event_dict.get("currency", "INR"),
                    event_dict.get("device_id", ""),
                    event_dict.get("ip_address", ""),
                    risk_score,
                    sev,
                    action,
                    json.dumps(decision_dict),
                    json.dumps(event_dict),
                    created_at,
                ),
            )
            conn.commit()

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT decision_json FROM transaction_records ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows]

    def query_transactions(
        self,
        page: int = 1,
        limit: int = 20,
        search: str = "",
        min_risk: int = 0,
        severity: str | None = None,
        action: str | None = None,
        window: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict[str, Any]:
        conditions = ["1=1"]
        params: list[Any] = []

        if min_risk > 0:
            conditions.append("risk_score >= ?")
            params.append(min_risk)

        if severity and severity.upper() != "ALL":
            conditions.append("severity = ?")
            params.append(severity.upper())

        if action and action.upper() != "ALL":
            conditions.append("action = ?")
            params.append(action.upper())

        if search:
            s_term = f"%{search.strip()}%"
            conditions.append(
                "(transaction_id LIKE ? OR customer_id LIKE ? OR device_id LIKE ? OR ip_address LIKE ?)"
            )
            params.extend([s_term, s_term, s_term, s_term])

        now = time.time()
        window_seconds = {
            "15m": 900,
            "1h": 3600,
            "24h": 86400,
            "7d": 604800,
        }.get(window or "", None)

        if window_seconds:
            conditions.append("created_at >= ?")
            params.append(now - window_seconds)

        where_clause = " WHERE " + " AND ".join(conditions)

        # Count
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT COUNT(*) FROM transaction_records{where_clause}", params
            )
            total = cursor.fetchone()[0]

            valid_sort_cols = {
                "created_at": "created_at",
                "risk_score": "risk_score",
                "amount": "amount",
            }
            sort_col = valid_sort_cols.get(sort_by, "created_at")
            direction = "ASC" if sort_order.lower() == "asc" else "DESC"

            offset = (page - 1) * limit
            query_sql = f"SELECT decision_json FROM transaction_records{where_clause} ORDER BY {sort_col} {direction} LIMIT ? OFFSET ?"
            cursor.execute(query_sql, params + [limit, offset])
            rows = cursor.fetchall()

            items = [json.loads(row[0]) for row in rows]
            pages = max(1, (total + limit - 1) // limit)

            return {
                "items": items,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": pages,
            }

    def get_analytics_summary(self, window: str = "24h") -> dict[str, Any]:
        now = time.time()
        window_seconds = {
            "15m": 900,
            "1h": 3600,
            "24h": 86400,
            "7d": 604800,
        }.get(window, 86400)

        t_start = now - window_seconds
        t_prev_start = t_start - window_seconds

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Current Window Stats
            cursor.execute(
                """
                SELECT 
                    COUNT(*),
                    SUM(CASE WHEN risk_score >= 60 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN risk_score >= 85 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN risk_score >= 60 THEN amount ELSE 0 END)
                FROM transaction_records WHERE created_at >= ?
                """,
                (t_start,),
            )
            row_curr = cursor.fetchone()
            total_txs = row_curr[0] or 0
            high_risk = row_curr[1] or 0
            critical_risk = row_curr[2] or 0
            protected_exposure = float(row_curr[3] or 0.0)

            # Actions Breakdown
            cursor.execute(
                "SELECT action, COUNT(*) FROM transaction_records WHERE created_at >= ? GROUP BY action",
                (t_start,),
            )
            act_rows = cursor.fetchall()
            actions_breakdown = {
                "ALLOW": 0,
                "MONITOR": 0,
                "STEP_UP": 0,
                "HOLD": 0,
                "BLOCK": 0,
            }
            for a_name, a_count in act_rows:
                if a_name in actions_breakdown:
                    actions_breakdown[a_name] = a_count

            # If zero transactions in the selected window, fallback to all available transaction records
            if total_txs == 0:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*),
                        SUM(CASE WHEN risk_score >= 60 THEN 1 ELSE 0 END),
                        SUM(CASE WHEN risk_score >= 85 THEN 1 ELSE 0 END),
                        SUM(CASE WHEN risk_score >= 60 THEN amount ELSE 0 END)
                    FROM transaction_records
                    """
                )
                row_all = cursor.fetchone()
                if row_all and (row_all[0] or 0) > 0:
                    total_txs = row_all[0] or 0
                    high_risk = row_all[1] or 0
                    critical_risk = row_all[2] or 0
                    protected_exposure = float(row_all[3] or 0.0)

                    cursor.execute(
                        "SELECT action, COUNT(*) FROM transaction_records GROUP BY action"
                    )
                    for a_name, a_count in cursor.fetchall():
                        if a_name in actions_breakdown:
                            actions_breakdown[a_name] = a_count

            # Rolling 60s TPS
            cursor.execute(
                "SELECT COUNT(*) FROM transaction_records WHERE created_at >= ?",
                (now - 60.0,),
            )
            tps_count = cursor.fetchone()[0] or 0
            tps_60s = round(tps_count / 60.0, 2)

            # Previous Window Stats
            cursor.execute(
                """
                SELECT 
                    COUNT(*),
                    SUM(CASE WHEN risk_score >= 60 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN risk_score >= 60 THEN amount ELSE 0 END)
                FROM transaction_records WHERE created_at >= ? AND created_at < ?
                """,
                (t_prev_start, t_start),
            )
            row_prev = cursor.fetchone()
            prev_total_txs = row_prev[0] or 0
            prev_high_risk = row_prev[1] or 0
            prev_protected_exposure = float(row_prev[2] or 0.0)

            return {
                "window": window,
                "start_timestamp": t_start,
                "end_timestamp": now,
                "total_transactions": total_txs,
                "total_risk_decisions": total_txs,
                "high_risk_count": high_risk,
                "critical_risk_count": critical_risk,
                "protected_exposure_inr": protected_exposure,
                "actions_breakdown": actions_breakdown,
                "tps_rolling_60s": tps_60s,
                "previous_window": {
                    "total_transactions": prev_total_txs,
                    "high_risk_count": prev_high_risk,
                    "protected_exposure_inr": prev_protected_exposure,
                },
            }


class SQLiteIncidentRepository:
    """Persistent SQLite repository for Active & Historical Incidents."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_sqlite(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS incidents (
                        incident_id TEXT PRIMARY KEY,
                        investigation_id TEXT UNIQUE NOT NULL,
                        status TEXT NOT NULL,
                        owner TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        risk_score INTEGER NOT NULL,
                        confidence REAL NOT NULL,
                        protected_exposure_inr REAL NOT NULL,
                        payload_json TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_inc_status ON incidents(status)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_inc_updated ON incidents(updated_at DESC)"
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to initialize incidents table: {exc}")

    def save_incident(self, incident_dict: dict[str, Any]) -> None:
        inc_id = (
            incident_dict.get("incident_id") or f"INC-{uuid.uuid4().hex[:6].upper()}"
        )
        inv_id = incident_dict.get("investigation_id") or inc_id
        now = time.time()
        created_at = incident_dict.get("created_at") or now
        updated_at = incident_dict.get("updated_at") or now

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO incidents (
                    incident_id, investigation_id, status, owner, priority, severity,
                    risk_score, confidence, protected_exposure_inr, payload_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inc_id,
                    inv_id,
                    incident_dict.get("status", "NEW"),
                    incident_dict.get("owner", "Unassigned (Risk Queue)"),
                    incident_dict.get("priority", "HIGH"),
                    incident_dict.get("severity", "HIGH"),
                    int(incident_dict.get("risk_score", 0)),
                    float(incident_dict.get("confidence", 0.9)),
                    float(incident_dict.get("protected_exposure_inr", 0.0)),
                    json.dumps(incident_dict),
                    created_at,
                    updated_at,
                ),
            )
            conn.commit()

    def get_active(self) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload_json FROM incidents WHERE status NOT IN ('RESOLVED', 'FALSE_POSITIVE') ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows]

    def get_by_id(self, incident_or_inv_id: str) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT payload_json FROM incidents WHERE incident_id = ? OR investigation_id = ?",
                (incident_or_inv_id, incident_or_inv_id),
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def update_incident(
        self, incident_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        existing = self.get_by_id(incident_id)
        if not existing:
            return None

        existing.update(updates)
        existing["updated_at"] = time.time()
        self.save_incident(existing)
        return existing


class SQLiteActionExecutionRepository:
    """Persistent SQLite repository for Action Gateway Executions & Live Safety Telemetry."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_sqlite(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS action_executions (
                        execution_id TEXT PRIMARY KEY,
                        action_token_id TEXT NOT NULL,
                        granted_action TEXT NOT NULL,
                        principal_id TEXT NOT NULL,
                        execution_status TEXT NOT NULL,
                        observed_outcome TEXT NOT NULL,
                        verification_status TEXT NOT NULL,
                        is_unsafe_violation INTEGER NOT NULL DEFAULT 0,
                        is_rejected INTEGER NOT NULL DEFAULT 0,
                        is_policy_violation INTEGER NOT NULL DEFAULT 0,
                        is_fail_closed INTEGER NOT NULL DEFAULT 0,
                        payload_json TEXT NOT NULL,
                        executed_at REAL NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to initialize action_executions table: {exc}")

    def record_execution(
        self,
        execution_dict: dict[str, Any],
        is_unsafe_violation: bool = False,
        is_rejected: bool = False,
        is_policy_violation: bool = False,
        is_fail_closed: bool = False,
    ) -> None:
        exec_id = (
            execution_dict.get("execution_id") or f"EXEC-{uuid.uuid4().hex[:6].upper()}"
        )
        now = time.time()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO action_executions (
                    execution_id, action_token_id, granted_action, principal_id, execution_status,
                    observed_outcome, verification_status, is_unsafe_violation, is_rejected,
                    is_policy_violation, is_fail_closed, payload_json, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exec_id,
                    execution_dict.get("action_token_id", ""),
                    execution_dict.get("granted_action", "STEP_UP"),
                    execution_dict.get("principal_id", ""),
                    execution_dict.get("execution_status", "EXECUTED"),
                    execution_dict.get("observed_outcome", ""),
                    execution_dict.get("verification_status", "PASS"),
                    1 if is_unsafe_violation else 0,
                    1 if is_rejected else 0,
                    1 if is_policy_violation else 0,
                    1 if is_fail_closed else 0,
                    json.dumps(execution_dict),
                    now,
                ),
            )
            conn.commit()

    def get_telemetry(self) -> dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    COUNT(*),
                    SUM(is_unsafe_violation),
                    SUM(is_rejected),
                    SUM(is_policy_violation),
                    SUM(is_fail_closed),
                    MAX(executed_at)
                FROM action_executions
                """
            )
            row = cursor.fetchone()
            total = row[0] or 0
            unsafe = row[1] or 0
            rejected = row[2] or 0
            policy_viols = row[3] or 0
            fail_closed = row[4] or 0
            last_ts = row[5]

            return {
                "live_unsafe_executions": unsafe,
                "rejected_executions": rejected,
                "policy_violations": policy_viols,
                "fail_closed_events": fail_closed,
                "total_executions": total,
                "successful_executions": max(0, total - rejected - fail_closed),
                "last_execution_timestamp": last_ts,
                "gateway_status": "ACTIVE_FAIL_CLOSED",
                "timestamp": time.time(),
            }


class SQLiteTimelineRepository:
    """Persistent SQLite repository for Investigation Timelines."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self._init_sqlite()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _init_sqlite(self) -> None:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS timeline_events (
                        event_id TEXT PRIMARY KEY,
                        investigation_id TEXT NOT NULL,
                        stage TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        actor TEXT NOT NULL,
                        details_json TEXT,
                        timestamp REAL NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_tl_inv ON timeline_events(investigation_id, timestamp ASC)"
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"Failed to initialize timeline_events table: {exc}")

    def add_event(
        self,
        investigation_id: str,
        stage: str,
        summary: str,
        actor: str = "SYSTEM",
        details: dict[str, Any] | None = None,
    ) -> None:
        evt_id = f"TL-{uuid.uuid4().hex[:8].upper()}"
        now = time.time()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO timeline_events (event_id, investigation_id, stage, summary, actor, details_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evt_id,
                    investigation_id,
                    stage,
                    summary,
                    actor,
                    json.dumps(details or {}),
                    now,
                ),
            )
            conn.commit()

    def get_timeline(self, investigation_id: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT event_id, investigation_id, stage, summary, actor, details_json, timestamp FROM timeline_events WHERE investigation_id = ? ORDER BY timestamp ASC",
                (investigation_id,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "event_id": row[0],
                    "investigation_id": row[1],
                    "stage": row[2],
                    "summary": row[3],
                    "actor": row[4],
                    "details": json.loads(row[5]) if row[5] else {},
                    "timestamp": row[6],
                }
                for row in rows
            ]
