"""
RazorShield AI — Security Tests: Cryptographic Audit & Injection Safety Invariants
Verifies SQL/Prompt injection safety and strict PII tokenization invariants on InvestigationPackages.
"""

import re
import uuid

from backend.app.domain.models import TransactionEvent
from backend.app.risk_service import RiskPipelineService


def test_injection_metadata_safety(valid_transaction_payload, test_db_dir):
    db_file = str(test_db_dir / f"sec_inj_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    # Malicious injection payloads in text fields
    payload = dict(valid_transaction_payload)
    payload["customer_id"] = "cust_001'; DROP TABLE audit_records; --"
    payload["merchant_id"] = "<script>alert('xss')</script>"

    decision = service.process_transaction_event(payload)
    assert decision.transaction_id == valid_transaction_payload["transaction_id"]

    # Ensure DB table was not dropped
    is_valid, count = service.audit_store.verify_ledger_integrity()
    assert is_valid is True
    assert count >= 1


def test_investigation_package_pii_and_tokenization_invariants(test_db_dir):
    db_file = str(test_db_dir / f"sec_token_{uuid.uuid4().hex}.db")
    service = RiskPipelineService(db_path=db_file)

    ev = TransactionEvent(
        event_id="ev_sec_101",
        idempotency_key="idemp_sec_101",
        transaction_id="tx_sec_101",
        customer_id="cust_ring_88",
        account_id="acc_ring_88",
        amount=150000.0,
        currency="INR",
        device_id="dev_shared_77",
        ip_address="192.168.1.100",
        merchant_id="merch_sec_1",
        merchant_category_code="5732",
        timestamp=1700000000.0,
    )
    service.process_transaction_event(ev.to_dict())

    package = service.graph_engine.generate_investigation_package(
        "cust_ring_88", max_hops=2
    )
    pkg_dict = package.to_dict()
    pkg_str = str(pkg_dict)

    # 1. Assert explicit token prefixes exist
    assert "cust_tok_" in pkg_str
    assert "ip_tok_" in pkg_str
    assert "dev_tok_" in pkg_str

    # 2. Assert no raw un-tokenized IPv4 regex match (e.g. 192.168.1.100 as raw string without ip_tok_)
    raw_ip_matches = re.findall(
        r"\b(?<!ip_tok_)(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", pkg_str
    )
    assert len(raw_ip_matches) == 0

    # 3. Assert no raw PAN, CVV, raw OTP, or email addresses
    assert "raw_pan" not in pkg_str.lower()
    assert "cvv" not in pkg_str.lower()
    assert "raw_otp" not in pkg_str.lower()
    email_matches = re.findall(r"[\w.-]+@[\w.-]+\.\w+", pkg_str)
    assert len(email_matches) == 0
