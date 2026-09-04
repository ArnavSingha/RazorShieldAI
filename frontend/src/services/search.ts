import { getAuthHeader } from './api';

export interface SearchResultItem {
  category: 'INCIDENT' | 'TRANSACTION' | 'ENTITY' | 'EVIDENCE' | 'ACTION_TOKEN';
  id: string;
  title: string;
  subtitle: string;
  link_id: string;
}

export interface GlobalSearchResponse {
  query: string;
  results: SearchResultItem[];
}

export async function executeGlobalSearch(query: string): Promise<GlobalSearchResponse> {
  const response = await fetch(`/api/v1/search?query=${encodeURIComponent(query)}`, {
    headers: {
      ...getAuthHeader(),
    },
  });

  if (!response.ok) {
    throw new Error(`Global search failed: ${response.statusText}`);
  }

  const payload = await response.json();
  return payload.data;
}
