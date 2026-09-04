import { fetchApi } from './api';
import { AttackReplayReport } from '../types/domain';

export async function getSimulatorScenarios(): Promise<string[]> {
  return fetchApi<string[]>('/api/v1/simulator/scenarios');
}

export async function runSimulatorScenario(scenarioType: string, seed: number = 1001, eventCount: number = 10): Promise<AttackReplayReport> {
  return fetchApi<AttackReplayReport>('/api/v1/simulator/run', {
    method: 'POST',
    body: JSON.stringify({ scenario_type: scenarioType, seed, event_count: eventCount }),
  });
}
