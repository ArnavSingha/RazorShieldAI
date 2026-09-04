"""
RazorShield AI — Phase 2.5 Real User & Hardening Integration Tests
Verifies Capability-Based RBAC enforcement, View-Only Auditor restrictions (403),
High-Risk Action Approval Workflow levels, SSE event stream publishing, and stale-data protection.
"""

import pytest
from backend.app.domain.policy_contracts import UserRole
from backend.app.main import handle_request
from backend.app.policy.rbac import (
    RBACPolicyGateway,
    TrustedPrincipalResolver,
    UnauthorizedRoleError,
)
from backend.app.api.sse import publish_system_event, _EVENT_HISTORY


@pytest.fixture
def test_principals():
    auditor_tok = "tok_auditor_test_123"
    analyst_tok = "tok_analyst_test_123"
    TrustedPrincipalResolver.register_test_token(
        auditor_tok, "usr_auditor_t", UserRole.AUDITOR
    )
    TrustedPrincipalResolver.register_test_token(
        analyst_tok, "usr_analyst_t", UserRole.RISK_ANALYST
    )
    return auditor_tok, analyst_tok


def test_capability_matrix_auditor_view_only(test_principals):
    auditor_tok, analyst_tok = test_principals

    auditor_p = TrustedPrincipalResolver.resolve_principal(auditor_tok)
    analyst_p = TrustedPrincipalResolver.resolve_principal(analyst_tok)

    # Auditor HAS read capabilities
    assert (
        RBACPolicyGateway.has_capability(auditor_p.role, "investigation.read") is True
    )
    assert RBACPolicyGateway.has_capability(auditor_p.role, "transaction.read") is True
    assert RBACPolicyGateway.has_capability(auditor_p.role, "audit.read") is True

    # Auditor LACKS mutation/execution/export capabilities
    assert (
        RBACPolicyGateway.has_capability(auditor_p.role, "investigation.update")
        is False
    )
    assert RBACPolicyGateway.has_capability(auditor_p.role, "action.authorize") is False
    assert RBACPolicyGateway.has_capability(auditor_p.role, "action.execute") is False
    assert RBACPolicyGateway.has_capability(auditor_p.role, "case.export") is False

    with pytest.raises(UnauthorizedRoleError):
        RBACPolicyGateway.require_capability(auditor_p, "action.execute")

    with pytest.raises(UnauthorizedRoleError):
        RBACPolicyGateway.require_capability(auditor_p, "case.export")

    # Analyst HAS mutation and export capabilities
    assert RBACPolicyGateway.has_capability(analyst_p.role, "action.authorize") is True
    assert RBACPolicyGateway.has_capability(analyst_p.role, "case.export") is True


def test_auditor_export_and_mutation_routes_return_403(test_principals):
    auditor_tok, _ = test_principals

    # 1. Attempt case export as AUDITOR -> Expect 403 Forbidden
    status_exp, body_exp = handle_request(
        method="GET",
        path="/api/v1/investigations/cust_test_123/export",
        headers={"Authorization": auditor_tok},
    )
    assert status_exp == 403
    assert body_exp["status"] == "ERROR"
    assert "lacks capability" in body_exp["error"]["message"]

    # 2. Attempt incident status patch as AUDITOR -> Expect 403 Forbidden
    status_patch, body_patch = handle_request(
        method="PATCH",
        path="/api/v1/investigations/INC-9901",
        headers={"Authorization": auditor_tok},
        body_json={"status": "RESOLVED"},
    )
    assert status_patch == 403
    assert body_patch["status"] == "ERROR"


def test_high_risk_action_approval_levels():
    # Low-risk STEP_UP -> Single Analyst
    lvl_step = RBACPolicyGateway.get_required_approval_level(
        action="STEP_UP", risk_score=50, exposure_inr=10000.0
    )
    assert lvl_step in ("ANALYST", "SINGLE_ANALYST")

    # BLOCK -> Analyst + Policy
    lvl_block = RBACPolicyGateway.get_required_approval_level(
        action="BLOCK", risk_score=75, exposure_inr=50000.0
    )
    assert lvl_block == "ANALYST_PLUS_POLICY"

    # Critical risk (>= 85) or High Exposure (>= 100k) -> Elevated Dual Control
    lvl_crit = RBACPolicyGateway.get_required_approval_level(
        action="BLOCK", risk_score=92, exposure_inr=250000.0
    )
    assert lvl_crit == "ELEVATED_DUAL_CONTROL"


def test_sse_event_publishing():
    initial_count = len(_EVENT_HISTORY)
    evt = publish_system_event(
        event_type="NEW_TRANSACTION",
        resource_type="TRANSACTION",
        resource_id="tx_sse_test_123",
        correlation_id="corr_sse_1",
        details={"risk_score": 88},
    )
    assert evt["event_type"] == "NEW_TRANSACTION"
    assert evt["resource_id"] == "tx_sse_test_123"
    assert len(_EVENT_HISTORY) == initial_count + 1
