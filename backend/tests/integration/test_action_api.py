"""
RazorShield AI — Integration Tests for Action Control Plane REST APIs
Verifies POST /api/v1/actions/authorize and POST /api/v1/actions/execute endpoints.
"""

import uuid
import pytest
from backend.app.domain.models import TransactionEvent
from backend.app.main import handle_request
from backend.app.risk_service import RiskPipelineService


@pytest.fixture
def risk_service_with_action_data():
    svc = RiskPipelineService()
    u_suffix = uuid.uuid4().hex[:6]
    ev = TransactionEvent(
        event_id=f"ev_act_api_{u_suffix}",
        idempotency_key=f"idemp_act_api_{u_suffix}",
        transaction_id=f"tx_act_api_{u_suffix}",
        customer_id=f"cust_act_api_{u_suffix}",
        account_id=f"acc_act_api_{u_suffix}",
        amount=150000.0,
        currency="INR",
        device_id=f"dev_act_api_{u_suffix}",
        ip_address="10.0.0.88",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    svc.process_transaction_event(ev.to_dict())
    return svc, f"cust_act_api_{u_suffix}"


def test_authorize_and_execute_action_api(risk_service_with_action_data):
    svc, cust_id = risk_service_with_action_data
    from backend.app.simulator.chaos_engine import ChaosController, ChaosFaultType
    from backend.app.policy.rbac import TrustedPrincipal, UserRole

    admin_p = TrustedPrincipal(
        principal_id="usr_admin", role=UserRole.ADMIN, is_authenticated=True
    )
    ChaosController.toggle_fault(ChaosFaultType.GEMINI_OFFLINE, True, admin_p)

    try:
        # 1. POST /api/v1/actions/authorize (Authenticated Operator Token)
        status_auth, resp_auth = handle_request(
            method="POST",
            path="/api/v1/actions/authorize",
            headers={
                "Authorization": "test_operator_token_xyz77",
                "X-Request-ID": "req_act_auth_1",
            },
            body_json={"investigation_id": cust_id},
            service_instance=svc,
        )

        assert status_auth == 200
        assert resp_auth["status"] in ("SUCCESS", "APPROVAL_REQUIRED")

        if resp_auth["status"] == "SUCCESS":
            token_dict = resp_auth["data"]["action_token"]
            assert token_dict["action_id"].startswith("ACT-")
            assert token_dict["hmac_signature"] != ""

            # 2. POST /api/v1/actions/execute
            status_exec, resp_exec = handle_request(
                method="POST",
                path="/api/v1/actions/execute",
                headers={"X-Request-ID": "req_act_exec_1"},
                body_json={"token": token_dict},
                service_instance=svc,
            )

            assert status_exec == 200
            assert resp_exec["status"] == "SUCCESS"
            assert resp_exec["data"]["status"] == "EXECUTED"
            assert resp_exec["data"]["verified"] is True
    finally:
        ChaosController.toggle_fault(ChaosFaultType.GEMINI_OFFLINE, False, admin_p)
