import React, { useEffect, useState } from 'react';
import { toast, Toaster } from 'sonner';
import type { components } from '../../api/openapi-types';
import { useCalendars } from '../../hooks/useCalendars';
import { useEvents } from '../../hooks/useEvents';

export function CalendarPanel({ onClose }: { onClose: () => void }) {
  const [selectedCalendar, setSelectedCalendar] = useState<string | null>(null);
  const [newCalName, setNewCalName] = useState('');
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventStart, setNewEventStart] = useState('');
  const [newEventEnd, setNewEventEnd] = useState('');
  const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);
  const [editingCalendarName, setEditingCalendarName] = useState<string>('');

  const { calendars, loading: loadingCals, error: calError, addCalendar, updateCalendar, removeCalendar, reload } = useCalendars();
  const { events, loading: loadingEvents, error: eventsError, create: createEventHook, remove: removeEventHook, refresh: refreshEvents } = useEvents(selectedCalendar);

  useEffect(() => {
    if (!selectedCalendar && calendars && calendars.length) setSelectedCalendar(calendars[0].id);
  }, [calendars]);

  // initialize new event start/end to next full hour and +1h
  useEffect(() => {
    const toLocalInput = (d: Date) => {
      const pad = (n: number) => String(n).padStart(2, '0');
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
        d.getHours()
      )}:${pad(d.getMinutes())}`;
    };

    const now = new Date();
    const next = new Date(now);
    next.setHours(now.getHours() + 1, 0, 0, 0);
    const end = new Date(next.getTime() + 60 * 60 * 1000);
    setNewEventStart(toLocalInput(next));
    setNewEventEnd(toLocalInput(end));
  }, []);

  useEffect(() => {
    let mounted = true;
    if (!selectedCalendar) {
      return;
    }

    // events are handled by useEvents hook; refresh when selectedCalendar changes
    void refreshEvents();

    return () => {
      mounted = false;
    };
  }, [selectedCalendar]);

  return (
    <div className="p-4">
      <Toaster position="bottom-right" />
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
                          try {
                            const ok = await updateCalendar(c.id, editingCalendarName);
                            if (!ok) throw new Error('update failed');
                            setEditingCalendarId(null);
                            setEditingCalendarName('');
                            toast.success('Kalender gespeichert');
                          } catch (err: any) {
                            toast.error('Kalender konnte nicht gespeichert werden: ' + String(err));
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
                          const ok = await removeCalendar(c.id);
                          if (!ok) toast.error('Kalender konnte nicht gelöscht werden.');
                          else toast.success('Kalender gelöscht');
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
                      const ok = await addCalendar(newCalName.trim());
                      if (ok) {
                        setNewCalName('');
                        toast.success('Kalender erstellt');
                      } else toast.error('Kalender konnte nicht erstellt werden.');
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
                {eventsError ? <div className="text-sm text-red-600 mt-2">{eventsError}</div> : null}
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
                            const ok = await removeEventHook(e.id);
                            if (!ok) toast.error('Ereignis konnte nicht gelöscht werden.');
                            else toast.success('Ereignis gelöscht');
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
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <input
                    type="datetime-local"
                    className="w-full rounded border px-2 py-1 text-sm"
                    value={newEventStart}
                    onChange={(e) => setNewEventStart(e.target.value)}
                  />
                  <input
                    type="datetime-local"
                    className="w-full rounded border px-2 py-1 text-sm"
                    value={newEventEnd}
                    onChange={(e) => setNewEventEnd(e.target.value)}
                  />
                </div>
                <div className="mt-2 flex justify-end gap-2">
                  <button
                    className="rounded bg-sky-600 px-3 py-1 text-sm text-white"
                    onClick={async () => {
                      if (!newEventTitle.trim() || !selectedCalendar) return;
                        try {
                          // validate start/end
                          const startIso = new Date(newEventStart).toISOString();
                          const endIso = new Date(newEventEnd).toISOString();
                          if (new Date(endIso) <= new Date(startIso)) {
                            toast.error('Ende muss nach Start liegen.');
                            return;
                          }

                          const payload: components['schemas']['EventCreate'] = {
                            title: newEventTitle.trim(),
                            description: '',
                            start: startIso,
                            end: endIso,
                            all_day: false,
                          };

                          const ok = await createEventHook(payload);
                          if (ok) {
                            setNewEventTitle('');
                            toast.success('Ereignis erstellt');
                          }
                        } catch (err: any) {
                          toast.error('Ereignis konnte nicht erstellt werden: ' + String(err));
                        }
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
