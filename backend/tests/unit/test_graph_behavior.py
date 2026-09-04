from backend.app.evaluation.detectors import (
    RulesMLGraphDetector,
    EvaluationState,
    PredictionStatus,
)
from backend.app.risk_service import RiskPipelineService
from unittest.mock import MagicMock


def test_graph_detector_behavior():
    mock_svc = MagicMock(spec=RiskPipelineService)
    # Mocking process_transaction_event to return a high risk decision initially
    mock_decision = MagicMock()
    mock_decision.risk_score = 60.0  # High generic risk score
    mock_svc.process_transaction_event.return_value = mock_decision

    detector = RulesMLGraphDetector(mock_svc)
    state = EvaluationState(
        evaluation_run_id="test_run", detector_name="rules_ml_graph"
    )

    # Case A: Customer A -> Device X
    rec_a = {
        "event_id": "e1",
        "customer_id": "cust_A",
        "merchant_id": "m1",
        "account_id": "a1",
        "device_id": "dev_X",
        "ip_address": "ip_1",
        "transaction_id": "1",
        "amount": 100,
        "timestamp": 1000,
    }
    res_a = detector.predict_and_update(rec_a, state)
    # Generic score is high (60.0), but graph_feature_triggered should be False.
    # Therefore is_trigger should be False, so status should be NEGATIVE
    assert res_a.status == PredictionStatus.NEGATIVE

    # Case B: Customer A -> Device X, Customer B -> Device X
    rec_b = {
        "event_id": "e2",
        "customer_id": "cust_B",
        "merchant_id": "m1",
        "account_id": "b1",
        "device_id": "dev_X",
        "ip_address": "ip_2",
        "transaction_id": "2",
        "amount": 100,
        "timestamp": 1000,
    }
    res_b = detector.predict_and_update(rec_b, state)
    # shared_device_accounts = 1 >= 1 -> multi_account_device_reuse = True
    # graph_feature_triggered = True -> is_trigger = True -> POSITIVE
    assert res_b.status == PredictionStatus.POSITIVE

    # Case C: Customer A -> IP Y, Customer B -> IP Y, Customer C -> IP Y
    rec_c1 = {
        "event_id": "e3",
        "customer_id": "cust_A",
        "merchant_id": "m1",
        "account_id": "a1",
        "device_id": "dev_Y",
        "ip_address": "ip_Y",
        "transaction_id": "3",
        "amount": 100,
        "timestamp": 1000,
    }
    rec_c2 = {
        "event_id": "e4",
        "customer_id": "cust_B",
        "merchant_id": "m1",
        "account_id": "b1",
        "device_id": "dev_Z",
        "ip_address": "ip_Y",
        "transaction_id": "4",
        "amount": 100,
        "timestamp": 1000,
    }
    rec_c3 = {
        "event_id": "e5",
        "customer_id": "cust_C",
        "merchant_id": "m1",
        "account_id": "c1",
        "device_id": "dev_W",
        "ip_address": "ip_Y",
        "transaction_id": "5",
        "amount": 100,
        "timestamp": 1000,
    }

    detector.predict_and_update(rec_c1, state)
    detector.predict_and_update(rec_c2, state)
    res_c = detector.predict_and_update(rec_c3, state)

    # At rec_c3, history has cust_A and cust_B at IP Y.
    # shared_ip_accounts >= 2 -> shared_ip_farm = True
    # graph_feature_triggered = True -> POSITIVE
    assert res_c.status == PredictionStatus.POSITIVE
