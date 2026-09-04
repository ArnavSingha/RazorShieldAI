"""
RazorShield AI — Unit Tests for Deterministic Policy Engine (Slice 4)
Verifies policy rules, AI recommendation overrides, override explanation summaries, and versioning.
"""

import uuid
import pytest
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.llm_provider import DeterministicFallbackLLMProvider
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.agent_contracts import RecommendedAction
from backend.app.domain.models import TransactionEvent
from backend.app.domain.policy_contracts import PolicyAction
from backend.app.policy.policy_engine import DeterministicPolicyEngine
from backend.app.risk.graph_engine import GraphEngine


@pytest.fixture
def policy_test_setup(test_db_dir):
    db_file = str(test_db_dir / f"pol_unit_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()
    engine = DeterministicPolicyEngine()
    agent = AgentInvestigatorGraph(
        graph_engine,
        audit_store,
        llm_provider=DeterministicFallbackLLMProvider(),
    )
    return engine, agent, graph_engine


def test_ai_block_overridden_to_step_up_due_to_trusted_customer_history(
    policy_test_setup,
):
    engine, agent, graph_engine = policy_test_setup

    # Single customer event (low ring linkage)
    ev = TransactionEvent(
        event_id="ev_pol_1",
        idempotency_key="idemp_pol_1",
        transaction_id="tx_pol_1",
        customer_id="cust_trusted_single",
        account_id="acc_pol_1",
        amount=180000.0,
        currency="INR",
        device_id="dev_single",
        ip_address="10.0.0.1",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    graph_engine.add_event(ev)

    agent_res = agent.run_investigation("cust_trusted_single")
    # Force AI recommendation to BLOCK to simulate AI recommendation
    agent_res.recommended_action = RecommendedAction.BLOCK

    package = graph_engine.generate_investigation_package(
        "cust_trusted_single", max_hops=2
    )
    decision = engine.evaluate_policy(agent_res, package)

    # 1. Assert Policy Overruled AI BLOCK -> STEP_UP
    assert decision.overridden is True
    assert decision.ai_recommendation == PolicyAction.BLOCK
    assert decision.final_action == PolicyAction.STEP_UP
    assert "TRUSTED_CUSTOMER_HISTORY" in decision.override_reason_codes
    assert "POLICY_OVERRIDE_AI" in decision.override_reason_codes
    assert (
        "AI recommended BLOCK, but deterministic Policy v1.0 enforced STEP_UP"
        in decision.explanation_summary
    )


def test_ai_allow_overridden_to_block_due_to_high_cluster_score(policy_test_setup):
    engine, agent, graph_engine = policy_test_setup

    # Coordinated fraud ring (High Cluster Score >= 85)
    t_base = 1700000000.0
    for i in range(5):
        ev = TransactionEvent(
            event_id=f"ev_ring_{i}",
            idempotency_key=f"idemp_ring_{i}",
            transaction_id=f"tx_ring_{i}",
            customer_id=f"cust_ring_{i}",
            account_id=f"acc_ring_{i}",
            amount=150000.0,
            currency="INR",
            device_id="dev_shared_ring",
            ip_address="192.168.1.100",
            merchant_id="merch_ring",
            merchant_category_code="5732",
            timestamp=t_base + (i * 10),
        )
        graph_engine.add_event(ev)

    agent_res = agent.run_investigation("cust_ring_0")
    # Force AI recommendation to ALLOW to simulate AI recommendation override
    agent_res.recommended_action = RecommendedAction.ALLOW

    package = graph_engine.generate_investigation_package("cust_ring_0", max_hops=2)
    decision = engine.evaluate_policy(agent_res, package)

    # Assert Policy Overruled AI ALLOW -> BLOCK due to mandatory high cluster score
    assert decision.overridden is True
    assert decision.ai_recommendation == PolicyAction.ALLOW
    assert decision.final_action == PolicyAction.BLOCK
    assert "HIGH_CLUSTER_RISK_MANDATORY_BLOCK" in decision.override_reason_codes
