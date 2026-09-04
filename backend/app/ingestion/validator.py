"""
RazorShield AI — Ingestion Event Validator
Protects risk engine against malformed or invalid transaction events.
"""

import time
from typing import Any, ClassVar

from backend.app.domain.models import GeoLocation, TransactionEvent
from backend.app.exceptions import ValidationError


class EventValidator:
    """Boundary validator protecting risk engine against malformed or invalid events."""

    SUPPORTED_CURRENCIES: ClassVar[set[str]] = {"INR", "USD", "EUR", "GBP"}

    @classmethod
    def validate_dict(cls, data: dict[str, Any]) -> TransactionEvent:
        if not isinstance(data, dict):
            raise ValidationError("Event payload must be a JSON object.")

        required_fields = [
            "event_id",
            "idempotency_key",
            "transaction_id",
            "customer_id",
            "amount",
            "currency",
            "payment_method",
            "timestamp",
        ]

        missing = [f for f in required_fields if f not in data or data[f] is None]
        if missing:
            raise ValidationError(
                message=f"Missing required transaction fields: {', '.join(missing)}",
                details={"missing_fields": missing},
            )

        amount = float(data["amount"])
        if amount <= 0:
            raise ValidationError(
                message=f"Transaction amount must be strictly positive. Got: {amount}",
                details={"amount": amount},
            )

        currency = str(data["currency"]).upper()
        if currency not in cls.SUPPORTED_CURRENCIES:
            raise ValidationError(
                message=f"Unsupported currency: {currency}. Must be one of {cls.SUPPORTED_CURRENCIES}",
                details={"currency": currency},
            )

        event_ts = float(data["timestamp"])
        now = time.time()
        if event_ts > now + 300:  # 5 minutes future tolerance
            raise ValidationError(
                message=f"Event timestamp cannot be in the future. Got: {event_ts}, Now: {now}",
                details={"timestamp": event_ts, "server_time": now},
            )

        geo = None
        if "geo_location" in data and isinstance(data["geo_location"], dict):
            g = data["geo_location"]
            geo = GeoLocation(
                country=g.get("country", ""),
                city=g.get("city", ""),
                lat=float(g.get("lat", 0.0)),
                lon=float(g.get("lon", 0.0)),
            )

        return TransactionEvent(
            event_id=str(data["event_id"]),
            idempotency_key=str(data["idempotency_key"]),
            transaction_id=str(data["transaction_id"]),
            customer_id=str(data["customer_id"]),
            account_id=str(data.get("account_id", "")),
            merchant_id=str(data.get("merchant_id", "")),
            amount=amount,
            currency=currency,
            payment_method=str(data["payment_method"]),
            card_bin=str(data.get("card_bin", "")),
            card_token=str(data.get("card_token", "")),
            device_id=str(data.get("device_id", "")),
            ip_address=str(data.get("ip_address", "")),
            geo_location=geo,
            user_agent=str(data.get("user_agent", "")),
            merchant_category_code=str(data.get("merchant_category_code", "")),
            timestamp=event_ts,
        )
