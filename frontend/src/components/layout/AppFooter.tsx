// F:\Kernschmied\frontend\src\components\layout\AppFooter.tsx

import React, { useEffect, useMemo, useState } from 'react';
import type { AppBootstrap } from '../../types/bootstrap';
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
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import IconBadge from '../common/IconBadge';
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
  const [bootstrap, setBootstrap] = useState<any | null>(null);
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
        const data = (await res.json()) as any;
        setBootstrap(data);
        setOnline(true);
        setLastChecked(new Date());
        setRequestId((data as any)?.request_id ?? res.headers.get('X-Request-Id'));
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
    <footer className="z-30 shrink-0 border-t border-border bg-white/80 backdrop-blur-md dark:border-white/10 dark:bg-slate-950/90 shadow-sm">
      <div className="flex h-12 items-center justify-between gap-3 px-4 text-sm text-text-soft dark:text-gray-300">
        {/* Linker Bereich */}
        <div className="flex items-center gap-3">
          <button
            ref={systemTriggerRef}
            className="flex items-center gap-2 rounded px-1 py-0.5 hover:underline focus:outline-none focus:ring-2 focus:ring-primary"
            onClick={() => {
              setSystemTab('overview');
              setSystemInfoOpen(true);
            }}
            aria-label="Systeminformationen öffnen"
          >
            <span className="font-semibold text-text dark:text-white">{appName}</span>
            <span className="rounded bg-surface-muted px-1.5 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              v{appVersion}
            </span>
          </button>

          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${envColor}`}>
            <Globe className="h-3 w-3" />
            {envLabel}
          </span>

          <div className="flex items-center gap-1.5">
            <StatusIcon className={`h-4 w-4 ${statusColor}`} />
            <button
              className="rounded px-1 text-xs hover:underline focus:outline-none focus:ring-2 focus:ring-primary"
              onClick={() => setSystemInfoOpen(true)}
            >
              {statusLabel}
            </button>
            {error && <span className="ml-1 text-xs text-danger" title={error}>⚠</span>}
          </div>
        </div>

        {/* Rechter Bereich */}
        <div className="flex items-center gap-3 flex-1 justify-end">
          <span className="hidden text-xs text-text-muted dark:text-gray-500 sm:inline">
            API {bootstrap?.versions?.api ?? apiVersion}
            <span className="mx-1">·</span>
            Schema {bootstrap?.schema_version ?? schemaVersion}
          </span>

          <div className="flex items-center gap-1">
            <button
              className={`rounded-lg p-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                autoRefresh
                  ? 'text-primary dark:text-primary'
                  : 'text-text-muted hover:bg-surface-hover hover:text-text dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white'
              }`}
              onClick={() => setAutoRefresh((v) => !v)}
              title={autoRefresh ? 'Auto-Refresh aktiv (30s)' : 'Auto-Refresh deaktiviert'}
              aria-label={autoRefresh ? 'Auto-Refresh deaktivieren' : 'Auto-Refresh aktivieren'}
            >
              <IconBadge
                icon={<RefreshCw className={autoRefresh ? 'animate-spin-slow' : ''} />}
                size="sm"
                variant={autoRefresh ? 'primary' : 'default'}
              />
            </button>

            <button
              ref={dateToggleRef}
              className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-hover hover:text-text focus:outline-none focus:ring-2 focus:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
              onClick={() => {
                setShowDatePicker((s) => !s);
                if (!showDatePicker) setSystemInfoOpen(false);
              }}
              aria-label="Datum auswählen"
              title="Datum auswählen"
            >
              <IconBadge icon={<CalendarDays />} size="sm" variant="default" />
            </button>

            <button
              className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-hover hover:text-text focus:outline-none focus:ring-2 focus:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
              onClick={() => {
                setSystemTab('overview');
                setSystemInfoOpen(true);
              }}
              aria-label="Systeminformationen"
              title="Systeminformationen"
            >
              <IconBadge icon={<Info />} size="sm" variant="default" />
            </button>
          </div>

          <Clock />
        </div>
      </div>

      {/* DatePicker Popup */}
      {showDatePicker && (
        <div
          ref={datePickerRef}
          className="fixed right-4 bottom-16 z-50 w-[min(520px,95%)] max-w-full rounded-xl border border-border-soft bg-white p-5 shadow-xl dark:border-white/10 dark:bg-slate-800"
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
          className="fixed right-4 bottom-16 z-50 w-[min(720px,95%)] max-w-full rounded-xl border border-border-soft bg-white p-5 shadow-xl dark:border-white/10 dark:bg-slate-800"
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
            chatHistoryOpen={chatHistoryOpen}
            setChatHistoryOpen={setChatHistoryOpen}
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
    <span className="flex items-center gap-1.5 font-mono text-xs text-text-muted dark:text-gray-400 w-44 text-right" aria-live="polite">
      <IconBadge icon={<ClockIcon />} size="sm" variant="default" />
      {formatted}
    </span>
  );
}

/** DatePicker-Popup (verbessert) */
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
  bootstrap?: any | null;
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
            className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-hover hover:text-text focus:outline-none focus:ring-2 focus:ring-primary dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
            onClick={() => setViewDate(new Date(year, month - 1, 1))}
            aria-label="Vorheriger Monat"
          >
            <IconBadge icon={<ChevronLeft />} size="sm" variant="default" />
          </button>
          <strong className="text-base text-text dark:text-white">
            {viewDate.toLocaleString('de-DE', { month: 'long', year: 'numeric' })}
          </strong>
          <button
            className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-hover hover:text-text focus:outline-none focus:ring-2 focus:ring-primary dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
            onClick={() => setViewDate(new Date(year, month + 1, 1))}
            aria-label="Nächster Monat"
          >
            <IconBadge icon={<ChevronRight />} size="sm" variant="default" />
          </button>
        </div>
        <button
          className="rounded-lg px-3 py-1.5 text-sm text-text-muted transition-colors hover:bg-surface-hover hover:text-text focus:outline-none focus:ring-2 focus:ring-primary dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
          onClick={onCancel}
        >
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
          <div key={w} className="py-1 font-medium text-text-muted dark:text-gray-400">
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
                  className={`h-8 w-full rounded-full flex items-center justify-center text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                    isSelected
                      ? 'bg-primary text-white hover:bg-primary-hover'
                      : isToday
                      ? 'bg-primary-soft text-primary hover:bg-primary/20 dark:bg-primary/20 dark:text-primary'
                      : 'hover:bg-surface-hover dark:hover:bg-slate-700'
                  }`}
                >
                  {d}
                </button>
              ) : (
                <span className="block h-8 w-full" />
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border-soft pt-3 dark:border-white/10">
        <div className="flex items-center gap-2">
          <IconBadge icon={<ClockIcon />} size="sm" variant="default" />
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="rounded-lg border border-border-soft bg-transparent px-2 py-1 text-sm text-text outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:text-white"
          />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button
            className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs transition-colors ${
              autoRefresh
                ? 'bg-primary-soft text-primary dark:bg-primary/20 dark:text-primary'
                : 'bg-surface-muted text-text-muted dark:bg-slate-700 dark:text-gray-400'
            }`}
            onClick={() => setAutoRefresh?.((v) => !v)}
            aria-label={autoRefresh ? 'Auto-Refresh deaktivieren' : 'Auto-Refresh aktivieren'}
          >
            <RefreshCw className={`h-3 w-3 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
            {autoRefresh ? 'Auto ein' : 'Auto aus'}
          </button>

          <button
            className="hidden items-center gap-1 rounded-full bg-surface-muted px-2 py-1 text-xs text-text-muted dark:bg-slate-700 dark:text-gray-400 md:flex"
            onClick={() => setSystemTab?.('versions')}
          >
            <Layers className="h-3 w-3" />
            Konf {bootstrap?.config_revision ?? configRevision}
          </button>

          <div className="hidden items-center gap-3 text-xs text-text-muted dark:text-gray-400 md:flex">
            <span className="flex items-center gap-1">
              <Cpu className="h-3 w-3" />
              <span>Modelle</span>
              <span className="rounded bg-surface-muted px-1.5 py-0.5 dark:bg-slate-700">
                {modelsCount ?? '—'}
              </span>
            </span>
            <span className="flex items-center gap-1">
              <FolderTree className="h-3 w-3" />
              <span>Werkzeuge</span>
              <span className="rounded bg-surface-muted px-1.5 py-0.5 dark:bg-slate-700">
                {toolsCount ?? '—'}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Systeminfo-Panel (verbessert) */
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
  chatHistoryOpen,
  setChatHistoryOpen,
}: {
  appName: string;
  appVersion: string;
  bootstrap: any | null;
  setBootstrap: React.Dispatch<React.SetStateAction<any | null>>;
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
  chatHistoryOpen?: boolean;
  setChatHistoryOpen?: React.Dispatch<React.SetStateAction<boolean>>;
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
        <h2 className="flex items-center gap-2 text-lg font-semibold text-text dark:text-white">
          <IconBadge icon={<Settings />} size="md" variant="primary" />
          Systeminformationen
        </h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-text-muted dark:text-gray-400">
            {lastChecked
              ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(lastChecked)
              : new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(new Date())}
          </span>
          <button
            className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-hover hover:text-text focus:outline-none focus:ring-2 focus:ring-primary dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
            onClick={onClose}
            aria-label="Schließen"
            title="Schließen"
          >
            <IconBadge icon={<X />} size="sm" variant="default" />
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-4 md:flex-row">
        <nav className="md:w-40">
          <ul className="space-y-1 text-sm">
            {(['overview', 'functions', 'versions', 'technical'] as const).map((tab) => {
              const icons = {
                overview: <Globe />,
                functions: <Zap />,
                versions: <Layers />,
                technical: <Server />,
              };
              const labels = {
                overview: 'Übersicht',
                functions: 'Funktionen',
                versions: 'Versionen',
                technical: 'Technik',
              };
              const isActive = systemTab === tab;
              return (
                <li key={tab}>
                  <button
                    className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                      isActive
                        ? 'bg-primary-soft text-primary dark:bg-primary/20 dark:text-primary'
                        : 'text-text-soft hover:bg-surface-hover dark:text-gray-300 dark:hover:bg-slate-800'
                    }`}
                    onClick={() => setSystemTab(tab)}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <IconBadge icon={icons[tab]} size="sm" variant={isActive ? 'primary' : 'default'} />
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
              <h3 className="text-lg font-semibold text-text dark:text-white">{appName}</h3>
              <p className="text-sm text-text-muted">Version {appVersion}</p>
              <p className="mt-1 text-sm text-text-muted">Lokale Chat- und Assistenzplattform</p>

              <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-border-soft p-4 dark:border-white/10">
                  <div className="flex items-center gap-2 font-medium text-text dark:text-white">
                    <Server className="h-4 w-4" />
                    Dienste
                  </div>
                  <ul className="mt-2 space-y-1 text-sm text-text-soft dark:text-gray-300">
                    <li className="flex justify-between">
                      <span>Backend</span>
                      <span className={online ? 'text-success' : online === false ? 'text-danger' : 'text-text-muted'}>
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

                <div className="rounded-lg border border-border-soft p-4 dark:border-white/10">
                  <div className="flex items-center gap-2 font-medium text-text dark:text-white">
                    <Layers className="h-4 w-4" />
                    Konfiguration
                  </div>
                  <div className="mt-2 text-sm text-text-soft dark:text-gray-300">
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
                    className="mt-3 rounded-full bg-surface-muted px-3 py-1 text-xs text-text-muted transition-colors hover:bg-surface-hover dark:bg-slate-700 dark:hover:bg-slate-600"
                    onClick={() => setSystemTab('versions')}
                  >
                    Details anzeigen
                  </button>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                  onClick={refreshStatus}
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Aktualisiere...' : 'Status neu prüfen'}
                </button>
                <button
                  className={`flex items-center gap-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary ${
                    autoRefresh
                      ? 'border-primary-soft bg-primary-soft text-primary dark:border-primary/30 dark:bg-primary/20 dark:text-primary'
                      : 'border-border-soft bg-white text-text-soft hover:bg-surface-hover dark:border-white/10 dark:bg-slate-800 dark:text-gray-300 dark:hover:bg-slate-700'
                  }`}
                  onClick={() => setAutoRefresh((v) => !v)}
                >
                  <RefreshCw className={`h-4 w-4 ${autoRefresh ? 'animate-spin-slow' : ''}`} />
                  {autoRefresh ? 'Auto-Refresh ein' : 'Auto-Refresh aus'}
                </button>
              </div>
            </div>
          )}

          {systemTab === 'functions' && (
            <div>
              <h3 className="text-lg font-semibold text-text dark:text-white">Funktionen</h3>
              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                {friendlyCaps.map((c) => {
                  const count =
                    c.title === 'KI-Modelle' ? modelsCount : c.title === 'Werkzeuge' ? toolsCount : null;
                  return (
                    <div
                      key={c.title}
                      className="flex items-center justify-between rounded-lg border border-border-soft p-3 dark:border-white/10"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-text-muted">{c.icon}</div>
                        <div>
                          <div className="font-medium text-text dark:text-white">
                            {c.title}
                            {count !== null && (
                              <span className="ml-2 text-xs text-text-muted">({count})</span>
                            )}
                          </div>
                          <div className="text-xs text-text-muted">
                            {c.ok === true ? 'Verfügbar' : c.ok === false ? 'Nicht aktiviert' : 'Unbekannt'}
                          </div>
                        </div>
                      </div>
                      {c.ok === true ? (
                        <CheckCircle className="h-5 w-5 text-success" />
                      ) : c.ok === false ? (
                        <XCircle className="h-5 w-5 text-text-muted" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-text-muted" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {systemTab === 'versions' && (
            <div>
              <h3 className="text-lg font-semibold text-text dark:text-white">Schnittstellen & Versionen</h3>
              <div className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div className="flex justify-between rounded-lg border border-border-soft p-3 dark:border-white/10">
                  <span className="text-text-muted">API</span>
                  <span className="font-mono text-text dark:text-white">{bootstrap?.versions?.api ?? apiVersion}</span>
                </div>
                <div className="flex justify-between rounded-lg border border-border-soft p-3 dark:border-white/10">
                  <span className="text-text-muted">Schema</span>
                  <span className="font-mono text-text dark:text-white">{bootstrap?.schema_version ?? schemaVersion}</span>
                </div>
                <div className="flex justify-between rounded-lg border border-border-soft p-3 dark:border-white/10">
                  <span className="text-text-muted">UI Schema</span>
                  <span className="font-mono text-text dark:text-white">{bootstrap?.ui_schema ?? 'n/a'}</span>
                </div>
                <div className="flex justify-between rounded-lg border border-border-soft p-3 dark:border-white/10">
                  <span className="text-text-muted">Bootstrap Schema</span>
                  <span className="font-mono text-text dark:text-white">{bootstrap?.bootstrap_schema ?? 'n/a'}</span>
                </div>
              </div>
            </div>
          )}

          {systemTab === 'technical' && (
            <div>
              <h3 className="text-lg font-semibold text-text dark:text-white">Technische Details</h3>
              <div className="mt-2 text-xs">
                <div className="mb-3 flex flex-wrap gap-4 text-text-muted dark:text-gray-400">
                  <span>Request ID: {requestId ?? '—'}</span>
                  <span>Letzte Prüfung: {lastChecked ? new Intl.DateTimeFormat('de-DE', { dateStyle: 'short', timeStyle: 'short' }).format(lastChecked) : '—'}</span>
                  {error && <span className="text-danger">Fehler: {error}</span>}
                  <button
                    className="rounded bg-surface-muted px-2 py-1 text-xs text-text-muted transition-colors hover:bg-surface-hover dark:bg-slate-700 dark:hover:bg-slate-600"
                    onClick={() => setChatHistoryOpen?.(true)}
                  >
                    Chat-Historie
                  </button>
                </div>
                <div className="max-h-64 overflow-auto rounded-lg border border-border-soft bg-surface-muted p-3 dark:border-white/10 dark:bg-slate-900/50">
                  <pre className="whitespace-pre-wrap break-all text-text-soft dark:text-gray-300">
                    {JSON.stringify(bootstrap ?? { online, error, versions: (bootstrap as any | null)?.versions }, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
          {chatHistoryOpen && (
            <ChatHistoryPanel onClose={() => setChatHistoryOpen?.(false)} />
          )}
        </div>
      </div>
    </>
  );
}