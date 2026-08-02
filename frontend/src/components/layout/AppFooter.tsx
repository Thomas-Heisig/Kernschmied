// F:\Kernschmied\frontend\src\components\layout\AppFooter.tsx

import React, { useEffect, useMemo, useState } from 'react';
import type { BootstrapResponse } from '../../types/bootstrap';
import { listCalendars } from '../../api/fetchCalendarClient';
import { sendSelectedDateIfOptIn } from '../../lib/calendar';
import {
  CalendarDays,
  Database,
  FolderTree,
  Plug,
  Server,
  Wifi,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Settings,
  Globe,
  Cpu,
  Zap,
  Layers,
  Clock as ClockIcon,
  Info,
} from 'lucide-react';
import ChatHistoryPanel from '../../components/chat/ChatHistoryPanel';

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
  schemaVersion = '1.0',
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
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [calendars, setCalendars] = useState<Array<{ id: string; name: string }>>([]);
  const [targetCalendarId, setTargetCalendarId] = useState<string | null>(null);
  const [systemInfoOpen, setSystemInfoOpen] = useState(false);
  const [systemTab, setSystemTab] = useState<'overview' | 'functions' | 'versions' | 'technical'>('overview');
  const [chatHistoryOpen, setChatHistoryOpen] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const autoRefreshIntervalMs = 30000;
  const [saveSelectionsEnabled] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem('calendar.saveSelection');
      return v === null ? true : v === 'true';
    } catch {
      return true;
    }
  });

  const [modelsCount, setModelsCount] = useState<number | null>(null);
  const [toolsCount, setToolsCount] = useState<number | null>(null);

  const datePickerRef = React.useRef<HTMLDivElement | null>(null);
  const dateToggleRef = React.useRef<HTMLButtonElement | null>(null);
  const systemInfoRef = React.useRef<HTMLDivElement | null>(null);
  const systemTriggerRef = React.useRef<HTMLButtonElement | null>(null);

  // Bootstrap laden
  useEffect(() => {
    let mounted = true;
    async function loadBootstrap() {
      try {
        const res = await fetch('/api/v1/bootstrap', { cache: 'no-store' });
        if (!mounted) return;
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const data = (await res.json()) as BootstrapResponse;
        setBootstrap(data);
        setOnline(true);
        setLastChecked(new Date());
        setRequestId((data as any)?.request_id ?? res.headers.get('X-Request-Id'));
        // Modelle & Tools zählen
        try {
          const m = await fetch('/api/v1/models', { cache: 'no-store' });
          if (m.ok) {
            const md = await m.json();
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
        try {
          const h = await fetch('/api/v1/health', { cache: 'no-store' });
          if (!mounted) return;
          if (h.ok) setOnline(true);
          else setOnline(false);
        } catch {
          if (!mounted) return;
          setOnline(false);
        }
        setError(err?.message ?? String(err));
      }
    }
    loadBootstrap();
    return () => { mounted = false; };
  }, []);

  // Auto-Refresh
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
    tick();
    return () => { cancelled = true; window.clearInterval(id); };
  }, [autoRefresh]);

  useEffect(() => {
    let mounted = true;
    async function ensureUserCalendarDefault() {
      if (!showDatePicker) return;
      try {
        const all = await listCalendars();
        if (!mounted) return;
        const userId = (bootstrap as any)?.user?.id;
        if (userId) {
          const own = (all || []).find((c) => c.owner_id === userId || (c.owner_id ?? '') === userId);
          if (own) setTargetCalendarId(own.id);
        }
      } catch {}
    }
    ensureUserCalendarDefault();
    return () => { mounted = false; };
  }, [showDatePicker]);

  // Klick ausserhalb / Escape
  React.useEffect(() => {
    function onDown(e: MouseEvent) {
      const target = e.target as Node | null;
      if (showDatePicker) {
        const insidePicker = datePickerRef.current?.contains(target ?? null);
        const onToggle = dateToggleRef.current?.contains(target ?? null);
        if (!insidePicker && !onToggle) setShowDatePicker(false);
      }
      if (systemInfoOpen) {
        const insideSys = systemInfoRef.current?.contains(target ?? null);
        const onToggleSys = systemTriggerRef.current?.contains(target ?? null);
        if (!insideSys && !onToggleSys) setSystemInfoOpen(false);
      }
    }
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [showDatePicker, systemInfoOpen]);

  React.useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        if (showDatePicker) setShowDatePicker(false);
        if (systemInfoOpen) setSystemInfoOpen(false);
      }
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [showDatePicker, systemInfoOpen]);

  // Ableitungen
  const appName = bootstrap?.application?.name ?? 'Kernschmied';
  const appVersion = bootstrap?.application?.version ?? applicationVersion;
  const env = (bootstrap?.environment ?? environment) as string;
  const envLabel = env === 'production' ? 'Produktiv' : env === 'development' ? 'Entwicklung' : env;
  const envColor =
    env === 'production'
      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300'
      : env === 'development'
      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
      : 'bg-gray-100 text-gray-800 dark:bg-gray-700/30 dark:text-gray-300';
  const statusLabel = online ? 'System bereit' : online === false ? 'System nicht erreichbar' : 'Unbekannt';
  const statusColor = online ? 'text-emerald-600' : online === false ? 'text-red-500' : 'text-gray-500';
  const StatusIcon = online ? CheckCircle : online === false ? XCircle : AlertCircle;

  const caps = (bootstrap?.capabilities ?? bootstrap?.features ?? {}) as Record<string, any>;
  const friendlyCaps: Array<{ title: string; ok: boolean | null; icon?: React.ReactNode }> = [
    { title: 'Live-Chat', ok: !!caps.chat_streaming, icon: <Zap className="w-4 h-4" /> },
    { title: 'KI-Modelle', ok: !!caps.model_service, icon: <Cpu className="w-4 h-4" /> },
    { title: 'Werkzeuge', ok: !!caps.tool_registry, icon: <FolderTree className="w-4 h-4" /> },
    { title: 'Speicherung', ok: caps.chat_persistence ?? null, icon: <Database className="w-4 h-4" /> },
    { title: 'Datei-Upload', ok: caps.file_upload ?? null, icon: <Plug className="w-4 h-4" /> },
  ];

  return (
    <footer className="z-30 shrink-0 border-t border-gray-200 bg-white/80 backdrop-blur-md dark:border-white/10 dark:bg-slate-950/90 shadow-sm">
      <div className="flex h-12 items-center justify-between gap-3 px-4 text-sm text-gray-600 dark:text-gray-300">
        {/* Linker Bereich */}
        <div className="flex items-center gap-3">
          <button
            ref={systemTriggerRef}
            className="flex items-center gap-2 hover:underline focus:outline-none focus:ring-2 focus:ring-sky-500 rounded px-1 py-0.5"
            onClick={() => {
              setSystemTab('overview');
              setSystemInfoOpen(true);
            }}
            aria-label="Systeminformationen öffnen"
          >
            <span className="font-semibold text-gray-900 dark:text-white">{appName}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
              v{appVersion}
            </span>
          </button>

          <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${envColor}`}>
            <Globe className="w-3 h-3" />
            {envLabel}
          </span>

          <div className="flex items-center gap-1.5">
            <StatusIcon className={`w-4 h-4 ${statusColor}`} />
            <button
              className="text-xs hover:underline focus:outline-none focus:ring-2 focus:ring-sky-500 rounded px-1"
              onClick={() => setSystemInfoOpen(true)}
            >
              {statusLabel}
            </button>
            {error && <span className="text-xs text-red-500 ml-1" title={error}>⚠</span>}
          </div>
        </div>

        {/* Rechter Bereich */}
        <div className="flex items-center gap-3 flex-1 justify-end">
          <span className="hidden sm:inline text-xs text-gray-400 dark:text-gray-500">
            API {bootstrap?.versions?.api ?? apiVersion}
            <span className="mx-1">·</span>
            Schema {bootstrap?.schema_version ?? schemaVersion}
          </span>

          <div className="flex items-center gap-1">
            <button
              className={`p-1.5 rounded hover:bg-gray-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors ${
                autoRefresh ? 'text-sky-600 dark:text-sky-400' : 'text-gray-400'
              }`}
              onClick={() => setAutoRefresh((v) => !v)}
              title={autoRefresh ? 'Auto-Refresh aktiv (30s)' : 'Auto-Refresh deaktiviert'}
            >
              <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
            </button>

            <button
              ref={dateToggleRef}
              className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
              onClick={() => {
                setShowDatePicker((s) => !s);
                if (!showDatePicker) setSystemInfoOpen(false);
              }}
              aria-label="Datum auswählen"
            >
              <CalendarDays className="w-4 h-4" />
            </button>

            <button
              className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
              onClick={() => {
                setSystemTab('overview');
                setSystemInfoOpen(true);
              }}
              aria-label="Systeminformationen"
            >
              <Info className="w-4 h-4" />
            </button>
          </div>

          <Clock />
        </div>
      </div>

      {/* DatePicker Popup */}
      {showDatePicker && (
        <div
          ref={datePickerRef}
          className="fixed right-4 bottom-16 z-50 w-[min(520px,95%)] max-w-full rounded-xl border border-gray-200 bg-white p-5 shadow-xl dark:border-gray-700 dark:bg-slate-800"
        >
          <DatePickerPopup
            initialDate={selectedDate ?? new Date()}
            setSelectedDate={setSelectedDate}
            onSelect={(d) => {
              setSelectedDate(d);
              setShowDatePicker(false);
            }}
            onCancel={() => setShowDatePicker(false)}
            saveSelectionsEnabled={saveSelectionsEnabled}
            autoRefresh={autoRefresh}
            setAutoRefresh={setAutoRefresh}
            setSystemTab={setSystemTab}
            bootstrap={bootstrap}
            configRevision={configRevision}
            modelsCount={modelsCount}
            toolsCount={toolsCount}
          />
        </div>
      )}

      {/* Systeminfo Panel */}
      {systemInfoOpen && (
        <div
          ref={systemInfoRef}
          className="fixed right-4 bottom-16 z-50 w-[min(720px,95%)] max-w-full rounded-xl border border-gray-200 bg-white p-5 shadow-xl dark:border-gray-700 dark:bg-slate-800"
        >
          <SystemInfoPanel
            appName={appName}
            appVersion={appVersion}
            bootstrap={bootstrap}
            setBootstrap={setBootstrap}
            online={online}
            setOnline={setOnline}
            error={error}
            setError={setError}
            lastChecked={lastChecked}
            setLastChecked={setLastChecked}
            requestId={requestId}
            setRequestId={setRequestId}
            configRevision={configRevision}
            modelsCount={modelsCount}
            toolsCount={toolsCount}
            friendlyCaps={friendlyCaps}
            systemTab={systemTab}
            setSystemTab={setSystemTab}
            onClose={() => setSystemInfoOpen(false)}
            isRefreshing={isRefreshing}
            setIsRefreshing={setIsRefreshing}
            autoRefresh={autoRefresh}
            setAutoRefresh={setAutoRefresh}
            apiVersion={apiVersion}
            schemaVersion={schemaVersion}
          />
        </div>
      )}
    </footer>
  );
}

// ------------------------------------------------------------
// Hilfskomponenten
// ------------------------------------------------------------

function Clock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  const formatted = useMemo(
    () =>
      new Intl.DateTimeFormat('de-DE', {
        weekday: 'short',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }).format(now),
    [now]
  );
  return (
    <span className="font-mono text-xs text-gray-500 dark:text-gray-400 w-44 text-right" aria-live="polite">
      {formatted}
    </span>
  );
}

/** DatePicker-Popup (unverändert, aber ich füge es der Vollständigkeit halber ein) */
function DatePickerPopup({
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
  saveSelectionsEnabled?: boolean;
  autoRefresh?: boolean;
  setAutoRefresh?: React.Dispatch<React.SetStateAction<boolean>>;
  setSystemTab?: (t: 'overview' | 'functions' | 'versions' | 'technical') => void;
  bootstrap?: BootstrapResponse | null;
  configRevision?: number;
  modelsCount?: number | null;
  toolsCount?: number | null;
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
  const today = new Date();
  const todayDate = today.getDate();
  const todayMonth = today.getMonth();
  const todayYear = today.getFullYear();

  function daysInMonth(y: number, m: number) {
    return new Date(y, m + 1, 0).getDate();
  }
  function startWeekday(y: number, m: number) {
    return new Date(y, m, 1).getDay();
  }

  const total = daysInMonth(year, month);
  const start = startWeekday(year, month);
  const days: (number | null)[] = [];
  for (let i = 0; i < start; i++) days.push(null);
  for (let d = 1; d <= total; d++) days.push(d);

  function pick(day: number) {
    const [hh, mm] = time.split(':').map((s) => parseInt(s, 10) || 0);
    const chosen = new Date(year, month, day, hh, mm);
    setSelectedDay(day);
    setSelectedDate(chosen);
    onSelect(chosen);
    if (saveSelectionsEnabled) {
      sendSelectedDateIfOptIn(chosen).catch(() => {});
    }
  }

  function onKey(e: React.KeyboardEvent) {
    if (!selectedDay) return;
    let d = selectedDay;
    if (e.key === 'ArrowLeft') d = Math.max(1, d - 1);
    else if (e.key === 'ArrowRight') d = Math.min(total, d + 1);
    else if (e.key === 'ArrowUp') d = Math.max(1, d - 7);
    else if (e.key === 'ArrowDown') d = Math.min(total, d + 7);
    else if (e.key === 'Enter') { pick(d); return; }
    else if (e.key === 'Escape') { onCancel(); return; }
    if (d !== selectedDay) {
      setSelectedDay(d);
      if (d <= 0) setViewDate(new Date(year, month - 1, 1));
    }
  }

  return (
    <div className="text-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <button
            className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded focus:outline-none focus:ring-2 focus:ring-sky-500"
            onClick={() => setViewDate(new Date(year, month - 1, 1))}
          >
            ◀
          </button>
          <strong className="text-base">
            {viewDate.toLocaleString('de-DE', { month: 'long', year: 'numeric' })}
          </strong>
          <button
            className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded focus:outline-none focus:ring-2 focus:ring-sky-500"
            onClick={() => setViewDate(new Date(year, month + 1, 1))}
          >
            ▶
          </button>
        </div>
        <button className="text-sm text-gray-500 hover:underline" onClick={onCancel}>
          Abbrechen
        </button>
      </div>

      <div
        className="grid grid-cols-7 gap-1 text-center text-xs focus:outline-none"
        tabIndex={0}
        onKeyDown={onKey}
        role="grid"
      >
        {['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'].map((w) => (
          <div key={w} className="font-medium text-gray-500 dark:text-gray-400 py-1">
            {w}
          </div>
        ))}
        {days.map((d, i) => {
          const isToday =
            d !== null && year === todayYear && month === todayMonth && d === todayDate;
          const isSelected = d !== null && selectedDay === d;
          return (
            <div key={i} className="py-1">
              {d !== null ? (
                <button
                  onClick={() => pick(d)}
                  className={`w-full h-8 rounded-full flex items-center justify-center text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 ${
                    isSelected
                      ? 'bg-sky-600 text-white hover:bg-sky-700'
                      : isToday
                      ? 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300 hover:bg-sky-200'
                      : 'hover:bg-gray-100 dark:hover:bg-slate-700'
                  }`}
                >
                  {d}
                </button>
              ) : (
                <span className="w-full h-8 block" />
              )}
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-3 mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <ClockIcon className="w-4 h-4 text-gray-400" />
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="rounded border border-gray-300 dark:border-gray-600 bg-transparent px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <button
            className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full transition-colors ${
              autoRefresh
                ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
            }`}
            onClick={() => setAutoRefresh?.((v) => !v)}
          >
            <RefreshCw className={`w-3 h-3 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
            {autoRefresh ? 'Auto ein' : 'Auto aus'}
          </button>

          <button
            className="hidden md:flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-700"
            onClick={() => setSystemTab?.('versions')}
          >
            <Layers className="w-3 h-3" />
            Konf {bootstrap?.config_revision ?? configRevision}
          </button>

          <div className="hidden md:flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3" />
              <span className="text-gray-500">Modelle</span>
              <span className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                {modelsCount ?? '—'}
              </span>
            </span>
            <span className="flex items-center gap-1">
              <FolderTree className="w-3 h-3" />
              <span className="text-gray-500">Werkzeuge</span>
              <span className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                {toolsCount ?? '—'}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Systeminfo-Panel – nun mit allen benötigten Props */
function SystemInfoPanel({
  appName,
  appVersion,
  bootstrap,
  setBootstrap,
  online,
  setOnline,
  error,
  setError,
  lastChecked,
  setLastChecked,
  requestId,
  setRequestId,
  configRevision,
  modelsCount,
  toolsCount,
  friendlyCaps,
  systemTab,
  setSystemTab,
  onClose,
  isRefreshing,
  setIsRefreshing,
  autoRefresh,
  setAutoRefresh,
  apiVersion,
  schemaVersion,
}: {
  appName: string;
  appVersion: string;
  bootstrap: BootstrapResponse | null;
  setBootstrap: React.Dispatch<React.SetStateAction<BootstrapResponse | null>>;
  online: boolean | null;
  setOnline: React.Dispatch<React.SetStateAction<boolean | null>>;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  lastChecked: Date | null;
  setLastChecked: React.Dispatch<React.SetStateAction<Date | null>>;
  requestId: string | null;
  setRequestId: React.Dispatch<React.SetStateAction<string | null>>;
  configRevision: number;
  modelsCount: number | null;
  toolsCount: number | null;
  friendlyCaps: Array<{ title: string; ok: boolean | null; icon?: React.ReactNode }>;
  systemTab: 'overview' | 'functions' | 'versions' | 'technical';
  setSystemTab: (t: 'overview' | 'functions' | 'versions' | 'technical') => void;
  onClose: () => void;
  isRefreshing: boolean;
  setIsRefreshing: React.Dispatch<React.SetStateAction<boolean>>;
  autoRefresh: boolean;
  setAutoRefresh: React.Dispatch<React.SetStateAction<boolean>>;
  apiVersion: string;
  schemaVersion: string;
}) {
  const caps = (bootstrap?.capabilities ?? bootstrap?.features ?? {}) as Record<string, any>;

  const refreshStatus = async () => {
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
  };

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Systeminformationen
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400">
            {lastChecked
              ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(lastChecked)
              : new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(new Date())}
          </span>
          <button
            className="p-1 hover:bg-gray-100 dark:hover:bg-slate-700 rounded focus:outline-none focus:ring-2 focus:ring-sky-500"
            onClick={onClose}
            aria-label="Schließen"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        <nav className="md:w-40">
          <ul className="space-y-1 text-sm">
            {(['overview', 'functions', 'versions', 'technical'] as const).map((tab) => {
              const icons = {
                overview: <Globe className="w-4 h-4" />,
                functions: <Zap className="w-4 h-4" />,
                versions: <Layers className="w-4 h-4" />,
                technical: <Server className="w-4 h-4" />,
              };
              const labels = {
                overview: 'Übersicht',
                functions: 'Funktionen',
                versions: 'Versionen',
                technical: 'Technik',
              };
              return (
                <li key={tab}>
                  <button
                    className={`flex items-center gap-2 w-full text-left px-3 py-2 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 ${
                      systemTab === tab
                        ? 'bg-sky-50 text-sky-700 dark:bg-sky-900/30 dark:text-sky-300'
                        : 'hover:bg-gray-100 dark:hover:bg-slate-800'
                    }`}
                    onClick={() => setSystemTab(tab)}
                  >
                    {icons[tab]}
                    {labels[tab]}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="flex-1 min-w-0">
          {systemTab === 'overview' && (
            <div>
              <h3 className="font-semibold text-lg">{appName}</h3>
              <p className="text-sm text-gray-500">Version {appVersion}</p>
              <p className="text-sm text-gray-500 mt-1">Lokale Chat- und Assistenzplattform</p>

              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="font-medium flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Dienste
                  </div>
                  <ul className="mt-2 space-y-1 text-sm">
                    <li className="flex justify-between">
                      <span>Backend</span>
                      <span className={online ? 'text-emerald-600' : online === false ? 'text-red-500' : 'text-gray-500'}>
                        {online ? 'Online' : online === false ? 'Nicht erreichbar' : 'Unbekannt'}
                      </span>
                    </li>
                    <li className="flex justify-between">
                      <span>Authentifizierung</span>
                      <span>{bootstrap?.authenticated ? 'Aktiv' : 'Nicht aktiv'}</span>
                    </li>
                    <li className="flex justify-between">
                      <span>Live-Chat</span>
                      <span>{caps.chat_streaming ? 'Verfügbar' : 'Nicht verfügbar'}</span>
                    </li>
                    <li className="flex justify-between">
                      <span>Modelle</span>
                      <span>{caps.model_service ? 'Verfügbar' : 'Nicht verfügbar'}</span>
                    </li>
                  </ul>
                </div>

                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                  <div className="font-medium flex items-center gap-2">
                    <Layers className="w-4 h-4" />
                    Konfiguration
                  </div>
                  <div className="mt-2 text-sm">
                    <div className="flex justify-between">
                      <span>Status</span>
                      <span>{bootstrap?.config_revision ? 'Aktuell' : 'Unbekannt'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Revision</span>
                      <span>{bootstrap?.config_revision ?? configRevision}</span>
                    </div>
                  </div>
                  <button
                    className="mt-3 text-xs px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    onClick={() => setSystemTab('versions')}
                  >
                    Details anzeigen
                  </button>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className="flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-sky-600 text-white hover:bg-sky-700 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500"
                  onClick={refreshStatus}
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Aktualisiere...' : 'Status neu prüfen'}
                </button>
                <button
                  className={`flex items-center gap-1 text-sm px-4 py-2 rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-sky-500 ${
                    autoRefresh
                      ? 'border-sky-300 bg-sky-50 text-sky-700 dark:bg-sky-900/20 dark:text-sky-300'
                      : 'border-gray-300 bg-white text-gray-700 dark:border-gray-600 dark:bg-slate-800 dark:text-gray-300'
                  }`}
                  onClick={() => setAutoRefresh((v) => !v)}
                >
                  <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
                  {autoRefresh ? 'Auto-Refresh ein' : 'Auto-Refresh aus'}
                </button>
              </div>
            </div>
          )}

          {systemTab === 'functions' && (
            <div>
              <h3 className="font-semibold text-lg">Funktionen</h3>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                {friendlyCaps.map((c) => {
                  const count =
                    c.title === 'KI-Modelle' ? modelsCount : c.title === 'Werkzeuge' ? toolsCount : null;
                  return (
                    <div
                      key={c.title}
                      className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-gray-700 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-gray-500">{c.icon}</div>
                        <div>
                          <div className="font-medium">
                            {c.title}
                            {count !== null && (
                              <span className="ml-2 text-xs text-gray-400">({count})</span>
                            )}
                          </div>
                          <div className="text-xs text-gray-400">
                            {c.ok === true ? 'Verfügbar' : c.ok === false ? 'Nicht aktiviert' : 'Unbekannt'}
                          </div>
                        </div>
                      </div>
                      {c.ok === true ? (
                        <CheckCircle className="w-5 h-5 text-emerald-500" />
                      ) : c.ok === false ? (
                        <XCircle className="w-5 h-5 text-gray-300" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {systemTab === 'versions' && (
            <div>
              <h3 className="font-semibold text-lg">Schnittstellen & Versionen</h3>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex justify-between">
                  <span className="text-gray-500">API</span>
                  <span className="font-mono">{bootstrap?.versions?.api ?? apiVersion}</span>
                </div>
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex justify-between">
                  <span className="text-gray-500">Schema</span>
                  <span className="font-mono">{bootstrap?.schema_version ?? schemaVersion}</span>
                </div>
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex justify-between">
                  <span className="text-gray-500">UI Schema</span>
                  <span className="font-mono">{bootstrap?.ui_schema ?? 'n/a'}</span>
                </div>
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex justify-between">
                  <span className="text-gray-500">Bootstrap Schema</span>
                  <span className="font-mono">{bootstrap?.bootstrap_schema ?? 'n/a'}</span>
                </div>
              </div>
            </div>
          )}

              {systemTab === 'technical' && (
            <div>
              <h3 className="font-semibold text-lg">Technische Details</h3>
              <div className="mt-2 text-xs">
                <div className="flex flex-wrap gap-4 text-gray-500 mb-3">
                  <span>Request ID: {requestId ?? '—'}</span>
                  <span>Letzte Prüfung: {lastChecked ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(lastChecked) : '—'}</span>
                  {error && <span className="text-red-500">Fehler: {error}</span>}
                      <button
                        className="text-xs px-2 py-1 rounded bg-gray-100"
                        onClick={() => setChatHistoryOpen(true)}
                      >Chat-Historie</button>
                </div>
                <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 max-h-64 overflow-auto bg-gray-50 dark:bg-slate-900/50">
                  <pre className="whitespace-pre-wrap break-all">
                    {JSON.stringify(bootstrap ?? { online, error, versions: (bootstrap as BootstrapResponse | null)?.versions }, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
              {chatHistoryOpen ? (
                <ChatHistoryPanel onClose={() => setChatHistoryOpen(false)} />
              ) : null}
        </div>
      </div>
    </>
  );
}