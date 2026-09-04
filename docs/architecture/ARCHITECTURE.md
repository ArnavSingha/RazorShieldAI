# RazorShield AI — System Architecture Specification

## Architecture Overview
RazorShield AI is structured as a **modular monolith** with clear domain separation between stream ingestion, risk calculation engines, graph intelligence, agentic investigation, policy validation, action execution, and audit logging.

---

## Technical Block Diagram
```text
                  PAYMENT EVENTS STREAM
                            ↓
                EVENT INGESTION & PIPELINE
                            ↓
                VALIDATION & IDEMPOTENCY 
           (Redis Primary / SQLite Fallback)
                            ↓
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
       SIGNAL ENGINE   ML ENGINE     GRAPH ENGINE
      (Rules/Velocity) (Isolation    (NetworkX Cluster
                         Forest)       Analysis)
             └──────────────┼──────────────┘
                            ↓
                     RISK AGGREGATOR
                            ↓
                    AI INVESTIGATOR (LangGraph Agent - Out-of-Band)
                            ↓
                     EVIDENCE LAYER
                            ↓
                   POLICY ENGINE & GUARDRAILS
                            ↓
                    ACTION GATEWAY
                            ↓
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
           ALLOW          STEP-UP       HOLD / BLOCK
             └──────────────┼──────────────┘
                            ↓
                     OUTCOME MONITOR
                            ↓
              AUDIT TRAIL / FEEDBACK / LEARNING
          (PostgreSQL Primary / SQLite Fallback)
```

---

## Storage & Database Architecture Source of Truth

- **Primary Production Storage Stack:**
  - **PostgreSQL**: Relational database for transactions, customer baselines, risk decisions, policy configs, incidents, and append-only audit events.
  - **Redis**: High-performance key-value cache for idempotency deduplication (`event_id` + `idempotency_key`), API rate limiting, and active session cache.
  - **Strict Fail-Closed Production Semantics:** When configured in `production` or `staging` mode, if Redis or PostgreSQL connections fail, the system raises an explicit `RuntimeError` and triggers controlled safe failure / review handling. Silent fallback to SQLite is prohibited in production.
- **Local Standalone / Offline Fallback:**
  - **SQLite + In-Memory Redis dictionary**: Explicitly permitted during local standalone development and offline unit testing when database services are unattached.
- **Integration Test Verification Status:**
  - **Verified in offline test run:** Adapter contract behavior, schema creation, atomic claim logic, cryptographic hash chaining, and strict production connection failure.
  - **Skipped when live services unattached:** Live TCP socket integration tests against running Redis and PostgreSQL containers (skipped gracefully unless `REDIS_URL`/`POSTGRES_URL` live containers are attached).

---

## Empirical Performance Benchmark Measurements

> [!NOTE]
> The following figures represent empirical benchmark measurements gathered across 3,000+ transaction evaluations, not hard SLAs.

- **Initial Engineering Benchmark Target:** `<25 ms` P95 under minimal in-memory conditions.
- **Current Measured Result (Hardened Pipeline):**
  - **Normal Baseline Traffic:** P50 = 25.42 ms | P90 = 32.13 ms | **P95 = 35.14 ms** | P99 = 49.64 ms (Avg = 26.76 ms).
  - **Suspicious Fraud Ring Traffic:** P50 = 25.70 ms | P90 = 32.18 ms | **P95 = 35.57 ms** | P99 = 45.11 ms (Avg = 27.03 ms).
  - **Concurrent Burst Workloads (1,000 parallel requests):** P50 = 259.90 ms | P90 = 368.18 ms | **P95 = 410.84 ms** | P99 = 561.89 ms (Avg = 266.47 ms).
- **Optimization Status:** `<25 ms` target not yet met after incorporating cryptographic audit hashing & strict storage contracts. Profiling and async batch optimizations are deferred until core feature slices complete.

