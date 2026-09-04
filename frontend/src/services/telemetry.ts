import { getAuthHeader } from './api';

export interface ActionTelemetryData {
  live_unsafe_executions: number;
  rejected_executions: number;
  policy_violations: number;
  fail_closed_events: number;
  total_executions: number;
  successful_executions: number;
  last_execution_timestamp: number | null;
  gateway_status: string;
  timestamp: number;
}

export async function fetchActionTelemetry(): Promise<ActionTelemetryData> {
  const response = await fetch('/api/v1/actions/telemetry', {
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch action telemetry: ${response.statusText}`);
  }

  const payload = await response.json();
  return payload.data;
}
