import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { AppBootstrap } from '../types/bootstrap';

export function useBootstrap() {
  const [bootstrap, setBootstrap] = useState<AppBootstrap | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle');
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setStatus('loading');
    setError(null);
    try {
      const raw = await apiGet('/bootstrap');
      // caller normalizes shape as needed; keep raw as-is
      setBootstrap(raw as AppBootstrap);
      setStatus('idle');
    } catch (err: any) {
      setError(err instanceof Error ? err : new Error(String(err)));
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    bootstrap,
    status,
    error,
    reloadBootstrap: load,
  };
}
