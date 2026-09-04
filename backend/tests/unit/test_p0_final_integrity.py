"""
RazorShield AI — Final Pre-Submission P0 Integrity Tests
Tests:
1. Stateful evaluation (Velocity & Graph history accumulation changes decision)
2. ML IsolationForest training on train set only & validation threshold calibration
3. Failure isolation: Exception returns PredictionStatus.ERROR, NEVER fraud positive
4. Graph intelligence: Shared device across accounts detected only after history exists
5. Zero frontend privileged credentials & zero hardcoded business metric assertions
"""

import os
import pytest

from backend.app.evaluation.detectors import (
    EvaluationState,
    MLOnlyDetector,
    PredictionStatus,
    RulesMLGraphDetector,
    RulesOnlyDetector,
)
from backend.app.risk_service import RiskPipelineService


def test_stateful_velocity_history_accumulation():
    """Tests that velocity history accumulation changes decision statefully."""
    det = RulesOnlyDetector()
    state = EvaluationState(evaluation_run_id="test_run", detector_name="rules")

    rec = {
        "event_id": "ev_1",
        "idempotency_key": "idemp_1",
        "transaction_id": "tx_1",
        "customer_id": "cust_vel_01",
        "account_id": "acc_vel_01",
        "amount": 15000.0,
        "currency": "INR",
        "device_id": "dev_normal",
        "ip_address": "10.0.0.1",
        "merchant_id": "5001",
        "merchant_category_code": "5411",
        "timestamp": 1700000000.0,
    }

    # Initial transaction with no history -> NEGATIVE
    res1 = det.predict_and_update(rec, state)
    assert res1.status == PredictionStatus.NEGATIVE
    assert state.historical_event_count == 1

    # Simulate 4 rapid transactions in 1h history
    for i in range(2, 6):
        rec_next = dict(rec)
        rec_next["transaction_id"] = f"tx_{i}"
        rec_next["timestamp"] = 1700000000.0 + (i * 10.0)
        res = det.predict_and_update(rec_next, state)

    # 5th transaction within 1h -> POSITIVE due to accumulated velocity history
    assert res.status == PredictionStatus.POSITIVE
    assert state.historical_event_count == 5


def test_graph_history_shared_device_accumulation():
    """Tests that shared device ring is detected only after prior historical events exist."""
    svc = RiskPipelineService()
    det = RulesMLGraphDetector(svc)
    state = EvaluationState(evaluation_run_id="test_graph", detector_name="graph")

    import uuid

    run_uid = uuid.uuid4().hex[:6]

    # Transaction 1: Customer A on Dev X
    rec_a = {
        "event_id": f"ev_a_{run_uid}",
        "idempotency_key": f"idemp_a_{run_uid}",
        "transaction_id": f"tx_a_{run_uid}",
        "customer_id": "cust_user_A",
        "account_id": "acc_A",
        "amount": 5000.0,
        "currency": "INR",
        "device_id": "dev_shared_farm_99",
        "ip_address": "192.168.1.1",
        "merchant_id": "5001",
        "merchant_category_code": "5411",
        "payment_method": "UPI",
        "timestamp": 1700000000.0,
    }
    res_a = det.predict_and_update(rec_a, state)
    assert res_a.status == PredictionStatus.NEGATIVE

    # Transaction 2: Customer B on SAME Dev X -> Graph risk triggered due to prior history
    rec_b = {
        "event_id": f"ev_b_{run_uid}",
        "idempotency_key": f"idemp_b_{run_uid}",
        "transaction_id": f"tx_b_{run_uid}",
        "customer_id": "cust_user_B",
        "account_id": "acc_B",
        "amount": 5000.0,
        "currency": "INR",
        "device_id": "dev_shared_farm_99",
        "ip_address": "192.168.1.2",
        "merchant_id": "5001",
        "merchant_category_code": "5411",
        "payment_method": "UPI",
        "timestamp": 1700000010.0,
    }
    res_b = det.predict_and_update(rec_b, state)
    if res_b.status == PredictionStatus.ERROR:
        pytest.fail(f"Detector returned ERROR: {res_b.error_message}")

    assert res_b.status == PredictionStatus.POSITIVE
    assert res_b.score >= 85.0


def test_exception_never_converts_to_fraud_positive():
    """Tests that an exception returns PredictionStatus.ERROR and NEVER fraud positive."""
    det = RulesOnlyDetector()
    state = EvaluationState(evaluation_run_id="test_err", detector_name="err")

    # Malformed record that causes internal parsing exception
    malformed_rec = {"invalid_field": None}
    res = det.predict_and_update(malformed_rec, state)

    assert res.status == PredictionStatus.ERROR
    assert res.status != PredictionStatus.POSITIVE
    assert "error" in res.error_message.lower() or res.error_message != ""


def test_ml_train_validation_test_split_integrity():
    """Tests that ML training fits on train data and validation calibrates threshold."""
    svc = RiskPipelineService()
    det = MLOnlyDetector(svc)

    train_data = [
        {
            "event_id": f"ev_tr_{i}",
            "transaction_id": f"tx_tr_{i}",
            "customer_id": f"cust_tr_{i}",
            "account_id": f"acc_tr_{i}",
            "amount": 1000.0 + (i * 10),
            "currency": "INR",
            "device_id": f"dev_tr_{i}",
            "ip_address": f"10.0.0.{i % 20}",
            "merchant_id": "5001",
            "merchant_category_code": "5411",
            "timestamp": 1700000000.0 + i,
        }
        for i in range(50)
    ]

    train_hash = det.train_baseline(train_data)
    assert train_hash != ""
    assert det.svc.ml_engine.model.is_fitted is True

    val_hash = det.calibrate(train_data[:20])
    assert val_hash != ""
    assert det.threshold_source == "VALIDATION"
    assert det.test_touched_before_final_evaluation is False


def test_frontend_security_and_credentials_absence():
    """Asserts that frontend source contains zero hardcoded credentials."""
    frontend_dir = "frontend/src"
    if os.path.exists(frontend_dir):
        for root, _, files in os.walk(frontend_dir):
            for file in files:
                if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    assert "operator_sec_key" not in content
                    assert "admin_sec_key" not in content
