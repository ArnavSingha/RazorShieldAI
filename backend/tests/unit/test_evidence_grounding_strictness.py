"""
RazorShield AI — Strict Evidence Grounding Unit Tests
Verifies NO EVIDENCE -> NO CLAIM invariant. Assert that unknown, empty, or mixed hallucinated evidence IDs
trigger EvidenceVerificationError and NEVER cause silent citation substitution or claim rewrites.
"""

import time
import pytest
from unittest.mock import MagicMock
from backend.app.agent.llm_provider import GeminiLLMProvider
from backend.app.agent.output_validator import (
    EvidenceVerificationError,
    AgentOutputValidator,
)
from backend.app.domain.agent_contracts import ProviderType, ReasoningMode
from backend.app.domain.models import TransactionEvent
from backend.app.risk.graph_engine import GraphEngine


@pytest.fixture
def mock_investigation_package():
    graph_engine = GraphEngine()
    ev1 = TransactionEvent(
        event_id="ev_strict_1",
        idempotency_key="idemp_strict_1",
        transaction_id="tx_strict_1",
        customer_id="cust_strict_101",
        account_id="acc_strict_101",
        amount=50000.0,
        currency="INR",
        device_id="dev_shared_strict",
        ip_address="192.168.1.50",
        merchant_id="merch_strict_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    ev2 = TransactionEvent(
        event_id="ev_strict_2",
        idempotency_key="idemp_strict_2",
        transaction_id="tx_strict_2",
        customer_id="cust_strict_102",
        account_id="acc_strict_102",
        amount=60000.0,
        currency="INR",
        device_id="dev_shared_strict",
        ip_address="192.168.1.50",
        merchant_id="merch_strict_1",
        merchant_category_code="5732",
        timestamp=1700000030.0,
    )
    graph_engine.add_event(ev1)
    graph_engine.add_event(ev2)
    return graph_engine.generate_investigation_package("cust_strict_101")


def build_mock_gemini_provider(json_response_str: str) -> GeminiLLMProvider:
    provider = GeminiLLMProvider(api_key="mock_key", model_name="gemini-3.6-flash")
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json_response_str
    mock_response.usage_metadata = MagicMock(
        prompt_token_count=100, candidates_token_count=50
    )
    mock_client.models.generate_content.return_value = mock_response
    provider.client = mock_client
    return provider


def test_strict_grounding_case1_valid_evidence_pass(mock_investigation_package):
    """Case 1: Gemini returns valid evidence ID -> PASS under ProviderType.GEMINI."""
    valid_id = mock_investigation_package.primary_evidence[0].evidence_id
    json_str = f"""{{
        "classification": "LIKELY_COORDINATED_FRAUD",
        "recommended_action": "HOLD",
        "action_rationale": "Validated shared device evidence.",
        "primary_reason": "Shared device risk",
        "findings": [{{"claim": "Shared device risk detected", "evidence_ids": ["{valid_id}"], "confidence": 0.95}}],
        "counter_signals": [{{"claim": "Normal location", "evidence_ids": ["{valid_id}"], "impact_on_hypothesis": "ATTENUATES_RISK"}}]
    }}"""
    provider = build_mock_gemini_provider(json_str)
    result = provider.generate_investigation_reasoning(mock_investigation_package, {})

    assert result["llm_provenance"].provider_type == ProviderType.GEMINI
    assert result["llm_provenance"].reasoning_mode == ReasoningMode.AGENTIC_LLM
    assert len(result["findings"]) == 1
    assert result["findings"][0].evidence_ids == [valid_id]


def test_strict_grounding_case2_unknown_evidence_triggers_fallback(
    mock_investigation_package,
):
    """Case 2: Gemini returns unknown evidence ID 'E-9999' -> Must trigger fallback, ZERO claims with E-9999."""
    json_str = """{
        "classification": "LIKELY_COORDINATED_FRAUD",
        "recommended_action": "HOLD",
        "action_rationale": "Hallucinated claim.",
        "primary_reason": "Fake risk",
        "findings": [{"claim": "Fraud detected", "evidence_ids": ["E-9999"], "confidence": 0.95}]
    }"""
    provider = build_mock_gemini_provider(json_str)
    result = provider.generate_investigation_reasoning(mock_investigation_package, {})

    assert (
        result["llm_provenance"].reasoning_mode
        == ReasoningMode.DETERMINISTIC_RULE_BASED
    )
    assert result["llm_provenance"].provider_type == ProviderType.DETERMINISTIC_FALLBACK
    all_cited_ids = [eid for f in result["findings"] for eid in f.evidence_ids]
    assert "E-9999" not in all_cited_ids


