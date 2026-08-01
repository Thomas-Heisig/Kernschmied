// F:\Kernschmied\frontend\src\components\layout\AppFooter.tsx

import React, { useEffect, useMemo, useState } from 'react';
import type { BootstrapResponse } from '../../types/bootstrap';
import FooterCalendar from '../calendar/FooterCalendar';
import { createEvent, listCalendars } from '../../api/fetchCalendarClient';
import type { components } from '../../api/openapi-types';
import { CalendarDays, Database, FolderTree, Plug, Server, Wifi } from 'lucide-react';

interface AppFooterProps {
  schemaVersion?: string;

  environment?: string;

  apiVersion?: string;

  applicationVersion?: string;

  configRevision?: number;

  modelRevision?: number;

  toolRevision?: number;

  backendOnline?: boolean;
}

export function AppFooter({
  schemaVersion,
  environment = 'Development',
  apiVersion = 'v1',
  applicationVersion = '0.1.0',
  configRevision = 1,
  modelRevision = 1,
  toolRevision = 1,
  backendOnline = true,
}: AppFooterProps) {
  const [bootstrap, setBootstrap] = useState<BootstrapResponse | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailTitle, setDetailTitle] = useState<string | null>(null);
  const [detailContent, setDetailContent] = useState<string | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [calendars, setCalendars] = useState<Array<{ id: string; name: string }>>([]);
  const [targetCalendarId, setTargetCalendarId] = useState<string | null>(null);
  const [eventModalOpen, setEventModalOpen] = useState(false);
  const [eventTitle, setEventTitle] = useState('');
  const [copied, setCopied] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [systemInfoOpen, setSystemInfoOpen] = useState(false);
  const [systemTab, setSystemTab] = useState<'overview' | 'functions' | 'versions' | 'technical'>('overview');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const autoRefreshIntervalMs = 30000; // 30s
  const [saveSelectionsEnabled, setSaveSelectionsEnabled] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem('calendar.saveSelection');
      // Default to true when no explicit preference is stored (opt-in default true)
      if (v === null) return true;
      return v === 'true';
    } catch {
      return true;
    }
  });

  const [modelsCount, setModelsCount] = useState<number | null>(null);
  const [toolsCount, setToolsCount] = useState<number | null>(null);

  // bootstrap/health loader (unchanged)

  useEffect(() => {
    let mounted = true;

    async function loadBootstrap() {
      try {
        const res = await fetch('/api/v1/bootstrap', { cache: 'no-store' });

        if (!mounted) return;

        if (!res.ok) {
          throw new Error(`${res.status} ${res.statusText}`);
        }

        const data = (await res.json()) as BootstrapResponse;
        setBootstrap(data);
        setOnline(true);
        setLastChecked(new Date());
        setRequestId((data as any)?.request_id ?? res.headers.get('X-Request-Id'));
        // fetch counts for models/tools if endpoints provided
        try {
          const m = await fetch('/api/v1/models', { cache: 'no-store' });
          if (m.ok) {
            const md = await m.json();
            // if API returns array or object with items
            if (Array.isArray(md)) setModelsCount(md.length);
            else if (typeof md === 'object' && md?.items) setModelsCount(md.items.length ?? null);
            else if (typeof md === 'object' && md?.length) setModelsCount(md.length ?? null);
          }
        } catch {}

        try {
          const t = await fetch('/api/v1/tools', { cache: 'no-store' });
          if (t.ok) {
            const td = await t.json();
            if (Array.isArray(td)) setToolsCount(td.length);
            else if (typeof td === 'object' && td?.items) setToolsCount(td.items.length ?? null);
            else if (typeof td === 'object' && td?.length) setToolsCount(td.length ?? null);
          }
        } catch {}
      } catch (err: any) {
        // Fallback: try health endpoint to at least determine online state
        try {
          const h = await fetch('/api/v1/health', { cache: 'no-store' });

          if (!mounted) return;

          if (h.ok) {
            setOnline(true);
          } else {
            setOnline(false);
          }
        } catch (err2) {
          if (!mounted) return;
          setOnline(false);
        }

        setError(err?.message ?? String(err));
      }
    }

    loadBootstrap();

    return () => {
      mounted = false;
    };
  }, []);

  // Auto-refresh when enabled
  useEffect(() => {
    if (!autoRefresh) return;
    let cancelled = false;
    const tick = async () => {
      try {
        const res = await fetch('/api/v1/bootstrap', { cache: 'no-store' });
        if (!res.ok) {
          setOnline(false);
          setError(`${res.status} ${res.statusText}`);
          return;
        }
        const data = await res.json();
        if (cancelled) return;
        setBootstrap(data);
        setOnline(true);
        setError(null);
        setLastChecked(new Date());
        setRequestId((data as any)?.request_id ?? res.headers.get('X-Request-Id'));
      } catch (e: any) {
        if (cancelled) return;
        setOnline(false);
        setError(String(e));
      }
    };

    const id = window.setInterval(tick, autoRefreshIntervalMs);
    // do an immediate tick
    tick();

    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, [autoRefresh]);

  useEffect(() => {
    let mounted = true;

    async function ensureUserCalendarDefault() {
      if (!showDatePicker) return;
      try {
        const all = await listCalendars();
        if (!mounted) return;
        // prefer bootstrap.user.id if available
        const userId = (bootstrap as any)?.user?.id;
        if (userId) {
          const own = (all || []).find(
            (c) => c.owner_id === userId || (c.owner_id ?? '') === userId,
          );
          if (own) setTargetCalendarId(own.id);
        }
      } catch {
        // ignore
      }
    }

    ensureUserCalendarDefault();

    return () => {
      mounted = false;
    };
  }, [showDatePicker]);

  function openDetail(title: string, data: any) {
    setDetailTitle(title);
    try {
      setDetailContent(JSON.stringify(data, null, 2));
    } catch {
      setDetailContent(String(data));
    }
    setDetailOpen(true);
  }

  function closeDetail() {
    setDetailOpen(false);
    setDetailTitle(null);
    setDetailContent(null);
  }

  // derive friendly values
  const appName = bootstrap?.application?.name ?? 'Kernschmied';
  const appVersion = bootstrap?.application?.version ?? applicationVersion;
  const env = (bootstrap?.environment ?? environment) as string;
  const envLabel = env === 'production' ? 'Produktiv' : env === 'development' ? 'Entwicklung' : env;
  const statusLabel = online ? 'System bereit' : online === false ? 'System nicht erreichbar' : 'Unbekannt';
  const statusColor = online ? 'text-emerald-600' : online === false ? 'text-red-500' : 'text-gray-500';

  // capabilities mapping for friendly display
  const caps = (bootstrap?.capabilities ?? bootstrap?.features ?? {}) as Record<string, any>;
  const friendlyCaps: Array<{ title: string; ok: boolean | null; emoji?: string }> = [
    { title: 'Live-Chat', ok: !!caps.chat_streaming, emoji: '💬' },
    { title: 'KI-Modelle', ok: !!caps.model_service, emoji: '🤖' },
    { title: 'Werkzeuge', ok: !!caps.tool_registry, emoji: '🧰' },
    { title: 'Speicherung', ok: caps.chat_persistence ?? null, emoji: '💾' },
    { title: 'Datei-Upload', ok: caps.file_upload ?? null, emoji: '📎' },
  ];
  
 

  return (
    <footer className="z-30 shrink-0 border-t border-border bg-white/90 backdrop-blur-md dark:border-white/10 dark:bg-slate-950/90">
      <div className="flex h-10 items-center justify-between gap-4 overflow-x-auto px-4 text-sm text-text-muted dark:text-gray-400">
        <div className="flex items-center gap-4">
          <button
            className="flex items-baseline gap-2 hover:underline focus:outline-none"
            onClick={() => {
              setSystemTab('overview');
              setSystemInfoOpen(true);
            }}
          >
            <strong className="text-sm font-semibold text-text dark:text-white">{appName}</strong>
            <span className="text-xs text-text-muted">{appVersion}</span>
          </button>

          <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-slate-800">
            {envLabel}
          </span>

          <div className="flex items-center gap-2">
            <span className={`${statusColor} font-medium`} aria-hidden>
              ●
            </span>
            <button className="text-xs hover:underline" onClick={() => setSystemInfoOpen(true)}>
              {statusLabel}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-xs text-text-muted">API {bootstrap?.versions?.api ?? apiVersion} · Schema {bootstrap?.schema_version ?? schemaVersion}</span>

          {/* Clock and calendar trigger */}
          <div className="flex items-center gap-2">
            <Clock />
            <button
              className="text-xs px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-slate-800 flex items-center gap-2"
              onClick={() => setShowDatePicker(true)}
              aria-label="Datum auswählen"
              title="Datum auswählen"
            >
              <CalendarDays className="w-4 h-4" />
              <span className="hidden sm:inline">Kalender</span>
            </button>
          </div>

          <button
            className="text-xs px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-slate-800"
            onClick={() => setSystemInfoOpen(true)}
            aria-label="Systeminfo"
          >
            ⓘ Systeminfo
          </button>

          {/* opt-in toggle for saving calendar selections */}
          <div className="ml-3 flex items-center gap-2 text-xs">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={saveSelectionsEnabled}
                onChange={(e) => {
                  setSaveSelectionsEnabled(e.target.checked);
                  try {
                    localStorage.setItem('calendar.saveSelection', e.target.checked ? 'true' : 'false');
                  } catch {}
                }}
              />
              <span>Speichern</span>
            </label>
          </div>
        </div>
      </div>

      {/* Inline DatePicker modal when requested */}
      {showDatePicker ? (
        <div className="fixed right-4 bottom-16 z-50 w-[min(520px,95%)] max-w-full rounded border bg-white p-4 shadow dark:bg-slate-800">
          <div className="flex items-center justify-between">
            <strong>Datum auswählen</strong>
            <button className="text-sm text-gray-500" onClick={() => setShowDatePicker(false)}>✕</button>
          </div>
          <div className="mt-3">
            {/* use the DatePicker defined inside this component */}
            <DatePicker
              initialDate={selectedDate ?? new Date()}
              setSelectedDate={(d) => setSelectedDate(d)}
              onSelect={(d) => {
                setSelectedDate(d);
                setShowDatePicker(false);
              }}
              onCancel={() => setShowDatePicker(false)}
            />
          </div>
        </div>
      ) : null}

      {systemInfoOpen && (
        <div className="fixed right-4 bottom-16 z-50 w-[min(720px,95%)] max-w-full rounded border bg-white p-4 shadow dark:bg-slate-800">
          <div className="flex items-center justify-between">
            <strong>Systeminformationen</strong>
            <div className="flex items-center gap-2">
                <div className="text-xs text-text-muted">{lastChecked ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(lastChecked) : new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(new Date())}</div>
              <button className="text-sm text-gray-500" onClick={() => setSystemInfoOpen(false)}>
                ✕
              </button>
            </div>
          </div>

          <div className="mt-3 flex gap-4">
            <nav className="w-40">
              <ul className="space-y-1 text-sm">
                <li>
                  <button className={`w-full text-left p-2 rounded ${systemTab === 'overview' ? 'bg-gray-100 dark:bg-slate-700' : ''}`} onClick={() => setSystemTab('overview')}>Übersicht</button>
                </li>
                <li>
                  <button className={`w-full text-left p-2 rounded ${systemTab === 'functions' ? 'bg-gray-100 dark:bg-slate-700' : ''}`} onClick={() => setSystemTab('functions')}>Funktionen</button>
                </li>
                <li>
                  <button className={`w-full text-left p-2 rounded ${systemTab === 'versions' ? 'bg-gray-100 dark:bg-slate-700' : ''}`} onClick={() => setSystemTab('versions')}>Versionen</button>
                </li>
                <li>
                  <button className={`w-full text-left p-2 rounded ${systemTab === 'technical' ? 'bg-gray-100 dark:bg-slate-700' : ''}`} onClick={() => setSystemTab('technical')}>Technik</button>
                </li>
              </ul>
            </nav>

            <div className="flex-1">
              {systemTab === 'overview' && (
                <div>
                  <h3 className="font-semibold">{appName} {appVersion}</h3>
                  <p className="text-sm text-text-muted">Lokale Chat- und Assistenzplattform</p>

                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded border p-3">
                      <div className="font-medium">Dienste</div>
                      <ul className="mt-2 space-y-1">
                        <li>Backend: <span className={online ? 'text-emerald-600' : 'text-red-500'}>{online ? 'Online' : online === false ? 'Nicht erreichbar' : 'Unbekannt'}</span></li>
                        <li>Authentifizierung: {bootstrap?.authenticated ? 'Aktiv' : 'Nicht aktiv'}</li>
                        <li>Live-Chat: {caps.chat_streaming ? 'Verfügbar' : 'Nicht verfügbar'}</li>
                        <li>Modelle: {caps.model_service ? 'Verfügbar' : 'Nicht verfügbar'}</li>
                      </ul>
                    </div>

                    <div className="rounded border p-3">
                      <div className="font-medium">Konfiguration</div>
                      <div className="mt-2 text-sm">Status: {bootstrap?.config_revision ? 'Aktuell' : 'Unbekannt'}</div>
                      <div className="text-sm">Revision: {bootstrap?.config_revision ?? configRevision}</div>
                      <div className="mt-2">
                            <button className="text-xs px-2 py-1 rounded bg-gray-100" onClick={() => { setSystemTab('versions'); }}>Details</button>
                      </div>
                    </div>
                  </div>

                      <div className="mt-3">
                        <button
                          className="text-sm px-3 py-1 rounded bg-sky-600 text-white flex items-center gap-2"
                          onClick={async () => {
                            setIsRefreshing(true);
                            try {
                              const res = await fetch('/api/v1/bootstrap', { cache: 'no-store' });
                              if (res.ok) {
                                const data = await res.json();
                                setBootstrap(data);
                                setOnline(true);
                                setError(null);
                                setLastChecked(new Date());
                                setRequestId((data as any)?.request_id ?? res.headers.get('X-Request-Id'));
                              } else {
                                setOnline(false);
                                setError(`${res.status} ${res.statusText}`);
                              }
                            } catch (e: any) {
                              setOnline(false);
                              setError(String(e));
                            } finally {
                              setIsRefreshing(false);
                            }
                          }}
                        >
                          {isRefreshing ? <span className="animate-spin">⟳</span> : null}
                          <span>Status neu prüfen</span>
                        </button>
                      </div>
                </div>
              )}

              {systemTab === 'functions' && (
                <div>
                  <h3 className="font-semibold">Funktionen</h3>
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    {friendlyCaps.map((c) => {
                      const count = c.title === 'KI-Modelle' ? modelsCount : c.title === 'Werkzeuge' ? toolsCount : null;

                      return (
                        <div key={c.title} className="rounded border p-3 text-sm flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span>{c.emoji}</span>
                            <div>
                              <div className="font-medium">{c.title} {count !== null ? <span className="ml-2 text-xs text-text-muted">{count}</span> : null}</div>
                              <div className="text-xs text-text-muted">{c.ok === true ? 'Verfügbar' : c.ok === false ? 'Nicht aktiviert' : 'Unbekannt'}</div>
                            </div>
                          </div>
                          {c.ok === true ? <span className="text-emerald-600">●</span> : c.ok === false ? <span className="text-gray-400">○</span> : <span className="text-gray-500">–</span>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {systemTab === 'versions' && (
                <div>
                  <h3 className="font-semibold">Schnittstellen & Versionen</h3>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded border p-3">API: {bootstrap?.versions?.api ?? apiVersion}</div>
                    <div className="rounded border p-3">Schema: {bootstrap?.schema_version ?? schemaVersion}</div>
                    <div className="rounded border p-3">UI Schema: {bootstrap?.ui_schema ?? 'n/a'}</div>
                    <div className="rounded border p-3">Bootstrap Schema: {bootstrap?.bootstrap_schema ?? 'n/a'}</div>
                  </div>
                </div>
              )}

              {systemTab === 'technical' && (
                <div>
                  <h3 className="font-semibold">Technische Details</h3>
                  <div className="mt-3 text-xs">
                    <div className="mb-2 text-xs text-text-muted">Request ID: {requestId ?? '—'} · Letzte Prüfung: {lastChecked ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(lastChecked) : '—'}</div>
                    <div className="rounded border p-3 max-h-64 overflow-auto bg-gray-50 dark:bg-slate-900">
                      <pre className="whitespace-pre-wrap">{JSON.stringify(bootstrap ?? { online, error, versions: (bootstrap as BootstrapResponse | null)?.versions }, null, 2)}</pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </footer>
  );
}

interface StatusItemProps {
  children: React.ReactNode;

  icon?: React.ReactNode;

  onClick?: () => void;
}

function StatusItem({ children, icon, onClick }: StatusItemProps) {
  const base = 'flex items-center gap-1.5 whitespace-nowrap';

  if (onClick) {
    return (
      <button
        onClick={onClick}
        className={
          base +
          ' cursor-pointer hover:underline focus:outline-none focus:ring-2 focus:ring-sky-500 rounded'
        }
        aria-label={typeof children === 'string' ? children : undefined}
      >
        {icon}

        <span>{children}</span>
      </button>
    );
  }

  return (
    <div className={base}>
      {icon}

      <span>{children}</span>
    </div>
  );
}

function Clock() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const formatted = useMemo(() => {
    return new Intl.DateTimeFormat('de-DE', {
      weekday: 'short',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(now);
  }, [now]);

  return (
    <span className="font-mono w-48 text-right" aria-live="polite">
      {formatted}
    </span>
  );
}

function DatePicker({
  initialDate,
  setSelectedDate,
  onSelect,
  onCancel,
  saveSelectionsEnabled,
  autoRefresh,
  setAutoRefresh,
  setSystemTab,
  bootstrap,
  configRevision,
  modelsCount,
  toolsCount,
}: {
  initialDate: Date;
  setSelectedDate: (d: Date) => void;
  onSelect: (d: Date) => void;
  onCancel: () => void;
  saveSelectionsEnabled: boolean;
  autoRefresh: boolean;
  setAutoRefresh: React.Dispatch<React.SetStateAction<boolean>>;
  setSystemTab: (t: 'overview' | 'functions' | 'versions' | 'technical') => void;
  bootstrap: BootstrapResponse | null;
  configRevision: number;
  modelsCount: number | null;
  toolsCount: number | null;
}) {
  const [viewDate, setViewDate] = useState<Date>(new Date(initialDate));
  const [selectedDay, setSelectedDay] = useState<number | null>(initialDate.getDate());
  const [time, setTime] = useState(() => {
    const h = String(initialDate.getHours()).padStart(2, '0');
    const m = String(initialDate.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  });

  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();

  function daysInMonth(y: number, m: number) {
    return new Date(y, m + 1, 0).getDate();
  }

  function startWeekday(y: number, m: number) {
    return new Date(y, m, 1).getDay();
  }

  const days = [] as (number | null)[];
  const start = startWeekday(year, month);
  const total = daysInMonth(year, month);

  for (let i = 0; i < start; i++) days.push(null);
  for (let d = 1; d <= total; d++) days.push(d);

  function pick(day: number) {
    const [hh, mm] = time.split(':').map((s) => parseInt(s, 10) || 0);
    const chosen = new Date(year, month, day, hh, mm);
    setSelectedDay(day);
    setSelectedDate(chosen);
    onSelect(chosen);
    // send to backend (prepared endpoint) only if user enabled saving
    if (saveSelectionsEnabled) {
        sendSelectedDateIfOptIn(chosen).catch(() => {});
    }
  }

  // keyboard navigation
  function onKey(e: React.KeyboardEvent) {
    if (!selectedDay) return;
    let d = selectedDay;

    if (e.key === 'ArrowLeft') d = Math.max(1, d - 1);
    else if (e.key === 'ArrowRight') d = Math.min(total, d + 1);
    else if (e.key === 'ArrowUp') d = Math.max(1, d - 7);
    else if (e.key === 'ArrowDown') d = Math.min(total, d + 7);
    else if (e.key === 'Enter') {
      pick(d);
      return;
    } else if (e.key === 'Escape') {
      onCancel();
      return;
    }

    if (d !== selectedDay) {
      setSelectedDay(d);
      // ensure visible
      if (d <= 0) setViewDate(new Date(year, month - 1, 1));
    }
  }

  return (
    <div className="text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            className="px-2 focus:ring-2 focus:ring-sky-500 rounded"
            onClick={() => setViewDate(new Date(year, month - 1, 1))}
          >
            ◀
          </button>
          <strong>{viewDate.toLocaleString('de-DE', { month: 'long', year: 'numeric' })}</strong>
          <button
            className="px-2 focus:ring-2 focus:ring-sky-500 rounded"
            onClick={() => setViewDate(new Date(year, month + 1, 1))}
          >
            ▶
          </button>
        </div>
        <div>
          <button className="text-xs text-gray-500" onClick={onCancel}>
            Abbrechen
          </button>
        </div>
      </div>

      <div
        className="mt-2 grid grid-cols-7 gap-1 text-center text-xs"
        tabIndex={0}
        onKeyDown={onKey}
      >
        {['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'].map((w) => (
          <div key={w} className="font-medium">
            {w}
          </div>
        ))}
        {days.map((d, i) => (
          <div key={i} className={`py-1 ${d ? 'cursor-pointer rounded' : ''}`}>
            {d ? (
              <button
                onClick={() => pick(d)}
                className={`w-full ${selectedDay === d ? 'bg-sky-600 text-white rounded' : 'hover:bg-gray-100 dark:hover:bg-slate-700 rounded'} focus:outline-none focus:ring-2 focus:ring-sky-500`}
              >
                {d}
              </button>
            ) : null}
          </div>
        ))}
      </div>

          <div className="flex items-center gap-2">
        <input
          className="flex-1 rounded border px-2 py-1"
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />
            <button
              className="ml-2 text-xs px-2 py-0.5 rounded bg-gray-50 dark:bg-slate-700"
              onClick={() => setAutoRefresh((v: boolean) => !v)}
              title="Automatisch aktualisieren (30s)"
            >
              {autoRefresh ? 'Auto‑Refresh: Ein' : 'Auto‑Refresh: Aus'}
            </button>

            {/* Konfiguration Badge (visible on md+) */}
            <button
              className="hidden md:inline-flex ml-2 items-center gap-2 text-xs px-2 py-0.5 rounded bg-gray-50 dark:bg-slate-700"
              onClick={() => setSystemTab('versions')}
              title={`Konfiguration Revision ${bootstrap?.config_revision ?? configRevision}`}
            >
              ⚙ Konf: {bootstrap?.config_revision ?? configRevision}
            </button>

            {/* Modelle/Werkzeuge indicators (compact) */}
            <div className="hidden md:flex items-center gap-2 ml-2 text-xs">
              <div className="flex items-center gap-2">
                <span className={bootstrap?.revisions?.model_registry ? 'text-emerald-600' : 'text-gray-400'}>🤖</span>
                <span>{bootstrap?.revisions?.model_registry ? 'Modelle bereit' : 'Modelle'}</span>
                <span className="ml-1 inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium rounded bg-gray-100 dark:bg-slate-700">{modelsCount ?? '—'}</span>
              </div>
              <div className="flex items-center gap-2 ml-3">
                <span className={bootstrap?.revisions?.tool_registry ? 'text-emerald-600' : 'text-gray-400'}>🧰</span>
                <span>{bootstrap?.revisions?.tool_registry ? 'Werkzeuge bereit' : 'Werkzeuge'}</span>
                <span className="ml-1 inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium rounded bg-gray-100 dark:bg-slate-700">{toolsCount ?? '—'}</span>
              </div>
            </div>

            {/* Feedback link */}
            <a className="hidden md:inline-block ml-3 text-xs text-sky-600 hover:underline" href="https://github.com/Thomas-Heisig/Kernschmied/issues/new" target="_blank" rel="noreferrer">Feedback</a>
      </div>
    </div>
  );
}

export async function sendSelectedDate(date: Date) {
  try {
    const res = await fetch('/api/v1/calendar/selection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected: date.toISOString() }),
    });

    if (!res.ok) {
      // Not fatal; backend may not implement this yet
      throw new Error(`${res.status} ${res.statusText}`);
    }

    return res.json();
  } catch (e) {
    // swallow; integration point prepared
    return null;
  }
}

export function shouldSendSelection(): boolean {
  try {
    const v = localStorage.getItem('calendar.saveSelection');
    if (v === null) return true;
    return v === 'true';
  } catch {
    return true;
  }
}

export async function sendSelectedDateIfOptIn(date: Date) {
  if (!shouldSendSelection()) return null;
  return sendSelectedDate(date);
}
