import { useEffect, useRef, useState } from 'react';
import { EffectiveWidget } from '../contracts/widgets';
import widgetsApi from '../api/widgets';

export default function useEffectiveWidgets(nodeId?: string | null) {
  const [widgets, setWidgets] = useState<EffectiveWidget[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const genRef = useRef(0);

  useEffect(() => {
    // cancel previous
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }

    if (!nodeId) {
      setWidgets([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    const myGen = ++genRef.current;

    setIsLoading(true);
    setError(null);

    widgetsApi
      .loadEffectiveWidgets(nodeId, controller.signal)
      .then((items) => {
        if (myGen !== genRef.current) return;
        setWidgets(items);
        setIsLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err : new Error(String(err)));
        setIsLoading(false);
      });

    return () => {
      try {
        controller.abort();
      } catch {}
    };
  }, [nodeId]);

  function reload() {
    if (!nodeId) return;
    genRef.current++;
    if (abortRef.current) {
      try {
        abortRef.current.abort();
      } catch {}
      abortRef.current = null;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    const myGen = ++genRef.current;
    setIsLoading(true);
    setError(null);

    widgetsApi
      .loadEffectiveWidgets(nodeId, controller.signal)
      .then((items) => {
        if (myGen !== genRef.current) return;
        setWidgets(items);
        setIsLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err : new Error(String(err)));
        setIsLoading(false);
      });
  }

  return { widgets, isLoading, error, reload } as const;
}
