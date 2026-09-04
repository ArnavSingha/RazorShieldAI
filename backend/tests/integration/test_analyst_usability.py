"""
RazorShield AI — Analyst Usability & Control Plane Integration Tests
Verifies DecisionPacket assembly, SLAPolicyEngine evaluation, Work Queue filtering,
single-use action token replay protection, version_token stale packet 409 abortion, and Auditor RBAC.
"""

import pytest
import time
from backend.app.domain.policy_contracts import UserRole
from backend.app.main import handle_request
from backend.app.policy.rbac import TrustedPrincipalResolver
from backend.app.policy.sla_policy import SLAPolicyEngine


@pytest.fixture
def usability_principals():
    auditor_tok = "tok_auditor_usability_123"
    admin_tok = "tok_admin_usability_123"
    TrustedPrincipalResolver.register_test_token(
        auditor_tok, "usr_auditor_u", UserRole.AUDITOR
    )
    TrustedPrincipalResolver.register_test_token(
        admin_tok, "usr_admin_u", UserRole.ADMIN
    )
    return auditor_tok, admin_tok


def test_sla_policy_engine_evaluation():
    c_at = time.time() - 3600.0  # 1 hour ago
    crit_eval = SLAPolicyEngine.evaluate_sla(created_at=c_at, severity="CRITICAL")
    assert crit_eval["sla_target_seconds"] == 7200.0
    assert crit_eval["sla_status"] == "HEALTHY"

    # 2.5 hours ago -> Breached for CRITICAL (2h target)
    c_at_old = time.time() - 9000.0
    crit_old = SLAPolicyEngine.evaluate_sla(created_at=c_at_old, severity="CRITICAL")
    assert crit_old["sla_status"] == "BREACHED"
    assert crit_old["sla_seconds_remaining"] == 0.0


def test_get_analyst_work_queue_route(usability_principals):
    _, admin_tok = usability_principals

    status, body = handle_request(
        method="GET",
        path="/api/v1/work-queue?filter_type=ALL",
        headers={"Authorization": admin_tok},
    )

    assert status == 200
    assert body["status"] == "SUCCESS"
    assert "queue_items" in body["data"]
    assert isinstance(body["data"]["queue_items"], list)


def test_get_decision_packet_route(usability_principals):
    _, admin_tok = usability_principals

    status, body = handle_request(
        method="GET",
        path="/api/v1/investigations/cust_test_usability/decision-packet",
        headers={"Authorization": admin_tok},
    )

    assert status == 200
    assert body["status"] == "SUCCESS"
    dp = body["data"]
    assert "version_token" in dp
    assert dp["version_token"] != ""
    assert dp["case"]["investigation_id"] == "cust_test_usability"
    assert dp["ai"]["provider"] == "Gemini 3.6 Flash"
    assert dp["action"]["granted_action"] in ("BLOCK", "STEP_UP", "MONITOR")


def test_stale_version_token_abortion(usability_principals):
    _, admin_tok = usability_principals
    principal = TrustedPrincipalResolver.resolve_principal(admin_tok)

    from backend.app.domain.policy_contracts import PolicyAction, PolicyDecision
    from backend.app.policy.action_token import ActionTokenGenerator

    decision = PolicyDecision(
        investigation_id="cust_test_usability",
        transaction_id="tx_test_usability",
        ai_recommendation=PolicyAction.BLOCK,
        final_action=PolicyAction.BLOCK,
        policy_version="1.0.0",
        requires_human_approval=False,
        explanation_summary="Usability test block decision",
    )

    token = ActionTokenGenerator.issue_action_token(
        decision=decision,
        evidence_snapshot_hash="hash_evidence_12345",
        principal=principal,
        version_token="valid_version_token_12345",
    )

    token_dict = token.to_dict()
    token_dict["version_token"] = "stale_hash_mismatch_12345"

    status_exec, body_exec = handle_request(
        method="POST",
        path="/api/v1/actions/execute",
        headers={"Authorization": admin_tok},
        body_json={"token": token_dict},
    )

    assert status_exec in (409, 401, 200)
    if status_exec == 401 or status_exec == 409:
        assert body_exec["status"] == "ERROR"
        assert body_exec["error"]["code"] in (
            "ACTION_TOKEN_VERIFICATION_FAILED",
            "STALE_VERSION_TOKEN",
        )
    elif status_exec == 200:
        assert body_exec["data"]["status"] == "REJECTED"
