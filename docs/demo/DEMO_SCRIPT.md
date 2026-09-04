# RazorShield AI — 5-Minute Production Demonstration Script

## Demonstration Narrative Architecture
**Core Message:** "RazorShield AI is an AI-native payment risk operating system that investigates suspicious activity, correlates graph entities, explains grounded evidence, enforces deterministic policy, executes bounded responses, and safely degrades when dependencies fail."

---

## 12-Scene Storyboard Sequence

### Scene 1: Baseline System Operations (0:00 - 0:30)
- **Visual:** Command Center showing live metric tickers & normal payment stream flowing at ~120 transactions/min.
- **Narrative:** "Here we see normal RazorShield payment activity flowing with sub-20ms evaluation latency and low risk scores."

### Scene 2: Attack Injection — Account Takeover (0:30 - 1:00)
- **Action:** Open Attack Simulator and launch `ATO-001` (Account Takeover scenario).
- **Visual:** Stream flags incoming transaction with risk score `84/100` (High).

### Scene 3: Signal Extraction & Anomaly Detection (1:00 - 1:30)
- **Action:** Click "Investigate" on transaction `tx_992104`.
- **Visual:** Signal breakdown highlights Geographic Velocity Anomaly (1200km travel in 4 mins) + IsolationForest anomaly score `0.88`.

### Scene 4: Graph Ring Intelligence (1:30 - 2:00)
- **Action:** Toggle to "Entity Graph" view.
- **Visual:** React Flow graph expands showing `dev_fp_99281a` linked across 5 distinct customer accounts within 1 hour.

### Scene 5: AI Evidence Collection (2:00 - 2:30)
- **Action:** Open AI Investigator trace panel.
- **Visual:** Step-by-step state machine trace showing `TRIAGE -> COLLECT_CONTEXT -> GENERATE_HYPOTHESIS -> VERIFY_EVIDENCE`. Structured evidence links highlighted.

### Scene 6: Friction Optimization — STEP-UP Recommendation (2:30 - 3:00)
- **Action:** Review AI recommendation.
- **Visual:** AI recommends `STEP-UP` (OTP challenge) instead of outright `BLOCK`, recognizing genuine customer conversion value.

### Scene 7: Policy Authorization Validation (3:00 - 3:15)
- **Visual:** Policy Engine evaluates recommendation against score bracket `61-80` (`STEP_UP`) or `81-95` (`HOLD` Triage) and confirms action authorization.

### Scene 8: Bounded Action Execution (3:15 - 3:30)
- **Action:** Click "Execute Policy Response".
- **Visual:** Action Gateway verifies HMAC-SHA256 ActionToken, checks single-use nonce, and logs executed state transition.

### Scene 9: Second Wave Burst Attack (3:30 - 4:00)
- **Action:** Simulator triggers second burst event on same compromised entity. Risk score climbs to `98/100` (Critical).
- **Visual:** System automatically escalates policy response to `BLOCK`.

### Scene 10: Chaos Injection — LLM Dependency Failure (4:00 - 4:30)
- **Action:** Open Chaos Controls and toggle `LLM_SERVICE_OFFLINE`.
- **Visual:** Submit new suspicious transaction. UI shows `LLM_OFFLINE_FALLBACK_ACTIVE`.

### Scene 11: Deterministic Safe Degradation (4:30 - 4:45)
- **Visual:** System falls back to Rule Engine + Graph score and enforces safe `STEP-UP` without crashing or approving blindly.

### Scene 12: Immutable Audit & Lineage Trace (4:45 - 5:00)
- **Action:** Navigate to Security Audit Center.
- **Visual:** Complete correlation trace `transaction_id -> risk_decision_id -> investigation_id -> policy_decision_id -> action_id -> audit_event_id` verified with cryptographic HMAC signature.
