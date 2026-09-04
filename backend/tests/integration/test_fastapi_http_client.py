"""
RazorShield AI — Integration Tests: FastAPI HTTP Client
Executes real HTTP requests via FastAPI app and TestClient/AsyncClient.
"""

import uuid

from backend.app.main import handle_request


def test_fastapi_http_endpoints_valid(valid_transaction_payload):
    headers = {
        "X-Request-ID": f"req_test_{uuid.uuid4().hex[:6]}",
        "X-Correlation-ID": f"corr_test_{uuid.uuid4().hex[:6]}",
    }

    # Test GET /health
    status_code, body = handle_request("GET", "/health", headers, {})
    assert status_code == 200
    assert body["status"] == "HEALTHY"

    # Test GET /api/v1/audit/verify
    status_code, body = handle_request("GET", "/api/v1/audit/verify", headers, {})
    assert status_code == 200
    assert body["status"] == "SUCCESS"
    assert "ledger_valid" in body["data"]

    # Test POST /api/v1/events/transaction
    status_code, body = handle_request(
        "POST", "/api/v1/events/transaction", headers, valid_transaction_payload
    )
    assert status_code == 200
    assert body["status"] == "SUCCESS"
    assert body["data"]["transaction_id"] == valid_transaction_payload["transaction_id"]
    assert body["metadata"]["request_id"] == headers["X-Request-ID"]
