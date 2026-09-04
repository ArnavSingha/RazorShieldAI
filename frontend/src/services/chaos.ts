import { fetchApi } from './api';
import { ChaosStatusData, SystemStatusData } from '../types/domain';

export async function getChaosStatus(): Promise<ChaosStatusData> {
  return fetchApi<ChaosStatusData>('/api/v1/simulator/chaos/status');
}

export async function getSystemStatus(): Promise<SystemStatusData> {
  return fetchApi<SystemStatusData>('/api/v1/system/status');
}

export async function toggleChaosFault(fault: string, enable: boolean, ttlSeconds: number = 60.0, authToken?: string): Promise<ChaosStatusData> {
  const headers: Record<string, string> = {};
  if (authToken) {
    headers['Authorization'] = authToken;
  }
  return fetchApi<ChaosStatusData>('/api/v1/simulator/chaos/toggle', {
    method: 'POST',
    headers,
    body: JSON.stringify({ fault, enable, ttl_seconds: ttlSeconds }),
  });
}
