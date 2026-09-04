"""
RazorShield AI — Control Plane Cryptographic Audit Logger
Appends policy decisions, human approvals, action tokens, and execution outcomes
to the cryptographic HMAC audit ledger.
"""

import time
from typing import Any

from backend.app.domain.policy_contracts import ActionResult, PolicyDecision


class ControlPlaneAuditLogger:
    """Appends control plane events to the HMAC audit ledger."""

    def __init__(self, audit_store: Any):
        self.audit_store = audit_store

    def log_policy_decision(self, decision: PolicyDecision, principal_id: str) -> str:
        record_payload = {
            "policy_decision_id": decision.policy_decision_id,
            "policy_version": decision.policy_version,
            "investigation_id": decision.investigation_id,
            "transaction_id": decision.transaction_id,
            "principal_id": principal_id,
            "ai_recommendation": decision.ai_recommendation.value,
            "final_action": decision.final_action.value,
            "overridden": decision.overridden,
            "override_reason_codes": decision.override_reason_codes,
            "explanation_summary": decision.explanation_summary,
            "requires_human_approval": decision.requires_human_approval,
            "timestamp": time.time(),
        }
        if hasattr(self.audit_store, "append_event"):
            entry = self.audit_store.append_event(
                decision_id=decision.policy_decision_id,
                transaction_id=decision.transaction_id,
                payload_dict=record_payload,
            )
            return str(entry.get("current_hash", ""))
        return ""

    def log_action_execution(self, result: ActionResult) -> str:
        record_payload = {
            "action_id": result.action_id,
            "transaction_id": result.transaction_id,
            "investigation_id": result.investigation_id,
            "policy_decision_id": result.policy_decision_id,
            "requested_action": result.requested_action.value,
            "executed_action": result.executed_action.value,
            "status": result.status.value,
            "previous_state": result.previous_state.value,
            "new_state": result.new_state.value,
            "observed_outcome": result.observed_outcome,
            "verified": result.verified,
            "execution_time_ms": result.execution_time_ms,
            "timestamp": time.time(),
        }
        if hasattr(self.audit_store, "append_event"):
            entry = self.audit_store.append_event(
                decision_id=result.action_id,
                transaction_id=result.transaction_id,
                payload_dict=record_payload,
            )
            tip_hash = str(entry.get("current_hash", ""))
            result.audit_chain_tip_hash = tip_hash
            return tip_hash
        return ""
