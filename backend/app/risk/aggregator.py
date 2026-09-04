"""
RazorShield AI — Composite Risk Aggregator
Aggregates normalized scores from Signal, ML, and Graph engines using calibrated weights
and safe degraded-mode fallbacks.
"""

from backend.app.domain.models import (
    GraphRiskResult,
    MLRiskResult,
    RiskComponent,
    RiskScore,
    RiskSignal,
)
from backend.app.domain.reason_codes import ReasonCode


class RiskAggregator:
    """Aggregates tri-engine risk metrics into a bounded composite score [0, 100]."""

    @classmethod
    def aggregate(
        cls,
        signals: list[RiskSignal],
        ml_result: MLRiskResult | None = None,
        graph_result: GraphRiskResult | None = None,
        ml_available: bool = True,
        graph_available: bool = True,
    ) -> RiskScore:
        # 1. Calculate Signal Engine Score
        if signals:
            # Weighted average of signal scores
            total_weight = sum(s.weight for s in signals)
            signal_score_norm = (
                sum(s.normalized_score * s.weight for s in signals) / total_weight
                if total_weight > 0
                else 0.0
            )
        else:
            signal_score_norm = 0.05  # Baseline minimal score

        signal_score_norm = min(1.0, max(0.0, signal_score_norm))

        # 2. Determine Operational Degraded Mode & Weighting Scheme
        if ml_available and graph_available and ml_result and graph_result:
            mode = ReasonCode.NORMAL_ALL_SYSTEMS
            w_signal, w_ml, w_graph = 0.40, 0.30, 0.30
        elif (not ml_available or not ml_result) and (graph_available and graph_result):
            mode = ReasonCode.DEGRADED_NO_ML
            w_signal, w_ml, w_graph = 0.60, 0.00, 0.40
        elif (ml_available and ml_result) and (not graph_available or not graph_result):
            mode = ReasonCode.DEGRADED_NO_GRAPH
            w_signal, w_ml, w_graph = 0.60, 0.40, 0.00
        else:
            mode = ReasonCode.DEGRADED_RULES_ONLY
            w_signal, w_ml, w_graph = 1.00, 0.00, 0.00

        # Extract normalized scores for ML and Graph
        ml_score_norm = (
            ml_result.normalized_score if (ml_result and ml_available) else 0.0
        )
        graph_score_norm = (
            graph_result.normalized_score if (graph_result and graph_available) else 0.0
        )

        # 3. Calculate Composite Score
        r_comp = (
            w_signal * signal_score_norm
            + w_ml * ml_score_norm
            + w_graph * graph_score_norm
        )
        r_comp = min(1.0, max(0.0, r_comp))
        final_score = round(r_comp * 100.0)

        # 4. Build Structured Components
        components: dict[str, RiskComponent] = {
            "signal": RiskComponent(
                component_name="Deterministic Signal Engine",
                raw_score=round(signal_score_norm, 4),
                normalized_score=round(signal_score_norm, 4),
                weight=w_signal,
                weighted_contribution=round(w_signal * signal_score_norm, 4),
            ),
            "ml": RiskComponent(
                component_name="Isolation Forest ML Engine",
                raw_score=round(ml_score_norm, 4),
                normalized_score=round(ml_score_norm, 4),
                weight=w_ml,
                weighted_contribution=round(w_ml * ml_score_norm, 4),
            ),
            "graph": RiskComponent(
                component_name="Heterogeneous Graph Engine",
                raw_score=round(graph_score_norm, 4),
                normalized_score=round(graph_score_norm, 4),
                weight=w_graph,
                weighted_contribution=round(w_graph * graph_score_norm, 4),
            ),
        }

        return RiskScore(
            composite_score_normalized=round(r_comp, 4),
            final_risk_score=final_score,
            components=components,
            degraded_mode=mode,
            is_valid=True,
        )
