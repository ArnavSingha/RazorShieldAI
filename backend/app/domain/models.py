"""
RazorShield AI — Domain Models & Schemas
Strongly typed domain classes for transaction events, signals, ML scores, graph clusters,
composite risk scores, and explanatory decisions.
"""

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass
class GeoLocation:
    country: str = "IN"
    city: str = "Mumbai"
    lat: float = 19.0760
    lon: float = 72.8777

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransactionEvent:
    event_id: str
    idempotency_key: str
    transaction_id: str
    customer_id: str
    merchant_id: str
    account_id: str
    amount: float
    currency: str = "INR"
    payment_method: str = "CARD"
    card_bin: str = "411111"
    card_token: str = "tok_bin_411111_0000"
    device_id: str = "dev_default"
    ip_address: str = "127.0.0.1"
    geo_location: GeoLocation | None = field(default_factory=GeoLocation)
    user_agent: str = "Mozilla/5.0"
    merchant_category_code: str = "5732"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        res = asdict(self)
        if isinstance(self.geo_location, GeoLocation):
            res["geo_location"] = self.geo_location.to_dict()
        return res


@dataclass
class CustomerProfile:
    customer_id: str
    avg_transaction_amount_30d: float = 2500.0
    std_transaction_amount_30d: float = 1200.0
    primary_device_id: str = "dev_default"
    primary_ip: str = "127.0.0.1"
    home_country: str = "IN"
    last_transaction_time: float = 0.0
    last_lat: float = 19.0760
    last_lon: float = 72.8777
    vip_tier: bool = False


@dataclass
class RiskSignal:
    signal_code: str
    raw_value: Any
    normalized_score: float  # [0.0, 1.0]
    reason_code: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    weight: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MLRiskResult:
    model_version: str
    raw_anomaly_score: float  # IsolationForest output
    normalized_score: float  # [0.0, 1.0]
    confidence: float
    reason_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GraphRiskResult:
    related_accounts: list[str]
    related_devices: list[str]
    related_ips: list[str]
    cluster_size: int
    normalized_score: float  # [0.0, 1.0]
    reason_codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskComponent:
    component_name: str
    raw_score: float
    normalized_score: float
    weight: float
    weighted_contribution: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RiskScore:
    composite_score_normalized: float  # [0.0, 1.0]
    final_risk_score: int  # [0, 100]
    components: dict[str, RiskComponent]
    degraded_mode: str
    is_valid: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite_score_normalized": self.composite_score_normalized,
            "final_risk_score": self.final_risk_score,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "degraded_mode": self.degraded_mode,
            "is_valid": self.is_valid,
        }


@dataclass
class RiskDecision:
    decision_id: str
    transaction_id: str
    risk_score: int  # [0, 100]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    decision: Literal["ALLOW", "MONITOR", "STEP_UP", "HOLD", "BLOCK"]
    confidence: float
    components: dict[str, dict[str, Any]]
    reason_codes: list[str]
    contributing_signals: list[dict[str, Any]]
    degraded_mode: str
    latency_ms: float
    created_at: float
    request_id: str
    correlation_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
