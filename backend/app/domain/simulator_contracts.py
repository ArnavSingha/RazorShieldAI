"""
RazorShield AI — Slice 5 Simulator & Chaos Domain Contracts
Defines Pydantic models for Threat Scenarios, Chaos Fault Toggles, Simulator Modes,
and Measurement-Driven Attack Replay Reports.
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.domain.policy_contracts import PolicyAction, TokenStatus


class ThreatScenarioType(str, Enum):
    ATO_001 = "ATO-001"
    CARD_TESTING_002 = "CARD_TESTING-002"
    MULE_RING_003 = "MULE_RING-003"
    VELOCITY_004 = "VELOCITY-004"
    SHARED_DEVICE_005 = "SHARED_DEVICE-005"
    CROSS_BORDER_006 = "CROSS_BORDER-006"
    MERCHANT_COMPROMISE_007 = "MERCHANT_COMPROMISE-007"


class ChaosFaultType(str, Enum):
    GEMINI_OFFLINE = "GEMINI_OFFLINE"
    ML_OFFLINE = "ML_OFFLINE"
    GRAPH_OFFLINE = "GRAPH_OFFLINE"
    REDIS_OFFLINE = "REDIS_OFFLINE"
    POSTGRES_OFFLINE = "POSTGRES_OFFLINE"
    AUDIT_OFFLINE = "AUDIT_OFFLINE"
    GATEWAY_OFFLINE = "GATEWAY_OFFLINE"


class SimulatorMode(str, Enum):
    PRODUCTION_SIMULATION = "PRODUCTION_SIMULATION"
    LOCAL_STANDALONE = "LOCAL_STANDALONE"


class ScenarioConfig(BaseModel):
    scenario_type: ThreatScenarioType
    seed: int = 1001
    event_count: int = 10
    customer_id: str = ""
    merchant_id: str = "merch_5732"
    mode: SimulatorMode = SimulatorMode.PRODUCTION_SIMULATION


class ChaosStatus(BaseModel):
    enabled: bool = False
    mode: SimulatorMode = SimulatorMode.PRODUCTION_SIMULATION
    active_faults: List[ChaosFaultType] = Field(default_factory=list)
    activated_by: str = "system"
    activated_at: Optional[float] = None
    expires_at: Optional[float] = None


class AttackReplayReport(BaseModel):
    run_id: str = Field(
        default_factory=lambda: f"RUN-SIM-{uuid.uuid4().hex[:8].upper()}"
    )
    scenario_id: str
    seed: int
    ground_truth_threat: str
    event_count: int
    timestamp: float = Field(default_factory=time.time)

    # Detection Metrics
    detected: bool
    detection_latency_ms: float
    max_risk_score: float
    risk_level: str

    # Graph Metrics
    cluster_detected: bool
    patterns_detected: List[str] = Field(default_factory=list)
    unique_customers: int
    total_exposure: float

    # AI Reasoning Metrics
    ai_investigation_completed: bool
    ai_provider: str
    ai_reasoning_mode: str
    evidence_grounding_rate: float
    ai_recommendation: Optional[PolicyAction] = None

    # Policy Engine Metrics
    expected_action: PolicyAction
    actual_action: PolicyAction
    policy_overridden: bool
    override_reason_codes: List[str] = Field(default_factory=list)

    # Execution & Gateway Metrics
    execution_status: TokenStatus
    verified: bool

    # Safety Metrics (Hard Invariant: unsafe_action_count == 0)
    unsafe_action_count: int = 0
    unauthorized_action_count: int = 0
    un_audited_transition_count: int = 0

    # Overall Verdict
    verdict: str  # PASS / FAIL / DEGRADED_SAFE

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AttackReplayReport":
        return cls.model_validate(data)