def test_strict_grounding_case3_empty_evidence_ids_triggers_fallback(
    mock_investigation_package,
):
    """Case 3: Gemini returns empty evidence_ids [] -> Must trigger fallback (NO EVIDENCE NO CLAIM)."""
    json_str = """{
        "classification": "SUSPICIOUS_ENTITY_FARM",
        "recommended_action": "STEP_UP",
        "action_rationale": "Empty evidence claim.",
        "primary_reason": "No evidence cited",
        "findings": [{"claim": "Ungrounded fraud claim", "evidence_ids": [], "confidence": 0.90}]
    }"""
    provider = build_mock_gemini_provider(json_str)
    result = provider.generate_investigation_reasoning(mock_investigation_package, {})

    assert (
        result["llm_provenance"].reasoning_mode
        == ReasoningMode.DETERMINISTIC_RULE_BASED
    )
    assert result["llm_provenance"].provider_type == ProviderType.DETERMINISTIC_FALLBACK


def test_strict_grounding_case4_mixed_valid_and_unknown_evidence_triggers_fallback(
    mock_investigation_package,
):
    """Case 4: Gemini returns mixed valid and unknown evidence IDs -> Must trigger fallback."""
    valid_id = mock_investigation_package.primary_evidence[0].evidence_id
    json_str = f"""{{
        "classification": "LIKELY_COORDINATED_FRAUD",
        "recommended_action": "HOLD",
        "action_rationale": "Mixed evidence IDs.",
        "primary_reason": "Mixed claim",
        "findings": [{{"claim": "Mixed fraud claim", "evidence_ids": ["{valid_id}", "E-9999"], "confidence": 0.90}}]
    }}"""
    provider = build_mock_gemini_provider(json_str)
    result = provider.generate_investigation_reasoning(mock_investigation_package, {})

    assert (
        result["llm_provenance"].reasoning_mode
        == ReasoningMode.DETERMINISTIC_RULE_BASED
    )
    assert result["llm_provenance"].provider_type == ProviderType.DETERMINISTIC_FALLBACK


def test_strict_grounding_case5_counter_signal_unknown_evidence_triggers_fallback(
    mock_investigation_package,
):
    """Case 5: Counter-signal contains unknown evidence ID 'E-9999' -> Must trigger fallback."""
    valid_id = mock_investigation_package.primary_evidence[0].evidence_id
    json_str = f"""{{
        "classification": "SUSPICIOUS_ENTITY_FARM",
        "recommended_action": "STEP_UP",
        "action_rationale": "Unknown counter signal evidence.",
        "primary_reason": "Counter signal flaw",
        "findings": [{{"claim": "Valid finding", "evidence_ids": ["{valid_id}"], "confidence": 0.90}}],
        "counter_signals": [{{"claim": "Counter claim", "evidence_ids": ["E-9999"], "impact_on_hypothesis": "ATTENUATES_RISK"}}]
    }}"""
    provider = build_mock_gemini_provider(json_str)
    result = provider.generate_investigation_reasoning(mock_investigation_package, {})

    assert (
        result["llm_provenance"].reasoning_mode
        == ReasoningMode.DETERMINISTIC_RULE_BASED
    )
    assert result["llm_provenance"].provider_type == ProviderType.DETERMINISTIC_FALLBACK


def test_output_validator_direct_rejection(mock_investigation_package):
    """Directly verifies AgentOutputValidator raises EvidenceVerificationError on ungrounded claims."""
    raw_bad_result = {
        "agent_run_id": "RUN-test-001",
        "investigation_id": "INV-test-001",
        "package_id": mock_investigation_package.package_id,
        "evidence_snapshot_hash": mock_investigation_package.evidence_snapshot_hash,
        "created_at": time.time(),
        "classification": "LIKELY_COORDINATED_FRAUD",
        "confidence": 0.90,
        "confidence_decomposition": {
            "completeness": 0.9,
            "consistency": 0.9,
            "pattern_agreement": 0.9,
            "counter_signal_strength": 0.1,
            "final_confidence": 0.9,
        },
        "findings": [
            {
                "claim": "Ungrounded claim",
                "evidence_ids": ["E-9999"],
                "confidence": 0.9,
                "verified": True,
            }
        ],
        "counter_signals": [],
        "risk_interpretation": {
            "severity": "HIGH",
            "primary_reason": "Test",
            "pattern_interaction_summary": "Test",
        },
        "adversarial_analysis": "No prompt manipulation detected. Strict grounding enforced.",
        "recommended_action": "HOLD",
        "action_rationale": "Test",
        "llm_provenance": {
            "provider_type": "GEMINI",
            "reasoning_mode": "AGENTIC_LLM",
            "model_name": "gemini-3.6-flash",
            "agent_graph_version": "v0.3.0",
            "prompt_version": "v2.1",
            "output_schema_version": "v1",
            "execution_time_ms": 10.0,
            "token_usage": {
                "prompt_tokens": 10,
                "completion_tokens": 10,
                "total_tokens": 20,
            },
        },
    }

    with pytest.raises(EvidenceVerificationError) as exc_info:
        AgentOutputValidator.validate_and_ground_result(
            raw_bad_result, mock_investigation_package
        )

    assert "E-9999" in str(exc_info.value)
