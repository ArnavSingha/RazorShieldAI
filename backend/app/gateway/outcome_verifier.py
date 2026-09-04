"""
RazorShield AI — Outcome Verifier
Verifies post-execution transaction state transitions match requested policy actions.
Raises ActionVerificationError if observed outcome diverges from requested action.
"""

from backend.app.domain.policy_contracts import PolicyAction, TransactionState
from backend.app.exceptions import RazorShieldError


class ActionVerificationError(RazorShieldError):
    """Raised when observed outcome state transition diverges from requested policy action."""

    def __init__(self, requested_action: str, observed_state: str):
        super().__init__(
            message=f"Outcome Verification Failure: Requested action '{requested_action}' did not result in expected state (observed: '{observed_state}').",
            status_code=500,
            error_code="ACTION_VERIFICATION_FAILED",
            details={
                "requested_action": requested_action,
                "observed_state": observed_state,
            },
        )


class OutcomeVerifier:
    """Verifies that executed action matches observed synthetic transaction state."""

    @classmethod
    def verify_outcome(
        cls, requested_action: PolicyAction, observed_state: TransactionState
    ) -> bool:
        """Verifies state transition mapping."""
        expected_state_map = {
            PolicyAction.ALLOW: TransactionState.AUTHORIZED,
            PolicyAction.MONITOR: TransactionState.MONITORED,
            PolicyAction.STEP_UP: TransactionState.STEP_UP_REQUIRED,
            PolicyAction.HOLD: TransactionState.HELD,
            PolicyAction.BLOCK: TransactionState.BLOCKED,
        }
        expected = expected_state_map.get(requested_action)

        if expected != observed_state:
            raise ActionVerificationError(
                requested_action=requested_action.value,
                observed_state=observed_state.value,
            )
        return True
