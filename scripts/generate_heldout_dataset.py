"""
RazorShield AI — Held-Out Fraud Evaluation Dataset Generator
Generates reproducible synthetic datasets for train, validation, and held-out test splits.
Includes hard negatives (legitimate shared devices, corporate NAT IPs, high-value purchases)
and hard positives (stealth fraud with normal amounts, graph-dependent mule accounts).
Zero label leakage design.
"""

import json
import os
import random
import sys

sys.path.insert(0, os.path.abspath("."))

from backend.app.domain.models import TransactionEvent


def generate_dataset(seed: int = 42, count: int = 500) -> list[dict]:
    rng = random.Random(seed)
    t_base = 1700000000.0
    records = []

    cust_ids = [f"cust_user_{i}" for i in range(1, 101)]
    merch_ids = [f"merch_{i}" for i in range(5001, 5020)]

    for i in range(count):
        is_fraud = rng.random() < 0.15  # 15% fraud rate
        c_id = rng.choice(cust_ids)
        m_id = str(rng.choice(merch_ids))

        if not is_fraud:
            # 85% Benign (Normal, Hard Negatives)
            benign_type = rng.choice(
                [
                    "NORMAL",
                    "HARD_NEG_CORP_NAT",
                    "HARD_NEG_SHARED_DEVICE",
                    "HARD_NEG_HIGH_VALUE",
                ]
            )

            if benign_type == "NORMAL":
                amt = rng.uniform(100.0, 5000.0)
                dev_id = f"dev_{c_id}"
                ip_addr = f"10.0.0.{rng.randint(1, 20)}"
                mcc = "5411"
            elif benign_type == "HARD_NEG_CORP_NAT":
                # Legitimate corporate office shared NAT IP
                amt = rng.uniform(500.0, 8000.0)
                dev_id = f"dev_{c_id}"
                ip_addr = "192.168.1.100"  # Corporate NAT IP
                mcc = "5732"
            elif benign_type == "HARD_NEG_SHARED_DEVICE":
                # Legitimate household shared device
                amt = rng.uniform(1000.0, 12000.0)
                dev_id = "dev_family_ipad_shared"
                ip_addr = f"10.0.1.{rng.randint(1, 5)}"
                mcc = "5311"
            else:  # HARD_NEG_HIGH_VALUE
                # Legitimate high-value purchase (VIP / Travel)
                amt = rng.uniform(80000.0, 250000.0)
                dev_id = f"dev_{c_id}"
                ip_addr = f"10.0.2.{rng.randint(1, 10)}"
                mcc = "3000"  # Airlines

            fraud_type = "BENIGN"
        else:
            # 15% Fraud (Hard Positives & Classic Patterns)
            fraud_type = rng.choice(
                [
                    "ATO-001",
                    "CARD_TESTING-002",
                    "MULE_RING-003",
                    "VELOCITY-004",
                    "SHARED_DEVICE-005",
                    "STEALTH_FRAUD-006",
                    "CROSS_BORDER-007",
                ]
            )

            if fraud_type == "ATO-001":
                amt = rng.uniform(150000.0, 300000.0)
                dev_id = f"dev_hacked_{rng.randint(1, 10)}"
                ip_addr = "198.51.100.99"
                mcc = "6051"
            elif fraud_type == "CARD_TESTING-002":
                amt = rng.uniform(10.0, 50.0)
                dev_id = f"dev_bot_{rng.randint(1, 5)}"
                ip_addr = "192.0.2.1"
                mcc = "5732"
            elif fraud_type == "MULE_RING-003":
                amt = rng.uniform(80000.0, 180000.0)
                dev_id = "dev_farm_shared_99"
                ip_addr = "192.168.1.100"
                mcc = "5732"
            elif fraud_type == "VELOCITY-004":
                amt = rng.uniform(20000.0, 50000.0)
                dev_id = f"dev_burst_{c_id}"
                ip_addr = "10.0.1.5"
                mcc = "5732"
            elif fraud_type == "SHARED_DEVICE-005":
                amt = rng.uniform(40000.0, 100000.0)
                dev_id = "dev_farm_shared_99"
                ip_addr = f"10.0.2.{rng.randint(1, 5)}"
                mcc = "5732"
            elif fraud_type == "STEALTH_FRAUD-006":
                # Hard Positive: Normal amount, normal IP, but subtle velocity anomaly
                amt = rng.uniform(1500.0, 4500.0)
                dev_id = f"dev_stealth_{c_id}"
                ip_addr = f"10.0.0.{rng.randint(1, 20)}"
                mcc = "5411"
            else:  # CROSS_BORDER-007
                amt = rng.uniform(100000.0, 250000.0)
                dev_id = f"dev_foreign_{c_id}"
                ip_addr = "81.2.69.142"
                mcc = "5311"

        ev = TransactionEvent(
            event_id=f"ev_eval_{i}",
            idempotency_key=f"idemp_eval_{seed}_{i}",
            transaction_id=f"tx_eval_{seed}_{i}",
            customer_id=c_id,
            account_id=f"acc_{c_id}",
            amount=amt,
            currency="INR",
            device_id=dev_id,
            ip_address=ip_addr,
            merchant_id=m_id,
            merchant_category_code=mcc,
            timestamp=t_base + (i * 10.0),
        )

        rec = ev.to_dict()
        rec["ground_truth_is_fraud"] = is_fraud
        rec["ground_truth_threat"] = fraud_type
        records.append(rec)

    return records


def main():
    os.makedirs("data/evaluation", exist_ok=True)

    train_data = generate_dataset(seed=101, count=500)
    val_data = generate_dataset(seed=202, count=250)
    test_data = generate_dataset(seed=303, count=500)

    for filename, dataset in [
        ("data/evaluation/train.jsonl", train_data),
        ("data/evaluation/validation.jsonl", val_data),
        ("data/evaluation/test.jsonl", test_data),
    ]:
        with open(filename, "w", encoding="utf-8") as f:
            for item in dataset:
                f.write(json.dumps(item) + "\n")
        print(f"[DATASET] Wrote {len(dataset)} records to {filename}")


if __name__ == "__main__":
    main()
