# RazorShield AI — Senior Engineering Review Checklist & Architecture Invariants

## 1. Hard Architecture Integrity Invariants

Every code slice MUST satisfy these 6 non-negotiable architectural invariants:

1. **Agent Authority Invariant:**  
   The AI Investigator state machine can ONLY advise and recommend. Under no circumstances can the LLM directly invoke Action Gateway execution endpoints.  
   `Flow: LLM Recommendation → Policy Engine Validation → Action Gateway Authorization → System Execution`.

2. **Sensitive-Data & PCI Compliance Invariant:**  
   Zero raw PANs, CVVs, PINs, OTPs, or API secrets may exist in application source code, synthetic datasets, log outputs, or test fixtures. Card data must be tokenized (`tok_bin_xxx`).

3. **Immutable Audit Invariant:**  
   Every high-impact risk action (`STEP-UP`, `HOLD`, `BLOCK`) MUST generate an immutable, cryptographic HMAC-signed audit event linking `transaction_id -> risk_decision_id -> investigation_id -> policy_decision_id -> action_id -> audit_event_id`.

4. **Distributed Idempotency Invariant:**  
   Duplicate payment events (`event_id` + `idempotency_key`) MUST return the existing cached response without executing duplicate risk scoring or action side effects.

5. **Safe Failure & Fail-Closed Invariant:**  
   Dependency failures (LLM offline, ML crash, Graph unattached) MUST NEVER result in silent transaction approvals. System degrades to deterministic rules and safe review states.

6. **RBAC & Authorization Boundary Invariant:**  
   API route handlers and policy endpoints MUST enforce explicit role checks. Read-only roles cannot execute actions or modify risk policies.

---

## 2. Senior Engineering Code Review Checklist

### A. Code Structure & Simplicity
- [ ] Is the code organized into clear layers (Route → Service → Domain → Repository)?
- [ ] Are functions small (< 40 lines) with a single conceptual responsibility?
- [ ] Are magic numbers/strings replaced with named constants, typed settings, or policy objects?
- [ ] Are there zero unneeded abstractions or framework bloat?

### B. Type Safety & Validation
- [ ] Is Python code 100% type-annotated (`mypy --strict` passes)?
- [ ] Are boundary inputs and outputs validated via Pydantic v2 schemas?
- [ ] Is TypeScript frontend code written in strict mode with zero `any` types?

### C. Error Handling & Logging
- [ ] Are exceptions caught explicitly with root causes preserved (`raise CustomError(...) from exc`)?
- [ ] Are logs emitted in structured JSON format with `correlation_id` and stable event names?
- [ ] Are emails, phone numbers, and IP subnets scrubbed before log serialization?

### D. Security & AI Safety
- [ ] Are untrusted metadata inputs wrapped in XML delimiters (`<untrusted_transaction_metadata>`)?
- [ ] Are AI recommendations validated against evidence links before policy check?
- [ ] Are API credentials loaded exclusively from environment variables?

### E. Performance & Testing
- [ ] Does synchronous risk evaluation execute within the `<50ms` target?
- [ ] Do unit, integration, and security tests pass cleanly (`pytest backend/tests/`)?
- [ ] Does static quality check (`python scripts/quality_check.py`) return `QUALITY GATE: PASS`?
