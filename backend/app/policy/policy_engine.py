"""
RazorShield AI — Deterministic Risk Policy Engine (v1.0)
Evaluates versioned system risk rules against composite risk score and AI recommendations.
System policy rules strictly overrule AI recommendations, generating explicit conflict explanation summaries.
"""

from typing import List
from backend.app.domain.agent_contracts import AgentInvestigationResult
from backend.app.domain.graph_contracts import InvestigationPackage
from backend.app.domain.policy_contracts import PolicyAction, PolicyDecision


class DeterministicPolicyEngine:
    """Versioned Policy Engine enforcing deterministic rule precedence over AI recommendations."""

    POLICY_VERSION: str = "v1.0"

    def evaluate_policy(
        self, agent_result: AgentInvestigationResult, package: InvestigationPackage
    ) -> PolicyDecision:
        ai_rec = PolicyAction(agent_result.recommended_action.value)
        cluster_score = package.cluster_risk.score

        overridden = False
        override_reasons: List[str] = []
        final_action = ai_rec
        explanation = f"Policy {self.POLICY_VERSION}: AI recommendation '{ai_rec.value}' accepted based on cluster risk score {cluster_score}/100."

        # Rule 1: Trusted Customer History Override (AI BLOCK -> Policy STEP_UP)
        # If entity has low single-user linkage or trusted account history, override BLOCK to STEP_UP
        if (
            ai_rec == PolicyAction.BLOCK
            and package.network_exposure.unique_customers <= 1
        ):
            overridden = True
            final_action = PolicyAction.STEP_UP
            override_reasons.append("TRUSTED_CUSTOMER_HISTORY")
            override_reasons.append("POLICY_OVERRIDE_AI")
            explanation = (
                f"AI recommended BLOCK, but deterministic Policy {self.POLICY_VERSION} enforced STEP_UP "
                "due to single customer involvement and low multi-account ring linkage."
            )

        # Rule 2: High Composite Cluster Risk Mandatory Override (AI ALLOW -> Policy BLOCK)
        elif (
            ai_rec in (PolicyAction.ALLOW, PolicyAction.MONITOR) and cluster_score >= 85
        ):
            overridden = True
            final_action = PolicyAction.BLOCK
            override_reasons.append("HIGH_CLUSTER_RISK_MANDATORY_BLOCK")
            override_reasons.append("POLICY_OVERRIDE_AI")
            explanation = (
                f"AI recommended {ai_rec.value}, but deterministic Policy {self.POLICY_VERSION} enforced BLOCK "
                f"due to critical composite cluster risk score ({cluster_score}/100 >= 85)."
            )

        # Rule 3: Rapid Velocity Burst Override (AI MONITOR -> Policy HOLD)
        elif (
            ai_rec == PolicyAction.MONITOR
            and package.temporal_analysis.burst_intensity_events_per_minute >= 5.0
        ):
            overridden = True
            final_action = PolicyAction.HOLD
            override_reasons.append("HIGH_TEMPORAL_VELOCITY_BURST")
            override_reasons.append("POLICY_OVERRIDE_AI")
            explanation = (
                f"AI recommended MONITOR, but deterministic Policy {self.POLICY_VERSION} enforced HOLD "
                f"due to high velocity burst intensity ({package.temporal_analysis.burst_intensity_events_per_minute} txns/min)."
            )

        # Check Human Approval Requirement for High-Impact Actions
        requires_approval = final_action in (PolicyAction.HOLD, PolicyAction.BLOCK)

        return PolicyDecision(
            policy_version=self.POLICY_VERSION,
            investigation_id=agent_result.investigation_id,
            transaction_id=agent_result.investigation_id,
            ai_recommendation=ai_rec,
            final_action=final_action,
            overridden=overridden,
            override_reason_codes=override_reasons,
            explanation_summary=explanation,
            requires_human_approval=requires_approval,
        )
