import React, { useEffect, useMemo, useState } from 'react';
import type { components } from '../../api/openapi-types';
import {
  listCalendars,
  listEvents,
  selectDate as apiSelectDate,
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

  useEffect(() => {
    let mounted = true;
    listCalendars()
      .then((c) => {
        if (!mounted) return;
        setCalendars(c || []);
      })
      .catch(() => {});

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

    listEvents(targetCalendarId, { time_min: start, time_max: end })
      .then((ev) => {
        if (!mounted) return;
        setEvents(ev || []);
      })
      .catch(() => {
        if (!mounted) return;
        setEvents([]);
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
          <ul className="mt-1 max-h-40 overflow-auto text-xs">
            {events.length === 0 ? (
              <li className="text-slate-500">Keine Ereignisse</li>
            ) : (
              events.map((e) => (
                <li key={e.id} className="py-1 border-b last:border-b-0">
                  <div className="font-medium">{e.title}</div>
                  <div className="text-slate-500 text-xs">
                    {new Date(e.start).toLocaleTimeString('de-DE')}
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
