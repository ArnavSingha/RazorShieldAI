import { fetchApi } from './api';
import { AuditVerificationData } from '../types/domain';

export async function verifyAuditLedger(): Promise<AuditVerificationData> {
  return fetchApi<AuditVerificationData>('/api/v1/audit/verify');
}
