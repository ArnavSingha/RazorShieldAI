"""
RazorShield AI — Structured JSON Logging & PII Scrubbing
Formats all system log entries as structured JSON and redacts sensitive parameters.
"""

import json
import logging
import re
import time
from typing import Any


class PIIScrubber:
    """Regex scrubber masking PII attributes in log messages and dictionary structures."""

    # Patterns for Email, Phone, Credit Card, IP Subnets
    EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
    PAN_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
    CVV_REGEX = re.compile(r"\b\d{3,4}\b")
    IP_REGEX = re.compile(r"\b(\d{1,3}\.\d{1,3}\.)\d{1,3}\.\d{1,3}\b")

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = cls.EMAIL_REGEX.sub(r"\1***@\2", text)
        text = cls.PAN_REGEX.sub(r"[REDACTED_PAN]", text)
        text = cls.IP_REGEX.sub(r"\1x.x", text)
        return text

    @classmethod
    def redact_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        scrubbed: dict[str, Any] = {}
        sensitive_keys = [
            "pan",
            "cvv",
            "pin",
            "otp",
            "password",
            "secret",
            "authorization",
            "bearer",
            "token",
            "api_key",
            "key",
        ]
        for key, value in data.items():
            lower_key = key.lower()
            if any(sensitive in lower_key for sensitive in sensitive_keys):
                scrubbed[key] = "[REDACTED_SENSITIVE]"
            elif isinstance(value, str):
                scrubbed[key] = cls.redact_text(value)
            elif isinstance(value, dict):
                scrubbed[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                scrubbed_list: list[Any] = [
                    cls.redact_dict(item)
                    if isinstance(item, dict)
                    else cls.redact_text(item)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
                scrubbed[key] = scrubbed_list
            else:
                scrubbed[key] = value
        return scrubbed


class JSONFormatter(logging.Formatter):
    """Formats log records into structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
            "component": getattr(record, "component", "risk-engine"),
            "request_id": getattr(record, "request_id", ""),
            "correlation_id": getattr(record, "correlation_id", ""),
            "transaction_id": getattr(record, "transaction_id", ""),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Merge extra payload if attached
        extra_payload = getattr(record, "payload", None)
        if isinstance(extra_payload, dict):
            log_obj["data"] = PIIScrubber.redact_dict(extra_payload)

        return json.dumps(log_obj)


def get_logger(name: str = "razorshield") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
