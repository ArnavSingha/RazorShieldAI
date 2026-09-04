"""
RazorShield AI — Security Tests: Slice 4 Control Plane Adversarial Safeguards
Tests header role spoofing rejection, forged HMAC tokens, expired TTL, atomic nonce replay lock,
policy version binding, stale snapshot hashes, and bound human approvals.
"""

import uuid
import pytest
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.models import TransactionEvent
from backend.app.domain.policy_contracts import UserRole
from backend.app.gateway.action_gateway import ActionGateway, ActionGatewayReplayError
from backend.app.policy.action_token import (
    ActionTokenGenerator,
    ActionTokenVerificationError,
)
from backend.app.policy.approval_matrix import (
    ApprovalBindingMismatchError,
    HumanApprovalMatrix,
)
from backend.app.policy.policy_engine import DeterministicPolicyEngine
from backend.app.policy.rbac import TrustedPrincipal, TrustedPrincipalResolver
from backend.app.risk.graph_engine import GraphEngine


from backend.app.agent.llm_provider import DeterministicFallbackLLMProvider


@pytest.fixture
def slice4_security_setup(test_db_dir):
    ActionGateway.reset_gateway_state()
    db_file = str(test_db_dir / f"sec_slice4_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()
    policy_engine = DeterministicPolicyEngine()
    agent = AgentInvestigatorGraph(
        graph_engine, audit_store, llm_provider=DeterministicFallbackLLMProvider()
    )

    ev = TransactionEvent(
        event_id="ev_sec_4",
        idempotency_key="idemp_sec_4",
        transaction_id="tx_sec_4",
        customer_id="cust_sec_4",
        account_id="acc_sec_4",
        amount=120000.0,
        currency="INR",
        device_id="dev_sec_4",
        ip_address="10.0.0.4",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    graph_engine.add_event(ev)
    return agent, graph_engine, policy_engine, audit_store


def test_role_header_spoofing_rejected():
    # Attempting to supply header_principal_id = 'admin' without valid auth secret resolves to READ_ONLY role
    principal = TrustedPrincipalResolver.resolve_principal(
        auth_token=None, header_principal_id="admin"
    )
    assert principal.is_authenticated is False
    assert principal.role == UserRole.READ_ONLY


def test_forged_action_token_signature_rejected(slice4_security_setup):
    agent, graph_engine, policy_engine, _ = slice4_security_setup
    agent_res = agent.run_investigation("cust_sec_4")
    package = graph_engine.generate_investigation_package("cust_sec_4", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    principal = TrustedPrincipal(
        principal_id="usr_op", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    token = ActionTokenGenerator.issue_action_token(
        decision, package.evidence_snapshot_hash, principal
    )

    # Forging signature
    forged_token = token.model_copy(deep=True)
    forged_token.hmac_signature = "forged_signature_hash_12345"

    with pytest.raises(ActionTokenVerificationError) as exc_info:
        ActionTokenGenerator.verify_action_token(
            forged_token, active_policy_version="v1.0"
        )
    assert "HMAC signature invalid" in str(exc_info.value)


def test_expired_action_token_rejected(slice4_security_setup):
    agent, graph_engine, policy_engine, _ = slice4_security_setup
    agent_res = agent.run_investigation("cust_sec_4")
    package = graph_engine.generate_investigation_package("cust_sec_4", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    principal = TrustedPrincipal(
        principal_id="usr_op", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    # Issue token with negative TTL (already expired)
    expired_token = ActionTokenGenerator.issue_action_token(
        decision, package.evidence_snapshot_hash, principal, ttl_seconds=-10.0
    )

    with pytest.raises(ActionTokenVerificationError) as exc_info:
        ActionTokenGenerator.verify_action_token(
            expired_token, active_policy_version="v1.0"
        )
    assert "Action token expired" in str(exc_info.value)


def test_policy_version_mismatch_rejected(slice4_security_setup):
    agent, graph_engine, policy_engine, _ = slice4_security_setup
    agent_res = agent.run_investigation("cust_sec_4")
    package = graph_engine.generate_investigation_package("cust_sec_4", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    principal = TrustedPrincipal(
        principal_id="usr_op", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    token = ActionTokenGenerator.issue_action_token(
        decision, package.evidence_snapshot_hash, principal
    )

    # Verifying token against updated active policy version 'v1.1'
    with pytest.raises(ActionTokenVerificationError) as exc_info:
        ActionTokenGenerator.verify_action_token(token, active_policy_version="v1.1")
    assert "Policy version mismatch" in str(exc_info.value)


def test_stale_evidence_snapshot_rejected(slice4_security_setup):
    agent, graph_engine, policy_engine, _ = slice4_security_setup
    agent_res = agent.run_investigation("cust_sec_4")
    package = graph_engine.generate_investigation_package("cust_sec_4", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    principal = TrustedPrincipal(
        principal_id="usr_op", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    token = ActionTokenGenerator.issue_action_token(
        decision, package.evidence_snapshot_hash, principal
    )

    # Verifying token against altered current snapshot hash
    with pytest.raises(ActionTokenVerificationError) as exc_info:
        ActionTokenGenerator.verify_action_token(
            token, current_snapshot_hash="altered_snapshot_hash_99"
        )
    assert "Stale evidence snapshot" in str(exc_info.value)


def test_atomic_nonce_replay_protection_triggers_error(slice4_security_setup):
    agent, graph_engine, policy_engine, audit_store = slice4_security_setup
    agent_res = agent.run_investigation("cust_sec_4")
    package = graph_engine.generate_investigation_package("cust_sec_4", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    principal = TrustedPrincipal(
        principal_id="usr_op", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    token = ActionTokenGenerator.issue_action_token(
        decision, package.evidence_snapshot_hash, principal
    )

    # 1. First execution succeeds
    res1 = ActionGateway.execute_action_token(token, audit_logger=audit_store)
    assert res1.status.value in ("EXECUTED", "ALREADY_EXECUTED")

    # 2. Replaying token nonce with different action_id raises ActionGatewayReplayError
    replayed_token = token.model_copy(deep=True)
    replayed_token.action_id = "ACT-REPLAY-NEW-ID"
    with pytest.raises(ActionGatewayReplayError) as exc_info:
        ActionGateway.execute_action_token(replayed_token, audit_logger=audit_store)
    assert "ACTION_NONCE_REPLAYED" in str(exc_info.value.to_dict())


def test_approval_binding_mismatch_raises_error(slice4_security_setup):
    agent, graph_engine, policy_engine, _ = slice4_security_setup
    agent_res = agent.run_investigation("cust_sec_4")
    package = graph_engine.generate_investigation_package("cust_sec_4", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    analyst = TrustedPrincipal(
        principal_id="usr_analyst_01", role=UserRole.RISK_ANALYST, is_authenticated=True
    )
    binding = HumanApprovalMatrix.create_approval_binding(
        "ACT-001", decision, package.evidence_snapshot_hash, analyst
    )

    # Attempting to verify binding for a different action_id 'ACT-002'
    with pytest.raises(ApprovalBindingMismatchError) as exc_info:
        HumanApprovalMatrix.verify_approval_binding(
            binding, "ACT-002", decision, package.evidence_snapshot_hash
        )
    assert "Action ID mismatch" in str(exc_info.value)
