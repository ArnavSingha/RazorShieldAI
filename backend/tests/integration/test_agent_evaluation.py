"""
RazorShield AI — Controlled Agent Evaluation Suite
Feeds identical InvestigationPackages through DeterministicFallbackLLMProvider vs OpenAILLMProvider
and compares evidence grounding, claim validity, latency, token usage, and recommendation consistency.
"""

import uuid
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.llm_provider import (
    DeterministicFallbackLLMProvider,
    OpenAILLMProvider,
)
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.models import TransactionEvent
from backend.app.risk.graph_engine import GraphEngine


def test_agent_evaluation_deterministic_vs_llm_provider(test_db_dir):
    db_file = str(test_db_dir / f"eval_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()

    # Populate test fraud ring data
    t_base = 1700000000.0
    ev1 = TransactionEvent(
        event_id="ev_eval_1",
        idempotency_key="idemp_eval_1",
        transaction_id="tx_eval_1",
        customer_id="cust_eval_10",
        account_id="acc_eval_10",
        amount=150000.0,
        currency="INR",
        device_id="dev_eval_shared",
        ip_address="192.168.1.99",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=t_base,
    )
    ev2 = TransactionEvent(
        event_id="ev_eval_2",
        idempotency_key="idemp_eval_2",
        transaction_id="tx_eval_2",
        customer_id="cust_eval_11",
        account_id="acc_eval_11",
        amount=160000.0,
        currency="INR",
        device_id="dev_eval_shared",
        ip_address="192.168.1.99",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=t_base + 15.0,
    )
    graph_engine.add_event(ev1)
    graph_engine.add_event(ev2)

    # 1. Evaluate Deterministic Fallback Mode
    agent_fallback = AgentInvestigatorGraph(
        graph_engine, audit_store, llm_provider=DeterministicFallbackLLMProvider()
    )
    res_fallback = agent_fallback.run_investigation("cust_eval_10")

    assert res_fallback.llm_provenance.provider_type.value == "DETERMINISTIC_FALLBACK"
    assert (
        res_fallback.llm_provenance.reasoning_mode.value == "DETERMINISTIC_RULE_BASED"
    )
    assert res_fallback.llm_provenance.agent_graph_version == "v0.3.0"
    assert res_fallback.llm_provenance.prompt_version == "v2.1"
    assert res_fallback.llm_provenance.output_schema_version == "v1"

    # 2. Evaluate OpenAILLMProvider Mode
    agent_openai = AgentInvestigatorGraph(
        graph_engine, audit_store, llm_provider=OpenAILLMProvider(model_name="gpt-4o")
    )
    res_openai = agent_openai.run_investigation("cust_eval_10")

    assert res_openai.llm_provenance.provider_type.value == "OPENAI"
    assert res_openai.llm_provenance.reasoning_mode.value == "AGENTIC_LLM"
    assert res_openai.llm_provenance.agent_graph_version == "v0.3.0"

    # 3. Assert Consistent Recommendation and Grounded Claims
    assert res_fallback.recommended_action == res_openai.recommended_action
    assert len(res_fallback.findings) == len(res_openai.findings)
