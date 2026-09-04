"""
RazorShield AI — Unit Tests: Real Isolation Forest Model
Verifies IsolationForest model fitting, decision_function scoring, and bounds [0.0, 1.0].
"""

from backend.app.domain.models import CustomerProfile
from backend.app.ingestion.validator import EventValidator
from backend.app.risk.ml_engine import MLEngine, RealIsolationForestModel


def test_real_isolation_forest_model_fit_and_score():
    model = RealIsolationForestModel(n_estimators=30, seed=42)
    model.fit_synthetic_baseline()

    # Normal feature vector: amount_ratio=1.0, log_amount=7.5, device_mismatch=0.0, ip_mismatch=0.0
    normal_features = [1.0, 7.5, 0.0, 0.0]
    _raw_norm, score_norm, valid_norm = model.score_sample(normal_features)
    assert valid_norm is True
    assert 0.0 <= score_norm <= 1.0

    # Anomalous feature vector: amount_ratio=8.5, log_amount=11.5, device_mismatch=1.0, ip_mismatch=1.0
    anomalous_features = [8.5, 11.5, 1.0, 1.0]
    _raw_anom, score_anom, valid_anom = model.score_sample(anomalous_features)
    assert valid_anom is True
    assert 0.0 <= score_anom <= 1.0
    assert score_anom > score_norm


def test_ml_engine_prediction_metadata(valid_transaction_payload):
    engine = MLEngine()
    customer = CustomerProfile(
        customer_id="cust_test_101",
        avg_transaction_amount_30d=4500.0,
        std_transaction_amount_30d=1000.0,
    )
    event = EventValidator.validate_dict(valid_transaction_payload)

    result = engine.predict_anomaly(event, customer)
    assert 0.0 <= result.normalized_score <= 1.0
    assert "sklearn_backend_active" in result.reason_metadata
    assert "note" in result.reason_metadata
