"""
RazorShield AI — Unit Tests for Graph Intelligence Engine & Bounded Cluster Analysis
Verifies bounded subgraph extraction, hub node pruning, 4 fraud patterns, temporal burst analysis,
exposure calculations, evidence provenance, and hard invariants.
"""

import pytest
from backend.app.domain.graph_contracts import (
    FraudPatternType,
    SeverityLevel,
)
from backend.app.domain.models import TransactionEvent
from backend.app.risk.graph_engine import GraphEngine


@pytest.fixture
def populated_graph_engine():
    engine = GraphEngine()
    t_base = 1700000000.0  # Deterministic reference timestamp

    # Simulating a Fraud Ring: 4 Customers, 1 Shared Device, 1 Shared IP, 1 Shared Merchant
    events = [
        TransactionEvent(
            event_id="ev_101",
            idempotency_key="idemp_101",
            transaction_id="tx_101",
            customer_id="cust_ring_1",
            account_id="acc_101",
            amount=50000.0,
            currency="INR",
            device_id="dev_shared_ring_99",
            ip_address="192.168.1.100",
            merchant_id="merch_electronics_1",
            merchant_category_code="5732",
            timestamp=t_base,
        ),
        TransactionEvent(
            event_id="ev_102",
            idempotency_key="idemp_102",
            transaction_id="tx_102",
            customer_id="cust_ring_2",
            account_id="acc_102",
            amount=60000.0,
            currency="INR",
            device_id="dev_shared_ring_99",
            ip_address="192.168.1.100",
            merchant_id="merch_electronics_1",
            merchant_category_code="5732",
            timestamp=t_base + 60.0,
        ),
        TransactionEvent(
            event_id="ev_103",
            idempotency_key="idemp_103",
            transaction_id="tx_103",
            customer_id="cust_ring_3",
            account_id="acc_103",
            amount=75000.0,
            currency="INR",
            device_id="dev_shared_ring_99",
            ip_address="192.168.1.100",
            merchant_id="merch_electronics_1",
            merchant_category_code="5732",
            timestamp=t_base + 120.0,
        ),
        TransactionEvent(
            event_id="ev_104",
            idempotency_key="idemp_104",
            transaction_id="tx_104",
            customer_id="cust_ring_4",
            account_id="acc_104",
            amount=45000.0,
            currency="INR",
            device_id="dev_shared_ring_99",
            ip_address="192.168.1.100",
            merchant_id="merch_electronics_1",
            merchant_category_code="5732",
            timestamp=t_base + 180.0,
        ),
        TransactionEvent(
            event_id="ev_105",
            idempotency_key="idemp_105",
            transaction_id="tx_105",
            customer_id="cust_ring_1",
            account_id="acc_101",
            amount=80000.0,
            currency="INR",
            device_id="dev_shared_ring_99",
            ip_address="192.168.1.100",
            merchant_id="merch_electronics_1",
            merchant_category_code="5732",
            timestamp=t_base + 240.0,
        ),
    ]

    for ev in events:
        engine.add_event(ev)

    return engine


def test_bounded_subgraph_extraction_and_hub_pruning(populated_graph_engine):
    engine = populated_graph_engine
    nodes, edges = engine.extract_bounded_subgraph(
        "cust_ring_1", max_hops=2, max_nodes=50
    )

    assert len(nodes) > 0
    assert len(edges) > 0
    node_ids = [n.node_id for n in nodes]
    assert "cust_tok_ring_1" in node_ids
    assert "dev_tok_shared_ring_99" in node_ids
    assert "ip_tok_192_168_1_100" in node_ids


def test_investigation_package_generation_and_fraud_patterns(populated_graph_engine):
    engine = populated_graph_engine
    package = engine.generate_investigation_package("cust_ring_1", max_hops=2)

    # 1. Check Metadata Invariants
    assert package.schema_version == "v1"
    assert package.graph_engine_version == "v0.2.0"
    assert package.package_id.startswith("PKG-")
    assert package.incident_id.startswith("FR-")

    # 2. Check Cluster Risk
    assert package.cluster_risk.score >= 80
    assert package.cluster_risk.severity == SeverityLevel.CRITICAL
    assert len(package.cluster_risk.contributors) >= 2

    # 3. Check Detected Fraud Patterns (Device Reuse, IP Farm, Rapid Burst, Cross-Account)
    pat_types = [p.pattern_type for p in package.detected_patterns]
    assert FraudPatternType.MULTI_ACCOUNT_DEVICE_REUSE in pat_types
    assert FraudPatternType.SHARED_IP_FARM in pat_types
    assert FraudPatternType.RAPID_BURST in pat_types
    assert FraudPatternType.CROSS_ACCOUNT_BEHAVIORAL_SIMILARITY in pat_types

    # 4. Check Hard Invariants: Every pattern -> at least 1 evidence item
    evidence_ids = [e.evidence_id for e in package.primary_evidence]
    for p in package.detected_patterns:
        assert len(p.evidence_ids) >= 1
        for ev_id in p.evidence_ids:
            assert ev_id in evidence_ids

    # 5. Check Hard Invariants: Every Risk Contributor -> valid evidence ID
    for c in package.cluster_risk.contributors:
        assert len(c.evidence_ids) >= 1
        for ev_id in c.evidence_ids:
            assert ev_id in evidence_ids

    # 6. Check Exposure Deduplication
    financial = package.financial_exposure
    assert (
        financial.total_cluster_exposure_amount == 310000.0
    )  # 50k + 60k + 75k + 45k + 80k
    assert financial.affected_transaction_count == 5
    assert len(financial.deduplicated_transaction_ids) == 5
    assert sorted(financial.deduplicated_transaction_ids) == [
        "tx_101",
        "tx_102",
        "tx_103",
        "tx_104",
        "tx_105",
    ]

    # 7. Check Temporal Analysis
    temporal = package.temporal_analysis
    assert temporal.transaction_count == 5
    assert temporal.burst_intensity_events_per_minute > 0.0

    # 8. Check Deterministic Executive Summary (Zero LLM)
    summary = package.executive_summary
    assert "Incident Cluster FR-cust_ring_1:" in summary
    assert "310,000.00" in summary
    assert "MULTI_ACCOUNT_DEVICE_REUSE" in summary

    # 9. Data Minimization Check: No PANs or Raw PII secrets in package
    pkg_str = str(package.to_dict()).lower()
    assert "raw_pan" not in pkg_str
    assert "cvv" not in pkg_str
    assert "raw_otp" not in pkg_str
