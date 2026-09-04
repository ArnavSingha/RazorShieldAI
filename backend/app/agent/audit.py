"""
RazorShield AI — Agent Run Cryptographic Audit Logger
Appends agent execution runs, state transitions, tool call metadata, and final findings
to the cryptographic HMAC audit ledger.
"""

import time
from typing import Any

from backend.app.domain.agent_contracts import AgentInvestigationResult
from backend.app.domain.models import RiskDecision


class AgentAuditLogger:
    """Logs agent runs into the cryptographic audit ledger."""

    def __init__(self, audit_store: Any):
        self.audit_store = audit_store

    def log_agent_run(
        self,
        agent_run_id: str,
        package_id: str,
        result: AgentInvestigationResult,
        state_transitions: list[str],
        tool_calls: list[str],
    ) -> str:
        record_payload = {
            "agent_run_id": agent_run_id,
            "package_id": package_id,
            "investigation_id": result.investigation_id,
            "classification": result.classification.value,
            "confidence": result.confidence,
            "recommended_action": result.recommended_action.value,
            "provider_type": result.llm_provenance.provider_type.value,
            "reasoning_mode": result.llm_provenance.reasoning_mode.value,
            "agent_graph_version": result.agent_graph_version,
            "prompt_version": result.prompt_version,
            "output_schema_version": result.output_schema_version,
            "budget_status": result.budget_status,
            "state_transitions": state_transitions,
            "tool_calls": tool_calls,
            "finding_count": len(result.findings),
            "counter_signal_count": len(result.counter_signals),
            "execution_time_ms": result.llm_provenance.execution_time_ms,
            "timestamp": time.time(),
        }

        if hasattr(self.audit_store, "append_event"):
            entry = self.audit_store.append_event(
                decision_id=agent_run_id,
                transaction_id=result.investigation_id,
                payload_dict=record_payload,
            )
        elif hasattr(self.audit_store, "append_decision_audit"):
            dummy_dec = RiskDecision(
                decision_id=agent_run_id,
                transaction_id=result.investigation_id,
                risk_score=int(result.confidence * 100),
                risk_level=result.risk_interpretation.severity
                if result.risk_interpretation.severity
                in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
                else "HIGH",  # type: ignore
                decision=result.recommended_action.value
                if result.recommended_action.value
                in ("ALLOW", "MONITOR", "STEP_UP", "HOLD", "BLOCK")
                else "HOLD",  # type: ignore
                confidence=result.confidence,
                components={"agent": {"confidence": result.confidence}},
                reason_codes=[f"AGENT_{result.classification.value}"],
                contributing_signals=[],
                degraded_mode="NONE",
                latency_ms=result.llm_provenance.execution_time_ms,
                created_at=time.time(),
                request_id="",
                correlation_id="",
            )
            entry = self.audit_store.append_decision_audit(dummy_dec)
        else:
            return ""

        if isinstance(entry, dict):
            return str(entry.get("current_hash", ""))
        return ""
