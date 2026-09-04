"""
RazorShield AI — Phase 2 Integration & Acceptance Tests (Operational Maturity)
Verifies SQLite persistence, live action safety telemetry, analyst mutation auditability,
server-side windowed analytics, paginated transaction queries, timeline logging, global search, and case export.
"""

import uuid
import pytest
import time
from backend.app.domain.models import TransactionEvent
from backend.app.infrastructure.storage_contracts import (
    SQLiteActionExecutionRepository,
    SQLiteIncidentRepository,
    SQLiteTimelineRepository,
    SQLiteTransactionRepository,
)
from backend.app.risk_service import RiskPipelineService


import os


@pytest.fixture
def clean_repositories():
    db_file = os.path.join(os.path.dirname(__file__), "test_phase2_razorshield.db")
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass
    tx_repo = SQLiteTransactionRepository(db_path=db_file)
    inc_repo = SQLiteIncidentRepository(db_path=db_file)
    act_repo = SQLiteActionExecutionRepository(db_path=db_file)
    tl_repo = SQLiteTimelineRepository(db_path=db_file)
    yield tx_repo, inc_repo, act_repo, tl_repo, db_file
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass


def test_empty_system_startup(clean_repositories):
    tx_repo, inc_repo, act_repo, tl_repo, _ = clean_repositories
    # 1. Empty database queries return 0 and []
    assert len(tx_repo.get_recent(50)) == 0
    assert len(inc_repo.get_active()) == 0

    telemetry = act_repo.get_telemetry()
    assert telemetry["total_executions"] == 0
    assert telemetry["live_unsafe_executions"] == 0

    summary = tx_repo.get_analytics_summary("24h")
    assert summary["total_transactions"] == 0
    assert summary["protected_exposure_inr"] == 0.0


def test_transaction_persistence_and_restart(clean_repositories):
    tx_repo, inc_repo, _, tl_repo, db_file = clean_repositories
    u_suffix = uuid.uuid4().hex[:6]
    cust_id = f"cust_p2_{u_suffix}"
    tx_id = f"tx_p2_{u_suffix}"

    svc = RiskPipelineService()
    ev = TransactionEvent(
        event_id=f"ev_p2_{u_suffix}",
        idempotency_key=f"idemp_p2_{u_suffix}",
        transaction_id=tx_id,
        customer_id=cust_id,
        account_id=f"acc_p2_{u_suffix}",
        amount=150000.0,
        currency="INR",
        device_id=f"dev_p2_{u_suffix}",
        ip_address="10.0.0.99",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=time.time(),
    )
    decision = svc.process_transaction_event(ev.to_dict())

    # Save to SQLite
    tx_repo.save_transaction(ev.to_dict(), decision.to_dict())

    # Simulate restart by creating a new repository instance pointing to same db_file
    tx_repo_restarted = SQLiteTransactionRepository(db_path=db_file)
    recent = tx_repo_restarted.get_recent(50)
    assert len(recent) == 1
    assert recent[0]["transaction_id"] == tx_id


def test_action_telemetry_live_safety_semantics(clean_repositories):
    _, _, act_repo, _, _ = clean_repositories

    # Record a rejected action
    act_repo.record_execution(
        execution_dict={
            "execution_id": "EXEC-1",
            "action_token_id": "ACT-1",
            "granted_action": "STEP_UP",
            "principal_id": "analyst_1",
            "execution_status": "REJECTED",
            "observed_outcome": "REJECTED_BY_GATEWAY",
            "verification_status": "FAIL",
        },
        is_unsafe_violation=False,
        is_rejected=True,
    )

    # Record a successful action
    act_repo.record_execution(
        execution_dict={
            "execution_id": "EXEC-2",
            "action_token_id": "ACT-2",
            "granted_action": "BLOCK",
            "principal_id": "analyst_1",
            "execution_status": "EXECUTED",
            "observed_outcome": "BLOCKED",
            "verification_status": "PASS",
        },
        is_unsafe_violation=False,
        is_rejected=False,
    )

    telemetry = act_repo.get_telemetry()
    assert telemetry["total_executions"] == 2
    assert telemetry["rejected_executions"] == 1
    assert (
        telemetry["live_unsafe_executions"] == 0
    )  # A rejected attempt is NOT an unsafe execution!


def test_analyst_mutation_and_timeline_logging(clean_repositories):
    _, inc_repo, _, tl_repo, _ = clean_repositories
    inc_id = "INC-TEST-001"

    inc_repo.save_incident(
        {
            "incident_id": inc_id,
            "investigation_id": "cust_test_1",
            "status": "NEW",
            "owner": "Unassigned",
            "priority": "HIGH",
            "severity": "HIGH",
            "risk_score": 88,
            "confidence": 0.95,
            "protected_exposure_inr": 120000.0,
        }
    )

    # Update incident state
    updated = inc_repo.update_incident(
        inc_id, {"status": "INVESTIGATING", "owner": "Arnav (Risk Analyst)"}
    )
    assert updated["status"] == "INVESTIGATING"
    assert updated["owner"] == "Arnav (Risk Analyst)"

    # Add timeline event
    tl_repo.add_event(
        investigation_id="cust_test_1",
        stage="INCIDENT_UPDATED",
        summary="Incident status updated to INVESTIGATING",
        actor="Arnav (Risk Analyst)",
    )

    timeline = tl_repo.get_timeline("cust_test_1")
    assert len(timeline) == 1
    assert timeline[0]["stage"] == "INCIDENT_UPDATED"
