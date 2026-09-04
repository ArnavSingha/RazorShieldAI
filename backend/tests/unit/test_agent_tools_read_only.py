"""
RazorShield AI — Unit Tests for Read-Only Agent Tool Registry
Verifies code-level enforcement of read-only permissions and absence of mutating tools.
"""

import pytest
from backend.app.agent.tools import AgentToolRegistry, Permission, ToolDefinition


def test_agent_tool_registry_read_only_enforcement():
    registry = AgentToolRegistry()

    # 1. Assert default tool list permissions are READ_ONLY
    names = registry.list_tool_names()
    assert len(names) >= 6
    assert "get_investigation_package" in names
    assert "get_evidence_by_id" in names
    assert "get_entity_context" in names
    assert "get_transaction_context" in names
    assert "get_related_incidents" in names
    assert "get_policy_context" in names

    for name in names:
        tool = registry.get_tool(name)
        assert tool.permission == Permission.READ_ONLY

    # 2. Hard Invariant: Assert mutating tools are 100% absent
    mutating_tool_names = [
        "block_payment",
        "hold_payment",
        "change_policy",
        "delete_case",
        "modify_policy",
        "execute_action",
    ]
    for m_name in mutating_tool_names:
        assert m_name not in names

    # 3. Code-Level Enforcement Guard: Attempting to register a mutating tool must raise PermissionError
    fake_mutating_tool = ToolDefinition(
        name="block_payment",
        description="Attempts to block payment directly.",
        permission="MUTATING",  # Invalid mutating permission
        handler=lambda x: None,
    )
    with pytest.raises(PermissionError) as exc_info:
        registry.register_tool(fake_mutating_tool)

    assert "Security Violation: Mutating tool 'block_payment'" in str(exc_info.value)
