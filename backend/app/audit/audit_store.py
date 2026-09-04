"""
RazorShield AI — Immutable Audit Trail Store
Append-only audit ledger with HMAC signatures and SHA256 cryptographic hash-chaining.
Formula: hash_n = SHA256(canonical_event_json_bytes_n + hash_{n-1})
"""

import hashlib
import hmac
import json
import sqlite3
import time
from typing import Any

from backend.app.config import settings
from backend.app.domain.models import RiskDecision
from backend.app.logging_config import get_logger

logger = get_logger("razorshield.audit")


class AuditStore:
    """Immutable audit store enforcing cryptographic hash chaining and HMAC signatures."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.sqlite_db_path
        self.secret_key = settings.audit_hmac_secret.encode("utf-8")
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
        """Fetch current chain tip hash (hash_{n-1}). Returns genesis hash if empty."""
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
        """Append risk decision record to ledger with SHA256 hash chaining and HMAC signature."""
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

        try:
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
            logger.info(
                "Audit entry chained successfully",
                extra={"transaction_id": decision.transaction_id},
            )
        except Exception as exc:
            logger.error(
                "Audit store append error", extra={"payload": {"error": str(exc)}}
            )

        return audit_entry

    def append_event(
        self, decision_id: str, transaction_id: str, payload_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Appends arbitrary event payload to audit ledger."""
        prev_hash = self.get_latest_hash()
        canonical_json = json.dumps(payload_dict, sort_keys=True)
        payload_bytes = canonical_json.encode("utf-8")

        chain_input = payload_bytes + prev_hash.encode("utf-8")
        curr_hash = hashlib.sha256(chain_input).hexdigest()

        hmac_sig = hmac.new(
            self.secret_key, curr_hash.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        audit_entry = {
            "decision_id": decision_id,
            "transaction_id": transaction_id,
            "payload_json": canonical_json,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
            "hmac_signature": hmac_sig,
            "timestamp": time.time(),
        }

        try:
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
        except Exception as exc:
            logger.error(
                "Audit store append error", extra={"payload": {"error": str(exc)}}
            )

        return audit_entry

    def verify_ledger_integrity(self) -> tuple[bool, int]:
        """Verifies full cryptographic chain integrity from genesis to tip."""
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


CryptographicAuditStore = AuditStore
