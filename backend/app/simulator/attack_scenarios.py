"""
RazorShield AI — Synthetic Threat Scenario Generators
Generates deterministic synthetic transaction event sequences for 7 threat vectors:
ATO-001, CARD_TESTING-002, MULE_RING-003, VELOCITY-004, SHARED_DEVICE-005, CROSS_BORDER-006, MERCHANT_COMPROMISE-007.
Uses explicit integer seeds for 100% reproducible scenario event generation.
"""

import random
from typing import Any, Dict, List, Tuple
from backend.app.domain.models import TransactionEvent
from backend.app.domain.policy_contracts import PolicyAction
from backend.app.domain.simulator_contracts import ScenarioConfig, ThreatScenarioType


class AttackScenarioGenerator:
    """Generates reproducible threat scenario event streams with expected benchmark outcomes."""

    @classmethod
    def generate_scenario_events(
        cls, config: ScenarioConfig
    ) -> Tuple[List[TransactionEvent], Dict[str, Any]]:
        """
        Generates list of TransactionEvent objects and expected ground-truth metadata.
        Uses config.seed for deterministic pseudo-random sequence generation.
        """
        rng = random.Random(config.seed)
        t_base = 1700000000.0
        events: List[TransactionEvent] = []

        scenario_type = config.scenario_type
        cust_prefix = (
            config.customer_id
            or f"cust_{scenario_type.value.lower().replace('-', '_')}"
        )

        if scenario_type == ThreatScenarioType.ATO_001:
            # Account Takeover: Normal txns -> Sudden Device/IP/Geo Swap + High Value Transfer
            for i in range(config.event_count - 1):
                events.append(
                    TransactionEvent(
                        event_id=f"ev_ato_{config.seed}_{i}",
                        idempotency_key=f"idemp_ato_{config.seed}_{i}",
                        transaction_id=f"tx_ato_{config.seed}_{i}",
                        customer_id=cust_prefix,
                        account_id=f"acc_{cust_prefix}",
                        amount=rng.uniform(1000.0, 5000.0),
                        currency="INR",
                        device_id="dev_trusted_user",
                        ip_address="10.0.0.50",
                        merchant_id=config.merchant_id,
                        merchant_category_code="5732",
                        timestamp=t_base + (i * 3600.0),
                    )
                )
            # Takeover Event
            events.append(
                TransactionEvent(
                    event_id=f"ev_ato_{config.seed}_attack",
                    idempotency_key=f"idemp_ato_{config.seed}_attack",
                    transaction_id=f"tx_ato_{config.seed}_attack",
                    customer_id=cust_prefix,
                    account_id=f"acc_{cust_prefix}",
                    amount=250000.0,
                    currency="INR",
                    device_id="dev_hacked_attacker",
                    ip_address="198.51.100.99",  # Geo Anomaly
                    merchant_id="merch_crypto_exchange",
                    merchant_category_code="6051",
                    timestamp=t_base + ((config.event_count - 1) * 3600.0) + 60.0,
                )
            )
            ground_truth = {
                "scenario_id": "ATO-001",
                "ground_truth_threat": "Account Takeover via Device/IP Swap + High-Value Transfer",
                "expected_detection": True,
                "expected_pattern": "CROSS_ACCOUNT_BEHAVIORAL_SIMILARITY",
                "expected_policy": PolicyAction.STEP_UP,
                "target_entity": cust_prefix,
            }

        elif scenario_type == ThreatScenarioType.CARD_TESTING_002:
            # Card Testing: Rapid succession of micro-amounts (INR 10-50)
            for i in range(config.event_count):
                events.append(
                    TransactionEvent(
                        event_id=f"ev_ct_{config.seed}_{i}",
                        idempotency_key=f"idemp_ct_{config.seed}_{i}",
                        transaction_id=f"tx_ct_{config.seed}_{i}",
                        customer_id=cust_prefix,
                        account_id=f"acc_{cust_prefix}",
                        amount=rng.uniform(10.0, 50.0),
                        currency="INR",
                        device_id=f"dev_bot_{config.seed}",
                        ip_address="192.0.2.1",
                        merchant_id=config.merchant_id,
                        merchant_category_code="5732",
                        timestamp=t_base + (i * 2.0),  # Every 2 seconds
                    )
                )
            ground_truth = {
                "scenario_id": "CARD_TESTING-002",
                "ground_truth_threat": "Rapid Velocity Micro-Amount Card Testing Attack",
                "expected_detection": True,
                "expected_pattern": "RAPID_BURST",
                "expected_policy": PolicyAction.HOLD,
                "target_entity": cust_prefix,
            }

        elif scenario_type == ThreatScenarioType.MULE_RING_003:
            # Mule Ring: 6 different customer accounts sharing 1 device & IP farm
            shared_dev = f"dev_farm_{config.seed}"
            shared_ip = "192.168.1.100"
            for i in range(config.event_count):
                c_id = f"{cust_prefix}_mule_{i % 6}"
                events.append(
                    TransactionEvent(
                        event_id=f"ev_mule_{config.seed}_{i}",
                        idempotency_key=f"idemp_mule_{config.seed}_{i}",
                        transaction_id=f"tx_mule_{config.seed}_{i}",
                        customer_id=c_id,
                        account_id=f"acc_{c_id}",
                        amount=rng.uniform(80000.0, 180000.0),
                        currency="INR",
                        device_id=shared_dev,
                        ip_address=shared_ip,
                        merchant_id=config.merchant_id,
                        merchant_category_code="5732",
                        timestamp=t_base + (i * 15.0),
                    )
                )
            ground_truth = {
                "scenario_id": "MULE_RING-003",
                "ground_truth_threat": "Coordinated Multi-Account Fraud Ring with Shared Device & IP",
                "expected_detection": True,
                "expected_pattern": "MULTI_ACCOUNT_DEVICE_REUSE",
                "expected_policy": PolicyAction.BLOCK,
                "target_entity": f"{cust_prefix}_mule_0",
            }

        elif scenario_type == ThreatScenarioType.VELOCITY_004:
            # High Velocity Burst (>10 txns/min)
            for i in range(config.event_count):
                events.append(
                    TransactionEvent(
                        event_id=f"ev_vel_{config.seed}_{i}",
                        idempotency_key=f"idemp_vel_{config.seed}_{i}",
                        transaction_id=f"tx_vel_{config.seed}_{i}",
                        customer_id=cust_prefix,
                        account_id=f"acc_{cust_prefix}",
                        amount=rng.uniform(15000.0, 45000.0),
                        currency="INR",
                        device_id=f"dev_vel_{config.seed}",
                        ip_address="10.0.0.10",
                        merchant_id=config.merchant_id,
                        merchant_category_code="5732",
                        timestamp=t_base + (i * 3.0),
                    )
                )
            ground_truth = {
                "scenario_id": "VELOCITY-004",
                "ground_truth_threat": "High Frequency Velocity Burst Anomaly",
                "expected_detection": True,
                "expected_pattern": "RAPID_BURST",
                "expected_policy": PolicyAction.HOLD,
                "target_entity": cust_prefix,
            }

        elif scenario_type == ThreatScenarioType.SHARED_DEVICE_005:
            # Shared Device Reuse Across 8+ Accounts
            shared_dev = f"dev_shared_farm_{config.seed}"
            for i in range(max(8, config.event_count)):
                c_id = f"{cust_prefix}_user_{i}"
                events.append(
                    TransactionEvent(
                        event_id=f"ev_shdev_{config.seed}_{i}",
                        idempotency_key=f"idemp_shdev_{config.seed}_{i}",
                        transaction_id=f"tx_shdev_{config.seed}_{i}",
                        customer_id=c_id,
                        account_id=f"acc_{c_id}",
                        amount=rng.uniform(50000.0, 120000.0),
                        currency="INR",
                        device_id=shared_dev,
                        ip_address=f"10.0.0.{10 + (i % 3)}",
                        merchant_id=config.merchant_id,
                        merchant_category_code="5732",
                        timestamp=t_base + (i * 20.0),
                    )
                )
            ground_truth = {
                "scenario_id": "SHARED_DEVICE-005",
                "ground_truth_threat": "Device Farm Reuse Across 8+ Customer Accounts",
                "expected_detection": True,
                "expected_pattern": "MULTI_ACCOUNT_DEVICE_REUSE",
                "expected_policy": PolicyAction.HOLD,
                "target_entity": f"{cust_prefix}_user_0",
            }

        elif scenario_type == ThreatScenarioType.CROSS_BORDER_006:
            # Cross-Border Geo Anomaly: Transaction in Mumbai followed 5 mins later in London
            events.append(
                TransactionEvent(
                    event_id=f"ev_cb_{config.seed}_1",
                    idempotency_key=f"idemp_cb_{config.seed}_1",
                    transaction_id=f"tx_cb_{config.seed}_1",
                    customer_id=cust_prefix,
                    account_id=f"acc_{cust_prefix}",
                    amount=20000.0,
                    currency="INR",
                    device_id=f"dev_cb_{config.seed}",
                    ip_address="49.207.180.1",  # Mumbai, India
                    merchant_id=config.merchant_id,
                    merchant_category_code="5732",
                    timestamp=t_base,
                )
            )
            events.append(
                TransactionEvent(
                    event_id=f"ev_cb_{config.seed}_2",
                    idempotency_key=f"idemp_cb_{config.seed}_2",
                    transaction_id=f"tx_cb_{config.seed}_2",
                    customer_id=cust_prefix,
                    account_id=f"acc_{cust_prefix}",
                    amount=180000.0,
                    currency="GBP",
                    device_id=f"dev_cb_{config.seed}_foreign",
                    ip_address="81.2.69.142",  # London, UK
                    merchant_id="merch_uk_luxury",
                    merchant_category_code="5311",
                    timestamp=t_base + 300.0,  # 5 Mins later (Impossible flight)
                )
            )
            ground_truth = {
                "scenario_id": "CROSS_BORDER-006",
                "ground_truth_threat": "Impossible Traveler Cross-Border Geo Anomaly",
                "expected_detection": True,
                "expected_pattern": "CROSS_ACCOUNT_BEHAVIORAL_SIMILARITY",
                "expected_policy": PolicyAction.STEP_UP,
                "target_entity": cust_prefix,
            }

        else:  # ThreatScenarioType.MERCHANT_COMPROMISE_007
            # Merchant MCC Anomaly Spike: Sudden flood of high amount txns under MCC 7995 (Gambling)
            for i in range(config.event_count):
                events.append(
                    TransactionEvent(
                        event_id=f"ev_mc_{config.seed}_{i}",
                        idempotency_key=f"idemp_mc_{config.seed}_{i}",
                        transaction_id=f"tx_mc_{config.seed}_{i}",
                        customer_id=f"{cust_prefix}_victim_{i}",
                        account_id=f"acc_victim_{i}",
                        amount=rng.uniform(120000.0, 200000.0),
                        currency="INR",
                        device_id=f"dev_mc_{config.seed}_{i}",
                        ip_address=f"10.0.1.{i}",
                        merchant_id="merch_compromised_casino",
                        merchant_category_code="7995",  # Gambling
                        timestamp=t_base + (i * 10.0),
                    )
                )
            ground_truth = {
                "scenario_id": "MERCHANT_COMPROMISE-007",
                "ground_truth_threat": "Merchant MCC Anomaly & High Risk Spike",
                "expected_detection": True,
                "expected_pattern": "RAPID_BURST",
                "expected_policy": PolicyAction.HOLD,
                "target_entity": f"{cust_prefix}_victim_0",
            }

        return events, ground_truth
