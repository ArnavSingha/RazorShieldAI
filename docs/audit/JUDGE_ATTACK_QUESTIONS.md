# RAZORSHIELD AI — 30 ADVERSARIAL JUDGE ATTACK QUESTIONS & DEFENSIBLE ANSWERS

**Audit Date:** August 30, 2026  
**Target:** Razorpay Track 02 Judge Interrogation Preparedness  

---

### Q1: "Why is your hybrid False Positive Rate 90.54%? Isn't that unviable for merchants?"
- **Evidence-Based Answer:** In payment risk architecture, score $\ge 50$ triggers a **2FA OTP `STEP_UP` challenge**, not an outright payment cancellation. An OTP challenge introduces soft friction ($\approx \text{₹250}$ drop-off friction) while intercepting ₹51.07L in fraud. For zero-friction flows, our standalone IsolationForest operates at **11.35% FPR and 44.83% precision**.
- **Repository Evidence:** [`backend/app/policy/engine.py:38`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/policy/engine.py#L38) (`action = "STEP_UP"` for scores 61–80); [`scripts/run_evaluation.py:99`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/scripts/run_evaluation.py#L99).
- **Safe Presentation Answer:** *"Our hybrid detector prioritizes catching 89.61% of fraud by routing high-risk events to 2FA OTP verification, protecting ₹51.07L with minimal customer drop-off."*
- **What NOT to Claim:** Do NOT claim the system blocks 90% of legitimate transactions.

### Q2: "Can Gemini hallucinate and block an innocent customer?"
- **Evidence-Based Answer:** No. First, Gemini is strictly **advisory** and cannot issue financial decisions. Second, our `NO-EVIDENCE-NO-CLAIM` validator raises `EvidenceVerificationError` if any claim cites an evidence ID not present in the immutable SHA-256 evidence snapshot, activating deterministic fallback.
- **Repository Evidence:** [`backend/app/agent/llm_provider.py:140-155`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/agent/llm_provider.py#L140-L155); [`test_evidence_grounding_strictness.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/tests/unit/test_evidence_grounding_strictness.py).
- **Safe Presentation Answer:** *"Gemini generates hypothesis briefs, but our policy engine deterministically controls execution, and strict citation hard gates prevent hallucinations."*
- **What NOT to Claim:** Do NOT claim LLMs are inherently 100% immune to hallucinations without mentioning our server-side validation hard gate.

### Q3: "Can an attacker replay an ActionToken to execute an unauthorized payout freeze twice?"
- **Evidence-Based Answer:** No. ActionTokens contain single-use UUID nonces and a 300-second TTL. The Action Gateway locks nonces atomically using thread-safe primitives (`SET NX EX` semantics), raising `ActionGatewayReplayError` (HTTP 409) on any duplicate attempt.
- **Repository Evidence:** [`backend/app/gateway/action_gateway.py:90-94`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/gateway/action_gateway.py#L90-L94); [`test_action_token_security.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/tests/security/test_action_token_security.py).
- **Safe Presentation Answer:** *"Every action is single-use, HMAC-signed, and protected by atomic nonce consumption."*
- **What NOT to Claim:** Do NOT claim ActionTokens are client-side JWTs.

### Q4: "How do you prove your test dataset is genuinely held out?"
- **Evidence-Based Answer:** `train.jsonl` (seed 101), `validation.jsonl` (seed 202), and `test.jsonl` (seed 303) are generated independently. Model training and threshold calibration execute strictly on train/val splits; `test.jsonl` is consumed in a read-only stream by `scripts/run_evaluation.py` with zero label feedback.
- **Repository Evidence:** [`scripts/generate_heldout_dataset.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/scripts/generate_heldout_dataset.py); [`backend/app/evaluation/detectors.py:15-30`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/evaluation/detectors.py#L15-L30).
- **Safe Presentation Answer:** *"Our evaluation evaluates 500 isolated test records generated with distinct seeds and zero label leakage."*
- **What NOT to Claim:** Do NOT claim this is real merchant data; acknowledge it is high-fidelity synthetic evaluation data.

### Q5: "Why did you use Gemini if Rules, ML, and Graph already compute risk scores?"
- **Evidence-Based Answer:** Machine learning and graph algorithms produce raw numbers (e.g. `score = 78`), but human risk analysts require contextual synthesis (multi-hop cluster relationships, contradictory signals, and timeline correlation) to make informed manual reviews rapidly. Gemini acts as an autonomous synthesizer.
- **Repository Evidence:** [`backend/app/agent/orchestrator.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/agent/orchestrator.py); [`InvestigationWorkspace.tsx`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/frontend/src/components/investigations/InvestigationWorkspace.tsx).
- **Safe Presentation Answer:** *"ML and graph detect the anomaly in milliseconds; Gemini explains the coordinated fraud network to the analyst in plain English with exact citations."*
- **What NOT to Claim:** Do NOT claim Gemini computes the risk score.

### Q6: "Why are there zero test observations in the hard BLOCK range (>95)?"
- **Evidence-Based Answer:** In payment risk, hard blocks are reserved for confirmed malicious vectors. On our 500-record test set, the highest risk transactions scored between 81 and 94 (`HOLD` triage queue), capturing $23.38\%$ recall with $7.33\%$ FPR. We honestly report that hard BLOCK is unobserved rather than manufacturing artificial 100-score outliers.
- **Repository Evidence:** [`docs/audit/FINAL_FORENSIC_SYSTEM_AUDIT.md:Section 4`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/docs/audit/FINAL_FORENSIC_SYSTEM_AUDIT.md).
- **Safe Presentation Answer:** *"Hard blocks require human triage from the HOLD queue (Score 81–95), where our precision reaches 38.46%."*
- **What NOT to Claim:** Do NOT claim the system autonomously hard-blocked transactions on the test set.

### Q7: "What happens if Gemini API is completely down during an ongoing attack?"
- **Evidence-Based Answer:** The system executes a seamless failover to `DeterministicFallbackLLMProvider`, generating structured rule-derived investigation summaries without interrupting transaction scoring, policy evaluation, or Action Gateway execution.
- **Repository Evidence:** [`backend/app/agent/llm_provider.py:210`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/agent/llm_provider.py#L210); [`test_chaos_resilience.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/tests/security/test_chaos_resilience.py).
- **Safe Presentation Answer:** *"Our control plane operates with zero runtime dependency on LLMs; fallback providers ensure 100% operational continuity if APIs fail."*
- **What NOT to Claim:** Do NOT claim the LLM is hosted locally.

### Q8: "What prevents an analyst from executing an unauthorized payout freeze?"
- **Evidence-Based Answer:** The backend enforces Role-Based Access Control (RBAC). `ANALYST` roles can only trigger `STEP_UP` and `INVESTIGATE`; only `ADMIN` roles possess the cryptographic capability to execute `HOLD` and `BLOCK` actions.
- **Repository Evidence:** [`backend/app/policy/rbac.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/policy/rbac.py); [`test_phase2_5_hardening.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/tests/integration/test_phase2_5_hardening.py).
- **Safe Presentation Answer:** *"High-risk actions require elevated ADMIN credentials enforced cryptographically at the Action Gateway."*
- **What NOT to Claim:** Do NOT claim security is handled by disabling frontend buttons.

### Q9: "Where is model training performed?"
- **Evidence-Based Answer:** Model training is executed in `MLEngine.fit_baseline()` using `scikit-learn`'s `IsolationForest` on 500 clean feature vectors from `train.jsonl`. The model instance is held in memory for sub-millisecond inference during transaction processing.
- **Repository Evidence:** [`backend/app/ml/engine.py:38`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/ml/engine.py#L38); [`test_ml_real_iforest.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/tests/unit/test_ml_real_iforest.py).
- **Safe Presentation Answer:** *"Isolation Forest is trained unsupervised on historical transaction baselines to detect multi-dimensional numerical outliers."*
- **What NOT to Claim:** Do NOT claim the model is a deep neural network or LLM fine-tune.

### Q10: "How does the graph engine prevent memory explosion on high-degree nodes like payment gateways?"
- **Evidence-Based Answer:** `GraphEngine` implements hub pruning and bounded 2-hop radius queries. High-degree merchant gateway nodes are filtered during traversal to focus purely on card-device-IP multi-account clusters.
- **Repository Evidence:** [`backend/app/graph/engine.py:65`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/app/graph/engine.py#L65); [`test_graph_intelligence_cluster.py`](file:///c:/Users/arnav/OneDrive/Desktop/Assingments/RazorShield%20AI/backend/tests/unit/test_graph_intelligence_cluster.py).
- **Safe Presentation Answer:** *"We prune shared payment infrastructure hubs and bound traversals to 2 hops to ensure sub-5ms graph query latencies."*
- **What NOT to Claim:** Do NOT claim the graph is stored in a distributed Neo4j cluster (it is an in-memory heterogeneous graph).

---

### Q11–Q30 Quick-Fire Adversarial Matrix

| # | Question | Evidence-Based Short Answer | Code Reference | What NOT to Claim |
| :-: | :--- | :--- | :--- | :--- |
| **11** | *What is your transaction evaluation latency?* | Sub-15ms for Tri-Engine risk scoring; 1.5–3s for asynchronous Gemini investigation briefs. | `backend/app/risk_service.py:151` | Don't claim LLM runs in sub-10ms. |
| **12** | *How is the ₹250 FP cost derived?* | Models ₹150 tier-1 verification + ₹100 lost margin on 2FA customer drop-off. | `scripts/run_evaluation.py:99` | Don't claim it's a universal banking standard. |
| **13** | *Can an analyst edit an audit record?* | No. Records are SHA-256 Merkle-chained; tampering invalidates the cryptographic integrity check. | `backend/app/audit/store.py:65` | Don't claim it is stored on a public blockchain. |
| **14** | *What happens if the audit store is down?* | The risk service fails closed and rejects the transaction with `AuditPersistenceError`. | `backend/app/risk_service.py:171` | Don't claim transactions process un-audited. |
| **15** | *Is this defense-only?* | Yes. 100% synthetic in-memory event simulation with zero exploit, probing, or attack capabilities. | Whole Repo Inspection | Don't claim offensive penetration capabilities. |
| **16** | *Does the UI support dark mode?* | Yes. Built with custom Tailwind fintech theme with high-contrast status tokens. | `frontend/src/index.css` | Don't claim formal WCAG 2.2 certification. |
| **17** | *How are streaming events pushed to UI?* | Via Server-Sent Events (`/api/stream/events`) connected to `LiveRiskStream.tsx`. | `backend/app/api/stream.py` | Don't claim raw WebSockets. |
| **18** | *How do you prevent TOCTOU attack on evidence?* | Token binds to `evidence_snapshot_hash`; if evidence mutates before execution, token is rejected. | `backend/app/policy/action_token.py:126` | Don't claim static state caching. |
| **19** | *What features does IsolationForest use?* | 7 features: Amount, 30d Z-score, 1h count, 24h count, 1h volume, Hour, Device reuse. | `backend/app/ml/engine.py:50` | Don't claim NLP text features. |
| **20** | *How do you detect mule rings?* | 2-hop graph BFS tracks accounts sharing compromised devices (`dev_farm_shared_99`). | `backend/app/graph/engine.py:80` | Don't claim single-transaction rules alone catch it. |
| **21** | *What is the database technology?* | SQLite local engine with adapter interfaces for PostgreSQL / Redis. | `backend/app/config.py:20` | Don't claim a live distributed cluster is running locally. |
| **22** | *How do you handle expired tokens?* | Action Gateway compares `time.time() > token.expires_at` and raises HTTP 401. | `backend/app/policy/action_token.py:108` | Don't claim tokens are valid forever. |
| **23** | *What is the test pass rate?* | 96 passed, 1 skipped, 0 failed in pytest ($<30\text{s}$). | Pytest terminal output | Don't claim 100% test coverage of all edge cases. |
| **24** | *Can an unauthenticated user call APIs?* | No. Protected endpoints validate JWT bearer tokens and RBAC roles. | `backend/app/policy/rbac.py` | Don't claim public unprotected execution. |
| **25** | *How is the simulator implemented?* | Pre-configured generator injecting 7 synthetic attack bursts into the live stream. | `frontend/src/components/simulator/...` | Don't claim live live network traffic injection. |
| **26** | *What happens on negative amount injection?* | Pydantic validator rejects payload with HTTP 422 before reaching risk engines. | `backend/app/domain/validator.py:20` | Don't claim negative numbers score as fraud. |
| **27** | *Why do you use HMAC instead of Ed25519?* | Symmetric HMAC-SHA256 provides microsecond signing latency suitable for synchronous payment gateways. | `backend/app/policy/action_token.py:82` | Don't claim asymmetric Ed25519 was implemented. |
| **28** | *How does Policy Engine override AI?* | Deterministic policy matrix executes after AI, stepping down VIPs and stepping up high cluster risks. | `backend/app/policy/engine.py:50` | Don't claim AI has final override authority. |
| **29** | *What is your biggest known limitation?* | Precision is low (15.27%) under score-50 cutoff, requiring 2FA OTP step-up rather than outright blocking. | `docs/audit/FINAL_FORENSIC_SYSTEM_AUDIT.md` | Don't claim zero false positives. |
| **30** | *What would you build next for production?* | Merchant feedback loop ingestion for dynamic threshold tuning and Kafka event streaming. | `docs/audit/RED_YELLOW_GREEN_MATRIX.md` | Don't claim it is already running in production at Razorpay. |
