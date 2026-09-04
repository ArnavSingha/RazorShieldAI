"""
RazorShield AI — Policy-Driven SLA Configuration & Evaluation Engine
Decouples SLA target durations and breach evaluations from storage repository logic.
"""

import time
from typing import Any, Dict


class SLAPolicyEngine:
    """Configurable SLA policy targets and breach status evaluation."""

    # SLA targets in seconds by severity
    SLA_TARGET_SECONDS: Dict[str, float] = {
        "CRITICAL": 7200.0,  # 2 hours
        "HIGH": 14400.0,  # 4 hours
        "MEDIUM": 28800.0,  # 8 hours
        "LOW": 86400.0,  # 24 hours
    }

    # At-risk threshold (e.g. 30 minutes remaining)
    AT_RISK_THRESHOLD_SECONDS: float = 1800.0

    @classmethod
    def get_target_seconds(cls, severity: str) -> float:
        sev_upper = (severity or "HIGH").upper()
        return cls.SLA_TARGET_SECONDS.get(sev_upper, cls.SLA_TARGET_SECONDS["HIGH"])

    @classmethod
    def evaluate_sla(
        cls, created_at: float, severity: str, now: float | None = None
    ) -> Dict[str, Any]:
        ref_time = now or time.time()
        target_seconds = cls.get_target_seconds(severity)
        deadline = created_at + target_seconds
        remaining_seconds = deadline - ref_time

        if remaining_seconds <= 0:
            status = "BREACHED"
        elif remaining_seconds <= cls.AT_RISK_THRESHOLD_SECONDS:
            status = "AT_RISK"
        else:
            status = "HEALTHY"

        return {
            "sla_target_seconds": target_seconds,
            "sla_deadline": deadline,
            "sla_seconds_remaining": max(0.0, remaining_seconds),
            "sla_status": status,
        }
