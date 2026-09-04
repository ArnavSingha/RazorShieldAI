# RazorShield AI — REST & Event API Specifications

## API Endpoint Reference

### 1. Payment Event Ingestion Endpoint
`POST /api/v1/events/transaction`

**Headers:**
- `X-API-Key`: string (required)
- `Idempotency-Key`: string (required)

**Request Body:** `TransactionEvent` schema

**Response `200 OK`:**
```json
{
  "status": "SUCCESS",
  "data": {
    "transaction_id": "tx_992104",
    "composite_risk_score": 84,
    "decision": "HOLD",
    "requires_investigation": true,
    "investigation_id": "inv_88192",
    "evaluation_latency_ms": 18.4
  },
  "error": null,
  "metadata": {
    "correlation_id": "corr_99281a_881"
  }
}
```

---

### 2. Live Risk Stream SSE Endpoint
`GET /api/v1/stream/transactions`

**Response:** `text/event-stream` returning real-time evaluated transaction JSON objects.

---

### 3. AI Investigation Endpoint
`POST /api/v1/investigations/run`

**Request Body:**
```json
{
  "transaction_id": "tx_992104",
  "investigation_mode": "FULL_AGENTIC"
}
```

**Response `200 OK`:** `AIInvestigationOutput` schema with trace steps.

---

### 4. Policy Execution Endpoint
`POST /api/v1/actions/execute`

**Request Body:**
```json
{
  "transaction_id": "tx_992104",
  "requested_action": "BLOCK",
  "action_reason": "High fraud cluster correlation and velocity burst",
  "investigation_id": "inv_88192"
}
```

**Response `200 OK`:**
```json
{
  "status": "SUCCESS",
  "data": {
    "action_id": "act_77192",
    "action_executed": "BLOCK",
    "authorized_by": "POLICY_ENGINE",
    "audit_event_id": "audit_88192",
    "executed_at": "2026-08-23T12:35:00Z"
  }
}
```

---

### 5. Simulator Control Endpoint
`POST /api/v1/simulator/scenario/start`

**Request Body:**
```json
{
  "scenario_id": "ATO-001",
  "burst_rate_per_sec": 5,
  "total_events": 20
}
```
