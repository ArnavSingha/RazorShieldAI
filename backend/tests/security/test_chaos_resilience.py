"""
RazorShield AI — Resilience & Security Tests for Chaos Mode (Slice 5)
Verifies RBAC protection of chaos control APIs, failure injection under 7 fault types,
compound failure resilience, and the hard safety invariant (unsafe_action_count == 0).
"""

import pytest
from backend.app.domain.policy_contracts import UserRole
from backend.app.domain.simulator_contracts import (
    ChaosFaultType,
    ScenarioConfig,
    SimulatorMode,
    ThreatScenarioType,
)
from backend.app.gateway.action_gateway import ActionGateway
from backend.app.policy.rbac import TrustedPrincipal, UnauthorizedRoleError
from backend.app.risk_service import RiskPipelineService
from backend.app.simulator.chaos_engine import ChaosController
from backend.app.simulator.replay_engine import ScenarioReplayEngine


@pytest.fixture
def chaos_setup():
    ChaosController.reset_all_faults()
    ActionGateway.reset_gateway_state()
    svc = RiskPipelineService()
    admin_principal = TrustedPrincipal(
        principal_id="usr_admin_01", role=UserRole.ADMIN, is_authenticated=True
    )
    operator_principal = TrustedPrincipal(
        principal_id="usr_op_01", role=UserRole.MERCHANT_OPERATOR, is_authenticated=True
    )
    yield svc, admin_principal, operator_principal
    ChaosController.reset_all_faults()
    ActionGateway.reset_gateway_state()


def test_unauthorized_chaos_toggle_rejected(chaos_setup):
    _, _, operator_principal = chaos_setup
    # Merchant operator attempting to toggle chaos raises UnauthorizedRoleError
    with pytest.raises(UnauthorizedRoleError):
        ChaosController.toggle_fault(
            fault=ChaosFaultType.GEMINI_OFFLINE,
            enable=True,
            principal=operator_principal,
        )


def test_gemini_offline_fallbacks_safely_zero_unsafe_actions(chaos_setup):
    svc, admin_principal, operator_principal = chaos_setup
    ChaosController.toggle_fault(ChaosFaultType.GEMINI_OFFLINE, True, admin_principal)

    config = ScenarioConfig(scenario_type=ThreatScenarioType.MULE_RING_003, seed=1001)
    report = ScenarioReplayEngine.run_replay(config, operator_principal, svc)

    assert report.ai_investigation_completed is True
    assert report.ai_provider == "DETERMINISTIC_FALLBACK"
    assert report.unsafe_action_count == 0
    assert report.verdict == "DEGRADED_SAFE"


def test_audit_offline_causes_fail_closed_rejection(chaos_setup):
    svc, admin_principal, operator_principal = chaos_setup
    ChaosController.toggle_fault(ChaosFaultType.GEMINI_OFFLINE, True, admin_principal)
    ChaosController.toggle_fault(ChaosFaultType.AUDIT_OFFLINE, True, admin_principal)

    config = ScenarioConfig(scenario_type=ThreatScenarioType.ATO_001, seed=2002)
    report = ScenarioReplayEngine.run_replay(config, operator_principal, svc)

    assert report.execution_status.value == "REJECTED"
    assert report.unsafe_action_count == 0
    assert report.verdict == "DEGRADED_SAFE"


def test_redis_offline_in_production_simulation_triggers_safe_failure(chaos_setup):
    svc, admin_principal, operator_principal = chaos_setup
    ChaosController.toggle_fault(ChaosFaultType.REDIS_OFFLINE, True, admin_principal)

    config = ScenarioConfig(
        scenario_type=ThreatScenarioType.CARD_TESTING_002,
        seed=3003,
        mode=SimulatorMode.PRODUCTION_SIMULATION,
    )
    report = ScenarioReplayEngine.run_replay(config, operator_principal, svc)

    assert report.execution_status.value == "REJECTED"
    assert report.unsafe_action_count == 0
    assert report.verdict == "DEGRADED_SAFE"


def test_action_gateway_offline_rejects_execution(chaos_setup):
    svc, admin_principal, operator_principal = chaos_setup
    ChaosController.toggle_fault(ChaosFaultType.GEMINI_OFFLINE, True, admin_principal)
    ChaosController.toggle_fault(ChaosFaultType.GATEWAY_OFFLINE, True, admin_principal)

    config = ScenarioConfig(
        scenario_type=ThreatScenarioType.SHARED_DEVICE_005, seed=4004
    )
    report = ScenarioReplayEngine.run_replay(config, operator_principal, svc)

    assert report.execution_status.value == "REJECTED"
    assert report.unsafe_action_count == 0
    assert report.verdict == "DEGRADED_SAFE"


def test_compound_failures_gemini_and_audit_offline(chaos_setup):
    svc, admin_principal, operator_principal = chaos_setup
    ChaosController.toggle_fault(ChaosFaultType.GEMINI_OFFLINE, True, admin_principal)
    ChaosController.toggle_fault(ChaosFaultType.AUDIT_OFFLINE, True, admin_principal)

    config = ScenarioConfig(scenario_type=ThreatScenarioType.MULE_RING_003, seed=5005)
    report = ScenarioReplayEngine.run_replay(config, operator_principal, svc)

    assert report.ai_provider == "DETERMINISTIC_FALLBACK"
    assert report.execution_status.value == "REJECTED"
    assert report.unsafe_action_count == 0
    assert report.verdict == "DEGRADED_SAFE"
