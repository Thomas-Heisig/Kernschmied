import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, RefreshCw, Server, XCircle } from 'lucide-react';
import { loadSystemOverview } from '../../api/system';
import type { SystemOverviewResponse, SystemServiceState } from '../../contracts/system';

const SERVICE_LABELS: Record<string, string> = {
  config_service: 'Konfiguration',
  model_registry: 'Modell-Registry',
  tool_registry: 'Werkzeug-Registry',
  database: 'Datenbank',
};

export default function SystemOverview() {
  const [overview, setOverview] = useState<SystemOverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);

    void loadSystemOverview(controller.signal)
      .then(setOverview)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : 'Systemübersicht konnte nicht geladen werden.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });

    return () => controller.abort();
  }, [refreshKey]);

  if (isLoading && overview === null) {
    return <p className="text-sm text-text-muted dark:text-slate-400">Systemdaten werden geladen...</p>;
  }

  if (error && overview === null) {
    return (
      <div className="flex items-start gap-2 text-sm text-danger" role="alert">
        <AlertCircle size={18} className="mt-0.5 shrink-0" />
        <span>{error}</span>
      </div>
    );
  }

  if (!overview) return null;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <dl className="grid flex-1 grid-cols-2 gap-x-6 gap-y-3 text-sm lg:grid-cols-4">
          <SummaryValue label="Umgebung" value={overview.environment} />
          <SummaryValue label="API" value={overview.api_version} />
          <SummaryValue label="Konfiguration" value={`Revision ${overview.config_revision}`} />
          <SummaryValue label="Schema" value={overview.schema_version} />
        </dl>
        <button
          type="button"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
          aria-label="Systemübersicht neu laden"
          title="Neu laden"
          onClick={() => setRefreshKey((current) => current + 1)}
          disabled={isLoading}
        >
          <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase text-text-muted dark:text-slate-400">Dienste</h3>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {Object.entries(overview.services).map(([name, service]) => (
            <ServiceState key={name} name={SERVICE_LABELS[name] ?? name} state={service.status} />
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase text-text-muted dark:text-slate-400">Registries</h3>
        <dl className="grid grid-cols-2 gap-3 sm:max-w-md">
          <SummaryValue label="Modelle" value={String(overview.registries.models)} />
          <SummaryValue label="Werkzeuge" value={String(overview.registries.tools)} />
        </dl>
      </div>
    </div>
  );
}

function SummaryValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-text-muted dark:text-slate-400">{label}</dt>
      <dd className="mt-1 truncate font-medium text-text dark:text-white">{value}</dd>
    </div>
  );
}

function ServiceState({ name, state }: { name: string; state: SystemServiceState }) {
  const isUp = state === 'up';
  const isDown = state === 'down';
  const Icon = isUp ? CheckCircle2 : isDown ? XCircle : Server;
  const color = isUp ? 'text-success' : isDown ? 'text-danger' : 'text-text-muted dark:text-slate-400';

  return (
    <div className="flex min-w-0 items-center gap-2 bg-surface-muted px-3 py-2 dark:bg-slate-800/50">
      <Icon size={16} className={`shrink-0 ${color}`} aria-hidden="true" />
      <span className="truncate text-sm text-text-soft dark:text-slate-300">{name}</span>
      <span className={`ml-auto text-xs font-medium ${color}`}>{isUp ? 'Online' : isDown ? 'Offline' : 'Unbekannt'}</span>
    </div>
  );
}