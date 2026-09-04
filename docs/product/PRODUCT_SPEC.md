# RazorShield AI — Product Specification

## Executive Summary
**RazorShield AI** is an AI-native payment risk operating system engineered for real-time risk intelligence, fraud correlation, evidence-based investigation, policy-controlled response, and graceful failure recovery. Built specifically for the Razorpay AI Buildathon track **AI Risk Manager**, RazorShield AI moves beyond simple risk scoring classifiers and LLM chatbots to provide an end-to-end, enterprise-grade risk operations engine.

---

## Core Product Positioning
RazorShield AI is **not**:
- A generic fraud classification model.
- A prediction dashboard with mock alerts.
- A ChatGPT wrapper for fraud queries.

RazorShield AI **is**:
> **An AI-native payment risk operating system that investigates suspicious activity, correlates entities, explains evidence, enforces policy, executes bounded responses, and safely recovers when dependencies fail.**

---

## Primary Engineering Workflow
```text
Synthetic Payment Event
        ↓
Event Validation & Idempotency
        ↓
Signal Extraction (Velocity, Geo, Device, BIN)
        ↓
Risk Detection (Rules Engine + ML Anomaly Engine)
        ↓
Risk Aggregation (Normalized Score 0-100)
        ↓
Transaction / Entity Graph (Heterogeneous Cluster Analysis)
        ↓
AI Investigation (LangGraph State Machine Agent - Out-of-Band)
        ↓
Evidence Collection (Structured, Grounded Facts)
        ↓
Policy Evaluation (Configurable Authorization Matrix)
        ↓
Decision (ALLOW, MONITOR, STEP-UP, HOLD/REVIEW, BLOCK)
        ↓
Action Gateway (Bounded Execution Engine)
        ↓
Verification & Outcome Monitoring
        ↓
Audit Logging & System Feedback Loop
```

---

## Performance & Latency Metrics Strategy

- **Engineering Benchmark Target:** `<25ms` synchronous risk evaluation path under in-memory benchmark environment conditions.
- **Engineering Risk-Path Target:** `<50ms` synchronous risk path cap under defined benchmark conditions (measured at P50, P95, P99, Average, Max).
- **Asynchronous AI Investigation:** LLM evidence collection runs asynchronously out-of-band for high-risk events without blocking real-time payment responses.

---

## Core Modules & Functional Capabilities

### 1. Command Center Dashboard
- Real-time KPI Stream: Transactions/min, Risk Events, Active Incidents, Potential Exposure ($/₹), Prevented Loss, False-Positive Rate, Avg Decision Latency, Avg Investigation Latency, System Health Status.
- Zero mock metrics: All metrics aggregate from real stream and database state.

### 2. Live Transaction Stream
- Real-time table feed showing `transaction_id`, amount, currency, merchant, risk score, decision, contributing signals, latency, and status.
- Filterable by risk level (Low, Medium, High, Critical) and decision type.

### 3. Transaction Investigation Workspace
- Incident summary & risk breakdown (Rules score, ML score, Graph anomaly score).
- Evidence timeline & structured evidence grid (`claim_id`, `evidence_id`, `source`, `observed_value`).
- Visual entity relationship preview.
- AI Investigator trace log showing step-by-step hypothesis generation, evidence collection, and recommendation.

### 4. Interactive Transaction & Entity Graph
- Dynamic visual graph using React Flow.
- Nodes: Customer, Account, Device Fingerprint, Card Token, IP Address, Merchant, Transaction.
- Fraud ring cluster detection highlighting multi-account/shared-device collusions.

### 5. Policy Center
- Configurable risk policy engine:
  - `0 - 30`: ALLOW
  - `31 - 60`: MONITOR
  - `61 - 80`: STEP-UP (3DS / OTP challenge)
  - `81 - 95`: HOLD / REVIEW
  - `96 - 100`: BLOCK / INCIDENT
- Rule override matrix based on velocity thresholds, merchant category codes (MCC), and VIP customer exceptions.

### 6. Attack Simulator Engine
- Interactive scenario injection for ground-truth testing:
  - Account Takeover (ATO-001)
  - Card Testing Velocity Burst (CT-002)
  - Device Farm Collusion Ring (DF-003)
  - Cross-Border Anomaly (CBA-004)
  - Money Mule Routing (MM-005)

### 7. Chaos & Resilience Mode
- Controlled dependency failure toggles:
  - LLM Service Unavailable
  - ML Anomaly Service Failure
  - Graph Database Offline
  - Geolocation Enrichment Timeout
- Safe deterministic fallbacks for every scenario.

---

## Success Metrics & SLA Target
| Metric | Benchmark Target | High-Performance Target |
| :--- | :--- | :--- |
| Risk Evaluation Latency (P95) | < 50 ms | < 25 ms |
| AI Investigation Latency (P95) | < 3.5 sec | < 1.8 sec |
| Idempotency Deduplication | 100% | 100% |
| False Positive Rate | < 2.5% | < 1.2% |
| Safe Degraded Availability | 99.9% | 99.99% |
