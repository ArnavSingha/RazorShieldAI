import { fetchApi } from './api';
import {
  InvestigationPackage,
  AgentInvestigationResult,
  PolicyDecision,
  ActionToken,
  ActionExecutionResult,
  TransactionEvent,
  TransactionDecision
} from '../types/domain';

export async function createGraphInvestigation(entityId: string, maxHops: number = 2): Promise<InvestigationPackage> {
  return fetchApi<InvestigationPackage>('/api/v1/graph/investigations', {
    method: 'POST',
    body: JSON.stringify({ entity_id: entityId, max_hops: maxHops }),
  });
}

export async function getGraphInvestigation(investigationId: string): Promise<InvestigationPackage> {
  return fetchApi<InvestigationPackage>(`/api/v1/graph/investigations/${investigationId}`);
}

export async function runAgentInvestigation(investigationId: string): Promise<AgentInvestigationResult> {
  return fetchApi<AgentInvestigationResult>('/api/v1/agent/investigate', {
    method: 'POST',
    body: JSON.stringify({ investigation_id: investigationId }),
  });
}

export async function getAgentInvestigation(runId: string): Promise<AgentInvestigationResult> {
  return fetchApi<AgentInvestigationResult>(`/api/v1/agent/investigations/${runId}`);
}

export async function authorizeAction(investigationId: string, authToken?: string): Promise<{
  policy_decision: PolicyDecision;
  action_token: ActionToken;
  decision_packet?: Record<string, any>;
}> {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers['Authorization'] = authToken;
  }
  return fetchApi<{ policy_decision: PolicyDecision; action_token: ActionToken; decision_packet?: Record<string, any> }>('/api/v1/actions/authorize', {
    method: 'POST',
    headers,
    body: JSON.stringify({ investigation_id: investigationId }),
  });
}

export async function executeActionToken(token: ActionToken): Promise<ActionExecutionResult> {
  return fetchApi<ActionExecutionResult>('/api/v1/actions/execute', {
    method: 'POST',
    body: JSON.stringify({ token }),
  });
}

export async function processTransactionEvent(event: Partial<TransactionEvent>): Promise<TransactionDecision> {
  const fullEvent = {
    event_id: event.event_id || `evt_${Date.now()}`,
    idempotency_key: event.idempotency_key || `idem_${Date.now()}`,
    transaction_id: event.transaction_id || `txn_${Date.now()}`,
    customer_id: event.customer_id || 'cust_default',
    account_id: event.account_id || 'acc_default',
    merchant_id: event.merchant_id || 'merch_default',
    amount: event.amount || 5000,
    currency: event.currency || 'INR',
    payment_method: event.payment_method || 'CARD',
    card_bin: event.card_bin || '411111',
    card_token: event.card_token || 'tok_card_001',
    device_id: event.device_id || 'dev_001',
    ip_address: event.ip_address || '192.168.1.1',
    user_agent: event.user_agent || 'Mozilla/5.0',
    merchant_category_code: event.merchant_category_code || '5999',
    timestamp: event.timestamp || Date.now() / 1000,
  };

  return fetchApi<TransactionDecision>('/api/v1/events/transaction', {
    method: 'POST',
    body: JSON.stringify(fullEvent),
  });
}

export async function getRecentTransactions(): Promise<TransactionDecision[]> {
  return fetchApi<TransactionDecision[]>('/api/v1/transactions/recent');
}
