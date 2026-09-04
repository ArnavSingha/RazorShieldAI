"""
RazorShield AI — Integration Tests: End-to-End Real IsolationForest Verification
Proves that RiskService -> MLEngine -> RealIsolationForestModel -> IsolationForest pipeline
instantiates and evaluates real ML model features.
"""

import uuid

from backend.app.risk.ml_engine import RealIsolationForestModel
from backend.app.risk_service import RiskPipelineService


def test_end_to_end_iforest_model_integration(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"iforest_e2e_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    # Assert that MLEngine model is an instance of RealIsolationForestModel
    assert isinstance(service.ml_engine.model, RealIsolationForestModel)

    # Process transaction event through pipeline
    decision = service.process_transaction_event(valid_transaction_payload)
    assert decision.transaction_id == valid_transaction_payload["transaction_id"]

    # Verify ML Component score breakdown
    ml_comp = decision.components["ml"]
    assert "raw_score" in ml_comp
    assert "weight" in ml_comp
    assert ml_comp["weight"] == 0.30
