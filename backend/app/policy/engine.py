"""
RazorShield AI — Policy Engine & Threshold Evaluator
Translates composite risk score into deterministic risk level and mandated action.
"""

import uuid
from typing import Literal

from backend.app.domain.models import RiskDecision, RiskScore, TransactionEvent


class PolicyEngine:
    """Evaluates composite risk score against centralized policy matrix."""

    @classmethod
    def evaluate(
        cls,
        event: TransactionEvent,
        risk_score: RiskScore,
        reason_codes: list[str],
        contributing_signals: list[dict],
        latency_ms: float,
        request_id: str,
        correlation_id: str,
    ) -> RiskDecision:
        score = risk_score.final_risk_score

        if score <= 30:
            risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "LOW"
            action: Literal["ALLOW", "MONITOR", "STEP_UP", "HOLD", "BLOCK"] = "ALLOW"
            confidence = 0.95
        elif score <= 60:
            risk_level = "MEDIUM"
            action = "MONITOR"
            confidence = 0.90
        elif score <= 80:
            risk_level = "HIGH"
            action = "STEP_UP"
            confidence = 0.88
        elif score <= 95:
            risk_level = "HIGH"
            action = "HOLD"
            confidence = 0.92
        else:
            risk_level = "CRITICAL"
            action = "BLOCK"
            confidence = 0.98

        # Unique decision ID with UUID suffix to ensure primary key uniqueness
        decision_id = f"dec_{event.transaction_id}_{uuid.uuid4().hex[:8]}"

        return RiskDecision(
            decision_id=decision_id,
            transaction_id=event.transaction_id,
            risk_score=score,
            risk_level=risk_level,
            decision=action,
            confidence=confidence,
            components={k: v.to_dict() for k, v in risk_score.components.items()},
            reason_codes=reason_codes,
            contributing_signals=contributing_signals,
            degraded_mode=risk_score.degraded_mode,
            latency_ms=round(latency_ms, 2),
            created_at=event.timestamp,
            request_id=request_id,
            correlation_id=correlation_id,
        )
