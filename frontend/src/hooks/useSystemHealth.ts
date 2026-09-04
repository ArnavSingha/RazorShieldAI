import { useState, useEffect, useCallback } from 'react';
import { getSystemStatus } from '../services/chaos';
import { SystemStatusData } from '../types/domain';

export function useSystemHealth(pollIntervalMs: number = 10000) {
  const [systemStatus, setSystemStatus] = useState<SystemStatusData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<number | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const fetchStatus = useCallback(async () => {
    const start = performance.now();
    try {
      const status = await getSystemStatus();
      const end = performance.now();
      setLatencyMs(Math.round(end - start));
      setSystemStatus(status);
      setError(null);
      setLastChecked(Date.now());
    } catch (err: any) {
      setError(err.message || 'Failed to connect to RazorShield backend');
      setSystemStatus(null);
      setLastChecked(Date.now());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchStatus, pollIntervalMs]);

  const isUnreachable = !!error || (!loading && systemStatus === null);
  const isDegraded = systemStatus?.degraded_mode || (systemStatus?.active_faults && systemStatus.active_faults.length > 0);

  return {
    systemStatus,
    loading,
    error,
    lastChecked,
    latencyMs,
    isUnreachable,
    isDegraded,
    refetch: fetchStatus,
  };
}
