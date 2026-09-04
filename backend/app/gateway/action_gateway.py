"""
RazorShield AI — Action Gateway & Synthetic State Machine Execution Engine
Enforces fail-closed token verification, thread-safe single-use nonce lock (_nonce_lock / Redis adapter),
idempotent execution (ALREADY_EXECUTED), and synthetic transaction state transitions.
"""

import threading
import time
from typing import Any, Dict, Optional, Set

from backend.app.domain.policy_contracts import (
    ActionResult,
    ActionToken,
    PolicyAction,
    TokenStatus,
    TransactionState,
)
from backend.app.exceptions import RazorShieldError
from backend.app.gateway.outcome_verifier import OutcomeVerifier
from backend.app.policy.action_token import ActionTokenGenerator


class ActionGatewayReplayError(RazorShieldError):
    """Raised when an ActionToken nonce has already been consumed (Replay Attack Defense)."""

    def __init__(self, nonce: str):
        super().__init__(
            message=f"Action Gateway Security Failure: Nonce '{nonce}' has already been consumed. Replay attack detected.",
            status_code=409,
            error_code="ACTION_NONCE_REPLAYED",
            details={"nonce": nonce},
        )


class ActionGateway:
    """Fail-Closed Execution Gateway with Thread-Safe Single-Use Nonce Lock and Synthetic State Machine."""

    _nonce_lock = threading.Lock()
    _consumed_nonces: Set[str] = set()
    _executed_actions_registry: Dict[str, ActionResult] = {}
    _synthetic_transaction_states: Dict[str, TransactionState] = {}

    @classmethod
    def reset_gateway_state(cls) -> None:
        """Helper to clear in-memory registries for isolated unit testing."""
        with cls._nonce_lock:
            cls._consumed_nonces.clear()
            cls._executed_actions_registry.clear()
            cls._synthetic_transaction_states.clear()

    @classmethod
    def execute_action_token(
        cls,
        token: ActionToken,
        active_policy_version: str = "v1.0",
        current_snapshot_hash: str = "",
        expected_version_token: str = "",
        audit_logger: Optional[Any] = None,
    ) -> ActionResult:
        """
        Executes ActionToken under strict fail-closed security invariants:
        1. Check Idempotency (if action_id already executed -> return ALREADY_EXECUTED).
        2. Thread-safe Single-Use Nonce Lock.
        3. Verify Token HMAC signature, TTL, Policy Version, Snapshot Hash, and Version Token.
        4. Execute Synthetic Transaction State Transition.
        5. Perform Post-Execution Outcome Verification.
        """
        t0 = time.perf_counter()

        # 1. Idempotency Check
        if token.action_id in cls._executed_actions_registry:
            existing_res = cls._executed_actions_registry[token.action_id]
            return ActionResult(
                action_id=existing_res.action_id,
                transaction_id=existing_res.transaction_id,
                investigation_id=existing_res.investigation_id,
                policy_decision_id=existing_res.policy_decision_id,
                requested_action=existing_res.requested_action,
                executed_action=existing_res.executed_action,
                status=TokenStatus.ALREADY_EXECUTED,
                previous_state=existing_res.previous_state,
                new_state=existing_res.new_state,
                observed_outcome=existing_res.observed_outcome,
                verified=True,
                execution_time_ms=round((time.perf_counter() - t0) * 1000.0, 2),
                executed_at=time.time(),
            )

        # 2. Atomic Nonce Lock (Replay Defense)
        with cls._nonce_lock:
            if token.nonce in cls._consumed_nonces:
                raise ActionGatewayReplayError(nonce=token.nonce)
            cls._consumed_nonces.add(token.nonce)

        # 3. Fail-Closed Token Verification
        try:
            ActionTokenGenerator.verify_action_token(
                token=token,
                active_policy_version=active_policy_version,
                current_snapshot_hash=current_snapshot_hash
                or token.evidence_snapshot_hash,
                expected_version_token=expected_version_token,
            )
        except Exception as exc:
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return ActionResult(
                action_id=token.action_id,
                transaction_id=token.transaction_id,
                investigation_id=token.investigation_id,
                policy_decision_id=token.policy_decision_id,
                requested_action=token.action,
                executed_action=token.action,
                status=TokenStatus.REJECTED,
                previous_state=TransactionState.PENDING,
                new_state=TransactionState.PENDING,
                observed_outcome=f"FAIL_CLOSED_REJECTED: {str(exc)}",
                verified=False,
                execution_time_ms=dt_ms,
                executed_at=time.time(),
            )

        # 4. Synthetic State Transition Execution
        prev_state = cls._synthetic_transaction_states.get(
            token.transaction_id, TransactionState.PENDING
        )
        new_state = cls._map_action_to_state(token.action)
        cls._synthetic_transaction_states[token.transaction_id] = new_state

        # 5. Outcome Verification
        verified = OutcomeVerifier.verify_outcome(
            requested_action=token.action,
            observed_state=new_state,
        )

        dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        result = ActionResult(
            action_id=token.action_id,
            transaction_id=token.transaction_id,
            investigation_id=token.investigation_id,
            policy_decision_id=token.policy_decision_id,
            requested_action=token.action,
            executed_action=token.action,
            status=TokenStatus.EXECUTED,
            previous_state=prev_state,
            new_state=new_state,
            observed_outcome=f"TRANSACTION_{new_state.value}",
            verified=verified,
            execution_time_ms=dt_ms,
            executed_at=time.time(),
        )

        cls._executed_actions_registry[token.action_id] = result

        # Log audit entry if audit_logger available
        if audit_logger:
            if hasattr(audit_logger, "log_action_execution"):
                audit_logger.log_action_execution(result)
            elif hasattr(audit_logger, "append_event"):
                from backend.app.policy.audit import ControlPlaneAuditLogger

                cp_logger = ControlPlaneAuditLogger(audit_logger)
                cp_logger.log_action_execution(result)

        return result

    @staticmethod
    def _map_action_to_state(action: PolicyAction) -> TransactionState:
        if action == PolicyAction.ALLOW:
            return TransactionState.AUTHORIZED
        elif action == PolicyAction.MONITOR:
            return TransactionState.MONITORED
        elif action == PolicyAction.STEP_UP:
            return TransactionState.STEP_UP_REQUIRED
        elif action == PolicyAction.HOLD:
            return TransactionState.HELD
        elif action == PolicyAction.BLOCK:
            return TransactionState.BLOCKED
        return TransactionState.PENDING
