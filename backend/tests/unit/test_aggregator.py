"""
RazorShield AI — Unit Tests: Risk Aggregator
Verifies hardened risk formula: R_comp = w_s*R_s + w_m*R_m + w_g*R_g, bounded limits [0, 100],
and degraded mode weightings.
"""

from backend.app.domain.models import GraphRiskResult, MLRiskResult, RiskSignal
from backend.app.risk.aggregator import RiskAggregator


def test_normal_tri_engine_aggregation():
    signals = [
        RiskSignal(
            signal_code="SIG_TEST",
            raw_value=1.0,
            normalized_score=0.80,
            reason_code="HIGH_VELOCITY",
            severity="HIGH",
            weight=1.0,
        )
    ]
    ml_res = MLRiskResult(
        model_version="v1", raw_anomaly_score=0.5, normalized_score=0.70, confidence=0.9
    )
    graph_res = GraphRiskResult(
        related_accounts=["c1", "c2"],
        related_devices=["d1"],
        related_ips=["i1"],
        cluster_size=4,
        normalized_score=0.90,
        reason_codes=["DEVICE_ACCOUNT_REUSE"],
    )

    # Weights: w_s=0.40, w_m=0.30, w_g=0.30
    # R_comp = 0.4*0.80 + 0.3*0.70 + 0.3*0.90 = 0.32 + 0.21 + 0.27 = 0.80
    # Final Score = 80
    result = RiskAggregator.aggregate(
        signals, ml_res, graph_res, ml_available=True, graph_available=True
    )

    assert result.final_risk_score == 80
    assert result.degraded_mode == "NORMAL_ALL_SYSTEMS"
    assert result.components["signal"].weighted_contribution == 0.32
    assert result.components["ml"].weighted_contribution == 0.21
    assert result.components["graph"].weighted_contribution == 0.27


def test_degraded_no_ml_weighting():
    signals = [
        RiskSignal(
            signal_code="SIG_TEST",
            raw_value=1.0,
            normalized_score=0.80,
            reason_code="HIGH_VELOCITY",
            severity="HIGH",
            weight=1.0,
        )
    ]
    graph_res = GraphRiskResult(
        related_accounts=["c1"],
        related_devices=["d1"],
        related_ips=["i1"],
        cluster_size=2,
        normalized_score=0.50,
        reason_codes=[],
    )

    # Degraded Weights (No ML): w_s=0.60, w_m=0.00, w_g=0.40
    # R_comp = 0.60*0.80 + 0.00*0.00 + 0.40*0.50 = 0.48 + 0.20 = 0.68 -> 68
    result = RiskAggregator.aggregate(
        signals,
        ml_result=None,
        graph_result=graph_res,
        ml_available=False,
        graph_available=True,
    )

    assert result.final_risk_score == 68
    assert result.degraded_mode == "DEGRADED_NO_ML"
    assert result.components["signal"].weight == 0.60
    assert result.components["ml"].weight == 0.00
    assert result.components["graph"].weight == 0.40
