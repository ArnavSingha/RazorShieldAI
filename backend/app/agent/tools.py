"""
RazorShield AI — Read-Only Agent Tool Registry
Enforces code-level read-only permissions for the AI Investigator state machine.
Mutating tools (e.g. block_payment, hold_payment, change_policy) are strictly forbidden and absent from this registry.
"""

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class Permission(str, Enum):
    READ_ONLY = "READ_ONLY"
    MUTATING = "MUTATING"


class ToolDefinition(BaseModel):
    name: str
    description: str
    permission: Permission = Permission.READ_ONLY
    handler: Any = Field(exclude=True)


class AgentToolRegistry:
    """Enforces code-level read-only tool permission for AI state machine."""

    def __init__(self, graph_engine: Any = None):
        self._tools: Dict[str, ToolDefinition] = {}
        self.graph_engine = graph_engine
        self._register_default_read_only_tools()

    def register_tool(self, tool: ToolDefinition) -> None:
        if tool.permission != Permission.READ_ONLY:
            raise PermissionError(
                f"Security Violation: Mutating tool '{tool.name}' with permission '{tool.permission.value}' "
                "cannot be registered in Slice 3 AI Investigator Tool Registry. Read-only tools strictly required."
            )
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Agent tool '{name}' not found in registry.")
        return self._tools[name]

    def list_tool_names(self) -> List[str]:
        return list(self._tools.keys())

    def _register_default_read_only_tools(self) -> None:
        self.register_tool(
            ToolDefinition(
                name="get_investigation_package",
                description="Fetches deterministic InvestigationPackage for a given investigation_id or entity_id.",
                permission=Permission.READ_ONLY,
                handler=self.get_investigation_package,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="get_evidence_by_id",
                description="Retrieves specific EvidenceItem by evidence_id (e.g. E-1001).",
                permission=Permission.READ_ONLY,
                handler=self.get_evidence_by_id,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="get_entity_context",
                description="Retrieves historical profile & baseline context for a target entity_id.",
                permission=Permission.READ_ONLY,
                handler=self.get_entity_context,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="get_transaction_context",
                description="Retrieves transaction event details for a target transaction_id.",
                permission=Permission.READ_ONLY,
                handler=self.get_transaction_context,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="get_related_incidents",
                description="Retrieves historical related fraud incidents sharing entity clusters.",
                permission=Permission.READ_ONLY,
                handler=self.get_related_incidents,
            )
        )
        self.register_tool(
            ToolDefinition(
                name="get_policy_context",
                description="Retrieves read-only system risk policy thresholds and evaluation rules.",
                permission=Permission.READ_ONLY,
                handler=self.get_policy_context,
            )
        )

    def get_investigation_package(self, investigation_id: str) -> Dict[str, Any]:
        if self.graph_engine:
            pkg = self.graph_engine.generate_investigation_package(
                investigation_id, max_hops=2
            )
            return pkg.to_dict()
        return {"investigation_id": investigation_id, "status": "UNKNOWN_ENGINE"}

    def get_evidence_by_id(
        self, investigation_id: str, evidence_id: str
    ) -> Dict[str, Any]:
        if self.graph_engine:
            pkg = self.graph_engine.generate_investigation_package(
                investigation_id, max_hops=2
            )
            for ev in pkg.primary_evidence:
                if ev.evidence_id == evidence_id:
                    return ev.model_dump()
        return {"evidence_id": evidence_id, "status": "NOT_FOUND"}

    def get_entity_context(self, entity_id: str) -> Dict[str, Any]:
        return {
            "entity_id": entity_id,
            "account_age_days": 180,
            "prior_chargeback_count": 0,
            "kyc_status": "VERIFIED",
            "trust_score": 0.85,
        }

    def get_transaction_context(self, transaction_id: str) -> Dict[str, Any]:
        return {
            "transaction_id": transaction_id,
            "status": "EVALUATED",
            "currency": "INR",
            "risk_score_fastpath": 45,
        }

    def get_related_incidents(self, cluster_id: str) -> Dict[str, Any]:
        return {
            "cluster_id": cluster_id,
            "historical_incident_count": 0,
            "prior_ring_detections": [],
        }

    def get_policy_context(self) -> Dict[str, Any]:
        return {
            "policy_version": "v1.0",
            "block_threshold": 80,
            "hold_threshold": 60,
            "step_up_threshold": 35,
        }
