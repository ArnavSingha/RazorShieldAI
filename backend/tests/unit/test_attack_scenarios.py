"""
RazorShield AI — Unit Tests for Synthetic Threat Scenarios (Slice 5)
Verifies generation of all 7 threat scenario vectors and 100% deterministic seed reproducibility.
"""

from backend.app.domain.simulator_contracts import ScenarioConfig, ThreatScenarioType
from backend.app.simulator.attack_scenarios import AttackScenarioGenerator


def test_all_7_attack_scenarios_generate_valid_events():
    for scen_type in ThreatScenarioType:
        config = ScenarioConfig(scenario_type=scen_type, seed=1001, event_count=10)
        events, ground_truth = AttackScenarioGenerator.generate_scenario_events(config)

        assert len(events) >= 2
        assert ground_truth["scenario_id"] == scen_type.value
        assert ground_truth["ground_truth_threat"] != ""
        assert ground_truth["expected_detection"] is True
        assert ground_truth["target_entity"] != ""


def test_deterministic_seed_reproducibility():
    config1 = ScenarioConfig(
        scenario_type=ThreatScenarioType.MULE_RING_003, seed=8888, event_count=8
    )
    config2 = ScenarioConfig(
        scenario_type=ThreatScenarioType.MULE_RING_003, seed=8888, event_count=8
    )

    events1, _ = AttackScenarioGenerator.generate_scenario_events(config1)
    events2, _ = AttackScenarioGenerator.generate_scenario_events(config2)

    assert len(events1) == len(events2)
    for ev1, ev2 in zip(events1, events2):
        assert ev1.event_id == ev2.event_id
        assert ev1.amount == ev2.amount
        assert ev1.device_id == ev2.device_id
        assert ev1.ip_address == ev2.ip_address
