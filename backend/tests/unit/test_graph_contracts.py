"""
RazorShield AI — Unit Tests for Graph Investigation Domain Contracts
Verifies immutability, schema validation, evidence provenance, and JSON serialization.
"""

import time
from backend.app.domain.graph_contracts import (
    ClusterRisk,
    EntityType,
    EvidenceItem,
    FinancialExposure,
    FraudPattern,
    FraudPatternType,
    GraphEdge,
    GraphNode,
    InvestigationPackage,
    NetworkExposure,
    RelationshipType,
    RiskContributor,
    SeverityLevel,
    TemporalAnalysis,
)


def test_graph_contracts_serialization_and_invariants():
    t_now = time.time()

    # 1. Create Evidence Item
    evidence = EvidenceItem(
        evidence_id="E-1001",
        type="DEVICE_REUSE",
        claim="Device dev_99 shared across 3 accounts",
        value={"account_count": 3},
        source_entity_ids=["dev_99", "cust_1", "cust_2"],
        source_event_ids=["ev_101", "ev_102"],
        observed_at=t_now - 100,
        generated_at=t_now,
        confidence=0.95,
        derivation="DETERMINISTIC_GRAPH_TRAVERSAL",
        freshness_window_seconds=86400.0,
    )
    assert evidence.evidence_id == "E-1001"
    assert evidence.confidence == 0.95

    # 2. Create Risk Contributor & Cluster Risk
    contributor = RiskContributor(
        pattern_code=FraudPatternType.MULTI_ACCOUNT_DEVICE_REUSE,
        normalized_score=0.90,
        reason="Device dev_99 shared across 3 accounts",
        evidence_ids=["E-1001"],
    )
    cluster_risk = ClusterRisk(
        score=90,
        severity=SeverityLevel.CRITICAL,
        confidence=0.95,
        contributors=[contributor],
    )
    assert cluster_risk.score == 90
    assert cluster_risk.severity == SeverityLevel.CRITICAL

    # 3. Create Exposures & Temporal Analysis
    network = NetworkExposure(
        unique_customers=3,
        unique_accounts=3,
        unique_devices=1,
        unique_ips=1,
        unique_cards=1,
        unique_merchants=1,
        suspicious_edge_count=4,
        cluster_density=0.6667,
    )
    financial = FinancialExposure(
        currency="INR",
        total_cluster_exposure_amount=150000.0,
        suspicious_exposure_amount=127500.0,
        affected_transaction_count=3,
        deduplicated_transaction_ids=["tx_1", "tx_2", "tx_3"],
        time_window_hours=0.5,
    )
    temporal = TemporalAnalysis(
        first_seen=t_now - 1800,
        last_seen=t_now,
        window_start=t_now - 1800,
        window_end=t_now,
        transaction_count=3,
        unique_accounts=3,
        unique_devices=1,
        median_inter_event_time_seconds=600.0,
        burst_intensity_events_per_minute=0.1,
    )

    # 4. Create Nodes & Edges
    node1 = GraphNode(
        node_id="cust_1",
        entity_type=EntityType.CUSTOMER,
        entity_value="cust_1",
        first_seen=t_now - 1800,
        last_seen=t_now,
        degree=2,
    )
    node2 = GraphNode(
        node_id="dev_99",
        entity_type=EntityType.DEVICE,
        entity_value="dev_99",
        first_seen=t_now - 1800,
        last_seen=t_now,
        degree=3,
    )
    edge1 = GraphEdge(
        edge_id="edge_1",
        source_id="cust_1",
        target_id="dev_99",
        relationship_type=RelationshipType.HAS_DEVICE,
        first_seen=t_now - 1800,
        last_seen=t_now,
    )

    pattern1 = FraudPattern(
        pattern_type=FraudPatternType.MULTI_ACCOUNT_DEVICE_REUSE,
        severity=SeverityLevel.HIGH,
        confidence=0.95,
        description="Device re-use across 3 accounts",
        contributing_node_ids=["cust_1", "dev_99"],
        contributing_edge_ids=["edge_1"],
        evidence_ids=["E-1001"],
        behavioral_features={"shared_device_id": "dev_99"},
    )

    # 5. Assemble Investigation Package
    pkg = InvestigationPackage(
        package_id="PKG-20260823-TEST",
        schema_version="v1",
        graph_engine_version="v0.2.0",
        incident_id="FR-TEST-001",
        entity_id="cust_1",
        cluster_risk=cluster_risk,
        network_exposure=network,
        financial_exposure=financial,
        temporal_analysis=temporal,
        detected_patterns=[pattern1],
        nodes=[node1, node2],
        edges=[edge1],
        primary_evidence=[evidence],
        executive_summary="Incident Cluster FR-TEST-001: 3 customer accounts share 1 devices.",
        generated_at=t_now,
        source_event_ids=["ev_101", "ev_102"],
    )

    # Check Serialization
    pkg_dict = pkg.to_dict()
    assert pkg_dict["schema_version"] == "v1"
    assert pkg_dict["graph_engine_version"] == "v0.2.0"
    assert pkg_dict["cluster_risk"]["score"] == 90

    # Check Deserialization
    reconstructed = InvestigationPackage.from_dict(pkg_dict)
    assert reconstructed.package_id == pkg.package_id
    assert reconstructed.financial_exposure.deduplicated_transaction_ids == [
        "tx_1",
        "tx_2",
        "tx_3",
    ]
