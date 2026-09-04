"""
RazorShield AI — Unit Tests: Cryptographic Audit Tamper Detection & Fail-Closed Behavior
"""

import sqlite3
import time
import uuid

from backend.app.domain.models import RiskDecision
from backend.app.exceptions import AuditPersistenceError
from backend.app.infrastructure.storage_contracts import SQLiteAuditRepository
from backend.app.risk_service import RiskPipelineService
from backend.tests.pytest_compat import pytest


def test_audit_tamper_detection(test_db_dir):
    db_file = str(test_db_dir / f"audit_tamper_{uuid.uuid4().hex}.db")
    repo = SQLiteAuditRepository(db_path=db_file)

    d1 = RiskDecision(
        decision_id="dec_t_001",
        transaction_id="tx_t_001",
        risk_score=10,
        risk_level="LOW",
        decision="ALLOW",
        confidence=0.95,
        components={},
        reason_codes=[],
        contributing_signals=[],
        degraded_mode="NORMAL",
        latency_ms=1.1,
        created_at=time.time(),
        request_id="req_t_001",
        correlation_id="corr_t_001",
    )
    repo.append_decision_audit(d1)

    # Initial ledger must verify cleanly
    valid, count = repo.verify_ledger_integrity()
    assert valid is True
    assert count == 1

    # Directly tamper with SQLite audit_ledger database table row
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE audit_ledger SET payload_json = 'TAMPERED' WHERE sequence_id = 1"
    )
    conn.commit()
    conn.close()

    # Tampered ledger MUST fail integrity verification
    valid_after, _ = repo.verify_ledger_integrity()
    assert valid_after is False


def test_fail_closed_audit_append_failure(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"audit_failclose_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    # Force SQLite table corruption so append_decision_audit fails
    conn = sqlite3.connect(db_file)
    conn.execute("DROP TABLE audit_ledger")
    conn.commit()
    conn.close()

    # Risk processing MUST catch SQLite error and raise AuditPersistenceError (Fail Closed)
    with pytest.raises(AuditPersistenceError):
        service.process_transaction_event(valid_transaction_payload)
