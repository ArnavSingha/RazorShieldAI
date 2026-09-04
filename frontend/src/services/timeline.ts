import { getAuthHeader } from './api';

export interface TimelineEventItem {
  event_id: string;
  investigation_id: string;
  stage: string;
  summary: string;
  actor: string;
  details?: Record<string, any>;
  timestamp: number;
}

export async function fetchInvestigationTimeline(investigationId: string): Promise<TimelineEventItem[]> {
  const response = await fetch(`/api/v1/investigations/${investigationId}/timeline`, {
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch timeline: ${response.statusText}`);
  }

  const payload = await response.json();
  return payload.data?.events || [];
}

export async function exportInvestigationCase(investigationId: string): Promise<Record<string, any>> {
  const response = await fetch(`/api/v1/investigations/${investigationId}/export?format=json`, {
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to export investigation case: ${response.statusText}`);
  }

  const payload = await response.json();
  return payload.data;
}

export async function updateIncidentState(
  investigationId: string,
  updates: { status?: string; owner?: string; priority?: string; resolution_notes?: string }
): Promise<Record<string, any>> {
  const response = await fetch(`/api/v1/investigations/${investigationId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update incident: ${response.statusText}`);
  }

  const payload = await response.json();
  return payload.data;
}
