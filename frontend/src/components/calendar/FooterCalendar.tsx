// F:\Kernschmied\frontend\src\components\calendar\FooterCalendar.tsx

import React, { useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, X, Trash2, Save } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import type { components } from '../../api/openapi-types';
import {
  listCalendars,
  listEvents,
  selectDate as apiSelectDate,
  getEvent,
  patchEvent,
  deleteEvent,
} from '../../api/fetchCalendarClient';

export default function FooterCalendar({
  initialDate,
  targetCalendarId,
  setTargetCalendarId,
  onSelect,
  onCancel,
}: {
  initialDate: Date;
  targetCalendarId: string | null;
  setTargetCalendarId: (id: string | null) => void;
  onSelect: (d: Date) => void;
  onCancel: () => void;
}) {
  const [calendars, setCalendars] = useState<components['schemas']['CalendarOut'][]>([]);
  const [events, setEvents] = useState<components['schemas']['EventOut'][]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(initialDate);
  const [loadingCals, setLoadingCals] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [editingEvent, setEditingEvent] = useState<components['schemas']['EventOut'] | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoadingCals(true);
    setError(null);
    listCalendars()
      .then((c) => {
        if (!mounted) return;
        setCalendars(c || []);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(String(err));
      })
      .finally(() => {
        if (!mounted) return;
        setLoadingCals(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    if (!targetCalendarId) {
      setEvents([]);
      return;
    }

    const t0 = new Date(selectedDate);
    const start = new Date(t0.setHours(0, 0, 0, 0)).toISOString();
    const end = new Date(t0.setHours(23, 59, 59, 999)).toISOString();

    setLoadingEvents(true);
    setError(null);
    listEvents(targetCalendarId, { time_min: start, time_max: end })
      .then((ev) => {
        if (!mounted) return;
        setEvents(ev || []);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(String(err));
        setEvents([]);
      })
      .finally(() => {
        if (!mounted) return;
        setLoadingEvents(false);
      });

    return () => {
      mounted = false;
    };
  }, [targetCalendarId, selectedDate]);

  const day = selectedDate.getDate();

  function pick(d: number) {
    const chosen = new Date(
      selectedDate.getFullYear(),
      selectedDate.getMonth(),
      d,
      selectedDate.getHours(),
      selectedDate.getMinutes(),
    );
    setSelectedDate(chosen);
    onSelect(chosen);
    void apiSelectDate({ selected: chosen.toISOString() }).catch(() => {});
  }

  async function openEventDetail(eventId: string) {
    setError(null);
    try {
      const ev = await getEvent(targetCalendarId!, eventId);
      setEditingEvent(ev);
      setEditingEventId(eventId);
    } catch (err: any) {
      setError(String(err));
    }
  }

  async function saveEventEdits() {
    if (!editingEventId || !targetCalendarId || !editingEvent) return;
    try {
      const payload: components['schemas']['EventUpdate'] = {
        title: editingEvent.title,
        description: editingEvent.description ?? undefined,
        start: editingEvent.start,
        end: editingEvent.end,
        all_day: editingEvent.all_day ?? false,
      };

      await patchEvent(targetCalendarId, editingEventId, payload);
      setEditingEventId(null);
      setEditingEvent(null);
      // reload events
      const t0 = new Date(selectedDate);
      const start = new Date(t0.setHours(0, 0, 0, 0)).toISOString();
      const end = new Date(t0.setHours(23, 59, 59, 999)).toISOString();
      const ev = await listEvents(targetCalendarId, { time_min: start, time_max: end });
      setEvents(ev || []);
    } catch (err: any) {
      setError(String(err));
    }
  }

  async function removeEvent(id: string) {
    if (!targetCalendarId) return;
    try {
      await deleteEvent(targetCalendarId, id);
      // reload
      const t0 = new Date(selectedDate);
      const start = new Date(t0.setHours(0, 0, 0, 0)).toISOString();
      const end = new Date(t0.setHours(23, 59, 59, 999)).toISOString();
      const ev = await listEvents(targetCalendarId, { time_min: start, time_max: end });
      setEvents(ev || []);
    } catch (err: any) {
      setError(String(err));
    }
  }

  return (
    <div className="text-sm text-text-soft dark:text-gray-300">
      {/* Kalenderauswahl */}
      <div className="mb-3">
        <label htmlFor="calendar-select" className="block text-xs font-medium text-text-muted dark:text-gray-400">
          Ziel-Kalender
        </label>
        <select
          id="calendar-select"
          className="mt-1 w-full rounded-lg border border-border-soft bg-white/70 px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
          value={targetCalendarId ?? ''}
          onChange={(e) => setTargetCalendarId(e.target.value || null)}
        >
          <option value="">-- auswählen --</option>
          {calendars.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Kalenderkopf */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
            onClick={() => {
              const newDate = new Date(selectedDate);
              newDate.setMonth(newDate.getMonth() - 1);
              setSelectedDate(newDate);
            }}
            aria-label="Vorheriger Monat"
          >
            <IconBadge icon={<ChevronLeft />} size="sm" variant="default" />
          </button>
          <strong className="text-base text-text dark:text-white">
            {selectedDate.toLocaleString('de-DE', { month: 'long', year: 'numeric' })}
          </strong>
          <button
            type="button"
            className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
            onClick={() => {
              const newDate = new Date(selectedDate);
              newDate.setMonth(newDate.getMonth() + 1);
              setSelectedDate(newDate);
            }}
            aria-label="Nächster Monat"
          >
            <IconBadge icon={<ChevronRight />} size="sm" variant="default" />
          </button>
        </div>
        <button
          type="button"
          className="rounded-lg px-3 py-1.5 text-sm text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white"
          onClick={onCancel}
        >
          Abbrechen
        </button>
      </div>

      {/* Kalendertage */}
      <div className="mt-3 grid grid-cols-7 gap-1 text-center text-xs">
        {['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'].map((w) => (
          <div key={w} className="font-medium text-text-muted dark:text-gray-400">
            {w}
          </div>
        ))}
        {Array.from({ length: 31 }).map((_, i) => {
          const d = i + 1;
          const isSelected = day === d;
          return (
            <div key={d} className="py-1">
              <button
                type="button"
                onClick={() => pick(d)}
                className={[
                  'h-8 w-full rounded-full text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
                  isSelected
                    ? 'bg-primary text-white hover:bg-primary-hover'
                    : 'hover:bg-surface-hover dark:hover:bg-slate-700',
                ].join(' ')}
                aria-label={`Tag ${d} auswählen`}
              >
                {d}
              </button>
            </div>
          );
        })}
      </div>

      {/* Ereignisliste */}
      <div className="mt-3">
        <div className="text-xs font-semibold text-text-muted dark:text-gray-400">Ereignisse</div>
        <div className="mt-1 max-h-40 overflow-auto text-xs">
          {loadingEvents ? (
            <div className="flex items-center gap-2 text-text-muted">
              <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
              Lade Ereignisse …
            </div>
          ) : error ? (
            <div className="text-danger">{error}</div>
          ) : events.length === 0 ? (
            <div className="text-text-muted">Keine Ereignisse</div>
          ) : (
            <ul className="space-y-1.5">
              {events.map((e) => (
                <li key={e.id} className="rounded-lg border border-border-soft p-2 dark:border-white/10">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <button
                        type="button"
                        className="truncate font-medium text-text hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-white dark:hover:text-primary"
                        onClick={() => openEventDetail(e.id)}
                      >
                        {e.title}
                      </button>
                      <div className="text-text-muted dark:text-gray-500">
                        {new Date(e.start).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="rounded p-1 text-text-muted transition hover:bg-danger-soft hover:text-danger dark:text-gray-400 dark:hover:bg-danger/10 dark:hover:text-danger"
                      onClick={() => void removeEvent(e.id)}
                      aria-label={`Ereignis "${e.title}" löschen`}
                    >
                      <IconBadge icon={<Trash2 />} size="sm" variant="default" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Ereignis‑Editor (eingeklappt) */}
      {editingEventId && editingEvent && (
        <div className="mt-4 border-t border-border-soft pt-4 dark:border-white/10">
          <h4 className="text-sm font-semibold text-text dark:text-white">Ereignis bearbeiten</h4>
          <div className="mt-3 space-y-3">
            <div>
              <label htmlFor="edit-event-title" className="sr-only">Titel</label>
              <input
                id="edit-event-title"
                className="w-full rounded-lg border border-border-soft bg-white/70 px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                value={editingEvent.title}
                onChange={(e) =>
                  setEditingEvent((prev) => (prev ? { ...prev, title: e.target.value } : prev))
                }
                placeholder="Titel"
              />
            </div>
            <div>
              <label htmlFor="edit-event-description" className="sr-only">Beschreibung</label>
              <textarea
                id="edit-event-description"
                rows={3}
                className="w-full rounded-lg border border-border-soft bg-white/70 px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                value={editingEvent.description ?? ''}
                onChange={(e) =>
                  setEditingEvent((prev) => (prev ? { ...prev, description: e.target.value } : prev))
                }
                placeholder="Beschreibung"
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-lg border border-border-soft px-3 py-1.5 text-sm font-medium text-text-soft transition hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:border-white/10 dark:text-gray-300 dark:hover:bg-slate-800"
                onClick={() => {
                  setEditingEventId(null);
                  setEditingEvent(null);
                }}
              >
                Abbrechen
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:bg-primary/80 dark:hover:bg-primary"
                onClick={() => void saveEventEdits()}
              >
                <IconBadge icon={<Save />} size="sm" variant="default" />
                Speichern
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}