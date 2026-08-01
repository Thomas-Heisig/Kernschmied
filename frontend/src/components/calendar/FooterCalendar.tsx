import React, { useEffect, useMemo, useState } from 'react';
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
      setEditingEvent(ev as any);
      setEditingEventId(eventId);
    } catch (err: any) {
      setError(String(err));
    }
  }

  async function saveEventEdits() {
    if (!editingEventId || !targetCalendarId || !editingEvent) return;
    try {
      await patchEvent(targetCalendarId, editingEventId, {
        title: editingEvent.title,
        description: editingEvent.description ?? undefined,
        start: editingEvent.start as any,
        end: editingEvent.end as any,
        all_day: editingEvent.all_day ?? false,
      } as any);
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
    <div>
      <div className="mb-2">
        <label className="block text-xs mb-1">Ziel-Kalender</label>
        <select
          className="w-full rounded border px-2 py-1 text-sm"
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

      <div className="text-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <strong>
              {selectedDate.toLocaleString('de-DE', { month: 'long', year: 'numeric' })}
            </strong>
          </div>
          <div>
            <button className="text-xs text-gray-500" onClick={onCancel}>
              Abbrechen
            </button>
          </div>
        </div>

        <div className="mt-2 grid grid-cols-7 gap-1 text-center text-xs">
          {['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'].map((w) => (
            <div key={w} className="font-medium">
              {w}
            </div>
          ))}

          {Array.from({ length: 31 }).map((_, i) => {
            const d = i + 1;
            return (
              <div key={d} className={`py-1 ${d ? 'cursor-pointer rounded' : ''}`}>
                <button
                  onClick={() => pick(d)}
                  className={`w-full ${day === d ? 'bg-sky-600 text-white rounded' : 'hover:bg-gray-100 dark:hover:bg-slate-700 rounded'} focus:outline-none focus:ring-2 focus:ring-sky-500`}
                >
                  {d}
                </button>
              </div>
            );
          })}
        </div>

        <div className="mt-2">
          <div className="text-xs font-semibold">Ereignisse</div>
          <div className="mt-1 max-h-40 overflow-auto text-xs">
            {loadingEvents ? (
              <div className="text-slate-500">Lade Ereignisse …</div>
            ) : error ? (
              <div className="text-red-600">{error}</div>
            ) : events.length === 0 ? (
              <div className="text-slate-500">Keine Ereignisse</div>
            ) : (
              <ul>
                {events.map((e) => (
                  <li key={e.id} className="py-1 border-b last:border-b-0">
                    <div className="flex items-center justify-between">
                      <div>
                        <button
                          className="font-medium text-left"
                          onClick={() => openEventDetail(e.id)}
                        >
                          {e.title}
                        </button>
                        <div className="text-slate-500 text-xs">
                          {new Date(e.start).toLocaleTimeString('de-DE')}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          className="text-xs text-red-600"
                          onClick={() => void removeEvent(e.id)}
                        >
                          Löschen
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
      {editingEventId && editingEvent ? (
        <div className="mt-2 border-t pt-2">
          <h4 className="text-sm font-semibold">Ereignis bearbeiten</h4>
          <input
            className="w-full rounded border px-2 py-1 text-sm mt-2"
            value={editingEvent.title}
            onChange={(e) => setEditingEvent({ ...editingEvent, title: e.target.value } as any)}
          />
          <textarea
            className="w-full rounded border px-2 py-1 text-sm mt-2"
            rows={3}
            value={editingEvent.description ?? ''}
            onChange={(e) => setEditingEvent({ ...editingEvent, description: e.target.value } as any)}
          />
          <div className="mt-2 flex gap-2 justify-end">
            <button
              className="rounded px-3 py-1 text-sm"
              onClick={() => {
                setEditingEventId(null);
                setEditingEvent(null);
              }}
            >
              Abbrechen
            </button>
            <button
              className="rounded bg-sky-600 px-3 py-1 text-sm text-white"
              onClick={() => void saveEventEdits()}
            >
              Speichern
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
