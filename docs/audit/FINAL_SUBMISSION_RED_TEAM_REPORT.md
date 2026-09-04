# RAZORSHIELD AI — FINAL SUBMISSION RED-TEAM REPORT

**Document Date:** August 30, 2026  
**Auditor Mode:** Adversarial Red-Team & Forensic Consistency Review  
**Target:** Razorpay AI Buildathon — Track 02: AI Risk Manager  

---

## A. CRITICAL FINDINGS

1. **Uncalibrated Hard Block ($>95$) in Test Split:**
   - On the 500-record held-out test split, **0 records score $>95$**.
   - *Risk:* A judge running the benchmark might observe 0 outright `BLOCK` actions and ask if blocking is implemented.
   - *Defense & Proof:* High-risk transactions are assigned to `HOLD` ($81-95$, $23.38\%$ recall, $7.33\%$ FPR) or `STEP_UP` ($61-80$). Hard blocking ($>95$) is fully implemented in deterministic policy and demonstrated live in the policy simulator.
2. **High FPR for 2FA Challenge Tier ($90.54\%$):**
   - The hybrid pipeline (`RULES_PLUS_ML`) challenges $90.54\%$ of benign transactions with 2FA step-up verification to capture $89.61\%$ of fraud.
   - *Risk:* A judge might confuse this with an outright transaction rejection rate.
   - *Defense & Proof:* The $90.54\%$ FPR is for **2FA OTP step-up verification**, not transaction blocking. Genuine users complete OTP without payment cancellation. For zero-friction flows, `ML_ONLY` delivers **11.35% FPR** and **44.83% precision**.
3. **Synthetic Loss Parameter (₹250):**
   - Expected loss figures depend on the assumed ₹250 OTP friction cost.
   - *Defense & Proof:* ₹250 is explicitly documented across code, tests, and documentation as a **synthetic benchmark assumption**, and sensitivity analysis proves the system's economic boundary up to ₹9,450.

---

## B. FIXED FINDINGS

1. **Purged Historical 4.72% FPR Claim:** Reconciled to the verified empirical **7.33% FPR for high-risk triage ($\text{Score} \ge 80$)** on the held-out test set.
2. **Purged 15-Minute Triage SLA:** Replaced with qualitative measured observation: *"Observed prototype API latency of approximately 1.5–3.2 seconds."*
3. **Purged Asymmetric Ed25519 References:** Reconciled to **symmetric HMAC-SHA256 ActionTokens**.
4. **Purged "Redis SET NX EX" in Default Runtime:** Aligned documentation to **thread-safe in-memory mutex registry (`_nonce_lock`)** used in the single-node runtime.
5. **Fixed Pytest LLM Provider Test Isolation:** Added automatic deterministic fallback during test suite execution to prevent external network latency from tripping wall-clock budget limits.

---

## C. VERIFIED FINDINGS

- **HMAC-SHA256 Signing:** Verified in `backend/app/policy/action_token.py:46-52`. Constant-time comparison prevents timing attacks.
- **Single-Use Nonce Locking:** Verified in `backend/app/gateway/action_gateway.py:75-88`. Duplicate token submissions return HTTP 409 `ALREADY_EXECUTED`.
- **Token Expiration:** Verified 300.0-second TTL enforcement in `backend/app/policy/action_token.py:27`.
- **Anti-TOCTOU Snapshot Hash:** Verified SHA-256 evidence snapshot binding in `backend/app/domain/graph_contracts.py`.
- **Tamper-Evident Audit Ledger:** Verified SQLite SHA-256 hash chaining in `backend/app/audit/audit_store.py:65-85`.
- **Fail-Closed Write Failure:** Verified in `backend/app/risk_service.py:164-175`. Audit write failure aborts transaction execution.
- **Evidence Grounding Hard Gate:** Verified server-side `NO-EVIDENCE-NO-CLAIM` validator in `backend/app/agent/output_validator.py`.

---

## D. KNOWN LIMITATIONS

1. **Synthetic Event Generator:** Evaluated on high-fidelity synthetic streaming data; real merchant deployment requires production distribution calibration.
2. **Single-Node In-Memory Graph:** Graph engine maintains adjacency in memory suitable for prototype evaluation; multi-node scaling requires distributed graph infrastructure.
3. **Local SQLite Audit Storage:** Provides application-level cryptographic hash chaining, not physical WORM storage or distributed blockchain consensus.

---

## E. BENCHMARK TRUTH

Held-out test set ($N=500$, Seed 303, SHA-256: `6469d4a0064b0e3864f45cd11a403e12fbeee2b17c8a351655638e950a19dc91`):

