"""
RazorShield AI — Unit Tests: Graph Engine
Verifies heterogeneous cluster detection, device sharing, multi-account IP ring detection,
and normalized graph risk score calculation.
"""

from backend.app.ingestion.validator import EventValidator
from backend.app.risk.graph_engine import GraphEngine


def test_graph_isolated_transaction(valid_transaction_payload):
    engine = GraphEngine()
    event = EventValidator.validate_dict(valid_transaction_payload)

    result = engine.evaluate_graph(event)
    assert result.cluster_size >= 1
    assert result.normalized_score < 0.30


def test_graph_multi_account_device_sharing(valid_transaction_payload):
    engine = GraphEngine()

    # Link same device 'dev_shared_99' across 6 different customer accounts
    for i in range(6):
        payload = dict(valid_transaction_payload)
        payload["event_id"] = f"evt_graph_{i}"
        payload["transaction_id"] = f"tx_graph_{i}"
        payload["customer_id"] = f"cust_fraud_ring_{i}"
        payload["account_id"] = f"acc_fraud_ring_{i}"
        payload["device_id"] = "dev_shared_99"

        event = EventValidator.validate_dict(payload)
        result = engine.evaluate_graph(event)

    # 6th transaction must flag multi-account device cluster score >= 0.90
    assert len(result.related_accounts) >= 6
    assert result.normalized_score >= 0.90
    assert "DEVICE_ACCOUNT_REUSE" in result.reason_codes
