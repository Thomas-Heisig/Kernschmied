import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { AppBootstrap } from '../types/bootstrap';

export function useBootstrap() {
  const [bootstrap, setBootstrap] = useState<AppBootstrap | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [error, setError] = useState<Error | null>(null);
  // Initial load using local active flag + AbortController to be StrictMode-safe
  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    setStatus('loading');
    setError(null);

    void apiGet('/bootstrap', { signal: controller.signal })
      .then((raw) => {
        if (!active) return;
        setBootstrap(raw as AppBootstrap);
        setStatus('ready');
      })
      .catch((err: any) => {
        if (!active || controller.signal.aborted) return;
        setError(err instanceof Error ? err : new Error(String(err)));
        setStatus('error');
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  const reloadBootstrap = useCallback(async (): Promise<void> => {
    let active = true;
    const controller = new AbortController();

    setStatus('loading');
    setError(null);

    try {
      const raw = await apiGet('/bootstrap', { signal: controller.signal });
      if (!active) return;
      setBootstrap(raw as AppBootstrap);
      setStatus('ready');
    } catch (err: any) {
      if (!active || controller.signal.aborted) return;
      setError(err instanceof Error ? err : new Error(String(err)));
      setStatus('error');
    } finally {
      active = false;
    }
  }, []);

  return {
    bootstrap,
    status,
    error,
    reloadBootstrap,
  };
}
