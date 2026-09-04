import { useState, useEffect, useCallback } from 'react';
import { getActiveIncidents } from '../services/incidents';
import { ActiveIncident } from '../types/domain';

export function useIncidents(pollIntervalMs: number = 10000) {
  const [incidents, setIncidents] = useState<ActiveIncident[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await getActiveIncidents();
      setIncidents(data || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch active incidents');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchIncidents, pollIntervalMs]);

  return { incidents, loading, error, refetch: fetchIncidents };
}
