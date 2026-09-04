# RAZORSHIELD AI — 5-MINUTE LIVE JUDGE DEMO SCRIPT

**Competition:** Razorpay AI Buildathon — Track 02 (AI Risk Manager)  
**Time Limit:** 5 Minutes (Strict)  
**Presenter Objective:** Demonstrate a working, defense-only AI Risk Manager for Indian BFSI loss prevention with verified held-out evaluation, fail-closed security invariants, and honest false-positive cost accounting.

---

## 00:00 – 00:30 | Problem & Suspicious Transaction Ingestion

### WHAT I CLICK
1. Open browser to Command Center: `http://localhost:3000` (or `http://127.0.0.1:8000/`).
2. Point cursor to the live threat stream and click on the top high-value transaction (`tx_mule_spike_01`, amount ₹1,85,000.00).

### WHAT THE JUDGE SEES
- Executive KPI bar showing **₹51.07L Total Fraud Exposure**, active incident count, and live transaction stream.
- The selected transaction immediately opens a side drawer showing **Composite Risk Score: 78/100 (HIGH)** and recommended policy tier: **`STEP_UP`**.

### WHAT I SAY
> *"Good morning judges. RazorShield AI targets one specific, multi-crore loss class in Indian digital payments: **Coordinated Mule Account Rings and High-Velocity Account Takeovers (ATO)**.
> When an attacker attempts to route ₹1,85,000 across a newly linked card, our tri-engine risk pipeline scores the event in under 5 milliseconds and flags it for immediate step-up authentication before settlement."*

### WHAT BACKEND ACTUALLY DOES
- Ingestion API (`POST /api/v1/events/transaction`) runs `EventValidator.validate_dict()`.
- Evaluates transaction against `SignalEngine` (velocity, MCC surge), `MLEngine` (IsolationForest anomaly score), and `GraphEngine` (device sharing history).
- Aggregates scores via `ScoreAggregator.aggregate()` $\rightarrow$ composite score `78/100`.

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"This is live Razorpay production merchant data."* (State: *"This is a high-fidelity synthetic BFSI stream calibrated against realistic Indian loss patterns."*)
- ❌ **DO NOT SAY:** *"Our detector achieves 100% accuracy."*

---

## 00:30 – 01:15 | Tri-Engine Detection: Rules + IsolationForest + Graph

### WHAT I CLICK
1. In the Risk Breakdown drawer, click the **"Signals & Decomposition"** tab.
2. Toggle the breakdown views between **Rules**, **ML Anomaly**, and **Graph Subgraph**.

### WHAT THE JUDGE SEES
- **Rules Signal:** `MCC_5732_VOLUME_SURGE` (+30 pts) and `VELOCITY_SPIKE_5M` (+25 pts).
- **ML Engine:** Unsupervised `IsolationForest` anomaly score $0.62$ (+28 pts).
- **Graph Engine:** Mule cluster density score $0.74$ (+15 pts).
- Mathematical weight composition: $0.35 \times \text{Rules} + 0.35 \times \text{ML} + 0.30 \times \text{Graph}$.

### WHAT I SAY
> *"Rather than relying solely on black-box AI, RazorShield decomposes risk into three orthogonal pillars:
> 1. Deterministic rules for regulatory bounds and instant velocity breaches;
> 2. An unsupervised Isolation Forest model trained on benign transaction topologies to flag zero-day statistical anomalies;
> 3. Graph intelligence that identifies shared device fingerprints, card recycling, and IP subnets across accounts."*

### WHAT BACKEND ACTUALLY DOES
- `MLEngine` extracts numerical feature vectors (`amount`, `velocity_1h`, `velocity_24h`, `device_trust_score`) and queries pre-fitted `IsolationForest`.
- Dynamic weight re-normalization occurs if any single engine degrades (e.g. ML offline redistributes weight $0.35 \rightarrow 0.0$ to rules without pipeline failure).

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"Isolation Forest is a supervised deep learning model."*
- ❌ **DO NOT SAY:** *"The LLM calculates the transaction risk score."* (The LLM plays ZERO role in inline transaction scoring).

---

## 01:15 – 02:00 | Coordinated Mule-Ring Graph Investigation

### WHAT I CLICK
1. Click **"Investigate Subgraph"** button on the transaction drawer to navigate to the Graph View.
2. Click on the central node (`cust_mule_101`) to expand connected entities.

### WHAT THE JUDGE SEES
- Interactive React Flow graph canvas visualizing a 4-hop abuse ring:
  - 3 Customer accounts (`cust_101`, `cust_102`, `cust_103`) sharing a single device fingerprint (`dev_fingerprint_99`) and IP subnet (`192.168.1.100`).
  - Edge badges showing relationship types: `SHARED_DEVICE`, `SHARED_IP`, `PAYMENT_INSTRUMENT_RECYCLED`.
