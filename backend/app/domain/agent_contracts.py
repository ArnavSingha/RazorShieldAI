"""
RazorShield AI — AI Investigator Domain Contracts
Defines versioned, immutable schema contracts for Agent Findings, Counter Signals,
Confidence Decompositions, Risk Interpretations, Agent Resource Budgets, and Agent Investigation Results.
Enforces mathematical clamping [0.0, 1.0], explicit versioning metadata, and provider transparency.
"""

import time
from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class AgentClassification(str, Enum):
    LIKELY_COORDINATED_FRAUD = "LIKELY_COORDINATED_FRAUD"
    SUSPICIOUS_ENTITY_FARM = "SUSPICIOUS_ENTITY_FARM"
    ISOLATED_ANOMALY = "ISOLATED_ANOMALY"
    BENIGN_SHARED_INFRASTRUCTURE = "BENIGN_SHARED_INFRASTRUCTURE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class RecommendedAction(str, Enum):
    ALLOW = "ALLOW"
    STEP_UP = "STEP_UP"
    HOLD = "HOLD"
    BLOCK = "BLOCK"


class ProviderType(str, Enum):
    DETERMINISTIC_FALLBACK = "DETERMINISTIC_FALLBACK"
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    GEMINI = "GEMINI"
    LOCAL = "LOCAL"


class ReasoningMode(str, Enum):
    DETERMINISTIC_RULE_BASED = "DETERMINISTIC_RULE_BASED"
    AGENTIC_LLM = "AGENTIC_LLM"


class AgentResourceBudget(BaseModel):
    max_tool_calls: int = 10
    max_graph_reads: int = 5
    max_tokens: int = 4096
    max_wall_clock_ms: float = 30000.0
    max_retries: int = 3

    current_tool_calls: int = 0
    current_graph_reads: int = 0
    current_tokens: int = 0
    start_time: float = Field(default_factory=time.time)
    current_retries: int = 0
    budget_status: str = (
        "HEALTHY"  # HEALTHY, EXCEEDED_TOOL_CALLS, EXCEEDED_TOKENS, EXCEEDED_WALL_CLOCK
    )

    def consume_tool_call(self) -> None:
        self.current_tool_calls += 1
        if self.current_tool_calls > self.max_tool_calls:
            self.budget_status = "EXCEEDED_TOOL_CALLS"

    def consume_graph_read(self) -> None:
        self.current_graph_reads += 1
        if self.current_graph_reads > self.max_graph_reads:
            self.budget_status = "EXCEEDED_GRAPH_READS"

    def consume_tokens(self, count: int) -> None:
        self.current_tokens += count
        if self.current_tokens > self.max_tokens:
            self.budget_status = "EXCEEDED_TOKENS"

    def check_wall_clock(self) -> None:
        elapsed_ms = (time.time() - self.start_time) * 1000.0
        if elapsed_ms > self.max_wall_clock_ms:
            self.budget_status = "EXCEEDED_WALL_CLOCK"


class ClaimFinding(BaseModel):
    claim: str
    evidence_ids: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    verified: bool = True
    counter_evidence_ids: List[str] = Field(default_factory=list)


class CounterSignal(BaseModel):
    claim: str
    evidence_ids: List[str]
    impact_on_hypothesis: str  # e.g., "ATTENUATES_RISK", "NEUTRAL"


class RiskInterpretation(BaseModel):
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    primary_reason: str
    pattern_interaction_summary: str


class ConfidenceDecomposition(BaseModel):
    completeness: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    pattern_agreement: float = Field(ge=0.0, le=1.0)
    counter_signal_strength: float = Field(ge=0.0, le=1.0)
    final_confidence: float = Field(ge=0.0, le=1.0)

    @classmethod
    def compute_clamped_confidence(
        cls,
        completeness: float,
        consistency: float,
        pattern_agreement: float,
        counter_signal_strength: float,
        w_c: float = 0.35,
        w_s: float = 0.35,
        w_a: float = 0.30,
        w_x: float = 0.25,
    ) -> "ConfidenceDecomposition":
        raw_score = (
            w_c * completeness
            + w_s * consistency
            + w_a * pattern_agreement
            - w_x * counter_signal_strength
        )
        clamped = max(0.0, min(1.0, raw_score))
        return cls(
            completeness=round(completeness, 4),
            consistency=round(consistency, 4),
            pattern_agreement=round(pattern_agreement, 4),
            counter_signal_strength=round(counter_signal_strength, 4),
            final_confidence=round(clamped, 4),
        )


class LLMProvenance(BaseModel):
    provider_type: ProviderType
    reasoning_mode: ReasoningMode
    model_name: str
    agent_graph_version: str = "v0.3.0"
    prompt_version: str = "v2.1"
    output_schema_version: str = "v1"
    execution_time_ms: float
    token_usage: Dict[str, int] = Field(default_factory=dict)


class AgentInvestigationResult(BaseModel):
    agent_run_id: str  # e.g. "RUN-20260823-991A"
    investigation_id: str  # Incident ID or Package ID
    package_id: str
    evidence_snapshot_hash: str
    agent_graph_version: str = "v0.3.0"
    prompt_version: str = "v2.1"
    output_schema_version: str = "v1"
    classification: AgentClassification
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_decomposition: ConfidenceDecomposition
    findings: List[ClaimFinding]
    counter_signals: List[CounterSignal]
    adversarial_analysis: str
    risk_interpretation: RiskInterpretation
    recommended_action: RecommendedAction
    action_rationale: str
    budget_status: str = "HEALTHY"
    llm_provenance: LLMProvenance
    created_at: float

    @property
    def confidence_score(self) -> float:
        return self.confidence

    @property
    def execution_trace(self) -> str:
        return self.agent_run_id

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data["confidence_score"] = (
            round(self.confidence * 100)
            if self.confidence <= 1.0
            else round(self.confidence)
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInvestigationResult":
        return cls.model_validate(data)
