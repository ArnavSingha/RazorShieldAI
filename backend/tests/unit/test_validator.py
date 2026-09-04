"""
RazorShield AI — Unit Tests: Event Boundary Validation
"""

from backend.app.exceptions import ValidationError
from backend.app.ingestion.validator import EventValidator
from backend.tests.pytest_compat import pytest


def test_valid_payload_parsing(valid_transaction_payload):
    event = EventValidator.validate_dict(valid_transaction_payload)
    assert event.event_id.startswith("evt_test_")
    assert event.amount == 4500.0
    assert event.currency == "INR"
    assert event.geo_location.city == "Mumbai"


def test_missing_required_field(valid_transaction_payload):
    del valid_transaction_payload["amount"]
    with pytest.raises(ValidationError) as exc_info:
        EventValidator.validate_dict(valid_transaction_payload)
    assert "Missing required transaction fields" in str(exc_info.value)


def test_negative_amount_rejection(valid_transaction_payload):
    valid_transaction_payload["amount"] = -100.0
    with pytest.raises(ValidationError) as exc_info:
        EventValidator.validate_dict(valid_transaction_payload)
    assert "strictly positive" in str(exc_info.value)


def test_unsupported_currency_rejection(valid_transaction_payload):
    valid_transaction_payload["currency"] = "XYZ"
    with pytest.raises(ValidationError) as exc_info:
        EventValidator.validate_dict(valid_transaction_payload)
    assert "Unsupported currency" in str(exc_info.value)


def test_future_timestamp_rejection(valid_transaction_payload):
    import time

    valid_transaction_payload["timestamp"] = time.time() + 1000  # > 5 mins in future
    with pytest.raises(ValidationError) as exc_info:
        EventValidator.validate_dict(valid_transaction_payload)
    assert "cannot be in the future" in str(exc_info.value)