### Architectural Boundary Analysis
The elevated latency under concurrent burst conditions ($P95 = 410.84\text{ ms}$) reflects thread and database lock contention under synthetic burst loading. This empirical result directly validates the system's core architectural boundary:
1. **Critical Fast Path:** Synchronous validation, idempotency, deterministic signals, ML anomaly scoring, and basic entity lookups ($P95 \approx 35\text{ ms}$).
2. **Deep Investigation Path:** Multi-hop graph cluster expansion, fraud-ring risk exposure calculation, and AI evidence synthesis operate asynchronously out-of-band without blocking payment gateway SLAs.

---

## Provider-Agnostic LLM Abstraction Layer

- The AI Investigator state machine relies on a provider-agnostic interface (`LLMProviderInterface`).
- Provider and model selection are configured via environment variables (`LLM_PROVIDER`, `LLM_MODEL_NAME`) and pinned in dependency configurations (`pyproject.toml`).
- Application business rules and policy validation are strictly isolated from LLM provider choices.

---

## Detailed System Component Specifications

### 1. Ingestion & Idempotency Gateway
- **Function:** Receives payment transactions via REST API or synthetic WebSocket stream.
- **Idempotency Check:** Key built from `event_id` and `idempotency_key`. Redis primary lookup (with strict fail-closed production semantics). Duplicate events return cached response without re-processing.
- **Validation:** Pydantic schema validation ensuring required payment attributes (amount, currency, customer_id, merchant_id, device_fingerprint, ip_address, card_bin).

### 2. Tri-Engine Risk Assessment Matrix

#### A. Signal Engine (Rules & Velocity)
- Computes deterministic features:
  - Account Velocity (1h, 24h count & sum)
  - Device Change Indicator
  - Geographic Velocity (implausible distance calculation between sequential IPs)
  - BIN High-Risk List matching
  - Merchant Category Code (MCC) baseline mismatch

#### B. ML Engine (Anomaly Detection)
- Model: `scikit-learn IsolationForest` trained on normal customer transaction baseline distribution.
- Fails cleanly into `DEGRADED_NO_ML` mode if `scikit-learn` or trained model is unavailable. Does not fabricate heuristic scores.
- Output: Anomaly score `[0.0, 1.0]` and top anomalous feature contributions.

#### C. Graph Engine (Heterogeneous Ring Intelligence)
- In-memory NetworkX bipartite/multigraph structure storing relationships:
  - `(Customer) --[HAS_DEVICE]--> (Device)`
  - `(Customer) --[HAS_IP]--> (IPAddress)`
  - `(Customer) --[USES_CARD]--> (CardToken)`
  - `(Customer) --[TRANSACTS_AT]--> (Merchant)`
- Detects shared entity clusters across multiple distinct customer accounts within a sliding 24-hour window.

### 3. Risk Aggregator
Calculates the final composite risk score ($R_{comp}$) on a scale of $0 - 100$:
$$R_{comp} = w_{signal} \cdot R_{signal} + w_{ml} \cdot R_{ml} + w_{graph} \cdot R_{graph}$$
Default weights: $w_{signal} = 0.40$, $w_{ml} = 0.30$, $w_{graph} = 0.30$.
Automatically rescales weights when operating in degraded modes (`DEGRADED_NO_ML`, `DEGRADED_NO_GRAPH`, `DEGRADED_RULES_ONLY`).

### 4. Policy Engine & Guardrails
Evaluates recommended actions against system policy matrix:
- Enforces role-based action privileges.
- Rejects recommendation if evidence links are missing or invalid.
- Resolves conflicts between AI recommendations and hard deterministic business rules.

### 5. Action Gateway
- Bounded execution module responsible for dispatching response actions (`ALLOW`, `STEP-UP`, `HOLD`, `BLOCK`).
- Idempotent action execution ensures no double-blocking or repeated step-up prompts.

### 6. Immutable Cryptographic Audit Engine
- Records full correlation trace into PostgreSQL / SQLite audit ledger with SHA-256 hash chaining and HMAC signatures.
