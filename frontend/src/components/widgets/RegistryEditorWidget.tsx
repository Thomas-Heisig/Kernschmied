// F:\Kernschmied\frontend\src\components\widgets\RegistryEditorWidget.tsx

import React, { useEffect, useState } from 'react';
import { Database, RefreshCw, AlertCircle, Package } from 'lucide-react';
import IconBadge from '../common/IconBadge';

interface RegistryEditorWidgetProps {
  widget: any;
  nodeId?: string;
}

interface RegistryItem {
  id: string;
  name: string;
  type?: string;
  status?: string;
  widget_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export default function RegistryEditorWidget({ widget, nodeId }: RegistryEditorWidgetProps) {
  const [items, setItems] = useState<RegistryItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadRegistry = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/widgets/');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const j = await res.json();
      setItems(Array.isArray(j) ? j : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registry‑Daten konnten nicht geladen werden.');
      setItems(null);
    } finally {
      if (showRefresh) setIsRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void loadRegistry(false);
  }, []);

  const getStatusBadge = (status?: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      active: { label: 'Aktiv', className: 'bg-success-soft text-success dark:bg-success/20 dark:text-success' },
      inactive: { label: 'Inaktiv', className: 'bg-warning-soft text-warning dark:bg-warning/20 dark:text-warning' },
      disabled: { label: 'Deaktiviert', className: 'bg-danger-soft text-danger dark:bg-danger/20 dark:text-danger' },
    };
    const normalized = status?.toLowerCase() ?? '';
    const mapped = statusMap[normalized] ?? { label: status ?? 'Unbekannt', className: 'bg-surface-muted text-text-muted dark:bg-slate-800 dark:text-gray-400' };
    return (
      <span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${mapped.className}`}>
        {mapped.label}
      </span>
    );
  };

  return (
    <div className="rounded-xl border border-border-soft bg-white/90 p-4 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/80">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <IconBadge icon={<Database />} size="md" variant="primary" />
          <h3 className="text-sm font-semibold text-text dark:text-white">Widget Registry</h3>
          {items && (
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              {items.length}
            </span>
          )}
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => void loadRegistry(true)}
          disabled={isRefreshing}
          aria-label="Registry neu laden"
          title="Neu laden"
        >
          <IconBadge icon={<RefreshCw className={isRefreshing ? 'animate-spin' : ''} />} size="sm" variant="default" />
        </button>
      </div>

      {/* Inhalt */}
      {loading ? (
        <div className="flex items-center gap-2 py-4 text-sm text-text-muted dark:text-gray-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Lade Registry …
        </div>
      ) : error ? (
        <div className="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : items && items.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-border-soft dark:border-white/10">
          <table className="w-full text-sm">
            <thead className="bg-surface-muted dark:bg-slate-800/50">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-text-muted dark:text-gray-400">Name</th>
                <th className="px-3 py-2 text-left font-medium text-text-muted dark:text-gray-400">Component</th>
                <th className="px-3 py-2 text-left font-medium text-text-muted dark:text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-soft dark:divide-white/5">
              {items.map((item) => {
                const md = item.widget_metadata ?? item.metadata ?? {};
                const comp = (md?.component_type ?? item.type ?? '—') as string;
                return (
                  <tr
                    key={item.id}
                    className="transition-colors hover:bg-surface-hover dark:hover:bg-slate-800/50"
                  >
                    <td className="px-3 py-2 font-medium text-text dark:text-white">{item.name}</td>
                    <td className="px-3 py-2 font-mono text-xs text-text-soft dark:text-gray-300">{comp}</td>
                    <td className="px-3 py-2">{getStatusBadge(item.status)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <IconBadge icon={<Package />} size="lg" variant="default" />
          <span className="text-sm text-text-muted dark:text-gray-400">Keine Widgets in der Registry.</span>
        </div>
      )}
    </div>
  );
}