"""
RazorShield AI — Unit Tests for Agent Resource Budget Controls
Verifies safe termination and AgentBudgetExceededError handling for max tool calls,
max wall clock ms, and max token limits.
"""

import time
import uuid
import pytest
from backend.app.agent.investigator_graph import AgentInvestigatorGraph
from backend.app.agent.output_validator import AgentBudgetExceededError
from backend.app.audit.audit_store import CryptographicAuditStore
from backend.app.domain.agent_contracts import AgentResourceBudget
from backend.app.domain.models import TransactionEvent
from backend.app.risk.graph_engine import GraphEngine


@pytest.fixture
def agent_budget_setup(test_db_dir):
    db_file = str(test_db_dir / f"budget_unit_{uuid.uuid4().hex}.db")
    audit_store = CryptographicAuditStore(db_path=db_file)
    graph_engine = GraphEngine()

    ev1 = TransactionEvent(
        event_id="ev_b1",
        idempotency_key="idemp_b1",
        transaction_id="tx_b1",
        customer_id="cust_b_10",
        account_id="acc_b_10",
        amount=100000.0,
        currency="INR",
        device_id="dev_b_1",
        ip_address="192.168.1.1",
        merchant_id="merch_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    graph_engine.add_event(ev1)
    agent = AgentInvestigatorGraph(graph_engine, audit_store)
    return agent


def test_tool_call_budget_breach_triggers_safe_termination(agent_budget_setup):
    agent = agent_budget_setup
    strict_budget = AgentResourceBudget(max_tool_calls=1)  # Requires >= 3 tool calls

    with pytest.raises(AgentBudgetExceededError) as exc_info:
        agent.run_investigation("cust_b_10", budget=strict_budget)

    assert exc_info.value.status_code == 429
    assert exc_info.value.error_code == "AGENT_BUDGET_EXCEEDED"
    assert "EXCEEDED_TOOL_CALLS" in exc_info.value.message


def test_token_budget_breach_triggers_safe_termination(agent_budget_setup):
    agent = agent_budget_setup
    strict_budget = AgentResourceBudget(max_tokens=50)  # Requires 250 tokens

    with pytest.raises(AgentBudgetExceededError) as exc_info:
        agent.run_investigation("cust_b_10", budget=strict_budget)

    assert exc_info.value.status_code == 429
    assert "EXCEEDED_TOKENS" in exc_info.value.message


def test_wall_clock_budget_breach_triggers_safe_termination(agent_budget_setup):
    agent = agent_budget_setup
    strict_budget = AgentResourceBudget(max_wall_clock_ms=0.000001)  # Instant timeout

    time.sleep(0.01)  # Ensure wall-clock time passes
    with pytest.raises(AgentBudgetExceededError) as exc_info:
        agent.run_investigation("cust_b_10", budget=strict_budget)

    assert exc_info.value.status_code == 429
    assert "EXCEEDED_WALL_CLOCK" in exc_info.value.message
