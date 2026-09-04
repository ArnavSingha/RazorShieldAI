#!/usr/bin/env python3
"""
RazorShield AI — Multi-Scenario Comprehensive Performance Benchmark Runner
Measures latency (Avg, P50, P90, P95, P99, Max) across 1,000+ transaction evaluation workloads
spanning Normal, Suspicious Fraud Ring, and Burst Concurrency scenarios.
"""

import concurrent.futures
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List

root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Suppress all loggers for pure mathematical timing accuracy
logging.disable(logging.CRITICAL)

from backend.app.risk_service import RiskPipelineService


def make_normal_payload() -> Dict:
    uid = uuid.uuid4().hex[:8]
    return {
        "event_id": f"evt_norm_{uid}",
        "idempotency_key": f"idemp_norm_{uid}",
        "transaction_id": f"tx_norm_{uid}",
        "customer_id": "cust_norm_100",
        "account_id": "acc_norm_100",
        "merchant_id": "merch_norm_200",
        "amount": 2500.0,
        "currency": "INR",
        "payment_method": "CARD",
        "card_bin": "411111",
        "card_token": "tok_norm_001",
        "device_id": "dev_test_fp_01",
        "ip_address": "192.168.1.50",
        "geo_location": {
            "country": "IN",
            "city": "Mumbai",
            "lat": 19.0760,
            "lon": 72.8777,
        },
        "user_agent": "Mozilla/5.0",
        "merchant_category_code": "5732",
        "timestamp": time.time(),
    }


def make_suspicious_payload(idx: int) -> Dict:
    uid = uuid.uuid4().hex[:8]
    return {
        "event_id": f"evt_susp_{idx}_{uid}",
        "idempotency_key": f"idemp_susp_{idx}_{uid}",
        "transaction_id": f"tx_susp_{idx}_{uid}",
        "customer_id": f"cust_fraud_ring_{idx % 10}",
        "account_id": f"acc_fraud_ring_{idx % 10}",
        "merchant_id": "merch_susp_900",
        "amount": 98000.0,
        "currency": "INR",
        "payment_method": "CARD",
        "card_bin": "411111",
        "card_token": f"tok_fraud_{idx}",
        "device_id": "dev_shared_farm_99",
        "ip_address": "203.0.113.88",
        "geo_location": {
            "country": "US",
            "city": "New York",
            "lat": 40.7128,
            "lon": -74.0060,
        },
        "user_agent": "Mozilla/5.0 (Scraper)",
        "merchant_category_code": "5732",
        "timestamp": time.time(),
    }


def compute_metrics(latencies_ms: List[float]) -> Dict[str, float]:
    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)
    return {
        "count": float(n),
        "avg": round(sum(sorted_lats) / n, 2),
        "p50": round(sorted_lats[int(n * 0.50)], 2),
        "p90": round(sorted_lats[int(n * 0.90)], 2),
        "p95": round(sorted_lats[int(n * 0.95)], 2),
        "p99": round(sorted_lats[int(n * 0.99)], 2),
        "max": round(max(sorted_lats), 2),
    }


def print_scenario_report(scenario_name: str, metrics: Dict[str, float]) -> None:
    print(f"\n--- {scenario_name} ---")
    print(f" Sample Count: {int(metrics['count'])}")
    print(f" Average Latency: {metrics['avg']} ms")
    print(f" P50 Latency:     {metrics['p50']} ms")
    print(f" P90 Latency:     {metrics['p90']} ms")
    print(f" P95 Latency:     {metrics['p95']} ms")
    print(f" P99 Latency:     {metrics['p99']} ms")
    print(f" Max Latency:     {metrics['max']} ms")


def main():
    print("\n" + "=" * 65)
    print(" RAZORSHIELD AI — COMPREHENSIVE MULTI-SCENARIO BENCHMARK")
    print("=" * 65)

    scratch_dir = root_dir / "scratch"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    db_file = str(scratch_dir / f"bench_run_{uuid.uuid4().hex[:8]}.db")

    service = RiskPipelineService(db_path=db_file)

    # 1. Warmup (100 requests)
    print("[*] Performing 100 Warmup Pipeline Runs...")
    for _ in range(100):
        service.process_transaction_event(make_normal_payload())

    # 2. Scenario A — Normal Legitimate Traffic (1,000 samples)
    print("[*] Benchmarking Scenario A (Normal Legitimate Traffic - 1,000 Samples)...")
    lats_norm: List[float] = []
    for _ in range(1000):
        payload = make_normal_payload()
        t0 = time.perf_counter()
        service.process_transaction_event(payload)
        t1 = time.perf_counter()
        lats_norm.append((t1 - t0) * 1000.0)
    print_scenario_report("Scenario A: Normal Traffic", compute_metrics(lats_norm))

    # 3. Scenario B — Suspicious Fraud Ring & High Graph Complexity (1,000 samples)
    print(
        "[*] Benchmarking Scenario B (Suspicious Fraud Ring Traffic - 1,000 Samples)..."
    )
    lats_susp: List[float] = []
    for i in range(1000):
        payload = make_suspicious_payload(i)
        t0 = time.perf_counter()
        service.process_transaction_event(payload)
        t1 = time.perf_counter()
        lats_susp.append((t1 - t0) * 1000.0)
    print_scenario_report(
        "Scenario B: Suspicious Fraud Ring Traffic", compute_metrics(lats_susp)
    )

    # 4. Scenario C — Concurrent Burst Execution (1,000 samples across 10 worker threads)
    print("[*] Benchmarking Scenario C (Concurrent Burst Execution - 1,000 Samples)...")
    lats_burst: List[float] = []

    def eval_worker(idx: int) -> float:
        db_w = str(scratch_dir / f"bench_w_{uuid.uuid4().hex[:8]}.db")
        s_w = RiskPipelineService(db_path=db_w)
        payload = make_normal_payload()
        t0 = time.perf_counter()
        s_w.process_transaction_event(payload)
        t1 = time.perf_counter()
        return (t1 - t0) * 1000.0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(eval_worker, i) for i in range(1000)]
        for f in concurrent.futures.as_completed(futures):
            lats_burst.append(f.result())
    print_scenario_report(
        "Scenario C: Concurrent Burst Traffic", compute_metrics(lats_burst)
    )

    print("\n" + "=" * 65)
    print(" BENCHMARK COMPLETED SUCCESSFULLY")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
