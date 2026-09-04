"""
RazorShield AI — Integration Tests for Graph Investigation REST APIs
Verifies POST /api/v1/graph/investigations and GET /api/v1/graph/investigations/{investigation_id}.
"""

import uuid
import pytest
from backend.app.domain.models import TransactionEvent
from backend.app.main import handle_request
from backend.app.risk_service import RiskPipelineService


@pytest.fixture
def risk_service_with_graph_data():
    svc = RiskPipelineService()
    t_base = 1700000000.0
    u_suffix = uuid.uuid4().hex[:6]
    ev1 = TransactionEvent(
        event_id=f"ev_api_{u_suffix}_1",
        idempotency_key=f"idemp_api_{u_suffix}_1",
        transaction_id=f"tx_api_{u_suffix}_1",
        customer_id=f"cust_api_100_{u_suffix}",
        account_id=f"acc_api_100_{u_suffix}",
        amount=120000.0,
        currency="INR",
        device_id=f"dev_api_shared_{u_suffix}",
        ip_address="10.0.0.1",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=t_base,
    )
    ev2 = TransactionEvent(
        event_id=f"ev_api_{u_suffix}_2",
        idempotency_key=f"idemp_api_{u_suffix}_2",
        transaction_id=f"tx_api_{u_suffix}_2",
        customer_id=f"cust_api_101_{u_suffix}",
        account_id=f"acc_api_101_{u_suffix}",
        amount=150000.0,
        currency="INR",
        device_id=f"dev_api_shared_{u_suffix}",
        ip_address="10.0.0.1",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=t_base + 30.0,
    )
    svc.process_transaction_event(
        ev1.to_dict(), request_id="req_1", correlation_id="corr_1"
    )
    svc.process_transaction_event(
        ev2.to_dict(), request_id="req_2", correlation_id="corr_2"
    )
    return svc, f"cust_api_100_{u_suffix}"


def test_create_and_get_graph_investigation_api(risk_service_with_graph_data):
    svc, cust_id = risk_service_with_graph_data

    # 1. POST /api/v1/graph/investigations
    status, resp = handle_request(
        method="POST",
        path="/api/v1/graph/investigations",
        headers={"X-Request-ID": "req_investigate_1"},
        body_json={"entity_id": cust_id, "max_hops": 2},
        service_instance=svc,
    )

    assert status == 200
    assert resp["status"] == "SUCCESS"
    pkg = resp["data"]
    assert pkg["schema_version"] == "v1"
    assert pkg["graph_engine_version"] == "v0.2.0"
    assert pkg["entity_id"] == cust_id
    pkg_id = pkg["package_id"]
    incident_id = pkg["incident_id"]

    # 2. GET /api/v1/graph/investigations/{package_id}
    status_get, resp_get = handle_request(
        method="GET",
        path=f"/api/v1/graph/investigations/{pkg_id}",
        headers={"X-Request-ID": "req_get_1"},
        body_json={},
        service_instance=svc,
    )

    assert status_get == 200
    assert resp_get["status"] == "SUCCESS"
    assert resp_get["data"]["package_id"] == pkg_id

    # 3. GET /api/v1/graph/investigations/{incident_id}
    status_inc, resp_inc = handle_request(
        method="GET",
        path=f"/api/v1/graph/investigations/{incident_id}",
        headers={"X-Request-ID": "req_get_inc"},
        body_json={},
        service_instance=svc,
    )

    assert status_inc == 200
    assert resp_inc["status"] == "SUCCESS"
    assert resp_inc["data"]["incident_id"] == incident_id
