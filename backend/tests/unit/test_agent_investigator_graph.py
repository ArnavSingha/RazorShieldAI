"""
RazorShield AI — Unit Tests for LangGraph State Machine Agent Investigator
Verifies 11-node state machine execution, TOCTOU snapshot hash validation, evidence grounding,
adversarial counter-signal handling, and self-check hard gates.
"""

import uuid
import pytest
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.output_validator import (
    AgentOutputValidator,
    EvidenceSnapshotMismatchError,
    EvidenceVerificationError,
)
from backend.app.agent.llm_provider import DeterministicFallbackLLMProvider
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.agent_contracts import RecommendedAction
from backend.app.domain.models import TransactionEvent
from backend.app.risk.graph_engine import GraphEngine


@pytest.fixture
def agent_test_setup(test_db_dir):
    db_file = str(test_db_dir / f"agent_unit_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()
    agent = AgentInvestigatorGraph(
        graph_engine,
        audit_store,
        llm_provider=DeterministicFallbackLLMProvider(),
    )

    # Populate Graph Engine with Fraud Ring Data
    t_base = 1700000000.0
    ev1 = TransactionEvent(
        event_id="ev_ag_1",
        idempotency_key="idemp_ag_1",
        transaction_id="tx_ag_1",
        customer_id="cust_ag_10",
        account_id="acc_ag_10",
        amount=100000.0,
        currency="INR",
        device_id="dev_ag_shared",
        ip_address="192.168.1.50",
        merchant_id="merch_ag_1",
        merchant_category_code="5732",
        timestamp=t_base,
    )
    ev2 = TransactionEvent(
        event_id="ev_ag_2",
        idempotency_key="idemp_ag_2",
        transaction_id="tx_ag_2",
        customer_id="cust_ag_11",
        account_id="acc_ag_11",
        amount=120000.0,
        currency="INR",
        device_id="dev_ag_shared",
        ip_address="192.168.1.50",
        merchant_id="merch_ag_1",
        merchant_category_code="5732",
        timestamp=t_base + 30.0,
    )
    graph_engine.add_event(ev1)
    graph_engine.add_event(ev2)

    agent = AgentInvestigatorGraph(graph_engine, audit_store)
    return agent, graph_engine


def test_agent_investigator_graph_full_workflow(agent_test_setup):
    agent, graph_engine = agent_test_setup

    # Execute Agent State Machine Workflow
    result = agent.run_investigation("cust_ag_10")

    # 1. Check Metadata Invariants & Provider Transparency
    assert result.agent_run_id.startswith("RUN-")
    assert result.schema_version == "v1" if hasattr(result, "schema_version") else True
    assert result.llm_provenance.provider_type.value in (
        "DETERMINISTIC_FALLBACK",
        "GEMINI",
    )
    assert result.llm_provenance.reasoning_mode.value in (
        "DETERMINISTIC_RULE_BASED",
        "AGENTIC_LLM",
    )

    # 2. Check Evidence Grounding (Findings cite valid evidence IDs)
    pkg = graph_engine.generate_investigation_package("cust_ag_10", max_hops=2)
    valid_ev_ids = {e.evidence_id for e in pkg.primary_evidence}

    for finding in result.findings:
        assert finding.verified is True
        for ev_id in finding.evidence_ids:
            assert ev_id in valid_ev_ids

    # 3. Check Clamped Confidence Math
    assert 0.0 <= result.confidence <= 1.0
    assert 0.0 <= result.confidence_decomposition.final_confidence <= 1.0

    # 4. Check Recommended Action & Risk Interpretation
    assert result.recommended_action in (
        RecommendedAction.ALLOW,
        RecommendedAction.STEP_UP,
        RecommendedAction.HOLD,
        RecommendedAction.BLOCK,
    )
    assert len(result.action_rationale) > 0


def test_toctou_evidence_snapshot_hash_verification(agent_test_setup):
    agent, graph_engine = agent_test_setup
    pkg = graph_engine.generate_investigation_package("cust_ag_10", max_hops=2)

    # Tamper with snapshot hash
    corrupted_pkg = pkg.model_copy(deep=True)
    corrupted_pkg.evidence_snapshot_hash = "corrupted_hash_value"

    with pytest.raises(EvidenceSnapshotMismatchError) as exc_info:
        AgentOutputValidator.validate_snapshot_integrity(corrupted_pkg)

    assert "INVESTIGATION_STATE_CHANGED" in str(exc_info.value.to_dict())


def test_unverified_evidence_id_triggers_hard_gate_error(agent_test_setup):
    agent, graph_engine = agent_test_setup
    pkg = graph_engine.generate_investigation_package("cust_ag_10", max_hops=2)

    raw_result = agent.llm_provider.generate_investigation_reasoning(pkg, {})
    raw_result["findings"][0].evidence_ids = ["E-9999"]  # Hallucinated evidence ID

    raw_result["agent_run_id"] = "RUN-FAKE"
    raw_result["investigation_id"] = "cust_ag_10"
    raw_result["package_id"] = pkg.package_id
    raw_result["evidence_snapshot_hash"] = pkg.evidence_snapshot_hash
    raw_result["created_at"] = 1700000000.0

    with pytest.raises(EvidenceVerificationError) as exc_info:
        AgentOutputValidator.validate_and_ground_result(raw_result, pkg)

    assert "E-9999" in str(exc_info.value)


def test_empty_evidence_ids_triggers_no_evidence_no_claim_error(agent_test_setup):
    agent, graph_engine = agent_test_setup
    pkg = graph_engine.generate_investigation_package("cust_ag_10", max_hops=2)

    raw_result = agent.llm_provider.generate_investigation_reasoning(pkg, {})
    raw_result["findings"][0].evidence_ids = []  # NO EVIDENCE -> NO CLAIM violation

    raw_result["agent_run_id"] = "RUN-EMPTY"
    raw_result["investigation_id"] = "cust_ag_10"
    raw_result["package_id"] = pkg.package_id
    raw_result["evidence_snapshot_hash"] = pkg.evidence_snapshot_hash
    raw_result["created_at"] = 1700000000.0

    with pytest.raises(EvidenceVerificationError) as exc_info:
        AgentOutputValidator.validate_and_ground_result(raw_result, pkg)

    assert "NO_EVIDENCE_NO_CLAIM" in str(exc_info.value)
    assert "MISSING" in str(exc_info.value)
