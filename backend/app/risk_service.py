"""
RazorShield AI — Risk Pipeline Service
Primary orchestrator connecting validation -> atomic idempotency claim ->
tri-engine scoring -> policy engine decision -> fail-closed audit store.
"""

import time
from typing import Any

from backend.app.config import settings
from backend.app.domain.models import CustomerProfile, RiskDecision
from backend.app.exceptions import (
    AuditPersistenceError,
    IdempotencyConflictError,
    IdempotencyInProgressError,
)
from backend.app.infrastructure.storage_contracts import (
    AuditRepository,
    IdempotencyStore,
    PostgreSQLAuditRepository,
    RedisIdempotencyStore,
    SQLiteAuditRepository,
    SQLiteIdempotencyStore,
)
from backend.app.ingestion.validator import EventValidator
from backend.app.logging_config import get_logger
from backend.app.policy.engine import PolicyEngine
from backend.app.risk.aggregator import RiskAggregator
from backend.app.risk.graph_engine import GraphEngine
from backend.app.risk.ml_engine import MLEngine
from backend.app.risk.signal_engine import SignalEngine

logger = get_logger("razorshield.pipeline")


class RiskPipelineService:
    """Primary payment risk evaluation pipeline."""

    def __init__(
        self,
        db_path: str | None = None,
        idempotency_store: IdempotencyStore | None = None,
        audit_store: AuditRepository | None = None,
    ):
        if idempotency_store:
            self.idempotency_store = idempotency_store
        else:
            self.idempotency_store = (
                RedisIdempotencyStore()
                if settings.environment in ("production", "staging")
                else SQLiteIdempotencyStore(db_path)
            )

        if audit_store:
            self.audit_store = audit_store
        else:
            self.audit_store = (
                PostgreSQLAuditRepository()
                if settings.environment in ("production", "staging")
                else SQLiteAuditRepository(db_path)
            )

        self.signal_engine = SignalEngine()
        self.ml_engine = MLEngine()
        self.graph_engine = GraphEngine()

    def process_transaction_event(
        self,
        raw_payload: dict[str, Any],
        request_id: str = "",
        correlation_id: str = "",
        ml_available: bool = True,
        graph_available: bool = True,
    ) -> RiskDecision:
        t0 = time.perf_counter()

        # 1. API Boundary Validation
        event = EventValidator.validate_dict(raw_payload)

        # 2. Atomic Idempotency Claim (SET key value NX EX)
        status, cached_response = self.idempotency_store.claim(
            event.event_id, event.idempotency_key, settings.idempotency_ttl_seconds
        )

        if status == "ALREADY_EXISTS" and cached_response:
            logger.info(
                "Idempotency cache hit (Completed)",
                extra={"transaction_id": event.transaction_id},
            )
            raise IdempotencyConflictError(
                message=f"Duplicate transaction event detected: {event.event_id}",
                existing_response=cached_response,
            )
        elif status == "IN_PROGRESS":
            logger.warning(
                "Idempotency concurrent execution detected",
                extra={"transaction_id": event.transaction_id},
            )
            raise IdempotencyInProgressError(
                message=f"Duplicate transaction event currently processing: {event.event_id}"
            )

        # 3. Fetch Customer Baseline Profile
        customer_profile = CustomerProfile(
            customer_id=event.customer_id,
            primary_device_id="dev_test_fp_01",
            primary_ip="192.168.1.50",
            avg_transaction_amount_30d=4500.0,
            std_transaction_amount_30d=1200.0,
        )

        # 4. Tri-Engine Risk Evaluation
        signals = self.signal_engine.evaluate(event, customer_profile)

        ml_result = None
        if ml_available:
            try:
                ml_result = self.ml_engine.predict_anomaly(event, customer_profile)
            except Exception as exc:
                logger.warning(
                    "ML Engine evaluation exception",
                    extra={"payload": {"error": str(exc)}},
                )

        graph_result = None
        if graph_available:
            try:
                graph_result = self.graph_engine.evaluate_graph(event)
            except Exception as exc:
                logger.warning(
                    "Graph Engine evaluation exception",
                    extra={"payload": {"error": str(exc)}},
                )

        # 5. Composite Risk Aggregation
        risk_score = RiskAggregator.aggregate(
            signals=signals,
            ml_result=ml_result,
            graph_result=graph_result,
            ml_available=ml_available,
            graph_available=graph_available,
        )

        # 6. Policy Decision Mapping
        reason_codes = [s.reason_code for s in signals]
        if graph_result and graph_result.reason_codes:
            reason_codes.extend(graph_result.reason_codes)

        contributing_signals = [s.to_dict() for s in signals]
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        decision = PolicyEngine.evaluate(
            event=event,
            risk_score=risk_score,
            reason_codes=list(set(reason_codes)),
            contributing_signals=contributing_signals,
            latency_ms=latency_ms,
            request_id=request_id,
            correlation_id=correlation_id,
        )

        # 7. Fail-Closed Cryptographic Audit Store Append
        try:
            self.audit_store.append_decision_audit(decision)
        except Exception as exc:
            logger.error(
                "FATAL: Cryptographic audit append failed",
                extra={"transaction_id": event.transaction_id},
            )
            raise AuditPersistenceError(
                message=f"Audit recording failed for transaction {event.transaction_id}. Failing closed.",
                cause=exc,
            ) from exc

        # 8. Save Completed Response in Idempotency Store
        self.idempotency_store.save_result(
            event.event_id,
            event.idempotency_key,
            decision.to_dict(),
            settings.idempotency_ttl_seconds,
        )

        logger.info(
            f"Transaction risk decision computed: {decision.decision} ({decision.risk_score}/100)",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "transaction_id": decision.transaction_id,
                "data": {
                    "score": decision.risk_score,
                    "decision": decision.decision,
                    "latency_ms": decision.latency_ms,
                },
            },
        )

        return decision
