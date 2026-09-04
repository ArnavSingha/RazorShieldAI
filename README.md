# RazorShield AI — Real-Time Coordinated Fraud Defense Engine

> **RazorShield AI** is a fully implemented, automated-test-verified payment-risk control-plane prototype (UX Implementation Complete; Usability Validation Pending). It follows relevant OWASP transaction-authorization security guidance and is designed with WCAG 2.2 accessibility principles for server-authoritative decision making, policy enforcement, single-use action tokens, and cryptographic auditability.

---

## Technical Specifications & Consistency Defaults

- **LLM Engine:** Google Gemini 3.6 (`gemini-3.6-flash`) with structured JSON reasoning and deterministic rule-based fallback.
- **Frontend Architecture:** Vite + React 18 + `@xyflow/react` compiled into `frontend/dist` and directly served by FastAPI at root (`GET /`).
- **Security & Authorization:** Environment-backed dynamic principal authorization with backend capability RBAC (`RBACPolicyGateway`) and server-side single-use action tokens.
- **Authentication Model:** Standalone prototype identity simulation (`DEV ROLE SIMULATION`) for local testing. Production deployment requires integration with external identity providers (OIDC/SAML), session management, MFA/2FA, and KMS secret management.
- **Policy-Driven SLA Engine:** Policy-driven SLA targets (`CRITICAL=2h`, `HIGH=4h`, `MEDIUM=8h`, `LOW=24h`) evaluated dynamically server-side (`SLAPolicyEngine`).
- **State Version Freshness:** Server-assembled `DecisionPacket` with SHA-256 `version_token`. Execution requests validate `expected_version_token` and abort with `409 STALE_DECISION_PACKET` if case state shifted.

---

## 🔒 Note on Authentication & Production Deployment Realism

1. **Authentication:** The UI includes an explicit `DEV ROLE SIMULATION` selector to allow testing RBAC capability boundaries (`AUDITOR`, `RISK_ANALYST`, `OPERATOR`, `ADMIN`) in local development mode.
2. **Authorization:** All authorization checks are enforced **server-side** on every API endpoint (`RBACPolicyGateway.require_capability`). Client-side button hiding or modal input requirements (`"EXECUTE"`) are purely UI double-confirmation controls.
3. **Production Deployment Requirements:** Production deployment requires integrating an external Identity Provider (OIDC/Okta/SAML), session cookie management, MFA/2FA step-up prompts, and cloud KMS secret key management.

---

## 🔒 Note on Test Fixtures & Negative Assertion Patterns

Strings such as `admin_sec_key_99`, `operator_sec_key_77`, `defaultDemoNodes`, or `192.168.1.100` appearing in test suites, simulation fixtures, or `scripts/submission_integrity_check.py` are **strictly negative-test assertion patterns** (used by automated quality scripts to assert that legacy hardcoded secrets do *not* exist in production application code) and **synthetic benchmark data** (used for isolated unit testing). They are not runtime secrets or live operational credentials.

---

## Quick Start & Environment Setup

1. **Copy Environment Template:**
   ```bash
   cp .env.example .env
   ```
2. **Configure API Keys (Optional):**
   ```env
   LLM_PROVIDER=gemini
   LLM_MODEL_NAME=gemini-3.6-flash
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. **Run Environment & Quality Verification:**
   ```bash
   python scripts/check_environment.py
   python scripts/quality_check.py
   ```
4. **Start Application Server:**
   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```
   Navigate to `http://localhost:8000` to view the compiled Command Center SPA.

---

## 📊 Track 02 Held-Out Evaluation Benchmark

RazorShield AI evaluates 4 detector tiers against an isolated, untouched 500-record held-out dataset (`data/evaluation/test.jsonl`, 77 fraud, 423 benign):

| Detector Configuration | Precision | Recall | F1 Score | FPR | Total Expected Loss (₹250 FP Cost)* |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`ML_ONLY` (IsolationForest)** | **44.83%** | 50.65% | **47.56%** | **11.35%** | ₹37,46,815.92 |
| **`RULES_PLUS_ML` (Hybrid)** | 15.27% | **89.61%** | 26.09% | 90.54% | **₹1,17,330.82** |
| **`RULES_ML_GRAPH` (Tri-Engine)**| 15.51% | 87.01% | 26.33% | 86.29% | ₹8,63,423.32 |
| **`RULES_ONLY` (Baseline)** | 21.36% | 81.82% | 33.88% | 54.85% | ₹5,96,782.94 |

*\*Methodology Note: ₹250 is a synthetic intervention-cost assumption used for benchmark comparison (modeling 2FA customer drop-off friction rather than payment cancellation). The hybrid configuration prioritizes recall (89.61%), challenging suspect transactions with stepped-up verification. For zero-friction flows, the standalone Isolation Forest operates at an 11.35% FPR and 44.83% precision.*

### Reproduce Benchmark with 1 Command:
```bash
python scripts/run_evaluation.py
```

---

## 🔒 Policy Engine Decision Tiers

- **`0 – 30`** $\rightarrow$ **`ALLOW`** (Instant zero-friction clearance)
- **`31 – 60`** $\rightarrow$ **`MONITOR`** (Telemetry logging)
- **`61 – 80`** $\rightarrow$ **`STEP_UP`** (2FA OTP verification challenge)
- **`81 – 95`** $\rightarrow$ **`HOLD`** (Manual analyst review queue)
- **`> 95`** $\rightarrow$ **`BLOCK`** *(Hard reject — unobserved in test split; demonstrated in policy simulation)*

---

## Documentation Index

- [Held-Out Evaluation Report](file:///docs/evaluation/HELDOUT_EVALUATION.md)
- [Final Forensic System Audit](file:///docs/audit/FINAL_FORENSIC_SYSTEM_AUDIT.md)
- [Judge Demo Truth Table](file:///docs/audit/JUDGE_DEMO_TRUTH_TABLE.md)
- [Clean Checkout Reproduction Guide](file:///docs/audit/CLEAN_CHECKOUT_REPRODUCTION.md)
- [Adversarial Judge Attack Questions](file:///docs/audit/JUDGE_ATTACK_QUESTIONS.md)
- [System Architecture](file:///docs/architecture/ARCHITECTURE.md)
- [AI Safety & Grounding Schema](file:///docs/ai-safety/AI_SAFETY.md)
- [Security & RBAC Model](file:///docs/security/SECURITY_MODEL.md)

