// F:\Kernschmied\frontend\src\components\widgets\CalendarWidget.tsx

import React, { useEffect, useState, useMemo } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, RefreshCw, AlertCircle } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import { listCalendars, listEvents } from '../../api/fetchCalendarClient';
import type { components } from '../../api/openapi-types';

interface CalendarWidgetProps {
  widget: any;
  nodeId?: string;
  configuration?: Record<string, unknown> | null;
}

export default function CalendarWidget({ widget, nodeId }: CalendarWidgetProps) {
  const [events, setEvents] = useState<components['schemas']['EventOut'][]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewDate, setViewDate] = useState<Date>(new Date());

  const today = new Date();

  // Helper: Ersten und letzten Tag des Monats
  const monthStart = useMemo(() => {
    return new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
  }, [viewDate]);

  const monthEnd = useMemo(() => {
    return new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0);
  }, [viewDate]);

  // Events für den aktuellen Monat laden
  const loadEvents = async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    setError(null);

    try {
      const calendars = await listCalendars();
      if (!calendars || calendars.length === 0) {
        setEvents([]);
        return;
      }

      const startISO = monthStart.toISOString();
      const endISO = monthEnd.toISOString();

      const allEvents: components['schemas']['EventOut'][] = [];
      for (const cal of calendars) {
        const ev = await listEvents(cal.id, {
          time_min: startISO,
          time_max: endISO,
        });
        allEvents.push(...(ev || []));
      }
      setEvents(allEvents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Kalender konnte nicht geladen werden.');
      setEvents([]);
    } finally {
      if (showRefresh) setIsRefreshing(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    void loadEvents(false);
  }, [viewDate]);

  // Events für einen bestimmten Tag
  const getEventsForDay = (day: number) => {
    const date = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
    const dateStr = date.toDateString();
    return events.filter((e) => new Date(e.start).toDateString() === dateStr);
  };

  // Kalendergitter generieren
  const daysInMonth = monthEnd.getDate();
  const firstDayOfMonth = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1).getDay();
  // Anpassung: 0 = Sonntag, aber wir wollen Montag als ersten Tag
  const startOffset = firstDayOfMonth === 0 ? 6 : firstDayOfMonth - 1;

  const weekDays = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

  return (
    <div className="rounded-xl border border-border-soft bg-white/90 p-4 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/80">
      {/* Kopfzeile */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <IconBadge icon={<CalendarDays />} size="md" variant="primary" />
          <h3 className="text-sm font-semibold text-text dark:text-white">Kalender</h3>
          {events.length > 0 && (
            <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-text-muted dark:bg-slate-800 dark:text-gray-400">
              {events.length}
            </span>
          )}
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => void loadEvents(true)}
          disabled={isRefreshing}
          aria-label="Kalender neu laden"
          title="Neu laden"
        >
          <IconBadge icon={<RefreshCw className={isRefreshing ? 'animate-spin' : ''} />} size="sm" variant="default" />
        </button>
      </div>

      {/* Monatsnavigation */}
      <div className="flex items-center justify-between mb-2">
        <button
          type="button"
          className="rounded-lg p-1 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1))}
          aria-label="Vorheriger Monat"
        >
          <IconBadge icon={<ChevronLeft />} size="sm" variant="default" />
        </button>
        <span className="text-sm font-medium text-text dark:text-white">
          {viewDate.toLocaleString('de-DE', { month: 'long', year: 'numeric' })}
        </span>
        <button
          type="button"
          className="rounded-lg p-1 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
          onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1))}
          aria-label="Nächster Monat"
        >
          <IconBadge icon={<ChevronRight />} size="sm" variant="default" />
        </button>
      </div>

      {/* Kalendergitter */}
      {loading ? (
        <div className="flex items-center gap-2 py-4 text-sm text-text-muted dark:text-gray-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          Lade Kalender …
        </div>
      ) : error ? (
        <div className="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger-soft px-3 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : (
        <>
          {/* Wochentage */}
          <div className="grid grid-cols-7 gap-0.5 text-center text-xs mb-1">
            {weekDays.map((w) => (
              <div key={w} className="py-1 font-medium text-text-muted dark:text-gray-500">
                {w}
              </div>
            ))}
          </div>

          {/* Tage */}
          <div className="grid grid-cols-7 gap-0.5 text-center text-xs">
            {Array.from({ length: startOffset }).map((_, i) => (
              <div key={`empty-${i}`} className="py-1" />
            ))}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const date = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
              const isToday = date.toDateString() === today.toDateString();
              const dayEvents = getEventsForDay(day);
              const hasEvent = dayEvents.length > 0;

              return (
                <div
                  key={day}
                  className={[
                    'relative py-1 rounded-full text-xs transition-colors',
                    isToday
                      ? 'bg-primary text-white font-semibold'
                      : hasEvent
                        ? 'text-primary font-medium hover:bg-primary-soft dark:hover:bg-primary/20'
                        : 'text-text dark:text-gray-300 hover:bg-surface-hover dark:hover:bg-slate-800',
                  ].join(' ')}
                >
                  {day}
                  {hasEvent && !isToday && (
                    <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 h-1 w-1 rounded-full bg-primary" />
                  )}
                </div>
              );
            })}
          </div>

          {/* Ereignis‑Kurzliste (max. 3) */}
          {events.length > 0 && (
            <div className="mt-3 max-h-24 overflow-y-auto space-y-1 border-t border-border-soft pt-2 dark:border-white/10">
              {events.slice(0, 3).map((e) => (
                <div key={e.id} className="flex items-center gap-2 text-xs">
                  <span className="shrink-0 text-text-muted dark:text-gray-500">
                    {new Date(e.start).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="truncate text-text-soft dark:text-gray-300">{e.title}</span>
                  {e.all_day && (
                    <span className="shrink-0 rounded bg-surface-muted px-1.5 py-0.5 text-[10px] text-text-muted dark:bg-slate-800 dark:text-gray-500">
                      Ganztägig
                    </span>
                  )}
                </div>
              ))}
              {events.length > 3 && (
                <div className="text-xs text-text-muted dark:text-gray-500">
                  +{events.length - 3} weitere
                </div>
              )}
            </div>
          )}

          {/* Leerzustand (keine Events) */}
          {events.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-4 text-center">
              <IconBadge icon={<CalendarDays />} size="lg" variant="default" />
              <span className="text-sm text-text-muted dark:text-gray-400">Keine Ereignisse in diesem Monat.</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}