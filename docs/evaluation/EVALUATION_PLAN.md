# RazorShield AI — Evaluation Plan & Benchmark Harness

## Benchmark Evaluation Matrix
To measure systemic risk detection effectiveness, RazorShield AI includes an automated benchmark evaluation harness comparing four architectural configurations:

1. **Baseline 1:** Rules Engine Only
2. **Baseline 2:** ML Anomaly Model Only (IsolationForest)
3. **Baseline 3:** Rules + ML + Graph Ring Intelligence
4. **Full RazorShield AI:** Rules + ML + Graph + AI Investigator Agent + Policy Engine

---

## Evaluation Metrics & Benchmarks

| Metric | Formula / Definition | Engineering Benchmark Target |
| :--- | :--- | :--- |
| **Precision** | $\frac{TP}{TP + FP}$ | $> 94.5\%$ |
| **Recall** | $\frac{TP}{TP + FN}$ | $> 92.0\%$ |
| **F1 Score** | $2 \cdot \frac{Precision \cdot Recall}{Precision + Recall}$ | $> 93.2\%$ |
| **False Positive Rate** | $\frac{FP}{FP + TN}$ | $< 1.8\%$ |
| **Synchronous Risk Evaluation Latency (P50 / P95 / P99)** | Real-time risk scoring pipeline duration | Target: $< 25\text{ ms}$ (P50), $< 50\text{ ms}$ (P95/P99) |
| **AI Investigation Latency (P50 / P95)** | Complete agent trace generation duration | Target: $< 1800\text{ ms}$ (P50), $< 3500\text{ ms}$ (P95) |
| **Auto-Resolution Rate** | % events resolved without human escalation | $> 88.0\%$ |
| **Dependency Failure Recovery Rate**| % events safely handled under Chaos Mode | $100.0\%$ |

---

## Latency Measurement Protocol
Every benchmark run records precise duration metrics across execution stages:
- `ingestion_validation_ms`
- `idempotency_check_ms`
- `signal_rules_ms`
- `ml_isolation_forest_ms`
- `graph_cluster_ms`
- `composite_aggregator_ms`
- `total_synchronous_risk_path_ms`

Reports publish P50, P95, P99, Average, and Max latencies explicitly.

---

## Ground-Truth Synthetic Dataset
The benchmark harness executes against a ground-truth labeled dataset of 1,000 synthetic transaction scenarios:
- **750 Normal Transactions** (standard customer purchasing patterns)
- **100 Account Takeover Scenarios** (new device, geo velocity anomaly)
- **75 Card Testing Bursts** (rapid low-amount BIN velocity sweeps)
- **50 Coordinated Fraud Rings** (multi-account shared device clusters)
