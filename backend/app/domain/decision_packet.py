"""
RazorShield AI — Unified DecisionPacket Domain Model & Provenance Contract
Server-side assembled authoritative object containing complete case, transaction, risk, evidence,
AI provenance, policy decision, approval state, single-use action token, and deterministic version token.
"""

import hashlib
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class DecisionPacket(BaseModel):
    version_token: str = Field(
        description="Deterministic SHA-256 hash of case state + evidence snapshot"
    )
    case: Dict[str, Any] = Field(
        description="Incident status, owner, priority, severity, created_at, SLA"
    )
    transaction: Dict[str, Any] = Field(
        description="Transaction event details and amount exposure"
    )
    risk: Dict[str, Any] = Field(
        description="Composite risk score, risk level, confidence, contributing signals"
    )
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list, description="Primary deterministic evidence items"
    )
    graph_context: Dict[str, Any] = Field(
        default_factory=dict, description="Nodes, edges, cluster density, patterns"
    )
    ai: Dict[str, Any] = Field(
        default_factory=dict,
        description="LLM provider, model, recommendation, confidence, conflict alert",
    )
    policy: Dict[str, Any] = Field(
        default_factory=dict,
        description="Deterministic policy decision, reason codes, explanation",
    )
    approval: Dict[str, Any] = Field(
        default_factory=dict,
        description="Required approval level, dual control, approver roles",
    )
    action: Dict[str, Any] = Field(
        default_factory=dict,
        description="Single-use ActionToken, granted_action, target, expected_effect",
    )
    freshness: Dict[str, Any] = Field(
        default_factory=dict,
        description="Last confirmed timestamp, data_mode, is_stale",
    )
    actor: Dict[str, Any] = Field(
        default_factory=dict, description="Evaluating principal ID and role"
    )
    audit: Dict[str, Any] = Field(
        default_factory=dict,
        description="Correlation ID, request ID, audit ledger tip hash",
    )

    @classmethod
    def compute_version_token(
        cls,
        investigation_id: str,
        updated_at: float,
        evidence_snapshot_hash: str,
        risk_score: int,
        status: str,
    ) -> str:
        payload = f"{investigation_id}:{updated_at:.4f}:{evidence_snapshot_hash}:{risk_score}:{status}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionPacket":
        return cls.model_validate(data)
