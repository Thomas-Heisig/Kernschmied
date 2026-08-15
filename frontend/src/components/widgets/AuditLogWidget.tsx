// F:\Kernschmied\frontend\src\components\widgets\AuditLogWidget.tsx

import React, { useEffect, useState } from 'react';
import { RefreshCw, History, AlertCircle } from 'lucide-react';
import IconBadge from '../common/IconBadge';

interface AuditLogWidgetProps {
  widget: any;
  nodeId?: string;
}

interface AuditEntry {
  id?: string;
  timestamp?: string;
  time?: string;
  user?: string;
  actor?: string;
  action?: string;
  resource?: string;
  details?: Record<string, unknown>;
}

export default function AuditLogWidget({ widget, nodeId }: AuditLogWidgetProps) {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadEntries = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/audit');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const j = await res.json();
      setEntries(Array.isArray(j) ? j : j.items ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Audit‑Daten konnten nicht geladen werden.');
      setEntries(null);
    } finally {
      if (showRefresh) setIsRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void loadEntries(false);
  }, []);

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '—';
    try {
      return new Date(timestamp).toLocaleString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="rounded-xl border border-border-soft bg-white/90 p-4 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/80">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <IconBadge icon={<History />} size="md" variant="primary" />
          <h3 className="text-sm font-semibold text-text dark:text-white">Audit Log</h3>
          {entries && (
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              {entries.length}
            </span>
          )}
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => void loadEntries(true)}
          disabled={isRefreshing}
          aria-label="Audit‑Log neu laden"
          title="Neu laden"
        >
          <IconBadge icon={<RefreshCw className={isRefreshing ? 'animate-spin' : ''} />} size="sm" variant="default" />
        </button>
      </div>

      {/* Inhalt */}
      {loading ? (
        <div className="flex items-center gap-2 py-4 text-sm text-text-muted dark:text-gray-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Lade Audit‑Daten …
        </div>
      ) : error ? (
        <div className="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : entries && entries.length > 0 ? (
        <ul className="space-y-1.5 max-h-60 overflow-y-auto">
          {entries.slice(0, 15).map((entry, idx) => (
            <li
              key={entry.id ?? idx}
              className="flex items-start gap-2 rounded-lg border border-border-soft/50 px-3 py-2 text-xs dark:border-white/5"
            >
              <span className="shrink-0 font-mono text-text-muted dark:text-gray-500">
                {formatTime(entry.timestamp ?? entry.time)}
              </span>
              <span className="font-medium text-text dark:text-white">
                {entry.user ?? entry.actor ?? 'System'}
              </span>
              <span className="text-text-soft dark:text-gray-300">
                {entry.action ?? 'Aktion'}
              </span>
              {entry.resource && (
                <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] text-text-muted dark:bg-slate-800 dark:text-gray-500">
                  {entry.resource}
                </span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <IconBadge icon={<History />} size="lg" variant="default" />
          <span className="text-sm text-text-muted dark:text-gray-400">Keine Audit‑Einträge vorhanden.</span>
        </div>
      )}
    </div>
  );
}