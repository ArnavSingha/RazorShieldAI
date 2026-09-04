"""
RazorShield AI — Integration Tests for Agent Investigation REST APIs
Verifies POST /api/v1/agent/investigate and GET /api/v1/agent/investigations/{agent_run_id}.
"""

import uuid
import pytest
from backend.app.domain.models import TransactionEvent
from backend.app.main import handle_request
from backend.app.risk_service import RiskPipelineService


@pytest.fixture
def risk_service_with_agent_data():
    svc = RiskPipelineService()
    u_suffix = uuid.uuid4().hex[:6]
    ev = TransactionEvent(
        event_id=f"ev_ag_api_{u_suffix}",
        idempotency_key=f"idemp_ag_api_{u_suffix}",
        transaction_id=f"tx_ag_api_{u_suffix}",
        customer_id=f"cust_ag_api_{u_suffix}",
        account_id=f"acc_ag_api_{u_suffix}",
        amount=140000.0,
        currency="INR",
        device_id=f"dev_ag_api_{u_suffix}",
        ip_address="10.0.0.99",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    svc.process_transaction_event(ev.to_dict())
    return svc, f"cust_ag_api_{u_suffix}"


def test_create_and_get_agent_investigation_api(risk_service_with_agent_data):
    svc, cust_id = risk_service_with_agent_data

    # 1. POST /api/v1/agent/investigate
    status, resp = handle_request(
        method="POST",
        path="/api/v1/agent/investigate",
        headers={"X-Request-ID": "req_ag_post_1"},
        body_json={"investigation_id": cust_id},
        service_instance=svc,
    )

    assert status == 200
    assert resp["status"] == "SUCCESS"
    data = resp["data"]
    assert data["agent_run_id"].startswith("RUN-")
    assert data["llm_provenance"]["provider_type"] in (
        "DETERMINISTIC_FALLBACK",
        "GEMINI",
    )
    assert data["llm_provenance"]["reasoning_mode"] in (
        "DETERMINISTIC_RULE_BASED",
        "AGENTIC_LLM",
    )
    assert "findings" in data
    assert "counter_signals" in data
    run_id = data["agent_run_id"]

    # 2. GET /api/v1/agent/investigations/{run_id}
    status_get, resp_get = handle_request(
        method="GET",
        path=f"/api/v1/agent/investigations/{run_id}",
        headers={"X-Request-ID": "req_ag_get_1"},
        body_json={},
        service_instance=svc,
    )

    assert status_get == 200
    assert resp_get["status"] == "SUCCESS"
    assert resp_get["data"]["agent_run_id"] == run_id
