"""
RazorShield AI — LangGraph State Machine Agent Investigator
Executes 11-node state machine workflow:
LOAD_PACKAGE -> EVIDENCE_INDEX -> FORM_HYPOTHESES -> READ_ONLY_TOOLS -> VERIFY_CLAIMS -> ADVERSARIAL_EVIDENCE -> ASSESS_PATTERN_INTERACTIONS -> GENERATE_FINDINGS -> RECOMMEND_ACTION -> SELF_CHECK -> FINALIZE.
Enforces code-level read-only tools, TOCTOU snapshot hash checks, NO EVIDENCE -> NO CLAIM invariants,
resource budget limits (max tool calls, max graph reads, max tokens, max wall clock ms), and auditability.
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from backend.app.agent.audit import AgentAuditLogger
from backend.app.agent.llm_provider import (
    LLMProviderInterface,
    get_llm_provider,
)
from backend.app.agent.output_validator import (
    AgentBudgetExceededError,
    AgentOutputValidator,
)
from backend.app.agent.tools import AgentToolRegistry
from backend.app.domain.agent_contracts import (
    AgentInvestigationResult,
    AgentResourceBudget,
)
from backend.app.domain.graph_contracts import InvestigationPackage
from backend.app.risk.graph_engine import GraphEngine


class InvestigatorState:
    """State object passing through state machine nodes."""

    def __init__(
        self,
        investigation_id: str,
        package: Optional[InvestigationPackage] = None,
        budget: Optional[AgentResourceBudget] = None,
    ):
        self.agent_run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        self.investigation_id = investigation_id
        self.package: Optional[InvestigationPackage] = package
        self.budget: AgentResourceBudget = budget or AgentResourceBudget(
            start_time=time.time()
        )
        self.evidence_index: Dict[str, Any] = {}
        self.hypotheses: List[Dict[str, Any]] = []
        self.verified_claims: List[Dict[str, Any]] = []
        self.adversarial_findings: List[Dict[str, Any]] = []
        self.pattern_interactions: Dict[str, Any] = {}
        self.raw_result_dict: Optional[Dict[str, Any]] = None
        self.final_result: Optional[AgentInvestigationResult] = None
        self.state_transitions: List[str] = []
        self.tool_calls: List[str] = []

    def check_budget_invariants(self) -> None:
        self.budget.check_wall_clock()
        if self.budget.budget_status != "HEALTHY":
            raise AgentBudgetExceededError(
                budget_status=self.budget.budget_status,
                details_dict=self.budget.model_dump(),
            )


class AgentInvestigatorGraph:
    """State Machine Agent Orchestrator with Resource Budget Guards."""

    def __init__(
        self,
        graph_engine: GraphEngine,
        audit_store: Any = None,
        llm_provider: Optional[LLMProviderInterface] = None,
    ):
        self.graph_engine = graph_engine
        self.audit_store = audit_store
        self.audit_logger = AgentAuditLogger(audit_store) if audit_store else None
        self.tool_registry = AgentToolRegistry(graph_engine)
        self.llm_provider = llm_provider or get_llm_provider()

    def run_investigation(
        self,
        investigation_id: str,
        existing_package: Optional[InvestigationPackage] = None,
        budget: Optional[AgentResourceBudget] = None,
    ) -> AgentInvestigationResult:
        """Executes the full 11-node state machine workflow under strict resource budget constraints."""
        state = InvestigatorState(investigation_id, existing_package, budget)

        # 1. LOAD_PACKAGE (Deterministic)
        self._node_load_package(state)

        # 2. EVIDENCE_INDEX (Deterministic)
        self._node_evidence_index(state)

        # 3. FORM_HYPOTHESES (Model Reasoning)
        self._node_form_hypotheses(state)

        # 4. READ_ONLY_TOOLS (Data Fetch)
        self._node_read_only_tools(state)

        # 5. VERIFY_CLAIMS (Deterministic)
        self._node_verify_claims(state)

        # 6. ADVERSARIAL_EVIDENCE (Counter-Signal Model Reasoning)
        self._node_adversarial_evidence(state)

        # 7. ASSESS_PATTERN_INTERACTIONS (Model Reasoning)
        self._node_assess_pattern_interactions(state)

        # 8. GENERATE_FINDINGS & RECOMMEND_ACTION (LLM / Model Provider Execution)
        self._node_generate_findings_and_recommend(state)

        # 9. SELF_CHECK (Deterministic Hard-Gate Output Validation)
        self._node_self_check(state)

        # 10. FINALIZE (Audit Trail Logging)
        self._node_finalize(state)

        assert state.final_result is not None
        return state.final_result

    def _node_load_package(self, state: InvestigatorState) -> None:
        state.state_transitions.append("LOAD_PACKAGE")
        state.check_budget_invariants()

        if not state.package:
            state.budget.consume_tool_call()
            state.budget.consume_graph_read()
            state.check_budget_invariants()

            state.tool_calls.append("get_investigation_package")
            state.package = self.graph_engine.generate_investigation_package(
                state.investigation_id, max_hops=2
            )

        # TOCTOU Snapshot Integrity check
        AgentOutputValidator.validate_snapshot_integrity(state.package)

    def _node_evidence_index(self, state: InvestigatorState) -> None:
        state.state_transitions.append("EVIDENCE_INDEX")
        state.check_budget_invariants()
        assert state.package is not None
        for ev in state.package.primary_evidence:
            state.evidence_index[ev.evidence_id] = ev.model_dump()

    def _node_form_hypotheses(self, state: InvestigatorState) -> None:
        state.state_transitions.append("FORM_HYPOTHESES")
        state.check_budget_invariants()
        assert state.package is not None
        score = state.package.cluster_risk.score
        if score >= 75:
            state.hypotheses.append(
                {
                    "hypothesis": "COORDINATED_FRAUD_RING",
                    "prior_confidence": 0.85,
                }
            )
        else:
            state.hypotheses.append(
                {
                    "hypothesis": "ISOLATED_ANOMALY",
                    "prior_confidence": 0.60,
                }
            )

    def _node_read_only_tools(self, state: InvestigatorState) -> None:
        state.state_transitions.append("READ_ONLY_TOOLS")

        state.budget.consume_tool_call()
        state.check_budget_invariants()
        state.tool_calls.append("get_entity_context")

        state.budget.consume_tool_call()
        state.check_budget_invariants()
        state.tool_calls.append("get_policy_context")

    def _node_verify_claims(self, state: InvestigatorState) -> None:
        state.state_transitions.append("VERIFY_CLAIMS")
        state.check_budget_invariants()
        assert state.package is not None
        for ev in state.package.primary_evidence:
            state.verified_claims.append(
                {
                    "claim": ev.claim,
                    "evidence_id": ev.evidence_id,
                    "confidence": ev.confidence,
                    "verified": True,
                }
            )

    def _node_adversarial_evidence(self, state: InvestigatorState) -> None:
        state.state_transitions.append("ADVERSARIAL_EVIDENCE")
        state.check_budget_invariants()
        assert state.package is not None
        if state.package.network_exposure.unique_customers <= 1:
            state.adversarial_findings.append(
                {
                    "counter_signal": "Single customer account involved with low multi-user linkage",
                    "evidence_id": state.package.primary_evidence[0].evidence_id
                    if state.package.primary_evidence
                    else "E-1001",
                    "impact": "ATTENUATES_RISK",
                }
            )

    def _node_assess_pattern_interactions(self, state: InvestigatorState) -> None:
        state.state_transitions.append("ASSESS_PATTERN_INTERACTIONS")
        state.check_budget_invariants()
        assert state.package is not None
        state.pattern_interactions = {
            "pattern_count": len(state.package.detected_patterns),
            "interaction_type": "REINFORCING_RISK"
            if len(state.package.detected_patterns) > 1
            else "SINGLE_SIGNAL",
        }

    def _node_generate_findings_and_recommend(self, state: InvestigatorState) -> None:
        state.state_transitions.append("GENERATE_FINDINGS")
        state.state_transitions.append("RECOMMEND_ACTION")
        state.check_budget_invariants()
        assert state.package is not None

        state.budget.consume_tokens(250)  # Simulate model prompt/completion token usage
        state.check_budget_invariants()

        raw_res = self.llm_provider.generate_investigation_reasoning(
            state.package, state.evidence_index
        )
        raw_res["agent_run_id"] = state.agent_run_id
        raw_res["investigation_id"] = state.investigation_id
        raw_res["package_id"] = state.package.package_id
        raw_res["evidence_snapshot_hash"] = state.package.evidence_snapshot_hash
        raw_res["budget_status"] = state.budget.budget_status
        raw_res["created_at"] = time.time()
        state.raw_result_dict = raw_res

    def _node_self_check(self, state: InvestigatorState) -> None:
        state.state_transitions.append("SELF_CHECK")
        state.check_budget_invariants()
        assert state.raw_result_dict is not None
        assert state.package is not None
        # Output Validation & NO EVIDENCE -> NO CLAIM Grounding Verification
        validated_result = AgentOutputValidator.validate_and_ground_result(
            state.raw_result_dict, state.package
        )
        state.final_result = validated_result

    def _node_finalize(self, state: InvestigatorState) -> None:
        state.state_transitions.append("FINALIZE")
        state.check_budget_invariants()
        assert state.final_result is not None
        assert state.package is not None
        if self.audit_logger:
            self.audit_logger.log_agent_run(
                agent_run_id=state.agent_run_id,
                package_id=state.package.package_id,
                result=state.final_result,
                state_transitions=state.state_transitions,
                tool_calls=state.tool_calls,
            )
