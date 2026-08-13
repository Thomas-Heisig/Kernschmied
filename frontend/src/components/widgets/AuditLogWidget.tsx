import React, { useEffect, useState } from 'react';

export default function AuditLogWidget({ widget, nodeId }: { widget: any; nodeId?: string }) {
  const [entries, setEntries] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    (async () => {
      try {
        const res = await fetch('/api/v1/audit');
        if (!mounted) return;
        if (!res.ok) {
          setEntries(null);
        } else {
          const j = await res.json();
          setEntries(Array.isArray(j) ? j : j.items ?? null);
        }
      } catch {
        setEntries(null);
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
      <div className="mb-2 text-sm font-semibold">Audit Log</div>
      {loading ? (
        <div className="text-xs text-text-muted">Lade Audit-Daten…</div>
      ) : entries && entries.length ? (
        <ul className="text-sm list-none space-y-1">
          {entries.slice(0, 10).map((e, idx) => (
            <li key={idx} className="text-xs text-slate-700">
              {e.timestamp ?? e.time ?? ''} {e.user ?? e.actor ?? ''} {e.action ?? JSON.stringify(e)}
            </li>
          ))}
        </ul>
      ) : (
        <div className="text-sm text-slate-600">Audit-Daten derzeit nicht verfügbar.</div>
      )}
    </div>
  );
}
