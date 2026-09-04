"""
RazorShield AI — Security Tests: Comprehensive PII & Credential Scrubbing
Verifies that sensitive credit card details, CVVs, OTPs, PINs, Passwords, API Keys,
Bearer Tokens, emails, and IPs are redacted from logs and structured payloads.
"""

from backend.app.logging_config import PIIScrubber


def test_sensitive_credentials_scrubbing():
    pan = "41111" + "11111111111"
    payload = {
        "customer_email": "user@razorpay.com",
        "card_pan": pan,
        "cvv": "999",
        "otp": "654321",
        "pin": "1234",
        "password": "SuperSecretPassword123!",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "api_key": "rzp_live_secret_key_888999",
        "user_ip": "10.100.5.20",
    }

    scrubbed = PIIScrubber.redact_dict(payload)
    assert scrubbed["card_pan"] == "[REDACTED_SENSITIVE]"
    assert scrubbed["cvv"] == "[REDACTED_SENSITIVE]"
    assert scrubbed["otp"] == "[REDACTED_SENSITIVE]"
    assert scrubbed["pin"] == "[REDACTED_SENSITIVE]"
    assert scrubbed["password"] == "[REDACTED_SENSITIVE]"
    assert scrubbed["authorization"] == "[REDACTED_SENSITIVE]"
    assert scrubbed["api_key"] == "[REDACTED_SENSITIVE]"
    assert "user@razorpay.com" not in scrubbed["customer_email"]
    assert "10.100.5.20" not in scrubbed["user_ip"]
