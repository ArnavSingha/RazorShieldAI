# RazorShield AI — Security Model & Access Control Architecture

## 1. Authentication & Session Security
- **API Token Verification:** HMAC-SHA256 signature verification on all incoming merchant webhooks and system API calls.
- **Analyst Session Tokens:** JWT tokens with short-lived expiration (15 minutes) and refresh token rotation.

## 2. Role-Based Access Control (RBAC) Matrix

| Role | Read Data | Trigger Investigation | Configure Policy | Approve STEP-UP | Execute BLOCK/HOLD | View Audit Log |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ADMIN** | Yes | Yes | Yes | Yes | Yes | Yes |
| **RISK_ANALYST** | Yes | Yes | No | Yes | Yes | Yes |
| **MERCHANT_OPERATOR**| Yes (Own) | No | No | No | No | Read-Only |
| **AUDITOR** | Yes | No | No | No | No | Full Export |
| **READ_ONLY** | Yes | No | No | No | No | Limited |

## 3. Data Protection & PCI Compliance Standards
- **Tokenization:** All Primary Account Numbers (PAN) are replaced at ingestion with token `tok_bin_xxxx_xxxx`.
- **CVV/PIN/OTP:** Zero retention policy. Mandatory drop at payload parsing layer.
- **PII Scrubbing:** Automatic regex-based masking of emails, phone numbers, and street addresses prior to LLM prompt serialization.

## 4. Action Gateway Authorization Protocol
No action can execute without an authorization token signed by the Policy Engine:
```json
{
  "action_token_id": "act_tok_991823",
  "transaction_id": "tx_8819203",
  "requested_action": "BLOCK_PAYMENT",
  "policy_evaluation": "APPROVED",
  "policy_rule_matched": "RULE_CRITICAL_RISK_BLOCK",
  "authorized_by": "POLICY_ENGINE_V1",
  "timestamp": "2026-08-23T12:00:00Z"
}
```
If `requested_action` does not match `policy_evaluation`, the Action Gateway returns `403 FORBIDDEN` and flags a security alert.
