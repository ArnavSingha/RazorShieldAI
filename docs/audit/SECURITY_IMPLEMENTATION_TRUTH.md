# RAZORSHIELD AI — SECURITY IMPLEMENTATION TRUTH

**Document Status:** Red-Team Verified Against Literal Source Code  
**Target:** Razorpay AI Buildathon — Track 02: AI Risk Manager  

---

## 1. Cryptographic Token Generation & Verification

| Property | Actual Implementation | Source Code File & Line |
| :--- | :--- | :--- |
| **Signing Algorithm** | Symmetric **HMAC-SHA256** | `backend/app/policy/action_token.py:46-52` |
| **Secret Key Source** | Configured `settings.action_token_secret` | `backend/app/config.py` |
| **Canonical Payload** | JSON serialized `{action_id, decision_id, granted_action, evidence_snapshot_hash, nonce, expires_at, principal_id}` | `backend/app/policy/action_token.py:32-44` |
| **Token TTL** | Strict **300.0 seconds** ($5\text{ minutes}$) | `backend/app/policy/action_token.py:27` |
| **Signature Verification** | `hmac.compare_digest(token.hmac_signature, expected_sig)` (Constant-time comparison) | `backend/app/policy/action_token.py:65-72` |

---

## 2. Nonce Storage & Replay Prevention Truth

| Property | Actual Implementation | Source Code File & Line |
| :--- | :--- | :--- |
| **Storage Backend** | **In-Memory Python Set (`Set[str]`)** | `backend/app/gateway/action_gateway.py:41` |
| **Concurrency Lock** | **`threading.Lock()`** | `backend/app/gateway/action_gateway.py:40` |
| **Atomicity Mechanism** | Mutex-protected test-and-set: `with _nonce_lock: if nonce in _consumed: ... else _consumed.add(nonce)` | `backend/app/gateway/action_gateway.py:75-88` |
| **Replay Attack Result** | Returns `TokenStatus.ALREADY_EXECUTED` (HTTP 409) | `backend/app/gateway/action_gateway.py:82` |
| **External Dependency** | **Zero external Redis dependency in prototype single-node runtime.** *(Redis is supported via optional adapter in `backend/app/adapters/redis_adapter.py`)* | `backend/app/gateway/action_gateway.py` |

---

## 3. TOCTOU Evidence Snapshot Binding

| Property | Actual Implementation | Source Code File & Line |
| :--- | :--- | :--- |
| **Snapshot Hash** | SHA-256 Merkle root over tokenized node & edge IDs in `InvestigationPackage` | `backend/app/domain/graph_contracts.py:120-135` |
| **TOCTOU Guard** | Action execution re-computes active graph hash. If hash diverges from `token.evidence_snapshot_hash`, execution is rejected with `EvidenceSnapshotMismatchError` (HTTP 409). | `backend/app/agent/investigator_graph.py:210-225` |

---

## 4. RBAC & Principle of Least Privilege

| Role | Authorize Action | Execute Action | Export Audit Logs | Modify Chaos/Config |
| :--- | :---: | :---: | :---: | :---: |
| **`MERCHANT_VIEWER`** | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (403) |
| **`MERCHANT_OPERATOR`** | ✅ (ALLOW/STEP_UP) | ✅ (ALLOW/STEP_UP) | ❌ (403) | ❌ (403) |
| **`RISK_ANALYST`** | ✅ (All Tiers) | ❌ (Must dual-auth) | ❌ (403) | ❌ (403) |
| **`AUDITOR`** | ❌ (403) | ❌ (403) | ✅ (Read-Only) | ❌ (403) |
| **`ADMIN`** | ✅ (All Tiers) | ✅ (All Tiers) | ✅ | ✅ |

---

## 5. Audit Ledger & Fail-Closed Invariant

| Property | Actual Implementation | Source Code File & Line |
| :--- | :--- | :--- |
| **Storage Engine** | Local SQLite Table `action_audit_ledger` | `backend/app/audit/audit_store.py:25-45` |
| **Integrity Mechanism** | **Tamper-evident SHA-256 Hash Chain** where record $K$ stores `hash = SHA256(prev_hash + payload)` | `backend/app/audit/audit_store.py:65-85` |
| **Fail-Closed Policy** | If SQLite write fails (e.g. disk full / table lock), engine raises `AuditPersistenceError` and transaction fails closed. | `backend/app/risk_service.py:164-175` |
| **Immutability Scope** | Application-level tamper-evident verification. Not hardware WORM or distributed blockchain. | `backend/app/audit/audit_store.py` |
