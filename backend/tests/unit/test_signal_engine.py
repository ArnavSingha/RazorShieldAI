"""
RazorShield AI — Unit Tests: Signal Engine
"""

import time

from backend.app.domain.models import CustomerProfile
from backend.app.ingestion.validator import EventValidator
from backend.app.risk.signal_engine import SignalEngine


def test_velocity_and_amount_signals(valid_transaction_payload):
    engine = SignalEngine()
    customer = CustomerProfile(
        customer_id="cust_test_101",
        avg_transaction_amount_30d=1000.0,
        std_transaction_amount_30d=500.0,
    )

    for i in range(6):
        payload = dict(valid_transaction_payload)
        payload["event_id"] = f"evt_vel_{i}"
        payload["transaction_id"] = f"tx_vel_{i}"
        event = EventValidator.validate_dict(payload)
        signals = engine.evaluate(event, customer)

    signal_codes = [s.signal_code for s in signals]
    assert "SIG_VELOCITY_1H_COUNT" in signal_codes


def test_implausible_travel_speed_signal(valid_transaction_payload):
    engine = SignalEngine()
    now = time.time()

    customer = CustomerProfile(
        customer_id="cust_test_101",
        last_transaction_time=now - 600,
        last_lat=19.0760,
        last_lon=72.8777,
    )

    valid_transaction_payload["geo_location"] = {
        "country": "US",
        "city": "New York",
        "lat": 40.7128,
        "lon": -74.0060,
    }
    valid_transaction_payload["timestamp"] = now

    event = EventValidator.validate_dict(valid_transaction_payload)
    signals = engine.evaluate(event, customer)

    signal_codes = [s.signal_code for s in signals]
    assert "SIG_GEO_IMPLAUSIBLE_SPEED" in signal_codes
