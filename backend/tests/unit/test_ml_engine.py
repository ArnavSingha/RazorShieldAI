"""
RazorShield AI — Unit Tests: ML Isolation Forest Engine
Verifies anomaly scoring boundaries [0.0, 1.0], feature vector processing, and clean degraded failure.
"""

import pytest
from backend.app.domain.models import CustomerProfile
from backend.app.ingestion.validator import EventValidator
from backend.app.risk.ml_engine import MLEngine


def test_ml_anomaly_prediction_normal(valid_transaction_payload):
    engine = MLEngine()
    customer = CustomerProfile(
        customer_id="cust_test_101",
        avg_transaction_amount_30d=4500.0,
        std_transaction_amount_30d=1000.0,
    )
    event = EventValidator.validate_dict(valid_transaction_payload)

    result = engine.predict_anomaly(event, customer)
    assert 0.0 <= result.normalized_score <= 1.0
    assert result.model_version == "iforest-v1.2.0-real"
    assert result.confidence == 0.92


def test_ml_anomaly_prediction_high_deviation(high_risk_transaction_payload):
    engine = MLEngine()
    customer = CustomerProfile(
        customer_id="cust_test_101",
        avg_transaction_amount_30d=2000.0,
        std_transaction_amount_30d=500.0,
        primary_device_id="dev_primary_01",
    )
    event = EventValidator.validate_dict(high_risk_transaction_payload)

    result = engine.predict_anomaly(event, customer)
    assert result.normalized_score >= 0.0
    assert result.reason_metadata["device_mismatch"] is True


def test_ml_unfitted_model_raises_runtime_error(valid_transaction_payload):
    """Verifies that an unfitted or unavailable ML model raises RuntimeError instead of returning fake scores."""
    engine = MLEngine()
    engine.model.is_fitted = False

    customer = CustomerProfile(customer_id="cust_test_101")
    event = EventValidator.validate_dict(valid_transaction_payload)

    with pytest.raises(RuntimeError) as exc_info:
        engine.predict_anomaly(event, customer)
    assert "IsolationForest model unavailable" in str(exc_info.value)
