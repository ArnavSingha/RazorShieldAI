"""
RazorShield AI — Unit Tests: Ingestion Idempotency Gateway
"""

import uuid

from backend.app.ingestion.idempotency import IdempotencyGateway


def test_idempotency_save_and_retrieve(test_db_dir):
    db_file = str(test_db_dir / f"idemp_unit_{uuid.uuid4().hex}.db")
    gateway = IdempotencyGateway(db_path=db_file)

    event_id = "evt_idemp_100"
    idemp_key = "key_idemp_100"
    resp_payload = {"status": "SUCCESS", "decision": "ALLOW"}

    # First attempt: not found
    existing = gateway.get_cached_response(event_id, idemp_key)
    assert existing is None

    # Save decision
    gateway.save_decision_response(event_id, idemp_key, resp_payload)

    # Second attempt: cached response returned
    cached = gateway.get_cached_response(event_id, idemp_key)
    assert cached is not None
    assert cached["status"] == "SUCCESS"
    assert cached["decision"] == "ALLOW"
