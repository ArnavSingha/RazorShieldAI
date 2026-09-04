import { getAuthHeader } from './api';

export interface AnalyticsSummaryData {
  window: string;
  start_timestamp: number;
  end_timestamp: number;
  total_transactions: number;
  total_risk_decisions: number;
  high_risk_count: number;
  critical_risk_count: number;
  protected_exposure_inr: number;
  actions_breakdown: {
    ALLOW: number;
    MONITOR: number;
    STEP_UP: number;
    HOLD: number;
    BLOCK: number;
  };
  tps_rolling_60s: number;
  previous_window: {
    total_transactions: number;
    high_risk_count: number;
    protected_exposure_inr: number;
  };
}

export async function fetchAnalyticsSummary(window: string = '24h'): Promise<AnalyticsSummaryData> {
  const response = await fetch(`/api/v1/analytics/summary?window=${window}`, {
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch analytics summary: ${response.statusText}`);
  }

  const payload = await response.json();
  return payload.data;
}
