import React, { useEffect, useState } from 'react';

export default function RegistryEditorWidget({ widget, nodeId }: { widget: any; nodeId?: string }) {
  const [items, setItems] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    (async () => {
      try {
        const res = await fetch('/api/v1/widgets/');
        if (!mounted) return;
        if (!res.ok) {
          setItems(null);
        } else {
          const j = await res.json();
          setItems(Array.isArray(j) ? j : null);
        }
      } catch {
        setItems(null);
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
      <div className="mb-2 text-sm font-semibold">Widget Registry</div>
      {loading ? (
        <div className="text-xs text-text-muted">Lade Registry…</div>
      ) : items && items.length ? (
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="text-left">Name</th>
              <th className="text-left">Component</th>
              <th className="text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => {
              const md = i.widget_metadata ?? i.metadata ?? {};
              const comp = md?.component_type ?? i.type ?? null;
              return (
                <tr key={i.id} className="odd:bg-slate-50 even:bg-white">
                  <td className="py-1 pr-2">{i.name}</td>
                  <td className="py-1 pr-2">{comp}</td>
                  <td className="py-1 pr-2">{i.status}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : (
        <div className="text-sm text-slate-600">Registry-Daten derzeit nicht verfügbar.</div>
      )}
    </div>
  );
}
