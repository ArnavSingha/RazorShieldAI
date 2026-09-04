"""
RazorShield AI — Independent & Stateful Evaluation Detector Architecture
Implements stateful sequential event-stream detectors:
1. RulesOnlyDetector
2. MLOnlyDetector
3. RulesMLDetector
4. RulesMLGraphDetector

Features:
- Stateful Event Stream Evaluation (accumulates prior history deterministically)
- PredictionResult Enum: POSITIVE, NEGATIVE, ERROR, ABSTAIN (System errors NEVER become fraud positives)
- Zero Label Leakage Guarantee: No prediction method accesses ground truth fields.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any

from backend.app.domain.models import CustomerProfile, TransactionEvent
from backend.app.risk_service import RiskPipelineService


class PredictionStatus(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    ERROR = "ERROR"
    ABSTAIN = "ABSTAIN"


@dataclass
class PredictionResult:
    status: PredictionStatus
    score: float = 0.0
    reason_codes: list[str] = field(default_factory=list)
    error_message: str = ""


@dataclass
class EvaluationState:
    evaluation_run_id: str
    detector_name: str
    sequence_index: int = 0
    historical_event_count: int = 0
    history: list[TransactionEvent] = field(default_factory=list)


def prepare_clean_record(
    record: dict[str, Any], detector_tag: str, seq_idx: int, run_id: str = ""
) -> dict[str, Any]:
    """Strips ground truth fields and assigns unique run-scoped idempotency key."""
    clean = dict(record)
    clean.pop("ground_truth_is_fraud", None)
    clean.pop("ground_truth_threat", None)
    tag = f"{run_id}_{detector_tag}" if run_id else detector_tag
    clean["idempotency_key"] = f"eval_{tag}_{seq_idx}_{clean.get('transaction_id', '')}"
    clean["transaction_id"] = f"tx_{tag}_{seq_idx}_{clean.get('transaction_id', '')}"
    return clean


class BaseDetector(ABC):
    @abstractmethod
    def predict_and_update(
        self, record: dict[str, Any], state: EvaluationState
    ) -> PredictionResult:
        """Predicts risk for record using PRIOR history only, then appends event to state."""
        pass


class RulesOnlyDetector(BaseDetector):
    def predict_and_update(
        self, record: dict[str, Any], state: EvaluationState
    ) -> PredictionResult:
        try:
            clean_rec = prepare_clean_record(
                record, "rules", state.sequence_index, state.evaluation_run_id
            )
            event = TransactionEvent(
                **{
                    k: v
                    for k, v in clean_rec.items()
                    if k in TransactionEvent.__dataclass_fields__
                }
            )

            # Evaluate against accumulated state history
            c_1h, s_1h = 0, 0.0
            cutoff_1h = event.timestamp - 3600.0
            for past in state.history:
                if (
                    past.customer_id == event.customer_id
                    and past.timestamp >= cutoff_1h
                ):
                    c_1h += 1
                    s_1h += past.amount

            is_high_velocity = (
                (c_1h >= 4) or (s_1h > 50000.0) or (event.amount > 120000.0)
            )
            score = 75.0 if is_high_velocity else 15.0
            status = (
                PredictionStatus.POSITIVE
                if is_high_velocity
                else PredictionStatus.NEGATIVE
            )

            # Append event to state history AFTER prediction
            state.history.append(event)
            state.sequence_index += 1
            state.historical_event_count += 1

            return PredictionResult(status=status, score=score)
        except Exception as e:
            return PredictionResult(status=PredictionStatus.ERROR, error_message=str(e))


class MLOnlyDetector(BaseDetector):
    def __init__(self, svc: RiskPipelineService):
        self.svc = svc
        self.threshold = 0.50
        self.model_version = "IsolationForest_v1.0"
        self.threshold_source = "VALIDATION"
        self.test_touched_before_final_evaluation = False

    def train_baseline(self, train_records: list[dict[str, Any]]) -> str:
        """Fits baseline ML model on training records only."""
        clean_events = []
        for i, r in enumerate(train_records):
            clean_rec = prepare_clean_record(r, "train", i)
            ev = TransactionEvent(
                **{
                    k: v
                    for k, v in clean_rec.items()
                    if k in TransactionEvent.__dataclass_fields__
                }
            )
            clean_events.append(ev)

        self.svc.ml_engine.fit_baseline(clean_events)
        data_str = "".join(e.transaction_id for e in clean_events).encode("utf-8")
        return hashlib.sha256(data_str).hexdigest()[:16]

    def calibrate(self, val_records: list[dict[str, Any]]) -> str:
        """Calibrates threshold on validation set without test labels."""
        scores = []
        for i, r in enumerate(val_records):
            clean_rec = prepare_clean_record(r, "val", i)
            ev = TransactionEvent(
                **{
                    k: v
                    for k, v in clean_rec.items()
                    if k in TransactionEvent.__dataclass_fields__
                }
            )
            prof = CustomerProfile(customer_id=ev.customer_id)
            res = self.svc.ml_engine.predict_anomaly(ev, customer_profile=prof)
            scores.append(res.normalized_score)

        if scores:
            scores.sort()
            idx = int(len(scores) * 0.80)
            self.threshold = scores[min(idx, len(scores) - 1)]

        data_str = "".join(str(s) for s in scores).encode("utf-8")
        return hashlib.sha256(data_str).hexdigest()[:16]

    def predict_and_update(
        self, record: dict[str, Any], state: EvaluationState
    ) -> PredictionResult:
        try:
            clean_rec = prepare_clean_record(
                record, "ml", state.sequence_index, state.evaluation_run_id
            )
            event = TransactionEvent(
                **{
                    k: v
                    for k, v in clean_rec.items()
                    if k in TransactionEvent.__dataclass_fields__
                }
            )
            prof = CustomerProfile(customer_id=event.customer_id)
            ml_res = self.svc.ml_engine.predict_anomaly(event, customer_profile=prof)

            is_anomalous = ml_res.normalized_score >= self.threshold
            status = (
                PredictionStatus.POSITIVE if is_anomalous else PredictionStatus.NEGATIVE
            )

            state.history.append(event)
            state.sequence_index += 1
            state.historical_event_count += 1

            return PredictionResult(
                status=status, score=ml_res.normalized_score * 100.0
            )
        except Exception as e:
            return PredictionResult(status=PredictionStatus.ERROR, error_message=str(e))


class RulesMLDetector(BaseDetector):
    def __init__(self, svc: RiskPipelineService):
        self.svc = svc

    def predict_and_update(
        self, record: dict[str, Any], state: EvaluationState
    ) -> PredictionResult:
        try:
            clean_rec = prepare_clean_record(
                record, "rules_ml", state.sequence_index, state.evaluation_run_id
            )
            decision = self.svc.process_transaction_event(clean_rec)

            is_trigger = decision.risk_score >= 50
            status = (
                PredictionStatus.POSITIVE if is_trigger else PredictionStatus.NEGATIVE
            )

            event = TransactionEvent(
                **{
                    k: v
                    for k, v in clean_rec.items()
                    if k in TransactionEvent.__dataclass_fields__
                }
            )
            state.history.append(event)
            state.sequence_index += 1
            state.historical_event_count += 1

            return PredictionResult(status=status, score=float(decision.risk_score))
        except Exception as e:
            return PredictionResult(status=PredictionStatus.ERROR, error_message=str(e))


class RulesMLGraphDetector(BaseDetector):
    def __init__(self, svc: RiskPipelineService):
        self.svc = svc

    def predict_and_update(
        self, record: dict[str, Any], state: EvaluationState
    ) -> PredictionResult:
        try:
            clean_rec = prepare_clean_record(
                record, "rules_ml_graph", state.sequence_index, state.evaluation_run_id
            )

            # Explicit graph-derived feature extraction over accumulated state history
            shared_device_accounts = len(
                {
                    past.customer_id
                    for past in state.history
                    if past.device_id == clean_rec.get("device_id")
                    and past.customer_id != clean_rec.get("customer_id")
                }
            )
            shared_ip_accounts = len(
                {
                    past.customer_id
                    for past in state.history
                    if past.ip_address == clean_rec.get("ip_address")
                    and past.customer_id != clean_rec.get("customer_id")
                }
            )
            multi_account_device_reuse = shared_device_accounts >= 1
            shared_ip_farm = shared_ip_accounts >= 2
            graph_feature_triggered = multi_account_device_reuse or shared_ip_farm

            decision = self.svc.process_transaction_event(clean_rec)
            is_trigger = graph_feature_triggered

            status = (
                PredictionStatus.POSITIVE if is_trigger else PredictionStatus.NEGATIVE
            )
            score = max(
                float(decision.risk_score),
                85.0 if graph_feature_triggered else float(decision.risk_score),
            )

            event = TransactionEvent(
                **{
                    k: v
                    for k, v in clean_rec.items()
                    if k in TransactionEvent.__dataclass_fields__
                }
            )
            state.history.append(event)
            state.sequence_index += 1
            state.historical_event_count += 1

            return PredictionResult(status=status, score=score)
        except Exception as e:
            return PredictionResult(status=PredictionStatus.ERROR, error_message=str(e))
