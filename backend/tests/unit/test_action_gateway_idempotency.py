"""
RazorShield AI — Unit Tests for Action Gateway Idempotency & Synthetic State Machine
Verifies ALREADY_EXECUTED idempotency and synthetic transaction state transitions.
"""

import uuid
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.llm_provider import DeterministicFallbackLLMProvider
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.models import TransactionEvent
from backend.app.domain.policy_contracts import TokenStatus, TransactionState
from backend.app.gateway.action_gateway import ActionGateway
from backend.app.policy.action_token import ActionTokenGenerator
from backend.app.policy.policy_engine import DeterministicPolicyEngine
from backend.app.policy.rbac import TrustedPrincipal, UserRole
from backend.app.risk.graph_engine import GraphEngine


def test_action_gateway_synthetic_state_transitions_and_idempotency(test_db_dir):
    ActionGateway.reset_gateway_state()
    db_file = str(test_db_dir / f"gateway_unit_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()
    policy_engine = DeterministicPolicyEngine()
    agent = AgentInvestigatorGraph(
        graph_engine,
        audit_store,
        llm_provider=DeterministicFallbackLLMProvider(),
    )

    ev = TransactionEvent(
        event_id="ev_gw_1",
        idempotency_key="idemp_gw_1",
        transaction_id="tx_gw_1",
        customer_id="cust_gw_10",
        account_id="acc_gw_10",
        amount=140000.0,
        currency="INR",
        device_id="dev_gw_1",
        ip_address="10.0.0.10",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    graph_engine.add_event(ev)

    agent_res = agent.run_investigation("cust_gw_10")
    package = graph_engine.generate_investigation_package("cust_gw_10", max_hops=2)
    decision = policy_engine.evaluate_policy(agent_res, package)

    principal = TrustedPrincipal(
        principal_id="usr_op_01", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    token = ActionTokenGenerator.issue_action_token(
        decision, package.evidence_snapshot_hash, principal
    )

    # 1. Execute Token
    result1 = ActionGateway.execute_action_token(token, audit_logger=audit_store)
    assert result1.status == TokenStatus.EXECUTED
    assert result1.previous_state == TransactionState.PENDING
    assert result1.new_state in (
        TransactionState.STEP_UP_REQUIRED,
        TransactionState.HELD,
        TransactionState.AUTHORIZED,
    )
    assert result1.verified is True

    # 2. Re-Execute Token with same action_id -> Returns ALREADY_EXECUTED
    result2 = ActionGateway.execute_action_token(token, audit_logger=audit_store)
    assert result2.status == TokenStatus.ALREADY_EXECUTED
    assert result2.action_id == token.action_id
