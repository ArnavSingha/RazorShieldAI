# RazorShield AI — Threat Model (STRIDE Framework)

## Overview
This document specifies the security threat model for RazorShield AI using the **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

---

## Threat Matrix & Mitigation Controls

| Threat Category | Specific Threat Scenario | Impact | Mitigation & Security Control |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Adversary spoofs payment event source or merchant credentials. | High | Cryptographic API key signing, mutual TLS headers, strict Pydantic payload validation. |
| **Tampering** | Adversary injects malicious prompt payloads into merchant/transaction metadata to hijack AI investigator logic. | Critical | **Prompt Injection Defense:** Strict XML isolation (`<untrusted_data>`), Pydantic schema output validation, refusal of arbitrary system prompt overrides. |
| **Repudiation** | Analyst or automated agent takes action (e.g. blocking merchant) and denies origin. | High | **Immutable Audit Trail:** Append-only log with HMAC signatures capturing exact actor, prompt, evidence, policy result, and timestamp. |
| **Information Disclosure** | LLM context or logs leak customer PII, PAN, or sensitive account attributes. | Critical | **PII Masking & Tokenization Engine:** Masking email (`a***@domain.com`), IP subnet (`192.168.x.x`), tokenized cards (`tok_xxx`), zero raw PAN/CVV storage. |
| **Denial of Service** | Event stream flooding or expensive LLM query bombing designed to exhaust system resources. | High | Rate-limiting middleware (sliding window), max LLM iteration depth (cap = 5), fast deterministic circuit-breakers (< 50ms fallback). |
| **Elevation of Privilege** | Agent attempts to invoke unauthorized high-impact tool (e.g. `block_account` without policy check). | Critical | **Least-Privilege Tool Contract & Policy Supremacy:** AI agent cannot directly invoke write APIs; all actions pass through Policy Engine & Action Gateway. |

---

## Trust Boundaries
```text
[UNTRUSTED EXTERNAL WORLD]
  ├── Incoming API Requests / Webhooks
  └── Payment Stream Events
------------------ TRUST BOUNDARY 1: API Gateway (Auth & Input Validation) ------------------
[INGESTION ZONE]
  ├── Idempotency Check
  ├── Schema Validator
  └── PII Masking Engine
------------------ TRUST BOUNDARY 2: Isolated Engine Sandbox ------------------
[RISK ENGINE & AGENT CORE]
  ├── Rules Engine (Deterministic)
  ├── ML Engine (Isolated Predictor)
  ├── Graph Engine (NetworkX Memory)
  └── LLM Agent (LangGraph Sandbox, Untrusted Data Boundary)
------------------ TRUST BOUNDARY 3: Policy Authorization Gateway ------------------
[ACTION EXECUTION ZONE]
  ├── Policy Engine (Deterministic Rule Matrix)
  ├── Action Gateway (Enforcer)
  └── Audit Engine (Immutable Storage)
```
