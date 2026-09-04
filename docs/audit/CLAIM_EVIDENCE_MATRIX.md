# RAZORSHIELD AI — REPOSITORY CLAIM & EVIDENCE AUDIT MATRIX

**Audit Date:** August 30, 2026  
**Scope:** Complete repository inspection of all quantitative claims, architectural claims, and marketing terminology across README, documentation, and UI code.

---

| Claim / Terminology | Exact File Location | Repository Evidence Status | Verification Verdict | Required Rewrite / Framing |
| :--- | :--- | :--- | :---: | :--- |
| **"Reduces analyst triage from 15 minutes to under 30 seconds"** | `README.md`, `walkthrough.md` | API latency is measured ($\approx 1.5 - 3.2\text{s}$), but no controlled human-subject study of a 15m manual baseline exists. | 🔴 **UNSUPPORTED STATISTIC** | *"Autonomously synthesizes multi-hop cluster graphs and formats structured evidence briefs in $< 3$ seconds."* |
| **"4.72% Outright Block False Positive Rate"** | Prior audit reports | Empirical held-out test evaluation yields 31 FP / 423 Benign = **7.33% FPR** for $\text{Score} \ge 80$. | 🔴 **DISPROVED STATISTIC** | *"High-risk triage queue ($\text{Score} \ge 80 \rightarrow \text{HOLD}$) achieves 23.38% recall with a 7.33% False Positive Rate."* |
| **"Asymmetric Ed25519 Cryptographic Signatures"** | Legacy Architecture Notes | Code executes `hmac.new(SECRET_KEY, ... hashlib.sha256).hexdigest()`. | 🔴 **MISMATCHED CLAIM** | *"Symmetric HMAC-SHA256 signed ActionTokens with atomic single-use nonce locks."* |
| **"WCAG 2.2 AAA Certified"** | UI notes | Automated axe-core audits pass; no official third-party accessibility certificate exists. | 🟡 **OVERSTATED FRAMING** | *"Automated accessibility checks passing across all Command Center surfaces."* |
| **"100% Production Ready"** | Walkthrough summaries | Prototype running with in-memory graph and local SQLite database; requires Kafka/Redis clustering for enterprise scale. | 🟡 **PROTOTYPE MATURITY** | *"Fintech-grade risk management prototype with enterprise architectural invariants."* |
| **"89.61% Fraud Recall on Held-Out Test Set"** | `HELDOUT_EVALUATION.md`, `metrics.json` | 69 True Positives out of 77 fraud cases intercepted on `test.jsonl` ($N=500$). | 🟢 **VERIFIED & REPRODUCIBLE** | Keep as is: *"89.61% recall on high-value fraud attack scenarios."* |
| **"44.83% Precision & 11.35% FPR for ML Only"** | `HELDOUT_EVALUATION.md`, `metrics.json` | 39 TP, 48 FP, 375 TN, 38 FN on `test.jsonl` ($N=500$). | 🟢 **VERIFIED & REPRODUCIBLE** | Keep as is: *"IsolationForest achieves 44.83% precision and 11.35% FPR for zero-friction flows."* |
| **"NO-EVIDENCE-NO-CLAIM Hard Gate"** | `backend/app/agent/llm_provider.py` | Server-side validation raises `EvidenceVerificationError` on missing or unknown evidence citations. | 🟢 **VERIFIED & TESTED** | Keep as is: *"Cryptographic citation validation hard gate prevents ungrounded AI claims."* |
| **"Single-Use Nonce Replay Protection"** | `backend/app/gateway/action_gateway.py` | Atomic lock registry rejects duplicate nonces with HTTP 409 Conflict. | 🟢 **VERIFIED & TESTED** | Keep as is: *"Action Gateway enforces atomic single-use nonces to eliminate replay attacks."* |
| **"Tamper-Evident Merkle Audit Ledger"** | `backend/app/audit/store.py` | Chained SHA-256 hashes detect any modified, deleted, or reordered audit entry. | 🟢 **VERIFIED & TESTED** | Keep as is: *"Immutable SHA-256 Merkle chained audit ledger ensures compliance integrity."* |
| **"100% Defense-Only Operation"** | Repository-wide | Zero offensive tools, exploit generators, or unauthorized network probes present in codebase. | 🟢 **VERIFIED** | Keep as is: *"Strictly defense-only architecture in compliance with Track 02 mandate."* |
