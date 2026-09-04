// Domain Data Models & API Contracts for RazorShield AI

export interface SystemStatusData {
  environment: string;
  app_name: string;
  version: string;
  active_faults: string[];
  degraded_mode: boolean;
  components: {
    risk_engine: 'HEALTHY' | 'DEGRADED' | 'OFFLINE';
    ml_engine: 'HEALTHY' | 'OFFLINE';
    graph_engine: 'HEALTHY' | 'OFFLINE';
    gemini: 'HEALTHY' | 'OFFLINE';
    redis: 'HEALTHY' | 'OFFLINE';
    postgres: 'HEALTHY' | 'OFFLINE';
    audit: 'HEALTHY' | 'OFFLINE';
    action_gateway: 'HEALTHY' | 'OFFLINE';
  };
}

export interface TransactionEvent {
  event_id: string;
  idempotency_key: string;
  transaction_id: string;
  customer_id: string;
  account_id: string;
  merchant_id: string;
  amount: number;
  currency: string;
  payment_method: string;
  card_bin: string;
  card_token: string;
  device_id: string;
  ip_address: string;
  user_agent: string;
  merchant_category_code: string;
  timestamp: number;
}

export interface TransactionDecision {
  transaction_id: string;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  final_action: 'ALLOW' | 'STEP_UP' | 'BLOCK';
  rules_triggered: string[];
  ml_anomaly_score: number;
  graph_cluster_risk: number;
  gemini_reasoning?: string;
  execution_status: string;
  timestamp: number;
}

export interface GraphNode {
  id: string;
  entity_type: 'CUSTOMER' | 'ACCOUNT' | 'DEVICE' | 'IP' | 'CARD_TOKEN' | 'MERCHANT';
  risk_score: number;
  label?: string;
  connection_count?: number;
  is_suspicious?: boolean;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation_type: string;
  weight: number;
  is_suspicious?: boolean;
  metadata?: Record<string, any>;
}

export interface EvidenceItem {
  evidence_id: string;
  evidence_type: string;
  claim: string;
  confidence: number;
  source_entities: string[];
  source_events: string[];
  observed_at: number;
  freshness: string;
}

export interface InvestigationPackage {
  package_id: string;
  incident_id: string;
  entity_id: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  confidence_score: number;
  affected_accounts_count: number;
  total_financial_exposure_inr: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
  evidence_items: EvidenceItem[];
  evidence_snapshot_hash: string;
  time_window: string;
  detected_patterns: string[];
  created_at: number;
}

export interface AgentInvestigationResult {
  agent_run_id: string;
  investigation_id: string;
  ai_provider: 'GEMINI' | 'DETERMINISTIC_FALLBACK';
  execution_mode: 'LIVE_GEMINI' | 'DETERMINISTIC_FALLBACK';
  model_name: string;
  confidence?: number;
  confidence_score: number;
  recommended_action: 'ALLOW' | 'STEP_UP' | 'BLOCK';
  agent_reasoning: string;
  grounded_evidence_ids: string[];
  counter_signals: string[];
  pattern_interactions: string[];
  resource_usage: {
    tool_calls: number;
    tokens_used: number;
    latency_ms: number;
  };
  prompt_version: string;
  schema_version: string;
}

export interface PolicyDecision {
  decision_id: string;
  final_action: 'ALLOW' | 'STEP_UP' | 'BLOCK';
  policy_version: string;
  override_active: boolean;
  override_reason_codes: string[];
  requires_human_approval: boolean;
  confidence_threshold_applied: number;
  evidence_snapshot_hash: string;
}

export interface ActionToken {
  token_id: string;
  principal_id: string;
  role: string;
  granted_action: 'ALLOW' | 'STEP_UP' | 'BLOCK';
  evidence_snapshot_hash: string;
  issued_at: number;
  expires_at: number;
  nonce: string;
  signature: string;
}

export interface ActionExecutionResult {
  execution_id: string;
  action_id: string;
  token_id: string;
  execution_status: 'SUCCESS' | 'REJECTED' | 'FAILED';
  observed_outcome: string;
  verification_status: 'PASS' | 'FAIL';
  audit_event_id: string;
  executed_at: number;
}

export interface AuditVerificationData {
  ledger_valid: boolean;
  verified_chain_length: number;
  tip_hash: string;
  storage_mode: string;
}

export interface AttackReplayReport {
  scenario_id: string;
  scenario_type: string;
  ground_truth_threat: string;
  max_risk_score: number;
  ai_provider: string;
  actual_action: string;
  execution_status: string;
  unsafe_action_count: number;
  verdict: 'PASS' | 'FAIL';
  detection_latency_ms: number;
  grounding_rate_percent: number;
}

export interface ChaosStatusData {
  enabled: boolean;
  mode: string;
  active_faults: string[];
}

export interface EvaluationMetricsData {
  track_a_detection: Record<string, {
    precision: number;
    recall: number;
    f1_score: number;
    false_positive_cost_inr: number;
    total_expected_loss_inr: number;
    unsafe_action_count: number;
  }>;
  track_b_investigation: {
    grounding_rate: number;
    invalid_evidence_references: number;
    rejected_gemini_outputs: number;
    fallback_count: number;
    prompt_injection_cases_tested: number;
    prompt_injection_successes: number;
  };
  track_c_safety: {
    unsafe_actions: number;
    unauthorized_actions: number;
    un_audited_transitions: number;
    replay_rejections: number;
    fail_closed_verifications: string;
  };
}

export interface ActiveIncident {
  incident_id: string;
  name: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  confidence: number;
  exposure: string;
  affected_entities: number;
  detected_patterns: string;
  created_at: number;
  updated_at: number;
  status: 'NEW' | 'INVESTIGATING' | 'REVIEW' | 'ACTION_REQUIRED' | 'RESOLVED' | 'FALSE_POSITIVE';
}

