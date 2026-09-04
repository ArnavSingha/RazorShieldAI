# RazorShield AI — State Machine Agentic Design

## Agent Architecture
The RazorShield AI Investigator is designed as an explicit **LangGraph state machine** rather than an unconstrained autonomous loop.

```text
[START] 
   │
   ▼
[TRIAGE] (Risk score check: Is R_comp > 60?)
   │
   ├── (No) ──► [AUTO_CLOSE: ALLOW / LOW_RISK]
   │
   └── (Yes) ──► [COLLECT_TRANSACTION_CONTEXT]
                       │
                       ▼
                 [COLLECT_CUSTOMER_BASELINE]
                       │
                       ▼
                 [COLLECT_GRAPH_NEIGHBORHOOD]
                       │
                       ▼
                 [FORMULATE_HYPOTHESES]
                       │
                       ▼
                 [VERIFY_EVIDENCE_GROUNDING]
                       │
                       ▼
                 [GENERATE_RECOMMENDATION]
                       │
                       ▼
                 [POLICY_AUTHORIZATION_CHECK]
                       │
                       ├── (Passed) ──► [DISPATCH_ACTION_GATEWAY]
                       │
                       └── (Failed) ──► [ESCALATE_HUMAN_ANALYST]
```

---

## Tool Permissions & Isolation Matrix

| Tool Name | Permission Level | Input Signature | Output Schema | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `get_transaction_context` | `READ_ONLY` | `{transaction_id: str}` | `TransactionContext` | Fetches transaction signals & metadata. |
| `get_customer_baseline` | `READ_ONLY` | `{customer_id: str}` | `CustomerProfile` | Fetches 30-day historical baseline. |
| `get_graph_neighborhood` | `READ_ONLY` | `{entity_id: str, depth: int}` | `GraphSubgraph` | Returns connected entities & fraud clusters. |
| `request_step_up` | `HIGH_IMPACT_REQUEST` | `{transaction_id: str, reason: str}` | `ActionRequestStatus` | Submits 3DS/OTP challenge request to Policy Engine. |
| `request_hold_payment` | `HIGH_IMPACT_REQUEST` | `{transaction_id: str, reason: str}` | `ActionRequestStatus` | Submits Hold request to Policy Engine. |
| `request_block_payment`| `HIGH_IMPACT_REQUEST` | `{transaction_id: str, reason: str}` | `ActionRequestStatus` | Submits Block request to Policy Engine. |

---

## Hard Execution Constraints
1. Max iteration depth: 5 agent transitions.
2. Max execution timeout: 3500ms.
3. Fallback on LLM failure or timeout: Immediate fallback to Rule Engine decision + human analyst escalation flag.