- Cluster risk badge indicating high mule network confidence ($0.82$).

### WHAT I SAY
> *"Here the judge can see the power of our Graph Engine. While each individual transaction looks relatively normal in isolation, the graph reveals that 3 separate customer IDs are transacting from the exact same hardware fingerprint within 120 seconds.
> This is a textbook mule syndication pattern attempting to drain funds across synthetic merchant accounts."*

### WHAT BACKEND ACTUALLY DOES
- `GraphEngine.get_subgraph()` performs breadth-first traversal up to 2 hops around the target customer.
- Prunes high-degree hub nodes (e.g. public ISP gateways) to prevent graph explosion and computes subgraph density.

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"The graph was computed in advance with future data."* (Evaluation executes strictly stateful, temporal accumulation).
- ❌ **DO NOT SAY:** *"This requires an expensive distributed Neo4j cluster right now."* (Implemented as an in-memory NetworkX engine with Neo4j production contracts).

---

## 02:00 – 02:45 | Advisory AI Investigation & Evidence Grounding

### WHAT I CLICK
1. Click **"Run Gemini AI Investigation"** button on the graph investigation panel.
2. Hover over the generated finding citations (`[E-1001]`, `[E-1002]`).

### WHAT THE JUDGE SEES
- Structured AI Investigation card with:
  - Summary: *"High confidence mule ring detected across 3 accounts linked to device fingerprint `dev_fingerprint_99`."*
  - Grounded Claim Findings with clickable evidence tags (`E-1001`, `E-1002`).
  - Counter-signals: *"Customer has valid KYC tier 2 verification."*
  - Clear UI banner: **"Advisory Only — Deterministic Policy Holds Execution Authority"**.

### WHAT I SAY
> *"We use Google Gemini 3.6 Flash as an advisory copilot. Notice three strict architectural invariants:
> First, Gemini has zero direct action authority.
> Second, our `AgentOutputValidator` enforces **NO-EVIDENCE-NO-CLAIM**: every claim must reference a verified evidence ID from the deterministic package snapshot, or it is rejected.
> Third, if the LLM provider fails or is rate-limited, the system falls back to a deterministic rule-based explainer in under 2 milliseconds."*

### WHAT BACKEND ACTUALLY DOES
- `GraphEngine.generate_investigation_package()` creates a TOCTOU-hashed snapshot of evidence.
- Invokes `GeminiLLMProvider.investigate()`.
- Passes raw JSON through `AgentOutputValidator.validate_and_ground_result()` to verify evidence ID existence, schema conformance, and bounded confidence.

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"Gemini reduces analyst investigation time from 15 minutes to 30 seconds."* (Purged claim; state: *"Gemini synthesizes complex graph evidence into a structured brief for human review."*)
- ❌ **DO NOT SAY:** *"Gemini never hallucinates."* (State: *"Our hard-gate validator prevents ungrounded hallucinations from reaching the policy engine."*)

---

## 02:45 – 03:30 | Risk Score $\rightarrow$ Deterministic Policy $\rightarrow$ Action Token

### WHAT I CLICK
1. Click **"Review Policy Decision"** in the action bar.
2. View the Deterministic Policy Engine evaluation drawer.

### WHAT THE JUDGE SEES
- Deterministic Policy Matrix:
  - $\le 30$: `ALLOW`
  - $31 - 60$: `MONITOR`
  - $61 - 80$: `STEP_UP` (Current Transaction: 78/100)
  - $81 - 95$: `HOLD`
  - $> 95$: `BLOCK`
- Policy Decision Packet: `final_action: STEP_UP`, `requires_human_approval: true`, `policy_version: "v1.0.0"`.
- Cryptographic `ActionToken` generation details (HMAC-SHA256 signature, 300-second TTL, UUID nonce).

### WHAT I SAY
> *"RazorShield strictly separates AI reasoning from execution authority.
> The Deterministic Policy Engine evaluates the risk score and evidence against immutable tier thresholds. Because this transaction scored 78, policy mandates a `STEP_UP` challenge.
> To authorize execution, the policy gateway mints a cryptographically signed HMAC-SHA256 `ActionToken` bound to the exact evidence snapshot hash."*

### WHAT BACKEND ACTUALLY DOES
- `DeterministicPolicyEngine.evaluate()` maps score and findings to policy actions.
- `ActionTokenGenerator.generate_token()` creates an HMAC-SHA256 digest over `(action, transaction_id, evidence_hash, nonce, expires_at)`.

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"We use asymmetric Ed25519 signatures."* (We use symmetric HMAC-SHA256).
- ❌ **DO NOT SAY:** *"The AI decided to block the user."* (Policy engine determined `STEP_UP`).

---

## 03:30 – 04:15 | Security Controls, Replay Defense & Failure Handling

