// F:\Kernschmied\frontend\src\components\layout\AppFooter.tsx

import React, { useEffect, useMemo, useState } from 'react';
import type { BootstrapResponse } from '../../types/bootstrap';
import FooterCalendar from '../calendar/FooterCalendar';
import { createEvent } from '../../api/fetchCalendarClient';
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

  useEffect(() => {
    // calendar listing is now handled by FooterCalendar component
    return undefined;
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

  return (
    <footer className="z-30 shrink-0 border-t border-border bg-white/90 backdrop-blur-md dark:border-white/10 dark:bg-slate-950/90">
      <div className="flex h-10 items-center justify-between gap-6 overflow-x-auto px-4 text-xs text-text-muted dark:text-gray-400">
        {/* Linke Seite */}

        <div className="flex shrink-0 items-center gap-5">
          <StatusItem
            onClick={() =>
              openDetail(
                'Application',
                bootstrap?.application ?? { name: 'Kernschmied', version: applicationVersion },
              )
            }
          >
            <strong className="font-semibold text-text dark:text-white">
              {bootstrap?.application?.name ?? 'Kernschmied'}{' '}
              {bootstrap?.application?.version ?? applicationVersion}
            </strong>
          </StatusItem>

          <StatusItem
            onClick={() =>
              openDetail('Environment', { environment: bootstrap?.environment ?? environment })
            }
          >
            {bootstrap?.environment ?? environment}
          </StatusItem>

          <StatusItem
            icon={<Server size={14} />}
            onClick={() => openDetail('API', bootstrap?.versions ?? { api: apiVersion })}
          >
            API {bootstrap?.versions?.api ?? apiVersion}
          </StatusItem>

          {(bootstrap?.schema_version ?? schemaVersion) && (
            <StatusItem
              icon={<FolderTree size={14} />}
              onClick={() =>
                openDetail('Schema', { schema: bootstrap?.schema_version ?? schemaVersion })
              }
            >
              Schema {bootstrap?.schema_version ?? schemaVersion}
            </StatusItem>
          )}
        </div>

        {/* Mitte */}

        <div className="flex shrink-0 items-center gap-5">
          <StatusItem
            icon={<Database size={14} />}
            onClick={() =>
              openDetail('Config', {
                config_revision: bootstrap?.config_revision ?? configRevision,
                endpoints: bootstrap?.endpoints ?? null,
              })
            }
          >
            Config {bootstrap?.config_revision ?? configRevision}
          </StatusItem>

          <StatusItem
            icon={<Database size={14} />}
            onClick={async () => {
              setLoadingDetail(true);
              try {
                const r = await fetch('/api/v1/models', { cache: 'no-store' });
                const data = await r.json();
                openDetail('Models', data);
              } catch (e) {
                openDetail('Models', { error: String(e) });
              } finally {
                setLoadingDetail(false);
              }
            }}
          >
            Models {bootstrap?.revisions?.model_registry ?? modelRevision}
          </StatusItem>

          <StatusItem
            icon={<Plug size={14} />}
            onClick={async () => {
              setLoadingDetail(true);
              try {
                const r = await fetch('/api/v1/tools', { cache: 'no-store' });
                const data = await r.json();
                openDetail('Tools', data);
              } catch (e) {
                openDetail('Tools', { error: String(e) });
              } finally {
                setLoadingDetail(false);
              }
            }}
          >
            Tools {bootstrap?.revisions?.tool_registry ?? toolRevision}
          </StatusItem>

          <StatusItem
            icon={<Wifi size={14} />}
            onClick={() => openDetail('Health', { online, error, bootstrap })}
          >
            <span className={online ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500'}>
              ●
            </span>

            {online ? ' Backend online' : ' Backend offline'}

            {error ? <span className="ml-2 text-xs text-red-500">({error})</span> : null}
          </StatusItem>
        </div>

        {/* Rechte Seite */}

        <div className="flex shrink-0 items-center gap-2 font-medium relative">
          <button
            type="button"
            className="p-1"
            onClick={() => setShowDatePicker((s) => !s)}
            aria-label="Datum wählen"
            aria-expanded={showDatePicker}
          >
            <CalendarDays size={14} className="text-text-muted dark:text-gray-400" />
          </button>

          <Clock />

          {showDatePicker && (
            <div
              role="dialog"
              aria-modal="false"
              className="fixed right-4 bottom-16 z-50 w-72 max-w-full rounded border bg-white p-2 shadow dark:bg-slate-800"
            >
              <FooterCalendar
                initialDate={new Date()}
                targetCalendarId={targetCalendarId}
                setTargetCalendarId={setTargetCalendarId}
                onCancel={() => setShowDatePicker(false)}
                onSelect={(d) => {
                  setShowDatePicker(false);
                  setSelectedDate(d);
                  if (targetCalendarId) {
                    setEventModalOpen(true);
                    setEventTitle('');
                  } else {
                    openDetail('Ausgewähltes Datum', { selected: d.toISOString() });
                  }
                }}
              />
            </div>
          )}
        </div>
      </div>
      {detailOpen && (
        <div className="absolute right-4 bottom-12 z-50 w-80 max-w-full rounded border bg-white p-3 shadow dark:bg-slate-800">
          <div className="flex items-center justify-between">
            <strong>{detailTitle}</strong>
            <div className="flex items-center gap-2">
              {detailContent && (
                <button
                  className="text-sm text-gray-600 hover:text-black"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(detailContent);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 1500);
                    } catch {}
                  }}
                >
                  {copied ? 'Copied' : 'Copy'}
                </button>
              )}

              <button className="text-sm text-gray-500" onClick={closeDetail}>
                ✕
              </button>
            </div>
          </div>

          <pre className="mt-2 max-h-64 overflow-auto text-xs whitespace-pre-wrap">
            {detailContent}
          </pre>
        </div>
      )}

      {eventModalOpen && selectedDate && (
        <div className="absolute right-4 bottom-28 z-50 w-80 max-w-full rounded border bg-white p-3 shadow dark:bg-slate-800">
          <div className="flex items-center justify-between">
            <strong>Neues Ereignis</strong>
            <button className="text-sm text-gray-500" onClick={() => setEventModalOpen(false)}>
              ✕
            </button>
          </div>

          <div className="mt-2">
            <label className="text-xs">Titel</label>
            <input
              className="w-full rounded border px-2 py-1 text-sm"
              value={eventTitle}
              onChange={(e) => setEventTitle(e.target.value)}
            />
            <div className="mt-2 flex justify-end gap-2">
              <button
                className="rounded bg-gray-200 px-3 py-1 text-sm"
                onClick={() => setEventModalOpen(false)}
              >
                Abbrechen
              </button>
              <button
                className="rounded bg-sky-600 px-3 py-1 text-sm text-white"
                onClick={async () => {
                  if (!targetCalendarId) return;
                  const body = {
                    title: eventTitle || 'Neues Ereignis',
                    description: '',
                    start: selectedDate.toISOString(),
                    end: new Date(selectedDate.getTime() + 60 * 60 * 1000).toISOString(),
                    all_day: false,
                  };

                  try {
                    const data = await createEvent(targetCalendarId, body as any);
                    openDetail('Ereignis erstellt', data);
                  } catch (e: any) {
                    openDetail('Fehler beim Erstellen', { error: String(e) });
                  } finally {
                    setEventModalOpen(false);
                  }
                }}
              >
                Erstellen
              </button>
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
}: {
  initialDate: Date;
  setSelectedDate: (d: Date) => void;
  onSelect: (d: Date) => void;
  onCancel: () => void;
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
    // send to backend (prepared endpoint). ignore errors silently.
    sendSelectedDate(chosen).catch(() => {});
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

      <div className="mt-2 flex items-center gap-2">
        <input
          className="flex-1 rounded border px-2 py-1"
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />
        <button
          className="rounded bg-sky-600 px-3 py-1 text-white"
          onClick={() => {
            // if no specific day chosen, pick today
            const d = selectedDay ?? initialDate.getDate();
            pick(d);
          }}
        >
          OK
        </button>
      </div>
    </div>
  );
}

async function sendSelectedDate(date: Date) {
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
