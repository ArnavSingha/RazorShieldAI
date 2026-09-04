# RazorShield AI — 3-Track Empirical Evaluation & Risk Benchmark

## Evaluation Provenance Metadata
- **Evaluation Run ID:** `eval_run_b7c46af5`
- **Training Dataset Hash:** `7a358ddc9d75d3b3`
- **Validation Dataset Hash:** `d549a87d52231b82`
- **ML Model Version:** `IsolationForest_v1.0`
- **Calibrated Anomaly Threshold:** `0.4422` (Source: `VALIDATION`)
- **Test Split Touched Before Evaluation:** `False`

---

## TRACK A — Detection Metrics (Stateful Event-Stream Benchmark)

| Detector Tier | TP | FP | TN | FN | Errors | Coverage | Precision | Recall | F1 Score | FPR | FNR | FP Cost (₹) | FN Loss (₹) | Total Expected Loss (₹) | Unsafe Actions |
| ------------- | -- | -- | -- | -- | ------ | -------- | --------- | ------ | -------- | --- | --- | ----------- | ----------- | ----------------------- | -------------- |
| `RULES_ONLY` | 63 | 232 | 191 | 14 | `0` | 100.0% | **21.36%** | **81.82%** | **33.88%** | 54.85% | 18.18% | ₹58,000 | ₹538,783 | **₹596,783** | `0` |
| `ML_ONLY` | 39 | 48 | 375 | 38 | `0` | 100.0% | **44.83%** | **50.65%** | **47.56%** | 11.35% | 49.35% | ₹12,000 | ₹3,734,816 | **₹3,746,816** | `0` |
| `RULES_PLUS_ML` | 69 | 383 | 40 | 8 | `0` | 100.0% | **15.27%** | **89.61%** | **26.09%** | 90.54% | 10.39% | ₹95,750 | ₹21,581 | **₹117,331** | `0` |
| `RULES_ML_GRAPH` | 67 | 365 | 58 | 10 | `0` | 100.0% | **15.51%** | **87.01%** | **26.33%** | 86.29% | 12.99% | ₹91,250 | ₹772,173 | **₹863,423** | `0` |

---

## TRACK B — Investigation & Reasoning Quality (Sample Breakdown & Execution Provenance)

| Metric / Property | `GRAPH_INVESTIGATION` | `GEMINI_INVESTIGATION` |
| :--- | :---: | :---: |
| **Sample Count** | `50` | `50` |
| **Positive / Negative Cases** | `30 / 15` | `30 / 15` |
| **Adversarial Injection Cases** | `5` | `5` |
| **Raw Ungrounded Intercepts** | `0` | `5` |
| **Post-Validation Ungrounded Claims** | `0` | `0` |
| **Evidence Grounding Rate** | **100.0%** | **100.0%** |
| **Execution Mode** | `DETERMINISTIC_GRAPH_ENGINE` | `LIVE_GEMINI` |
| **Live Provider Call** | `False` | `True` |
| **Configured Provider** | `DeterministicGraphEngine_v1.0` | `Gemini-3.6-Flash` |
| **Active Execution Provider** | `DeterministicGraphEngine_v1.0` | `Gemini-3.6-Flash` |

---

## TRACK C — Control Plane & Execution Safety Metrics

- **Unauthorized Action Attempts Allowed:** `0`
- **Policy Overrides Audited:** `100%`
- **Replay Attack Rejections:** `100.0%` (HMAC Signed Tokens & Nonce Locks)
- **Unsafe Action Authorization Rate:** **0.00% (0 Unsafe Actions Recorded)**

---

## Dynamic Empirical Findings
1. **Lowest Expected Loss Tier:** `RULES_PLUS_ML` achieved the lowest measured financial loss of ₹117,331.
2. **Stateful Graph Intelligence:** Multi-hop ring detection accumulates evidence across events without label leakage.
3. **Zero Exception-to-Fraud Conversion:** 0 system errors were converted into fraud positives.

*Report generated at UTC 2026-08-30 09:06:02*
