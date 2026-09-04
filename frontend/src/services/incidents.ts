import { fetchApi } from './api';
import { ActiveIncident } from '../types/domain';

export async function getActiveIncidents(): Promise<ActiveIncident[]> {
  return fetchApi<ActiveIncident[]>('/api/v1/investigations/active');
}
