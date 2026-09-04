"""
RazorShield AI — Unit Tests: Atomic Idempotency Claim Primitive & Concurrency
"""

import uuid

from backend.app.infrastructure.storage_contracts import SQLiteIdempotencyStore


def test_atomic_idempotency_claim(test_db_dir):
    db_file = str(test_db_dir / f"idemp_atomic_{uuid.uuid4().hex}.db")
    store = SQLiteIdempotencyStore(db_path=db_file)

    event_id = "evt_conc_001"
    idemp_key = "key_conc_001"

    # First claim -> CLAIMED
    status1, payload1 = store.claim(event_id, idemp_key)
    assert status1 == "CLAIMED"
    assert payload1 is None

    # Second claim while processing -> IN_PROGRESS
    status2, payload2 = store.claim(event_id, idemp_key)
    assert status2 == "IN_PROGRESS"
    assert payload2 is None

    # Save final decision
    store.save_result(event_id, idemp_key, {"final": "ALLOW"})

    # Third claim after completion -> ALREADY_EXISTS with cached payload
    status3, payload3 = store.claim(event_id, idemp_key)
    assert status3 == "ALREADY_EXISTS"
    assert payload3 == {"final": "ALLOW"}
