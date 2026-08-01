import React, { useEffect, useState } from 'react';
import type { components } from '../../api/openapi-types';
import {
  listCalendars,
  createCalendar,
  patchCalendar,
  deleteCalendar,
  listEvents,
  createEvent,
  patchEvent,
  deleteEvent,
} from '../../api/fetchCalendarClient';

export function CalendarPanel({ onClose }: { onClose: () => void }) {
  const [calendars, setCalendars] = useState<components['schemas']['CalendarOut'][]>([]);
  const [selectedCalendar, setSelectedCalendar] = useState<string | null>(null);
  const [events, setEvents] = useState<components['schemas']['EventOut'][]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [newCalName, setNewCalName] = useState('');
  const [newEventTitle, setNewEventTitle] = useState('');
  const [loadingCals, setLoadingCals] = useState(false);
  const [calError, setCalError] = useState<string | null>(null);
  const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);
  const [editingCalendarName, setEditingCalendarName] = useState<string>('');

  async function reloadCalendars() {
    setCalError(null);
    setLoadingCals(true);
    try {
      const c = await listCalendars();
      setCalendars(c || []);
      if (!selectedCalendar && c && c.length) setSelectedCalendar(c[0].id);
    } catch (err: any) {
      setCalError(String(err));
      setCalendars([]);
    } finally {
      setLoadingCals(false);
    }
  }

  useEffect(() => {
    void reloadCalendars();
  }, []);

  useEffect(() => {
    let mounted = true;
    if (!selectedCalendar) {
      setEvents([]);
      return;
    }

    (async () => {
      setLoadingEvents(true);
      try {
        const now = new Date();
        const start = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
        const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59).toISOString();
        const ev = await listEvents(selectedCalendar, { time_min: start, time_max: end });
        if (!mounted) return;
        setEvents(ev || []);
      } catch (err: any) {
        if (!mounted) return;
        setEvents([]);
        setCalError(String(err));
        // show quick feedback
        alert('Ereignisse konnten nicht geladen werden: ' + String(err));
      } finally {
        if (!mounted) return;
        setLoadingEvents(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [selectedCalendar]);

  return (
    <div className="p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Kalenderverwaltung</h3>
        <div>
          <button className="mr-2 rounded px-2 py-1" onClick={onClose}>
            Schließen
          </button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <h4 className="font-medium">Kalender</h4>
          <ul className="mt-2 space-y-2">
            {calendars.map((c) => (
              <li key={c.id} className="flex items-center justify-between">
                <div className="flex-1">
                  {editingCalendarId === c.id ? (
                    <input
                      id="calendar-edit-input"
                      className="w-full rounded border px-2 py-1 text-sm"
                      value={editingCalendarName}
                      onChange={(e) => setEditingCalendarName(e.target.value)}
                    />
                  ) : (
                    <button
                      className={`text-left w-full ${selectedCalendar === c.id ? 'font-semibold' : ''}`}
                      onClick={() => setSelectedCalendar(c.id)}
                    >
                      {c.name}
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-2">
                  {editingCalendarId === c.id ? (
                    <>
                      <button
                        className="text-sm px-2"
                        onClick={async () => {
                          // save
                          try {
                            await patchCalendar(c.id, { name: editingCalendarName } as components['schemas']['CalendarUpdate']);
                            setEditingCalendarId(null);
                            setEditingCalendarName('');
                            await reloadCalendars();
                          } catch (err: any) {
                            setCalError(String(err));
                            alert('Kalender konnte nicht gespeichert werden: ' + String(err));
                          }
                        }}
                      >
                        Speichern
                      </button>
                      <button
                        className="text-sm px-2"
                        onClick={() => {
                          setEditingCalendarId(null);
                          setEditingCalendarName('');
                        }}
                      >
                        Abbrechen
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="text-sm px-2"
                        onClick={() => {
                          setEditingCalendarId(c.id);
                          setEditingCalendarName(c.name);
                        }}
                      >
                        Bearbeiten
                      </button>
                      <button
                        className="text-sm text-red-600 px-2"
                        onClick={async () => {
                          if (!window.confirm(`Kalender "${c.name}" wirklich löschen?`)) return;
                          try {
                            await deleteCalendar(c.id);
                            await reloadCalendars();
                          } catch (e: any) {
                            setCalError(String(e));
                            alert('Kalender konnte nicht gelöscht werden: ' + String(e));
                          }
                        }}
                      >
                        Löschen
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>

          {loadingCals ? <div className="text-sm text-slate-500 mt-2">Lade Kalender …</div> : null}
          {calError ? <div className="text-sm text-red-600 mt-2">{calError}</div> : null}

          <div className="mt-4">
            <input
              className="w-full rounded border px-2 py-1 text-sm"
              placeholder="Neuer Kalender"
              value={newCalName}
              onChange={(e) => setNewCalName(e.target.value)}
            />
            <div className="mt-2 flex justify-end gap-2">
              <button
                className="rounded bg-sky-600 px-3 py-1 text-sm text-white"
                onClick={async () => {
                  if (!newCalName.trim()) return;
                  try {
                    await createCalendar({ name: newCalName.trim() });
                    setNewCalName('');
                    await reloadCalendars();
                  } catch (err: any) {
                    setCalError(String(err));
                    alert('Kalender konnte nicht erstellt werden: ' + String(err));
                  }
                }}
              >
                Erstellen
              </button>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium">Ereignisse</h4>
          {selectedCalendar ? (
            <>
              <ul className="mt-2 space-y-2 max-h-64 overflow-auto text-sm">
                {loadingEvents && <div className="text-sm text-slate-500">Lade Ereignisse …</div>}
                {events.map((e) => (
                  <li key={e.id} className="border-b pb-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{e.title}</div>
                        <div className="text-xs text-slate-500">
                          {new Date(e.start).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          className="text-sm text-red-600"
                          onClick={async () => {
                            if (!window.confirm(`Ereignis "${e.title}" wirklich löschen?`)) return;
                            try {
                              await deleteEvent(selectedCalendar, e.id);
                              // reload events
                              const now = new Date();
                              const start = new Date(
                                now.getFullYear(),
                                now.getMonth(),
                                1,
                              ).toISOString();
                              const end = new Date(
                                now.getFullYear(),
                                now.getMonth() + 1,
                                0,
                                23,
                                59,
                                59,
                              ).toISOString();
                              const ev = await listEvents(selectedCalendar, {
                                time_min: start,
                                time_max: end,
                              });
                              setEvents(ev || []);
                            } catch (err: any) {
                              setCalError(String(err));
                              alert('Ereignis konnte nicht gelöscht werden: ' + String(err));
                            }
                          }}
                        >
                          Löschen
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>

              <div className="mt-4">
                <input
                  className="w-full rounded border px-2 py-1 text-sm"
                  placeholder="Neues Ereignis Titel"
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                />
                <div className="mt-2 flex justify-end gap-2">
                  <button
                    className="rounded bg-sky-600 px-3 py-1 text-sm text-white"
                    onClick={async () => {
                      if (!newEventTitle.trim() || !selectedCalendar) return;
                      try {
                        const start = new Date().toISOString();
                        const end = new Date(Date.now() + 60 * 60 * 1000).toISOString();
                        await createEvent(selectedCalendar, {
                          title: newEventTitle.trim(),
                          description: '',
                          start,
                          end,
                          all_day: false,
                        });
                        setNewEventTitle('');
                        // reload events
                        const now = new Date();
                        const s = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
                        const e = new Date(
                          now.getFullYear(),
                          now.getMonth() + 1,
                          0,
                          23,
                          59,
                          59,
                        ).toISOString();
                        const ev = await listEvents(selectedCalendar, { time_min: s, time_max: e });
                        setEvents(ev || []);
                      } catch {}
                    }}
                  >
                    Erstellen
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-sm text-slate-500">Kein Kalender ausgewählt</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CalendarPanel;
