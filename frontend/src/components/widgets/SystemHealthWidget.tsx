import React, { useEffect, useState } from 'react';

export default function SystemHealthWidget({ widget, nodeId }: { widget: any; nodeId?: string }) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    // Try to fetch a plausible system status endpoint; if not available, show "Nicht verfügbar"
    (async () => {
      try {
        const res = await fetch('/api/v1/system/status');
        if (!mounted) return;
        if (!res.ok) {
          setData(null);
        } else {
          setData(await res.json());
        }
      } catch {
        setData(null);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="rounded border border-border-soft px-3 py-4 bg-white/60 dark:bg-slate-900/40">
      <div className="mb-2 text-sm font-semibold">Systemstatus</div>
      {loading ? (
        <div className="text-xs text-text-muted">Lade Status…</div>
      ) : data ? (
        <div className="text-sm">
          <div>Backend: {String(data.backend ?? 'Nicht verfügbar')}</div>
          <div>Datenbank: {String(data.database ?? 'Nicht verfügbar')}</div>
          <div>Model Registry: {String(data.model_count ?? 'Nicht verfügbar')}</div>
          <div>Tool Registry: {String(data.tool_count ?? 'Nicht verfügbar')}</div>
        </div>
      ) : (
        <div className="text-sm text-slate-600">Nicht verfügbar</div>
      )}
    </div>
  );
}
