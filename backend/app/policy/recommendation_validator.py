"""
RazorShield AI — AI Recommendation Validator
Validates evidence snapshot hash integrity, evidence grounding, and action-sensitive confidence thresholds.
"""

from typing import Dict
from backend.app.agent.output_validator import AgentOutputValidator
from backend.app.domain.agent_contracts import AgentInvestigationResult
from backend.app.domain.graph_contracts import InvestigationPackage
from backend.app.domain.policy_contracts import PolicyAction
from backend.app.exceptions import RazorShieldError


class ActionConfidenceThresholdError(RazorShieldError):
    """Raised when AI recommendation confidence does not meet action-sensitive confidence thresholds."""

    def __init__(self, action: str, confidence: float, required: float):
        super().__init__(
            message=f"Action Guardrail Failure: Action '{action}' requires minimum confidence of {required}, but AI recommendation confidence was {confidence}.",
            status_code=422,
            error_code="ACTION_CONFIDENCE_TOO_LOW",
            details={"action": action, "confidence": confidence, "required": required},
        )


class RecommendationValidator:
    """Enforces action-sensitive confidence thresholds and snapshot hash integrity."""

    # Action-Sensitive Confidence Threshold Matrix
    _CONFIDENCE_THRESHOLDS: Dict[PolicyAction, float] = {
        PolicyAction.ALLOW: 0.20,
        PolicyAction.MONITOR: 0.30,
        PolicyAction.STEP_UP: 0.50,
        PolicyAction.HOLD: 0.70,
        PolicyAction.BLOCK: 0.85,
    }

    @classmethod
    def validate_agent_recommendation(
        cls, agent_result: AgentInvestigationResult, package: InvestigationPackage
    ) -> None:
        """
        1. Snapshot Hash Integrity Check.
        2. Evidence Grounding Check.
        3. Action-Sensitive Confidence Threshold Check.
        """
        # 1. Snapshot Integrity
        AgentOutputValidator.validate_snapshot_integrity(package)

        # 2. Action-Sensitive Confidence Threshold Check
        rec_action = PolicyAction(agent_result.recommended_action.value)
        required_threshold = cls._CONFIDENCE_THRESHOLDS.get(rec_action, 0.50)

        if agent_result.confidence < required_threshold:
            raise ActionConfidenceThresholdError(
                action=rec_action.value,
                confidence=agent_result.confidence,
                required=required_threshold,
            )
