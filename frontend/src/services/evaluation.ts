import { fetchApi } from './api';
import { EvaluationMetricsData } from '../types/domain';

export async function getEvaluationMetrics(): Promise<EvaluationMetricsData> {
  return fetchApi<EvaluationMetricsData>('/api/v1/evaluation/metrics');
}
