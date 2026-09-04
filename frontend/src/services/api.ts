// Base HTTP Client for RazorShield AI REST API

import { ApiResponse } from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export function getAuthHeader(): Record<string, string> {
  const role = (typeof window !== 'undefined' && localStorage.getItem('razorshield_sim_role')) || 'RISK_ANALYST';
  return {
    'Authorization': `Bearer ${role.toLowerCase()}_secret_token_123`,
    'X-Role': role,
  };
}

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const authHeaders = getAuthHeader();
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...authHeaders,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail && errJson.detail.message) {
        errorMessage = errJson.detail.message;
      } else if (errJson.error && errJson.error.message) {
        errorMessage = errJson.error.message;
      }
    } catch {
      // Ignore json parse error for non-json responses
    }
    throw new Error(errorMessage);
  }

  const json: ApiResponse<T> = await response.json();
  if (json.status === 'ERROR' && json.error) {
    throw new Error(json.error.message || 'API request failed');
  }

  return json.data;
}
