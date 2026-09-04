"""
RazorShield AI — Failure Tests: Resilience & Degraded Modes
"""

import uuid

from backend.app.risk_service import RiskPipelineService


def test_degraded_mode_ml_unavailable(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"fail_ml_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    decision = service.process_transaction_event(
        raw_payload=valid_transaction_payload,
        ml_available=False,
        graph_available=True,
    )

    assert decision.degraded_mode == "DEGRADED_NO_ML"
    assert decision.components["ml"]["weight"] == 0.0
    assert decision.components["signal"]["weight"] == 0.60
    assert decision.components["graph"]["weight"] == 0.40


def test_degraded_mode_rules_only(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"fail_both_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    decision = service.process_transaction_event(
        raw_payload=valid_transaction_payload,
        ml_available=False,
        graph_available=False,
    )

    assert decision.degraded_mode == "DEGRADED_RULES_ONLY"
    assert decision.components["signal"]["weight"] == 1.00
    assert decision.components["ml"]["weight"] == 0.00
    assert decision.components["graph"]["weight"] == 0.00