### WHAT I CLICK
1. Click **"Authorize & Execute Action"** with role `RISK_ANALYST`.
2. Observe state change $\rightarrow$ `STEP_UP_REQUIRED`.
3. Click the **"Simulate Replay Attack"** button (or re-submit the action token).
4. Navigate to the **"Chaos Controls"** tab and toggle `GEMINI_OFFLINE`.

### WHAT THE JUDGE SEES
- First execution succeeds with status `EXECUTED` and writes to the cryptographic audit trail.
- Replay attempt is immediately blocked with status `ALREADY_EXECUTED` (HTTP 409).
- With `GEMINI_OFFLINE` enabled, running an investigation immediately succeeds via `DETERMINISTIC_FALLBACK` with zero downtime.

### WHAT I SAY
> *"Security in financial risk infrastructure must be fail-closed:
> 1. Single-Use Nonces: Replay attacks fail immediately because nonces are consumed under an atomic mutex lock.
> 2. TOCTOU Defense: If the underlying investigation evidence changes before execution, the token is invalidated.
> 3. Degraded Resilience: As shown here under injected chaos faults, when Gemini or ML is taken offline, the system safely falls back without dropping a single payment event."*

### WHAT BACKEND ACTUALLY DOES
- `ActionGateway.execute_action()` verifies HMAC signature, checks expiration, claims nonce atomically, and executes synthetic state mutation.
- `CryptographicAuditStore.append_event()` records the execution in a SHA-256 hash-chained SQLite audit ledger.

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"We use a public blockchain."* (It is a local SHA-256 cryptographic hash-chained audit ledger).
- ❌ **DO NOT SAY:** *"Redis is required for standalone execution."* (In-memory thread-safe mutex and SQLite provide full standalone operation).

---

## 04:15 – 05:00 | Held-Out Benchmark & Honest Economic Tradeoffs

### WHAT I CLICK
1. Click on the **"Evaluation Benchmark"** tab in the main navigation.
2. Show the held-out test confusion matrix, precision/recall metrics, and cost sensitivity slider.

### WHAT THE JUDGE SEES
- Held-out test results ($N=500$, 77 fraud, 423 benign):
  - **`RULES_PLUS_ML` (Optimal):** Recall **89.61%**, FPR **90.54%**, Expected Loss **₹1,17,330.82**.
  - **`ML_ONLY`:** Precision **44.83%**, Recall **50.65%**, FPR **11.35%**, Expected Loss **₹37.46L**.
- Explicit disclaimer: *"Evaluation executed on 500 stateful held-out records. Cost model: ₹250 synthetic intervention cost per False Positive."*

### WHAT I SAY
> *"Finally, we present our held-out benchmark with complete scientific honesty.
> On 500 held-out records with zero label leakage, our `RULES_PLUS_ML` model achieves **89.61% Recall**, intercepting ₹50.85L in fraud exposure.
> While the headline False Positive Rate is 90.54%, in high-value fraud detection where a missed loss averages ₹2,697 but an OTP challenge costs ₹250 in customer friction, this configuration yields the **lowest total business loss (₹1.17L)**.
> All benchmark results can be reproduced by running a single command: `python scripts/run_evaluation.py`. Thank you."*

### WHAT BACKEND ACTUALLY DOES
- Reads `docs/evaluation/HELDOUT_EVALUATION.md` generated dynamically by `scripts/run_evaluation.py`.
- Computes expected loss: $\text{Loss} = (\text{FN} \times \text{AvgFraudLoss}) + (\text{FP} \times ₹250)$.

### WHAT NOT TO CLAIM
- ❌ **DO NOT SAY:** *"Our false positive rate is 4.72%."* (4.72% was an old disproved number; the true FPR is 90.54% for combined step-up sensitivity).
- ❌ **DO NOT SAY:** *"₹250 is an industry-standard accounting constant."* (It is an explicitly disclosed synthetic modeling assumption).

---

## Quick Reference Summary for Presenter

```text
========================================================================================
TIMING CHEAT SHEET:
0:00 - 0:30  |  The Problem: Mule Networks & ATO (₹51.07L Exposure)
0:30 - 1:15  |  Tri-Engine Detection: Rules + IsolationForest + Graph
1:15 - 2:00  |  Graph Abuse Ring: 3 Accounts -> 1 Device Fingerprint
2:00 - 2:45  |  Advisory AI: Grounded Gemini Findings (NO-EVIDENCE-NO-CLAIM)
2:45 - 3:30  |  Policy Gate: Score 78 -> STEP_UP + HMAC ActionToken
3:30 - 4:15  |  Security & Chaos: Replay Rejection + Deterministic Fallback
4:15 - 5:00  |  Held-Out Benchmark: 89.61% Recall, ₹1.17L Loss, 1-Command CLI
========================================================================================
```
