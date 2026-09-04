"""
RazorShield AI — Invariant Test: Slice 4 Makes Zero LLM Calls
Verifies that once an AgentInvestigationResult is generated in Slice 3, the entire Slice 4 control plane
(Recommendation Validation, Policy Evaluation, RBAC Authorization, Token Signing, Gateway Execution,
Outcome Verification, and Audit Logging) makes EXACTLY ZERO calls to any LLM Provider.
"""

import uuid
from unittest.mock import MagicMock
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.llm_provider import LLMProviderInterface
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.models import TransactionEvent
from backend.app.gateway.action_gateway import ActionGateway
from backend.app.policy.action_token import ActionTokenGenerator
from backend.app.policy.policy_engine import DeterministicPolicyEngine
from backend.app.policy.rbac import RBACPolicyGateway, TrustedPrincipal, UserRole
from backend.app.policy.recommendation_validator import RecommendationValidator
from backend.app.risk.graph_engine import GraphEngine


def test_slice4_control_plane_makes_zero_llm_calls(test_db_dir):
    ActionGateway.reset_gateway_state()
    db_file = str(test_db_dir / f"zero_llm_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()

    ev = TransactionEvent(
        event_id="ev_zero_llm",
        idempotency_key="idemp_zero_llm",
        transaction_id="tx_zero_llm",
        customer_id="cust_zero_llm",
        account_id="acc_zero_llm",
        amount=120000.0,
        currency="INR",
        device_id="dev_zero_llm",
        ip_address="10.0.0.1",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    graph_engine.add_event(ev)

    # 1. Create Mock LLM Provider with valid returned reasoning dictionary
    from backend.app.agent.llm_provider import DeterministicFallbackLLMProvider

    fallback_provider = DeterministicFallbackLLMProvider()
    pkg_zero = graph_engine.generate_investigation_package("cust_zero_llm", max_hops=2)
    ev_map = {item.evidence_id: item for item in pkg_zero.primary_evidence}

    mock_llm_provider = MagicMock(spec=LLMProviderInterface)
    mock_llm_provider.generate_investigation_reasoning.return_value = (
        fallback_provider.generate_investigation_reasoning(pkg_zero, ev_map)
    )

    # Instantiate Agent in Slice 3
    agent = AgentInvestigatorGraph(
        graph_engine, audit_store, llm_provider=mock_llm_provider
    )

    # Run Slice 3 reasoning -> calls mock_llm_provider once
    agent_res = agent.run_investigation("cust_zero_llm")
    assert mock_llm_provider.generate_investigation_reasoning.call_count == 1

    # Reset call count before starting Slice 4 Control Plane
    mock_llm_provider.generate_investigation_reasoning.reset_mock()

    # =========================================================================
    # SLICE 4 CONTROL PLANE EXECUTION (Recommendation -> Policy -> RBAC -> Token -> Gateway -> Verification -> Audit)
    # =========================================================================
    package = graph_engine.generate_investigation_package("cust_zero_llm", max_hops=2)
    principal = TrustedPrincipal(
        principal_id="usr_op_01", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )

    # Step A: Recommendation Validation
    RecommendationValidator.validate_agent_recommendation(agent_res, package)

    # Step B: Deterministic Policy Engine Evaluation
    policy_engine = DeterministicPolicyEngine()
    decision = policy_engine.evaluate_policy(agent_res, package)

    # Step C: RBAC Authorization Gate
    RBACPolicyGateway.authorize_role_action(principal, decision.final_action)

    # Step D: Issue Signed Action Token
    token = ActionTokenGenerator.issue_action_token(
        decision=decision,
        evidence_snapshot_hash=package.evidence_snapshot_hash,
        principal=principal,
    )

    # Step E: Action Gateway Execution & Synthetic State Transition
    result = ActionGateway.execute_action_token(
        token=token,
        active_policy_version="v1.0",
        current_snapshot_hash=package.evidence_snapshot_hash,
        audit_logger=audit_store,
    )

    assert result.verified is True
    assert result.status.value in ("EXECUTED", "ALREADY_EXECUTED")

    # =========================================================================
    # INVARIANT HARD ASSERTION: Zero LLM Calls in Slice 4
    # =========================================================================
    assert mock_llm_provider.generate_investigation_reasoning.call_count == 0
