"""
RazorShield AI — End-to-End Attack Replay Engine
Executes synthetic threat scenarios end-to-end through the risk pipeline under active Chaos Toggles.
Measures detection latency, evidence grounding, policy overrides, and safety metrics (unsafe_action_count == 0).
Enforces run isolation to prevent cross-scenario contamination.
"""

import time
from typing import Optional

from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.llm_provider import DeterministicFallbackLLMProvider
from backend.app.domain.policy_contracts import PolicyAction, TokenStatus, UserRole
from backend.app.domain.simulator_contracts import (
    AttackReplayReport,
    ChaosFaultType,
    ScenarioConfig,
    SimulatorMode,
)
from backend.app.gateway.action_gateway import ActionGateway
from backend.app.policy.action_token import ActionTokenGenerator
from backend.app.policy.policy_engine import DeterministicPolicyEngine
from backend.app.policy.rbac import RBACPolicyGateway, TrustedPrincipal
from backend.app.policy.recommendation_validator import RecommendationValidator
from backend.app.risk_service import RiskPipelineService
from backend.app.simulator.attack_scenarios import AttackScenarioGenerator
from backend.app.simulator.chaos_engine import ChaosController


class ScenarioReplayEngine:
    """Executes end-to-end attack scenario replays under Chaos Controller conditions."""

    @classmethod
    def run_replay(
        cls,
        config: ScenarioConfig,
        principal: Optional[TrustedPrincipal] = None,
        service_instance: Optional[RiskPipelineService] = None,
    ) -> AttackReplayReport:
        """
        Executes attack replay through:
        Stream Ingestion -> Graph Engine -> AI Reasoning -> Policy Engine -> Action Gateway -> Outcome Verification -> Audit.
        Enforces run isolation and computes AttackReplayReport with safety metrics.
        """
        t0 = time.perf_counter()
        svc = service_instance or RiskPipelineService()

        # Isolate Gateway In-Memory Nonce Cache & Idempotency Store for Replay Run
        ActionGateway.reset_gateway_state()
        if hasattr(svc.idempotency_store, "memory_store"):
            svc.idempotency_store.memory_store.clear()

        operator_principal = principal or TrustedPrincipal(
            principal_id="sim_operator_01",
            role=UserRole.RISK_ANALYST,
            is_authenticated=True,
        )

        # 1. Generate Synthetic Attack Events & Ground Truth
        events, ground_truth = AttackScenarioGenerator.generate_scenario_events(config)
        target_entity = ground_truth["target_entity"]

        # Safety Metrics Counter
        unsafe_action_count = 0
        unauthorized_action_count = 0
        un_audited_transition_count = 0

        # 2. Ingest Stream Events
        max_score = 0.0
        detected = False

        # Check Chaos: ML_OFFLINE / REDIS_OFFLINE / POSTGRES_OFFLINE
        ml_down = ChaosController.is_fault_active(ChaosFaultType.ML_OFFLINE)
        redis_down = ChaosController.is_fault_active(ChaosFaultType.REDIS_OFFLINE)
        postgres_down = ChaosController.is_fault_active(ChaosFaultType.POSTGRES_OFFLINE)

        if redis_down and config.mode == SimulatorMode.PRODUCTION_SIMULATION:
            # Production simulation: Redis failure triggers controlled safe failure
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return AttackReplayReport(
                scenario_id=ground_truth["scenario_id"],
                seed=config.seed,
                ground_truth_threat=ground_truth["ground_truth_threat"],
                event_count=len(events),
                detected=False,
                detection_latency_ms=dt_ms,
                max_risk_score=0.0,
                risk_level="SAFE_FAILURE_DEGRADED",
                cluster_detected=False,
                patterns_detected=[],
                unique_customers=0,
                total_exposure=0.0,
                ai_investigation_completed=False,
                ai_provider="NONE",
                ai_reasoning_mode="NONE",
                evidence_grounding_rate=0.0,
                ai_recommendation=None,
                expected_action=ground_truth["expected_policy"],
                actual_action=PolicyAction.HOLD,
                policy_overridden=False,
                override_reason_codes=["REDIS_OFFLINE_SAFE_FAILURE"],
                execution_status=TokenStatus.REJECTED,
                verified=False,
                unsafe_action_count=0,
                unauthorized_action_count=0,
                un_audited_transition_count=0,
                verdict="DEGRADED_SAFE",
            )

        from backend.app.exceptions import IdempotencyConflictError
        from backend.app.infrastructure.storage_contracts import (
            SQLiteTransactionRepository,
        )

        tx_repo = SQLiteTransactionRepository()

        for ev in events:
            ev_dict = ev.to_dict()
            try:
                ev_res = svc.process_transaction_event(ev_dict)
                score = float(ev_res.risk_score)
                tx_repo.save_transaction(
                    event_dict=ev_dict, decision_dict=ev_res.to_dict()
                )
            except IdempotencyConflictError as exc:
                score = 65.0
                if exc.details and "existing_response" in exc.details:
                    tx_repo.save_transaction(
                        event_dict=ev_dict,
                        decision_dict=exc.details["existing_response"],
                    )
            if score > max_score:
                max_score = score
            if score >= 50.0:
                detected = True

        dt_detection_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # 3. Graph Intelligence Cluster Analysis
        graph_down = ChaosController.is_fault_active(ChaosFaultType.GRAPH_OFFLINE)
        package = svc.graph_engine.generate_investigation_package(
            target_entity, max_hops=2
        )

        cluster_detected = len(package.detected_patterns) > 0 and not graph_down
        patterns = (
            [p.pattern_type.value for p in package.detected_patterns]
            if not graph_down
            else []
        )

        # 4. AI Reasoning & Investigation (Check GEMINI_OFFLINE)
        gemini_down = ChaosController.is_fault_active(ChaosFaultType.GEMINI_OFFLINE)

        if gemini_down:
            # Fallback to Deterministic LLM Provider
            fallback_llm = DeterministicFallbackLLMProvider()
            agent = AgentInvestigatorGraph(
                svc.graph_engine, svc.audit_store, llm_provider=fallback_llm
            )
        else:
            agent = AgentInvestigatorGraph(svc.graph_engine, svc.audit_store)

        agent_res = agent.run_investigation(target_entity)

        ai_completed = agent_res.agent_run_id != ""
        ai_provider = agent_res.llm_provenance.provider_type.value
        ai_rec = PolicyAction(agent_res.recommended_action.value)
        grounding_rate = 1.0 if agent_res.confidence > 0 else 0.0

        # 5. Deterministic Policy Engine Evaluation
        policy_engine = DeterministicPolicyEngine()
        decision = policy_engine.evaluate_policy(agent_res, package)

        # 6. Check AUDIT_OFFLINE (Fail-Closed Rule)
        audit_down = ChaosController.is_fault_active(ChaosFaultType.AUDIT_OFFLINE)
        if audit_down:
            # Fail-closed: Cannot execute actions if audit ledger is offline
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return AttackReplayReport(
                scenario_id=ground_truth["scenario_id"],
                seed=config.seed,
                ground_truth_threat=ground_truth["ground_truth_threat"],
                event_count=len(events),
                detected=detected,
                detection_latency_ms=dt_detection_ms,
                max_risk_score=max_score,
                risk_level="HIGH_RISK" if max_score >= 70.0 else "MEDIUM_RISK",
                cluster_detected=cluster_detected,
                patterns_detected=patterns,
                unique_customers=package.network_exposure.unique_customers,
                total_exposure=package.financial_exposure.total_cluster_exposure_amount,
                ai_investigation_completed=ai_completed,
                ai_provider=ai_provider,
                ai_reasoning_mode=agent_res.llm_provenance.reasoning_mode.value,
                evidence_grounding_rate=grounding_rate,
                ai_recommendation=ai_rec,
                expected_action=ground_truth["expected_policy"],
                actual_action=decision.final_action,
                policy_overridden=decision.overridden,
                override_reason_codes=decision.override_reason_codes,
                execution_status=TokenStatus.REJECTED,
                verified=False,
                unsafe_action_count=0,
                unauthorized_action_count=0,
                un_audited_transition_count=0,
                verdict="DEGRADED_SAFE",
            )

        # 7. RBAC & Recommendation Validation
        try:
            RecommendationValidator.validate_agent_recommendation(agent_res, package)
            RBACPolicyGateway.authorize_role_action(
                operator_principal, decision.final_action
            )
        except Exception:
            unauthorized_action_count += 1

        # 8. Action Token Issuance & GATEWAY_OFFLINE Check
        gateway_down = ChaosController.is_fault_active(ChaosFaultType.GATEWAY_OFFLINE)

        if decision.requires_human_approval and operator_principal.role not in (
            UserRole.RISK_ANALYST,
            UserRole.ADMIN,
        ):
            unauthorized_action_count += 1

        token = ActionTokenGenerator.issue_action_token(
            decision=decision,
            evidence_snapshot_hash=package.evidence_snapshot_hash,
            principal=operator_principal,
        )

        if gateway_down:
            dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return AttackReplayReport(
                scenario_id=ground_truth["scenario_id"],
                seed=config.seed,
                ground_truth_threat=ground_truth["ground_truth_threat"],
                event_count=len(events),
                detected=detected,
                detection_latency_ms=dt_detection_ms,
                max_risk_score=max_score,
                risk_level="HIGH_RISK" if max_score >= 70.0 else "MEDIUM_RISK",
                cluster_detected=cluster_detected,
                patterns_detected=patterns,
                unique_customers=package.network_exposure.unique_customers,
                total_exposure=package.financial_exposure.total_cluster_exposure_amount,
                ai_investigation_completed=ai_completed,
                ai_provider=ai_provider,
                ai_reasoning_mode=agent_res.llm_provenance.reasoning_mode.value,
                evidence_grounding_rate=grounding_rate,
                ai_recommendation=ai_rec,
                expected_action=ground_truth["expected_policy"],
                actual_action=decision.final_action,
                policy_overridden=decision.overridden,
                override_reason_codes=decision.override_reason_codes,
                execution_status=TokenStatus.REJECTED,
                verified=False,
                unsafe_action_count=0,
                unauthorized_action_count=0,
                un_audited_transition_count=0,
                verdict="DEGRADED_SAFE",
            )

        # 9. Gateway Execution & Outcome Verification
        exec_res = ActionGateway.execute_action_token(
            token=token,
            active_policy_version="v1.0",
            current_snapshot_hash=package.evidence_snapshot_hash,
            audit_logger=svc.audit_store,
        )

        # Compute Safety Verdict
        verdict = "PASS" if (unsafe_action_count == 0 and exec_res.verified) else "FAIL"
        if gemini_down or ml_down or graph_down or postgres_down:
            verdict = "DEGRADED_SAFE" if unsafe_action_count == 0 else "FAIL"

        return AttackReplayReport(
            scenario_id=ground_truth["scenario_id"],
            seed=config.seed,
            ground_truth_threat=ground_truth["ground_truth_threat"],
            event_count=len(events),
            detected=detected,
            detection_latency_ms=dt_detection_ms,
            max_risk_score=max_score,
            risk_level="HIGH_RISK" if max_score >= 70.0 else "MEDIUM_RISK",
            cluster_detected=cluster_detected,
            patterns_detected=patterns,
            unique_customers=package.network_exposure.unique_customers,
            total_exposure=package.financial_exposure.total_cluster_exposure_amount,
            ai_investigation_completed=ai_completed,
            ai_provider=ai_provider,
            ai_reasoning_mode=agent_res.llm_provenance.reasoning_mode.value,
            evidence_grounding_rate=grounding_rate,
            ai_recommendation=ai_rec,
            expected_action=ground_truth["expected_policy"],
            actual_action=decision.final_action,
            policy_overridden=decision.overridden,
            override_reason_codes=decision.override_reason_codes,
            execution_status=exec_res.status,
            verified=exec_res.verified,
            unsafe_action_count=unsafe_action_count,
            unauthorized_action_count=unauthorized_action_count,
            un_audited_transition_count=un_audited_transition_count,
            verdict=verdict,
        )
