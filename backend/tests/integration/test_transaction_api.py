"""
RazorShield AI — Integration Tests: Transaction API & End-to-End Ingestion Flow
"""

import uuid

from backend.app.main import handle_request
from backend.app.risk_service import RiskPipelineService


def test_e2e_transaction_event_flow(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"api_e2e_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    decision = service.process_transaction_event(valid_transaction_payload)
    assert decision.transaction_id == valid_transaction_payload["transaction_id"]
    assert decision.risk_score >= 0
    assert decision.decision in ("ALLOW", "MONITOR", "STEP_UP", "HOLD", "BLOCK")
    assert len(service.audit_store.get_latest_hash()) == 64


def test_api_route_handler_integration(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"api_handler_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    headers = {
        "X-Request-ID": "req_integration_001",
        "X-Correlation-ID": "corr_integration_001",
    }
    status_code, body = handle_request(
        "POST",
        "/api/v1/events/transaction",
        headers,
        valid_transaction_payload,
        service_instance=service,
    )
    assert status_code == 200
    assert body["status"] == "SUCCESS"
    assert body["data"]["transaction_id"] == valid_transaction_payload["transaction_id"]
