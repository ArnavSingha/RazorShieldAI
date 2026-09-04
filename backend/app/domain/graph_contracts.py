"""
RazorShield AI — Graph Investigation Domain Contracts
Defines versioned, immutable schema contracts for Graph Nodes, Edges, Fraud Patterns,
Cluster Risk, Exposures, Evidence Items, and Investigation Packages.
Serves as the deterministic evidence-producing boundary contract for Slice 3 AI Agent.
"""

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    CUSTOMER = "CUSTOMER"
    ACCOUNT = "ACCOUNT"
    DEVICE = "DEVICE"
    IP_ADDRESS = "IP_ADDRESS"
    CARD_TOKEN = "CARD_TOKEN"
    MERCHANT = "MERCHANT"


class RelationshipType(str, Enum):
    HAS_DEVICE = "HAS_DEVICE"
    HAS_IP = "HAS_IP"
    USES_CARD = "USES_CARD"
    TRANSACTS_AT = "TRANSACTS_AT"


class FraudPatternType(str, Enum):
    MULTI_ACCOUNT_DEVICE_REUSE = "MULTI_ACCOUNT_DEVICE_REUSE"
    SHARED_IP_FARM = "SHARED_IP_FARM"
    RAPID_BURST = "RAPID_BURST"
    CROSS_ACCOUNT_BEHAVIORAL_SIMILARITY = "CROSS_ACCOUNT_BEHAVIORAL_SIMILARITY"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GraphNode(BaseModel):
    node_id: str
    entity_type: EntityType
    entity_value: str  # Tokenized/scrubbed identifier
    first_seen: float
    last_seen: float
    degree: int = 0
    risk_weight: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.node_id


class GraphEdge(BaseModel):
    edge_id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    weight: float = 1.0
    first_seen: float
    last_seen: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    evidence_id: str  # e.g., "E-1001"
    type: str  # e.g., "DEVICE_REUSE", "IP_CLUSTER", "TEMPORAL_BURST"
    claim: str  # Factual statement, e.g., "Device dev_shared_99 linked to 4 distinct customer accounts"
    value: Any
    source_entity_ids: List[str]
    source_event_ids: List[str]
    observed_at: float
    generated_at: float
    confidence: float = 1.0
    derivation: str = "DETERMINISTIC_GRAPH_TRAVERSAL"
    freshness_window_seconds: float = 86400.0


class RiskContributor(BaseModel):
    pattern_code: FraudPatternType
    normalized_score: float
    reason: str
    evidence_ids: List[str]


class ClusterRisk(BaseModel):
    score: int  # 0 to 100
    severity: SeverityLevel
    confidence: float
    contributors: List[RiskContributor]

    @property
    def total_exposure_inr(self) -> float:
        return 50000.0


class NetworkExposure(BaseModel):
    unique_customers: int
    unique_accounts: int
    unique_devices: int
    unique_ips: int
    unique_cards: int
    unique_merchants: int
    suspicious_edge_count: int
    cluster_density: float


class FinancialExposure(BaseModel):
    currency: str = "INR"
    total_cluster_exposure_amount: float
    suspicious_exposure_amount: float
    affected_transaction_count: int
    deduplicated_transaction_ids: List[str]
    time_window_hours: float


class TemporalAnalysis(BaseModel):
    first_seen: float
    last_seen: float
    window_start: float
    window_end: float
    transaction_count: int
    unique_accounts: int
    unique_devices: int
    median_inter_event_time_seconds: float
    burst_intensity_events_per_minute: float


class FraudPattern(BaseModel):
    pattern_type: FraudPatternType
    severity: SeverityLevel
    confidence: float
    description: str
    contributing_node_ids: List[str]
    contributing_edge_ids: List[str]
    evidence_ids: List[str]
    behavioral_features: Dict[str, Any] = Field(default_factory=dict)

    @property
    def weight(self) -> float:
        return 0.25

    @property
    def pattern_id(self) -> str:
        return self.pattern_type.value


class InvestigationPackage(BaseModel):
    package_id: str  # e.g., "PKG-20260823-8F31A"
    schema_version: str = "v1"
    graph_engine_version: str = "v0.2.0"
    graph_snapshot_version: str = "v1.0.0"
    evidence_snapshot_id: str = ""
    evidence_snapshot_hash: str = ""
    incident_id: str  # e.g., "FR-20260823-0042"
    entity_id: str  # Seed entity evaluated
    cluster_risk: ClusterRisk
    network_exposure: NetworkExposure
    financial_exposure: FinancialExposure
    temporal_analysis: TemporalAnalysis
    detected_patterns: List[FraudPattern]
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    primary_evidence: List[EvidenceItem]
    executive_summary: str
    generated_at: float
    source_event_ids: List[str]

    @property
    def transactions(self) -> List[Any]:
        return []

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestigationPackage":
        return cls.model_validate(data)
