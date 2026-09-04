#!/usr/bin/env python3
"""
RazorShield AI — Slice 1 Remediation Verification & Performance Benchmark Runner
Executes unit, integration, security, failure resilience, and performance benchmark suites.
"""

import sys
import os
import time
import inspect
import importlib.util
from pathlib import Path
from typing import Callable, List, Tuple

root_dir = Path(__file__).parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


class SimpleFixtureRegistry:
    @staticmethod
    def valid_transaction_payload():
        import uuid

        uid = uuid.uuid4().hex[:8]
        return {
            "event_id": f"evt_test_{uid}",
            "idempotency_key": f"idemp_test_key_{uid}",
            "transaction_id": f"tx_test_{uid}",
            "customer_id": "cust_test_101",
            "account_id": "acc_test_881",
            "merchant_id": "merch_test_771",
            "amount": 4500.0,
            "currency": "INR",
            "payment_method": "CARD",
            "card_bin": "411111",
            "card_token": "tok_bin_411111_0001",
            "device_id": "dev_test_fp_01",
            "ip_address": "192.168.1.50",
            "geo_location": {
                "country": "IN",
                "city": "Mumbai",
                "lat": 19.0760,
                "lon": 72.8777,
            },
            "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)",
            "merchant_category_code": "5732",
            "timestamp": time.time(),
        }

    @staticmethod
    def high_risk_transaction_payload():
        import uuid

        uid = uuid.uuid4().hex[:8]
        return {
            "event_id": f"evt_test_high_{uid}",
            "idempotency_key": f"idemp_test_key_{uid}",
            "transaction_id": f"tx_test_high_{uid}",
            "customer_id": "cust_test_101",
            "account_id": "acc_test_881",
            "merchant_id": "merch_test_771",
            "amount": 95000.0,
            "currency": "INR",
            "payment_method": "CARD",
            "card_bin": "411111",
            "card_token": "tok_bin_411111_0001",
            "device_id": "dev_shared_farm_09",
            "ip_address": "203.0.113.45",
            "geo_location": {
                "country": "US",
                "city": "New York",
                "lat": 40.7128,
                "lon": -74.0060,
            },
            "user_agent": "Mozilla/5.0",
            "merchant_category_code": "5732",
            "timestamp": time.time(),
        }


def run_benchmark():
    print("\n" + "=" * 60)
    print(" RAZORSHIELD AI — PIPELINE LATENCY BENCHMARK")
    print("=" * 60)

    import uuid
    from backend.app.risk_service import RiskPipelineService

    db_file = str(root_dir / "scratch" / f"bench_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    latencies: List[float] = []
    # Warmup 5 runs
    for _ in range(5):
        payload = SimpleFixtureRegistry.valid_transaction_payload()
        service.process_transaction_event(payload)

    # Benchmark 50 runs
    for _ in range(50):
        payload = SimpleFixtureRegistry.valid_transaction_payload()
        t0 = time.perf_counter()
        service.process_transaction_event(payload)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    latencies.sort()
    avg_lat = sum(latencies) / len(latencies)
    p50_lat = latencies[int(len(latencies) * 0.50)]
    p95_lat = latencies[int(len(latencies) * 0.95)]
    p99_lat = latencies[int(len(latencies) * 0.99)]
    max_lat = max(latencies)

    print(f" Measured Latency Sample Count: {len(latencies)}")
    print(f" Average Latency: {avg_lat:.2f} ms")
    print(f" P50 Latency:     {p50_lat:.2f} ms")
    print(f" P95 Latency:     {p95_lat:.2f} ms")
    print(f" P99 Latency:     {p99_lat:.2f} ms")
    print(f" Max Latency:     {max_lat:.2f} ms")
    print("=" * 60 + "\n")


def run_all_tests():
    print("=" * 60)
    print(" RAZORSHIELD AI — SLICE 1 AUTOMATED TEST SUITE")
    print("=" * 60)

    tests_dir = root_dir / "backend" / "tests"
    test_files = list(tests_dir.glob("**/test_*.py"))

    passed_count = 0
    failed_count = 0
    failures: List[Tuple[str, str]] = []

    tmp_dir = root_dir / "scratch" / "test_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for test_file in sorted(test_files):
        rel_path = test_file.relative_to(root_dir)
        module_name = f"test_mod_{test_file.stem}"

        spec = importlib.util.spec_from_file_location(module_name, str(test_file))
        if not spec or not spec.loader:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            print(f"[FAIL] Loading {rel_path}: {exc}")
            failed_count += 1
            failures.append((str(rel_path), f"Module load error: {exc}"))
            continue

        test_funcs = [
            (name, func)
            for name, func in inspect.getmembers(module, inspect.isfunction)
            if name.startswith("test_")
        ]

        for func_name, func in test_funcs:
            test_label = f"{rel_path}::{func_name}"
            sig = inspect.signature(func)
            kwargs = {}

            for param in sig.parameters:
                if param == "valid_transaction_payload":
                    kwargs["valid_transaction_payload"] = (
                        SimpleFixtureRegistry.valid_transaction_payload()
                    )
                elif param == "high_risk_transaction_payload":
                    kwargs["high_risk_transaction_payload"] = (
                        SimpleFixtureRegistry.high_risk_transaction_payload()
                    )
                elif param == "tmp_path":
                    kwargs["tmp_path"] = tmp_dir

            try:
                func(**kwargs)
                print(f" [PASS] {test_label}")
                passed_count += 1
            except Exception as exc:
                print(f" [FAIL] {test_label}: {exc}")
                failed_count += 1
                failures.append((test_label, str(exc)))

    print("\n" + "=" * 60)
    print(f" SUMMARY: {passed_count} Passed | {failed_count} Failed")
    print("=" * 60)

    if failed_count == 0 and passed_count > 0:
        run_benchmark()
        print(" SLICE 1 TESTS RESULT: PASS")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print(" SLICE 1 TESTS RESULT: FAIL")
        for label, err in failures:
            print(f"  - {label}: {err}")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