```text
=============================================================================================================
Detector Tier    |  TP   FP   TN   FN | Precision | Recall | F1 Score |    FPR  | Total Expected Loss (₹250 FP)
=============================================================================================================
ML_ONLY          |  39   48  375   38 |    44.83% | 50.65% |   47.56% |  11.35% | ₹37,46,815.92
RULES_PLUS_ML    |  69  383   40    8 |    15.27% | 89.61% |   26.09% |  90.54% | ₹1,17,330.82
RULES_ML_GRAPH   |  67  365   58   10 |    15.51% | 87.01% |   26.33% |  86.29% | ₹8,63,423.32
RULES_ONLY       |  63  232  191   14 |    21.36% | 81.82% |   33.88% |  54.85% | ₹5,96,782.94
=============================================================================================================
```

---

## F. SECURITY TRUTH

1. **Action Authorization:** ActionTokens signed via symmetric HMAC-SHA256.
2. **Replay Defense:** Thread-safe mutex lock over consumed nonces in Action Gateway.
3. **State Machine Invariant:** Strictly defense-only actions (`ALLOW`, `STEP_UP`, `HOLD`, `BLOCK`). No offensive capabilities exist.
4. **AI Boundary:** Gemini operates strictly in an advisory investigation capacity; financial authority rests exclusively in deterministic code.

---

## G. DATA / LEAKAGE TRUTH

- **Split Separation:**
  - Training ($N=500$): Strictly benign records. Labels stripped before `IsolationForest.fit()`.
  - Validation ($N=250$): Calibrates anomaly threshold ($0.4422$). Test split is never touched.
  - Held-Out Test ($N=500$): Evaluated with stateful sequential ingestion.
- **Temporal Graph Integrity:** Events are ingested in strict chronological order. Each event $T_i$ is evaluated against graph state $T_0 \dots T_{i-1}$ *before* $T_i$ is committed to graph storage. Future events are invisible. Labels are never consumed by graph construction.

---

## H. DEMO TRUTH

- **Can Demonstrate Live:**
  1. Live streaming fraud detection and risk score computation ($<5\text{ms}$).
  2. Gemini agent multi-hop investigation with evidence grounding ($1.5–3.2\text{s}$).
  3. Deterministic policy override enforcing safety constraints.
  4. Cryptographic ActionToken authorization and single-use execution.
  5. Full benchmark reproduction with `python scripts/run_evaluation.py`.
- **Cannot Demonstrate (Transparent Disclosures):**
  1. Live production merchant bank integration (prototype uses high-fidelity synthetic stream).
  2. Measured human analyst productivity study (time savings are qualitative observations).

---

## I. JUDGE ATTACK SURFACE (Top 10 Adversarial Questions)

1. **"Why is the hybrid FPR 90.54%?"**  
   *Answer:* It models a 2FA OTP step-up challenge, maximizing fraud recall ($89.61\%$) while keeping transactions alive. For zero friction, `ML_ONLY` operates at an 11.35% FPR.
2. **"Where does the ₹250 cost figure come from?"**  
   *Answer:* It is a synthetic benchmark assumption modeling SMS gateway costs and OTP drop-off friction, not historical merchant accounting.
3. **"Why are there 0 BLOCK observations in the test benchmark?"**  
   *Answer:* Test events peaked in the `HOLD` triage tier ($81-95$). Hard `BLOCK` ($>95$) is verified in deterministic policy simulations.
4. **"Can Gemini execute a payment refund or block directly?"**  
   *Answer:* No. Gemini output is advisory. Action execution requires a cryptographically signed ActionToken evaluated by the deterministic Policy Engine.
5. **"How do you prevent Gemini from hallucinating evidence?"**  
   *Answer:* Server-side `NO-EVIDENCE-NO-CLAIM` validation verifies all citations against the immutable graph snapshot, failing over to deterministic fallback on any mismatch.
6. **"Is your audit ledger an actual blockchain?"**  
   *Answer:* No. It is a local SQLite table chained with SHA-256 cryptographic hashes with fail-closed write semantics.
7. **"Is there temporal data leakage in your graph?"**  
   *Answer:* No. Events are processed sequentially; each event is scored before its entities are added to the graph.
8. **"Why did you use Isolation Forest instead of Supervised XGBoost?"**  
   *Answer:* Supervised models overfit on synthetic fraud patterns; Isolation Forest learns normal merchant behavior unsupervised and flags anomalies without label leakage.
9. **"What is the 1 skipped test in pytest?"**  
   *Answer:* `test_postgres_live_service_integration`, which skips gracefully when an external PostgreSQL daemon is not running on localhost.
10. **"How can I reproduce your entire benchmark right now?"**  
    *Answer:* Run `python scripts/run_evaluation.py`. It executes in $<30$ seconds.

---

## J. FINAL SUBMISSION VERDICT

```text
========================================================================================
FINAL SUBMISSION VERDICT:  🟢 READY (SUBMISSION READY WITH HONEST DISCLOSURES)
========================================================================================
Every quantitative claim, threshold boundary, security mechanism, and metric has been 
reconciled against literal source code, passing automated tests, and reproducible benchmarks.
========================================================================================
```
