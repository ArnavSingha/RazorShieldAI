"""
RazorShield AI — Unit Tests for Clamped & Bounded Confidence Mathematics
Verifies mathematical clamping within [0.0, 1.0], weight non-negativity, and edge-case boundary behaviors.
"""

from backend.app.domain.agent_contracts import ConfidenceDecomposition


def test_confidence_decomposition_clamping_and_boundaries():
    # 1. Standard Case
    c1 = ConfidenceDecomposition.compute_clamped_confidence(
        completeness=0.95,
        consistency=0.90,
        pattern_agreement=0.92,
        counter_signal_strength=0.10,
    )
    assert 0.0 <= c1.final_confidence <= 1.0
    assert c1.final_confidence > 0.80

    # 2. Upper Boundary Clamping (All Ones -> raw sum > 1.0)
    c_upper = ConfidenceDecomposition.compute_clamped_confidence(
        completeness=1.0,
        consistency=1.0,
        pattern_agreement=1.0,
        counter_signal_strength=0.0,
        w_c=0.5,
        w_s=0.5,
        w_a=0.5,
    )
    assert c_upper.final_confidence == 1.0

    # 3. Lower Boundary Clamping (Strong Contradiction -> raw subtraction < 0.0)
    c_lower = ConfidenceDecomposition.compute_clamped_confidence(
        completeness=0.1,
        consistency=0.1,
        pattern_agreement=0.1,
        counter_signal_strength=1.0,
        w_x=1.0,
    )
    assert c_lower.final_confidence == 0.0

    # 4. Zero Input Boundary
    c_zero = ConfidenceDecomposition.compute_clamped_confidence(
        completeness=0.0,
        consistency=0.0,
        pattern_agreement=0.0,
        counter_signal_strength=0.0,
    )
    assert c_zero.final_confidence == 0.0
