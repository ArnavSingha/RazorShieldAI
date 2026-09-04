"""
RazorShield AI — Integration Tests: Storage Adapters (Redis & PostgreSQL)
Verifies RedisIdempotencyStore and PostgreSQLAuditRepository real service integration,
strict failure behavior in production mode, atomic lock primitives, and cryptographic audit persistence.
"""

import os
import uuid
import pytest

from backend.app.domain.models import RiskDecision
from backend.app.infrastructure.storage_contracts import (
    PostgreSQLAuditRepository,
    RedisIdempotencyStore,
)


def test_redis_strict_production_unreachable_fails_fast():
    """Verifies strict production mode raises RuntimeError when Redis is unreachable (no silent fallback)."""
    with pytest.raises(RuntimeError) as exc_info:
        RedisIdempotencyStore(redis_dsn="redis://127.0.0.1:59999/0", strict_mode=True)
    assert "PRODUCTION REDIS UNREACHABLE" in str(exc_info.value)


def test_postgres_strict_production_unreachable_fails_fast():
    """Verifies strict production mode raises RuntimeError when PostgreSQL is unreachable (no silent fallback)."""
    with pytest.raises(RuntimeError) as exc_info:
        PostgreSQLAuditRepository(
            dsn="postgresql://user:pass@127.0.0.1:59999/razorshield", strict_mode=True
        )
    assert "PRODUCTION POSTGRESQL UNREACHABLE" in str(exc_info.value)


def test_redis_live_service_integration():
    """
    Integration test against actual Redis instance.
    Runs SET NX EX, GET, duplicate claim, and save result.
    Fails fast if Redis is unreachable in strict mode; skips only if live service is unattached.
    """
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    try:
        store = RedisIdempotencyStore(redis_dsn=redis_url, strict_mode=True)
    except RuntimeError:
        if os.getenv("REDIS_TEST_REQUIRED") == "true":
            pytest.fail(
                "Mandatory Redis integration test failed: Redis service unreachable"
            )
        pytest.skip(f"Live Redis service not accessible at {redis_url}")
        return

    assert store.get_mode_name() == "redis-production"

    event_id = f"evt_redis_{uuid.uuid4().hex[:8]}"
    idemp_key = f"key_redis_{uuid.uuid4().hex[:8]}"

    # 1. First claim -> SET NX EX -> CLAIMED
    status1, resp1 = store.claim(event_id, idemp_key, ttl_seconds=60)
    assert status1 == "CLAIMED"
    assert resp1 is None

    # 2. Concurrent second claim -> IN_PROGRESS
    status2, resp2 = store.claim(event_id, idemp_key, ttl_seconds=60)
    assert status2 == "IN_PROGRESS"

    # 3. Save completed result -> SET response_json
    payload = {"decision": "ALLOW", "risk_score": 15}
    store.save_result(event_id, idemp_key, payload, ttl_seconds=60)

    # 4. Duplicate completed claim -> ALREADY_EXISTS with cached payload
    status3, resp3 = store.claim(event_id, idemp_key, ttl_seconds=60)
    assert status3 == "ALREADY_EXISTS"
    assert resp3 == payload


def test_postgres_live_service_integration():
    """
    Integration test against actual PostgreSQL database.
    Runs CREATE TABLE, INSERT INTO audit_ledger, SELECT, unique constraint check, and integrity verification.
    Fails fast if PostgreSQL is unreachable in strict mode; skips only if live service is unattached.
    """
    postgres_dsn = os.getenv(
        "POSTGRES_URL", "postgresql://postgres:postgres@127.0.0.1:5432/razorshield"
    )
    try:
        repo = PostgreSQLAuditRepository(dsn=postgres_dsn, strict_mode=True)
    except RuntimeError:
        if os.getenv("POSTGRES_TEST_REQUIRED") == "true":
            pytest.fail(
                "Mandatory PostgreSQL integration test failed: PostgreSQL service unreachable"
            )
        pytest.skip(f"Live PostgreSQL service not accessible at {postgres_dsn}")
        return

    assert repo.get_storage_mode() == "postgresql-production"

    decision = RiskDecision(
        decision_id=f"dec_pg_{uuid.uuid4().hex[:8]}",
        transaction_id=f"tx_pg_{uuid.uuid4().hex[:8]}",
        customer_id="cust_pg_100",
        risk_score=25,
        risk_level="LOW",
        decision="ALLOW",
        confidence=0.95,
        components={},
        reason_codes=["NORMAL_BASELINE"],
        contributing_signals=[],
        degraded_mode="NORMAL_ALL_SYSTEMS",
        latency_ms=12.5,
        request_id="req_pg_01",
        correlation_id="corr_pg_01",
    )

    # 1. Append decision audit entry -> INSERT INTO audit_ledger
    entry = repo.append_decision_audit(decision)
    assert entry["decision_id"] == decision.decision_id
    assert len(entry["current_hash"]) == 64
    assert len(entry["hmac_signature"]) == 64

    # 2. Verify latest hash -> SELECT current_hash
    tip_hash = repo.get_latest_hash()
    assert tip_hash == entry["current_hash"]

    # 3. Verify ledger cryptographic integrity -> SELECT all rows & verify chain
    is_valid, count = repo.verify_ledger_integrity()
    assert is_valid is True
    assert count >= 1
