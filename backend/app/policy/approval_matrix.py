"""
RazorShield AI — Human Approval Matrix & Cryptographic Binding
Generates and verifies cryptographic approval bindings for high-impact actions (HOLD / BLOCK).
Replaying or tampering with human approvals across different actions triggers ApprovalBindingMismatchError.
"""

import hashlib
import hmac
import time
from backend.app.config import settings
from backend.app.domain.policy_contracts import (
    HumanApprovalBinding,
    PolicyDecision,
    UserRole,
)
from backend.app.exceptions import RazorShieldError
from backend.app.policy.rbac import TrustedPrincipal, UnauthorizedRoleError


class ApprovalBindingMismatchError(RazorShieldError):
    """Raised when a human approval binding signature fails or is replayed for a different action."""

    def __init__(self, message: str, details_dict: dict):
        super().__init__(
            message=f"Human Approval Binding Security Violation: {message}",
            status_code=409,
            error_code="APPROVAL_BINDING_MISMATCH",
            details=details_dict,
        )


class HumanApprovalMatrix:
    """Manages cryptographic binding and verification of human analyst approvals."""

    SECRET_KEY: bytes = settings.audit_hmac_secret.encode("utf-8")

    @classmethod
    def create_approval_binding(
        cls,
        action_id: str,
        decision: PolicyDecision,
        evidence_snapshot_hash: str,
        approver: TrustedPrincipal,
    ) -> HumanApprovalBinding:
        """
        Creates an HMAC-SHA256 signed HumanApprovalBinding bound to:
        action_id, investigation_id, transaction_id, policy_decision_id, evidence_snapshot_hash, approver_principal_id, approval_timestamp.
        """
        if approver.role not in (UserRole.RISK_ANALYST, UserRole.ADMIN):
            raise UnauthorizedRoleError(
                principal_id=approver.principal_id,
                role=approver.role.value,
                action=f"APPROVE_{decision.final_action.value}",
            )

        t_now = time.time()
        binding = HumanApprovalBinding(
            action_id=action_id,
            investigation_id=decision.investigation_id,
            transaction_id=decision.transaction_id,
            policy_decision_id=decision.policy_decision_id,
            evidence_snapshot_hash=evidence_snapshot_hash,
            approver_principal_id=approver.principal_id,
            approver_role=approver.role,
            approval_timestamp=t_now,
        )

        sig_input = f"{binding.approval_id}:{action_id}:{decision.investigation_id}:{decision.transaction_id}:{decision.policy_decision_id}:{evidence_snapshot_hash}:{approver.principal_id}:{t_now}".encode(
            "utf-8"
        )
        sig = hmac.new(cls.SECRET_KEY, sig_input, hashlib.sha256).hexdigest()
        binding.approval_signature = sig
        return binding

    @classmethod
    def verify_approval_binding(
        cls,
        binding: HumanApprovalBinding,
        target_action_id: str,
        target_decision: PolicyDecision,
        current_snapshot_hash: str,
    ) -> None:
        """Verifies that human approval signature is valid and strictly matches target action context."""
        # 1. Context Match Verification
        if binding.action_id != target_action_id:
            raise ApprovalBindingMismatchError(
                f"Action ID mismatch: approval bound to '{binding.action_id}', target is '{target_action_id}'.",
                {"bound_action": binding.action_id, "target_action": target_action_id},
            )

        if binding.investigation_id != target_decision.investigation_id:
            raise ApprovalBindingMismatchError(
                f"Investigation ID mismatch: approval bound to '{binding.investigation_id}', target is '{target_decision.investigation_id}'.",
                {
                    "bound_inv": binding.investigation_id,
                    "target_inv": target_decision.investigation_id,
                },
            )

        if binding.evidence_snapshot_hash != current_snapshot_hash:
            raise ApprovalBindingMismatchError(
                "Stale evidence snapshot: approval bound to different snapshot hash.",
                {
                    "bound_hash": binding.evidence_snapshot_hash,
                    "current_hash": current_snapshot_hash,
                },
            )

        # 2. HMAC Signature Verification
        sig_input = f"{binding.approval_id}:{binding.action_id}:{binding.investigation_id}:{binding.transaction_id}:{binding.policy_decision_id}:{binding.evidence_snapshot_hash}:{binding.approver_principal_id}:{binding.approval_timestamp}".encode(
            "utf-8"
        )
        calc_sig = hmac.new(cls.SECRET_KEY, sig_input, hashlib.sha256).hexdigest()

        if calc_sig != binding.approval_signature:
            raise ApprovalBindingMismatchError(
                "Invalid approval HMAC signature. Approval payload has been tampered with.",
                {"expected_sig": calc_sig, "actual_sig": binding.approval_signature},
            )
