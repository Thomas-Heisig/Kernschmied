// F:\Kernschmied\frontend\src\components\widgets\SystemHealthWidget.tsx

import { useEffect, useState } from 'react';
import { Activity, RefreshCw, AlertCircle, CheckCircle, XCircle, Clock, Server, Database, Cpu, Package } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import { loadSystemOverview } from '../../api/system';
import type { SystemOverviewResponse } from '../../contracts/system';

interface SystemHealthWidgetProps {
  widget: any;
  nodeId?: string;
}

export default function SystemHealthWidget(_props: SystemHealthWidgetProps) {
  const [data, setData] = useState<SystemOverviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadStatus = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    setError(null);

    try {
      setData(await loadSystemOverview());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Systemstatus konnte nicht geladen werden.');
      setData(null);
    } finally {
      if (showRefresh) setIsRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void loadStatus(false);
  }, []);

  const getStatusBadge = (value: string | boolean | number | undefined) => {
    if (value === undefined || value === null) {
      return {
        icon: <Clock className="h-3 w-3" />,
        label: 'Unbekannt',
        className: 'bg-warning-soft text-warning dark:bg-warning/20 dark:text-warning',
      };
    }
    const normalized = String(value).toLowerCase();
    const isOk = typeof value === 'boolean' ? value : normalized === 'ok' || normalized === 'up' || normalized === 'healthy' || normalized === 'online';
    if (isOk) {
      return {
        icon: <CheckCircle className="h-3 w-3" />,
        label: 'Online',
        className: 'bg-success-soft text-success dark:bg-success/20 dark:text-success',
      };
    }
    return {
      icon: <XCircle className="h-3 w-3" />,
      label: 'Offline',
      className: 'bg-danger-soft text-danger dark:bg-danger/20 dark:text-danger',
    };
  };

  const statusFields = [
    { key: 'backend', label: 'Backend', icon: <Server className="h-4 w-4" />, value: data?.status },
    { key: 'database', label: 'Datenbank', icon: <Database className="h-4 w-4" />, value: data?.services.database?.status },
    { key: 'model_count', label: 'Modelle', icon: <Cpu className="h-4 w-4" />, value: data?.registries.models },
    { key: 'tool_count', label: 'Werkzeuge', icon: <Package className="h-4 w-4" />, value: data?.registries.tools },
  ];

  return (
    <div className="rounded-xl border border-border-soft bg-white/90 p-4 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/80">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <IconBadge icon={<Activity />} size="md" variant="primary" />
          <h3 className="text-sm font-semibold text-text dark:text-white">Systemstatus</h3>
          {data && (
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              Aktiv
            </span>
          )}
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => void loadStatus(true)}
          disabled={isRefreshing}
          aria-label="Systemstatus neu laden"
          title="Neu laden"
        >
          <IconBadge icon={<RefreshCw className={isRefreshing ? 'animate-spin' : ''} />} size="sm" variant="default" />
        </button>
      </div>

      {/* Inhalt */}
      {loading ? (
        <div className="flex items-center gap-2 py-4 text-sm text-text-muted dark:text-gray-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Lade Systemstatus …
        </div>
      ) : error ? (
        <div className="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {statusFields.map(({ key, label, icon, value }) => {
            // Prüfe, ob ein Wert existiert
            const hasValue = value !== undefined && value !== null;
            const displayValue = hasValue ? value : '—';

            // Für numerische Felder (model_count, tool_count) zeigen wir die Zahl ohne Badge
            if (key === 'model_count' || key === 'tool_count') {
              const count = typeof displayValue === 'number' ? displayValue : Number(displayValue);
              const validCount = !isNaN(count) && count >= 0 ? count : '—';
              return (
                <div key={key} className="flex items-center gap-3 rounded-lg border border-border-soft bg-surface-muted/50 px-3 py-2 dark:border-white/5 dark:bg-slate-800/30">
                  <span className="text-text-muted dark:text-gray-400">{icon}</span>
                  <span className="text-xs text-text-muted dark:text-gray-400">{label}</span>
                  <span className="ml-auto font-mono text-sm font-semibold text-text dark:text-white">{validCount}</span>
                </div>
              );
            }

            const badge = getStatusBadge(displayValue);
            return (
              <div key={key} className="flex items-center gap-3 rounded-lg border border-border-soft bg-surface-muted/50 px-3 py-2 dark:border-white/5 dark:bg-slate-800/30">
                <span className="text-text-muted dark:text-gray-400">{icon}</span>
                <span className="text-xs text-text-muted dark:text-gray-400">{label}</span>
                <span className={`ml-auto inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium ${badge.className}`}>
                  {badge.icon}
                  {badge.label}
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 py-6 text-center">
          <IconBadge icon={<Activity />} size="lg" variant="default" />
          <span className="text-sm text-text-muted dark:text-gray-400">Systemstatus nicht verfügbar.</span>
        </div>
      )}
    </div>
  );
}