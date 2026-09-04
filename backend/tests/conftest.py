import sys
import time
import uuid
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path for test runners
root_dir = Path(__file__).parent.parent.parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pytest


@pytest.fixture(autouse=True)
def setup_test_rbac_tokens(monkeypatch):
    monkeypatch.setenv("RAZORSHIELD_ADMIN_TOKEN", "test_admin_token_xyz99")
    monkeypatch.setenv("RAZORSHIELD_ANALYST_TOKEN", "test_analyst_token_xyz88")
    monkeypatch.setenv("RAZORSHIELD_OPERATOR_TOKEN", "test_operator_token_xyz77")
    monkeypatch.setenv("RAZORSHIELD_AUDITOR_TOKEN", "test_auditor_token_xyz66")


@pytest.fixture
def test_db_dir() -> Path:
    root_dir = Path(__file__).parent.parent.parent.resolve()
    p = root_dir / "scratch" / "test_databases"
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


@pytest.fixture
def valid_transaction_payload() -> dict[str, Any]:
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


@pytest.fixture
def high_risk_transaction_payload() -> dict[str, Any]:
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
