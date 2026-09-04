# RAZORSHIELD AI — ONE-PAGE JUDGE CHEAT SHEET

**Track:** Razorpay AI Buildathon — Track 02: AI Risk Manager  
**Project:** RazorShield AI Command Center  
**Repository State:** Frozen & Audited (96/96 Unit Tests Passed, 100% Quality Gates Clean)

---

## 1. Core Technical Snapshot

| Dimension | Exact Implementation Truth |
| :--- | :--- |
| **Problem** | Coordinated financial loss in digital payments caused by rapid fund draining before risk teams can intervene. |
| **Loss Class** | **Mule Account Syndicates, High-Velocity Velocity Bursts & Account Takeovers (ATO)** in Indian digital commerce. |
| **Architecture** | Defense-in-depth pipeline: Real-time Ingestion $\rightarrow$ Tri-Engine Risk Scoring $\rightarrow$ Graph Subgraph Traversal $\rightarrow$ Advisory LLM Reasoning $\rightarrow$ Deterministic Policy Engine $\rightarrow$ Fail-Closed Action Gateway. |
| **ML Model** | Unsupervised `IsolationForest` ($n_{\text{estimators}}=50$, $\text{contamination}=0.05$, $\text{random\_state}=42$) trained on benign feature space (`amount_ratio`, `log_amount`, `device_mismatch`, `ip_mismatch`). |
| **Held-Out Dataset** | $N=500$ statefully streamed records (77 fraud, 423 benign; SHA-256: `6469d4a0e9...`) evaluated with zero label leakage. |
| **Key Metrics** | **`RULES_PLUS_ML`:** **89.61% Recall**, 15.27% Precision, 90.54% FPR, **₹1,17,330.82 Expected Loss** (Lowest total business loss). |
| **AI Role** | **Strictly advisory copilot** (Google Gemini 3.6 Flash); validated by `AgentOutputValidator` under strict `NO-EVIDENCE-NO-CLAIM`. Zero financial authority. |
| **Policy Tiers** | $\le 30$: `ALLOW` \| $31-60$: `MONITOR` \| $61-80$: `STEP_UP` \| $81-95$: `HOLD` \| $>95$: `BLOCK` (Policy simulation). |
| **Security Controls** | Symmetric HMAC-SHA256 ActionTokens, 300s TTL, thread-safe single-use UUID nonces, anti-TOCTOU evidence snapshot hashes, server-side RBAC, and SHA-256 hash-chained audit ledger. |
| **Biggest Limitation** | High false-positive intervention rate (90.54%) under combined sensitivity, requiring 2FA OTP step-up challenges rather than outright blocking. |

---

## 2. Top 10 Hardest Judge Questions & 1-Sentence Answers

1. **Why is your False Positive Rate 90.54%?**  
   *Because in high-value fraud ($₹51.07\text{L}$ exposure), missing a fraud costs $₹2,697$ while an OTP challenge costs $₹250$, so maximizing sensitivity to $89.61\%$ minimises total expected business loss.*

2. **Why should I trust synthetic benchmark data?**  
   *Real BFSI fraud records cannot be shared due to RBI/PCI-DSS privacy regulations, so we synthesized 500 realistic records with statistical distributions calibrated against published Indian fraud patterns and evaluated under strict chronological state accumulation.*

3. **Why use Isolation Forest instead of Supervised XGBoost?**  
   *Emerging fraud attacks and zero-day account takeovers have zero historical ground-truth labels, making unsupervised anomaly isolation in feature space more robust against label contamination.*

4. **Can Gemini hallucinate fake fraud evidence?**  
   *No, because our `AgentOutputValidator` hard-gates every output: any claim citing an unknown Evidence ID is immediately rejected with `EvidenceVerificationError` before reaching policy.*

5. **Can Gemini directly block accounts or move money?**  
   *No, Gemini is strictly advisory; only our deterministic policy engine and human-authorized Action Gateway possess execution capability.*

6. **Can an ActionToken be intercepted and replayed?**  
   *No, ActionTokens contain single-use UUID nonces consumed under a thread-safe mutex lock, causing duplicate execution attempts to return HTTP 409 `ALREADY_EXECUTED`.*

7. **What happens if a customer's fraud state changes before token execution?**  
   *ActionTokens cryptographically bind the SHA-256 hash of the investigation evidence snapshot; any mutation in graph entities invalidates the token with `INVESTIGATION_STATE_CHANGED`.*

8. **What happens if Gemini is rate-limited or goes offline during live payments?**  
   *The system instantly engages `DeterministicFallbackLLMProvider` in under 2 milliseconds, maintaining 100% payment pipeline uptime with explicit fallback provenance logging.*

9. **Where does the ₹250 False Positive cost number come from?**  
   *It is an explicitly disclosed synthetic model parameter representing $₹5$ SMS OTP gateway cost plus estimated $₹245$ customer cart abandonment friction margin during step-up verification.*

10. **Why is there no BLOCK action in the held-out test results?**  
    *Because held-out scores peaked at $83/100$ (`HOLD`), reserving hard `BLOCK` ($>95$) for catastrophic syndicate attacks, which we honestly disclose rather than fabricating artificial test set blocks.*

---

## 3. Five-Command CLI Verification

```powershell
# 1. Held-Out Evaluation (< 25s)
python scripts/run_evaluation.py

# 2. Pytest Unit & Integration Suite (< 25s)
python -m pytest backend/tests -v

# 3. Frontend Production Build (< 10s)
npm run build

# 4. Secret & Quality Gate Check (< 35s)
python scripts/quality_check.py

# 5. Pre-Flight Submission Integrity Check (< 10s)
python scripts/submission_integrity_check.py
```
