"""
RazorShield AI — Unit Tests: Cryptographic Audit Store
"""

import time
import uuid

from backend.app.domain.models import RiskDecision
from backend.app.infrastructure.storage_contracts import SQLiteAuditRepository


def test_audit_hash_chaining_and_verification(test_db_dir):
    db_file = str(test_db_dir / f"audit_unit_{uuid.uuid4().hex}.db")
    store = SQLiteAuditRepository(db_path=db_file)

    d1 = RiskDecision(
        decision_id="dec_a_001",
        transaction_id="tx_a_001",
        risk_score=15,
        risk_level="LOW",
        decision="ALLOW",
        confidence=0.95,
        components={},
        reason_codes=[],
        contributing_signals=[],
        degraded_mode="NORMAL",
        latency_ms=1.2,
        created_at=time.time(),
        request_id="req_001",
        correlation_id="corr_001",
    )
    d1_ret = store.append_decision_audit(d1)
    assert len(d1_ret["current_hash"]) == 64

    d2 = RiskDecision(
        decision_id="dec_a_002",
        transaction_id="tx_a_002",
        risk_score=85,
        risk_level="HIGH",
        decision="BLOCK",
        confidence=0.98,
        components={},
        reason_codes=["HETEROGENEOUS_RING_CLUSTER"],
        contributing_signals=[],
        degraded_mode="NORMAL",
        latency_ms=2.1,
        created_at=time.time(),
        request_id="req_002",
        correlation_id="corr_002",
    )
    d2_ret = store.append_decision_audit(d2)
    assert len(d2_ret["current_hash"]) == 64
    assert d1_ret["current_hash"] != d2_ret["current_hash"]

    is_valid, count = store.verify_ledger_integrity()
    assert is_valid is True
    assert count == 2
