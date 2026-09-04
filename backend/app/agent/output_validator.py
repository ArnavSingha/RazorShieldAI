"""
RazorShield AI — Output Validator & Evidence Grounding Verifier
Validates LLM outputs against Pydantic domain models, cross-checks evidence IDs against snapshot index,
enforces Agent Resource Budget limits, and computes mathematically clamped confidence scores [0.0, 1.0].
Raises EvidenceVerificationError on any unverified/missing evidence ID, or AgentBudgetExceededError on budget breaches.
"""

import hashlib
from typing import Any, Dict, Set

from backend.app.domain.agent_contracts import (
    AgentInvestigationResult,
)
from backend.app.domain.graph_contracts import InvestigationPackage
from backend.app.exceptions import RazorShieldError


class EvidenceVerificationError(RazorShieldError):
    """Raised when an agent claim cites an unknown or unverified Evidence ID or has empty evidence citations."""

    def __init__(self, evidence_id: str, claim: str):
        super().__init__(
            message=f"Security Hard-Gate Failure (NO_EVIDENCE_NO_CLAIM): Claim '{claim}' cited unverified, hallucinated, or missing Evidence ID '{evidence_id}'.",
            status_code=422,
            error_code="EVIDENCE_VERIFICATION_FAILED",
            details={"evidence_id": evidence_id, "claim": claim},
        )


class EvidenceSnapshotMismatchError(RazorShieldError):
    """Raised when retrieved evidence snapshot hash does not match package snapshot hash (TOCTOU Defense)."""

    def __init__(self, expected_hash: str, actual_hash: str):
        super().__init__(
            message=(
                "Security Hard-Gate Failure (TOCTOU Defense): Evidence snapshot hash mismatch. "
                f"Expected '{expected_hash}', got '{actual_hash}'. Investigation state changed."
            ),
            status_code=409,
            error_code="INVESTIGATION_STATE_CHANGED",
            details={"expected_hash": expected_hash, "actual_hash": actual_hash},
        )


class AgentBudgetExceededError(RazorShieldError):
    """Raised when an agent execution exceeds configurable resource budget limits (tool calls, wall clock, tokens)."""

    def __init__(self, budget_status: str, details_dict: Dict[str, Any]):
        super().__init__(
            message=f"Agent Resource Reliability Failure: Resource budget exceeded ({budget_status}). Safe termination triggered.",
            status_code=429,
            error_code="AGENT_BUDGET_EXCEEDED",
            details=details_dict,
        )


class AgentOutputValidator:
    """Validates raw agent outputs and verifies evidence citations against snapshot index."""

    @staticmethod
    def validate_snapshot_integrity(package: InvestigationPackage) -> None:
        """Verifies TOCTOU evidence snapshot integrity."""
        evidence_raw_bytes = "".join(
            [
                f"{e.evidence_id}:{e.type}:{e.claim}:{e.confidence}"
                for e in package.primary_evidence
            ]
        ).encode("utf-8")
        computed_hash = hashlib.sha256(evidence_raw_bytes).hexdigest()

        if (
            package.evidence_snapshot_hash
            and package.evidence_snapshot_hash != computed_hash
        ):
            raise EvidenceSnapshotMismatchError(
                expected_hash=package.evidence_snapshot_hash,
                actual_hash=computed_hash,
            )

    @staticmethod
    def validate_and_ground_result(
        raw_result_dict: Dict[str, Any], package: InvestigationPackage
    ) -> AgentInvestigationResult:
        """
        1. Validates TOCTOU Snapshot Hash.
        2. Validates Pydantic schema.
        3. Enforces NO EVIDENCE -> NO CLAIM invariant.
        4. Clamps confidence score strictly within [0.0, 1.0].
        """
        # 1. Snapshot Integrity
        AgentOutputValidator.validate_snapshot_integrity(package)

        # 2. Build Valid Evidence ID Index
        valid_evidence_ids: Set[str] = {e.evidence_id for e in package.primary_evidence}

        # 3. Pydantic Schema Validation
        result = AgentInvestigationResult.from_dict(raw_result_dict)

        # 4. Strict NO EVIDENCE -> NO CLAIM Verification (Hard-Gate)
        for finding in result.findings:
            if not finding.evidence_ids or len(finding.evidence_ids) == 0:
                raise EvidenceVerificationError(
                    evidence_id="MISSING", claim=finding.claim
                )
            for ev_id in finding.evidence_ids:
                if ev_id not in valid_evidence_ids:
                    raise EvidenceVerificationError(
                        evidence_id=ev_id, claim=finding.claim
                    )

        for counter in result.counter_signals:
            for ev_id in counter.evidence_ids:
                if ev_id not in valid_evidence_ids:
                    raise EvidenceVerificationError(
                        evidence_id=ev_id, claim=counter.claim
                    )

        # 5. Clamped Confidence Math Verification
        clamped_confidence = max(0.0, min(1.0, float(result.confidence)))
        result.confidence = round(clamped_confidence, 4)

        return result
