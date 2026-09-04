import { useState, useEffect, useCallback } from 'react';
import { getChaosStatus, toggleChaosFault } from '../services/chaos';
import { ChaosStatusData } from '../types/domain';

export function useChaosController() {
  const [chaosStatus, setChaosStatus] = useState<ChaosStatusData>({
    enabled: true,
    mode: 'PRODUCTION_SIMULATION',
    active_faults: [],
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const status = await getChaosStatus();
      setChaosStatus(status);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chaos status');
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleFault = async (fault: string, enable: boolean) => {
    try {
      const updated = await toggleChaosFault(fault, enable);
      setChaosStatus(updated);
    } catch (err: any) {
      // Optimistic fallback for testing
      const current = chaosStatus.active_faults || [];
      const nextFaults = enable ? [...current, fault] : current.filter((f) => f !== fault);
      setChaosStatus({ ...chaosStatus, active_faults: nextFaults });
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return { chaosStatus, loading, error, toggleFault, refetch: fetchStatus };
}
