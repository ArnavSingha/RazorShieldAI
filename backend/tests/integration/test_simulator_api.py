"""
RazorShield AI — Integration Tests for Attack Simulator & Chaos REST APIs
Verifies GET /api/v1/simulator/scenarios, GET /api/v1/simulator/chaos/status,
POST /api/v1/simulator/chaos/toggle, and POST /api/v1/simulator/run REST endpoints.
"""

import pytest
from backend.app.main import handle_request
from backend.app.risk_service import RiskPipelineService
from backend.app.simulator.chaos_engine import ChaosController


@pytest.fixture
def simulator_api_setup():
    ChaosController.reset_all_faults()
    svc = RiskPipelineService()
    yield svc
    ChaosController.reset_all_faults()


def test_simulator_scenarios_and_chaos_status_api(simulator_api_setup):
    svc = simulator_api_setup

    # 1. GET /api/v1/simulator/scenarios
    status_scen, resp_scen = handle_request(
        method="GET",
        path="/api/v1/simulator/scenarios",
        headers={},
        body_json={},
        service_instance=svc,
    )
    assert status_scen == 200
    assert "ATO-001" in resp_scen["data"]
    assert "MULE_RING-003" in resp_scen["data"]

    # 2. GET /api/v1/simulator/chaos/status
    status_st, resp_st = handle_request(
        method="GET",
        path="/api/v1/simulator/chaos/status",
        headers={},
        body_json={},
        service_instance=svc,
    )
    assert status_st == 200
    assert resp_st["data"]["enabled"] is True


def test_toggle_chaos_and_run_replay_api(simulator_api_setup):
    svc = simulator_api_setup

    # 1. POST /api/v1/simulator/chaos/toggle (Authenticated Admin Secret Key)
    status_tog, resp_tog = handle_request(
        method="POST",
        path="/api/v1/simulator/chaos/toggle",
        headers={"Authorization": "test_admin_token_xyz99"},
        body_json={"fault": "GEMINI_OFFLINE", "enable": True, "ttl_seconds": 60.0},
        service_instance=svc,
    )
    assert status_tog == 200
    assert "GEMINI_OFFLINE" in resp_tog["data"]["active_faults"]

    # 2. POST /api/v1/simulator/run
    status_run, resp_run = handle_request(
        method="POST",
        path="/api/v1/simulator/run",
        headers={"Authorization": "test_operator_token_xyz77"},
        body_json={"scenario_type": "ATO-001", "seed": 5555, "event_count": 5},
        service_instance=svc,
    )
    assert status_run == 200
    assert resp_run["status"] == "SUCCESS"
    assert resp_run["data"]["scenario_id"] == "ATO-001"
    assert resp_run["data"]["ai_provider"] == "DETERMINISTIC_FALLBACK"
    assert resp_run["data"]["unsafe_action_count"] == 0
