# RazorShield AI — Test Strategy & Security Audit Framework

## Test Suite Architecture

```text
tests/
  unit/
    test_rules_engine.py
    test_ml_isolation_forest.py
    test_graph_cluster_detector.py
    test_policy_engine.py
    test_idempotency_validator.py
  integration/
    test_api_ingestion.py
    test_agent_investigator.py
    test_action_gateway.py
  security/
    test_rbac_authorization.py
    test_prompt_injection_defense.py
    test_pii_redaction.py
  adversarial/
    test_fraud_scenarios.py
  resilience/
    test_dependency_chaos.py
```

---

## Test Execution Matrix

### 1. Unit Tests (`pytest tests/unit/`)
- Tests deterministic scoring boundaries (0, 30, 60, 80, 95, 100 score brackets).
- Verifies IsolationForest anomaly extraction outputs.
- Verifies Pydantic model parsing and sanitization.

### 2. Integration Tests (`pytest tests/integration/`)
- Tests complete transaction event ingestion through scoring, policy lookup, and response.
- Verifies SSE streaming message format and connection stability.

### 3. Security & Adversarial Tests (`pytest tests/security/`)
- Validates prompt injection payloads embedded in `merchant_notes` and `user_agent`.
- Verifies RBAC restrictions for `MERCHANT_OPERATOR` and `READ_ONLY` accounts attempting policy modifications.

### 4. Chaos Resilience Tests (`pytest tests/resilience/`)
- Simulates LLM timeout and verifies safe fallback to deterministic rules.
- Simulates Graph database failure and verifies relational 1-hop fallback.
