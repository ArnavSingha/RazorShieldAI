"""
RazorShield AI — Slice 4 Control Plane & Policy Domain Contracts
Defines versioned, immutable Pydantic schemas for Roles, Policy Actions, Action Tokens,
Human Approval Bindings, Policy Decisions, and Action Gateway Results.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    READ_ONLY = "READ_ONLY"
    RISK_ANALYST = "RISK_ANALYST"
    MERCHANT_OPERATOR = "MERCHANT_OPERATOR"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    MONITOR = "MONITOR"
    STEP_UP = "STEP_UP"
    HOLD = "HOLD"
    BLOCK = "BLOCK"


class TokenStatus(str, Enum):
    ISSUED = "ISSUED"
    EXECUTED = "EXECUTED"
    ALREADY_EXECUTED = "ALREADY_EXECUTED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    INVALID = "INVALID"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class TransactionState(str, Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    MONITORED = "MONITORED"
    STEP_UP_REQUIRED = "STEP_UP_REQUIRED"
    HELD = "HELD"
    BLOCKED = "BLOCKED"


class HumanApprovalBinding(BaseModel):
    approval_id: str = Field(
        default_factory=lambda: f"APP-{uuid.uuid4().hex[:8].upper()}"
    )
    action_id: str
    investigation_id: str
    transaction_id: str
    policy_decision_id: str
    evidence_snapshot_hash: str
    approver_principal_id: str
    approver_role: UserRole
    approval_timestamp: float = Field(default_factory=time.time)
    approval_signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanApprovalBinding":
        return cls.model_validate(data)


class PolicyDecision(BaseModel):
    policy_decision_id: str = Field(
        default_factory=lambda: f"POL-{uuid.uuid4().hex[:8].upper()}"
    )
    policy_version: str = "v1.0"
    investigation_id: str
    transaction_id: str
    ai_recommendation: PolicyAction
    final_action: PolicyAction
    overridden: bool = False
    override_reason_codes: List[str] = Field(default_factory=list)
    explanation_summary: str
    requires_human_approval: bool = False
    approval_binding: Optional[HumanApprovalBinding] = None
    created_at: float = Field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyDecision":
        return cls.model_validate(data)


class ActionToken(BaseModel):
    token_version: str = "v1.0"
    action_id: str = Field(
        default_factory=lambda: f"ACT-{uuid.uuid4().hex[:8].upper()}"
    )
    transaction_id: str
    investigation_id: str
    policy_decision_id: str
    principal_id: str
    action: PolicyAction
    issued_at: float = Field(default_factory=time.time)
    expires_at: float
    policy_version: str = "v1.0"
    evidence_snapshot_hash: str
    version_token: str = ""
    authorized_role: UserRole
    action_hash: str
    nonce: str = Field(default_factory=lambda: uuid.uuid4().hex)
    hmac_signature: str = ""

    @property
    def token_id(self) -> str:
        return self.action_id

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionToken":
        return cls.model_validate(data)


class ActionResult(BaseModel):
    action_id: str
    transaction_id: str
    investigation_id: str
    policy_decision_id: str
    requested_action: PolicyAction
    executed_action: PolicyAction
    status: TokenStatus
    previous_state: TransactionState
    new_state: TransactionState
    observed_outcome: str
    verified: bool
    execution_time_ms: float
    executed_at: float = Field(default_factory=time.time)
    audit_chain_tip_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionResult":
        return cls.model_validate(data)
