# RazorShield AI — Data Model & Risk Score Mathematics Specification

## 1. Domain Entity Relationship Diagram

```text
 Customer (1) ──── (N) Account (1) ──── (N) Transaction (1) ──── (1) RiskScore
     │                                           │                     │
     ├── (N) Device                              ├── (1) Incident       ├── (N) RiskSignal
     ├── (N) IPAddress                           └── (1) Case           └── (1) Evidence
     └── (N) CardToken                                                     │
                                                                           └── (1) AgentAction
                                                                                   │
                                                                                   └── (1) AuditEvent
```

---

## 2. Risk Score Mathematics & Calibration Framework

### A. Normalized Component Metrics
Each risk engine computes a normalized score bounded strictly in $[0, 1]$:
- $R_{signal} \in [0.0, 1.0]$: Normalized deterministic rule & velocity score.
- $R_{ml} \in [0.0, 1.0]$: Normalized IsolationForest anomaly metric.
- $R_{graph} \in [0.0, 1.0]$: Normalized heterogeneous cluster risk metric.

### B. Weighted Composite Scoring Equation
$$R_{comp} = w_{signal} \cdot R_{signal} + w_{ml} \cdot R_{ml} + w_{graph} \cdot R_{graph}$$
$$\text{Final Risk Score} = \text{round}(R_{comp} \times 100) \in [0, 100]$$

### C. Standard Weighting Matrix & Safe Degraded Fallback Modes

| Operational Mode | $w_{signal}$ | $w_{ml}$ | $w_{graph}$ | Condition & Triggers |
| :--- | :---: | :---: | :---: | :--- |
| **NORMAL_ALL_SYSTEMS** | `0.40` | `0.30` | `0.30` | All engines operational ($\sum w_i = 1.0$). |
| **DEGRADED_NO_ML** | `0.60` | `0.00` | `0.40` | ML engine offline / timed out. |
| **DEGRADED_NO_GRAPH** | `0.60` | `0.40` | `0.00` | Graph service unattached / disabled. |
| **DEGRADED_RULES_ONLY**| `1.00` | `0.00` | `0.00` | Both ML & Graph unavailable (Fail-safe mode). |

### D. Structured Risk Score & Reason Codes Schema
```json
{
  "risk_score_id": "rsc_77192",
  "transaction_id": "tx_992104",
  "composite_score": 83,
  "risk_level": "HIGH",
  "mode": "NORMAL_ALL_SYSTEMS",
  "breakdown": {
    "signal": {"raw_score": 0.82, "weight": 0.40, "weighted_contribution": 0.328},
    "ml": {"raw_score": 0.76, "weight": 0.30, "weighted_contribution": 0.228},
    "graph": {"raw_score": 0.91, "weight": 0.30, "weighted_contribution": 0.273}
  },
  "contributing_signals": [
    {
      "signal_code": "SIG_GEO_VELOCITY_ANOMALY",
      "name": "Geographic Velocity Anomaly",
      "severity": "HIGH",
      "value": "1200km in 4 minutes",
      "weight": 0.35,
      "reason_code": "IMPLAUSIBLE_TRAVEL_SPEED"
    },
    {
      "signal_code": "SIG_SHARED_DEVICE_CLUSTER",
      "name": "Shared Device Cluster",
      "severity": "CRITICAL",
      "value": "Linked to 5 accounts in 1h",
      "weight": 0.40,
      "reason_code": "MULTI_ACCOUNT_DEVICE_COLLUSION"
    }
  ]
}
```

---

## 3. Storage & Storage Fallback Semantics

### Production / Multi-Instance Deployment
- **PostgreSQL:** Primary relational database for transaction events, customer baselines, policies, incident cases, and append-only audit events.
- **Redis:** Primary high-performance idempotency cache (`event_id` + `idempotency_key`), API rate limiting, and session state.
- **Redis Failure Behavior:** In multi-instance production, if Redis is unattached, nodes **DO NOT** silently fall back to isolated per-instance local caches (which would allow race conditions and break distributed idempotency). Instead, the system transitions to a **Controlled Degraded Review State** where unverified duplicate transactions are safely deferred to the `PENDING_REVIEW` queue.

### Local Standalone Mode
- **SQLite + In-Memory Dictionary:** Used exclusively for single-process local development, offline unit testing, and isolated demonstration runs.
