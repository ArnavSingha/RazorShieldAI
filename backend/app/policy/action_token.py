"""
RazorShield AI — Signed Action Token Generator & Verifier
Generates and verifies HMAC-SHA256 signed ActionTokens with 300s TTL, policy version binding,
and single-use nonces.
"""

import hashlib
import hmac
import json
import time
import uuid

from backend.app.config import settings
from backend.app.domain.policy_contracts import ActionToken, PolicyDecision
from backend.app.exceptions import RazorShieldError
from backend.app.policy.rbac import TrustedPrincipal


class ActionTokenVerificationError(RazorShieldError):
    """Raised when ActionToken signature is invalid, expired, or tampered with."""

    def __init__(self, message: str, details_dict: dict):
        super().__init__(
            message=f"Action Token Security Failure: {message}",
            status_code=401,
            error_code="ACTION_TOKEN_VERIFICATION_FAILED",
            details=details_dict,
        )


class ActionTokenGenerator:
    """Issues and verifies HMAC-SHA256 signed ActionTokens."""

    SECRET_KEY: bytes = settings.audit_hmac_secret.encode("utf-8")
    DEFAULT_TTL_SECONDS: float = 300.0  # 5 Minutes

    @classmethod
    def issue_action_token(
        cls,
        decision: PolicyDecision,
        evidence_snapshot_hash: str,
        principal: TrustedPrincipal,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        version_token: str = "",
    ) -> ActionToken:
        t_now = time.time()
        t_exp = t_now + ttl_seconds
        act_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"

        # Action Hash (SHA256 over action string and transaction ID)
        act_hash = hashlib.sha256(
            f"{decision.final_action.value}:{decision.transaction_id}".encode("utf-8")
        ).hexdigest()

        token = ActionToken(
            token_version="v1.0",
            action_id=act_id,
            transaction_id=decision.transaction_id,
            investigation_id=decision.investigation_id,
            policy_decision_id=decision.policy_decision_id,
            principal_id=principal.principal_id,
            action=decision.final_action,
            issued_at=t_now,
            expires_at=t_exp,
            policy_version=decision.policy_version,
            evidence_snapshot_hash=evidence_snapshot_hash,
            version_token=version_token,
            authorized_role=principal.role,
            action_hash=act_hash,
            nonce=uuid.uuid4().hex,
        )

        token.hmac_signature = cls.compute_token_signature(token)
        return token

    @classmethod
    def compute_token_signature(cls, token: ActionToken) -> str:
        """Computes HMAC-SHA256 signature over canonical token dictionary (excluding hmac_signature)."""
        raw_dict = token.model_dump()
        raw_dict["hmac_signature"] = ""
        canonical_bytes = json.dumps(raw_dict, sort_keys=True).encode("utf-8")
        return hmac.new(cls.SECRET_KEY, canonical_bytes, hashlib.sha256).hexdigest()

    @classmethod
    def verify_action_token(
        cls,
        token: ActionToken,
        active_policy_version: str = "v1.0",
        current_snapshot_hash: str = "",
        expected_version_token: str = "",
    ) -> None:
        """
        1. HMAC Signature Verification.
        2. TTL Expiration Check.
        3. Policy Version Match Check.
        4. Stale Snapshot Check.
        5. Version Token Match Check.
        """
        # 1. Signature Verification
        calc_sig = cls.compute_token_signature(token)
        if calc_sig != token.hmac_signature:
            raise ActionTokenVerificationError(
                "HMAC signature invalid. Action token has been tampered with.",
                {"expected_sig": calc_sig, "actual_sig": token.hmac_signature},
            )

        # 2. Expiration Check
        t_now = time.time()
        if t_now > token.expires_at:
            raise ActionTokenVerificationError(
                f"Action token expired at {token.expires_at} (current time: {t_now}).",
                {
                    "issued_at": token.issued_at,
                    "expires_at": token.expires_at,
                    "current_time": t_now,
                },
            )

        # 3. Policy Version Binding Check
        if active_policy_version and token.policy_version != active_policy_version:
            raise ActionTokenVerificationError(
                f"Policy version mismatch: token issued under '{token.policy_version}', active policy is '{active_policy_version}'.",
                {
                    "token_policy_version": token.policy_version,
                    "active_policy_version": active_policy_version,
                },
            )

        # 4. Snapshot Hash Matching Check
        if (
            current_snapshot_hash
            and token.evidence_snapshot_hash != current_snapshot_hash
        ):
            raise ActionTokenVerificationError(
                "Stale evidence snapshot: token evidence snapshot hash mismatch.",
                {
                    "token_snapshot_hash": token.evidence_snapshot_hash,
                    "current_snapshot_hash": current_snapshot_hash,
                },
            )

        # 5. Version Token Check
        if (
            expected_version_token
            and token.version_token
            and token.version_token != expected_version_token
        ):
            from backend.app.exceptions import RazorShieldError

            raise RazorShieldError(
                message=f"Stale DecisionPacket detected: version token '{token.version_token}' does not match expected '{expected_version_token}'. Execution aborted.",
                status_code=409,
                error_code="STALE_DECISION_PACKET",
                details={
                    "token_version": token.version_token,
                    "expected_version": expected_version_token,
                },
            )
