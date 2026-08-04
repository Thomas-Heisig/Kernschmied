import React, { useEffect, useState } from 'react';
import { Toaster, toast } from 'sonner';
import type { components } from '../../api/openapi-types';
import CalendarView from './CalendarView';
import * as api from '../../api/fetchCalendarClient';

export default function CalendarPanel({ onClose }: { onClose: () => void }) {
  const [calendarsState, setCalendarsState] = useState<components['schemas']['CalendarOut'][]>([]);
  const [selectedCalendarId, setSelectedCalendarId] = useState<string | null>(null);
  const [eventsState, setEventsState] = useState<components['schemas']['EventOut'][]>([]);
  const [loadingCals, setLoadingCals] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [newCalName, setNewCalName] = useState('');

  const loadCalendars = async () => {
    setLoadingCals(true);
    try {
      const c = await api.listCalendars();
      setCalendarsState(c || []);
      if (!selectedCalendarId && c && c.length) setSelectedCalendarId(c[0].id);
    } catch (err) {
      toast.error('Kalender konnten nicht geladen werden');
    } finally {
      setLoadingCals(false);
    }
  };

  const loadEvents = async (calendarId: string | null) => {
    if (!calendarId) return setEventsState([]);
    setLoadingEvents(true);
    try {
      const start = new Date();
      const end = new Date();
      end.setMonth(end.getMonth() + 1);
      const events = await api.listEvents(calendarId, {
        time_min: start.toISOString(),
        time_max: end.toISOString(),
      });
      setEventsState(events || []);
    } catch (err) {
      toast.error('Ereignisse konnten nicht geladen werden');
    } finally {
      setLoadingEvents(false);
    }
  };

  useEffect(() => {
    void loadCalendars();
  }, []);

  useEffect(() => {
    void loadEvents(selectedCalendarId);
  }, [selectedCalendarId]);

  const handleAddCalendar = async () => {
    if (!newCalName.trim()) return;
    try {
      await api.createCalendar({ name: newCalName.trim() } as any);
      setNewCalName('');
      void loadCalendars();
      toast.success('Kalender erstellt');
    } catch (err) {
      toast.error('Kalender konnte nicht erstellt werden');
    }
  };

  const handleRemoveCalendar = async (id: string) => {
    if (!window.confirm('Kalender wirklich löschen?')) return;
    try {
      await api.deleteCalendar(id);
      toast.success('Kalender gelöscht');
      if (selectedCalendarId === id) setSelectedCalendarId(null);
      void loadCalendars();
    } catch (err) {
      toast.error('Löschen fehlgeschlagen');
    }
  };

  const handleCreateEvent = async (payload: components['schemas']['EventCreate']) => {
    if (!selectedCalendarId) return false;
    try {
      await api.createEvent(selectedCalendarId, payload);
      void loadEvents(selectedCalendarId);
      toast.success('Ereignis erstellt');
      return true;
    } catch (err) {
      toast.error('Ereignis konnte nicht erstellt werden');
      return false;
    }
  };

  const handleUpdateEvent = async (id: string, payload: components['schemas']['EventUpdate']) => {
    if (!selectedCalendarId) return false;
    try {
      await api.patchEvent(selectedCalendarId, id, payload);
      void loadEvents(selectedCalendarId);
      toast.success('Ereignis aktualisiert');
      return true;
    } catch (err) {
      toast.error('Aktualisierung fehlgeschlagen');
      return false;
    }
  };

  const handleRemoveEvent = async (id: string) => {
    if (!selectedCalendarId) return false;
    try {
      await api.deleteEvent(selectedCalendarId, id);
      void loadEvents(selectedCalendarId);
      toast.success('Ereignis gelöscht');
      return true;
    } catch (err) {
      toast.error('Löschen fehlgeschlagen');
      return false;
    }
  };

  return (
    <div className="p-4">
      <Toaster position="bottom-right" />
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Kalenderverwaltung</h3>
        <div>
          <button className="mr-2 rounded px-2 py-1" onClick={onClose}>
            Schließen
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <div className="mb-3">
            <input
              className="w-full rounded border px-2 py-1 text-sm"
              placeholder="Neuer Kalendername"
              value={newCalName}
              onChange={(e) => setNewCalName(e.target.value)}
            />
            <div className="mt-2 flex gap-2">
              <button className="px-3 py-1 bg-sky-600 text-white rounded" onClick={handleAddCalendar}>
                Hinzufügen
              </button>
            </div>
          </div>

          <div>
            {loadingCals ? (
              <div>Lade...</div>
            ) : (
              <ul className="space-y-2">
                {calendarsState.map((c) => (
                  <li key={c.id} className="flex items-center justify-between">
                    <button className="text-left flex-1" onClick={() => setSelectedCalendarId(c.id)}>
                      {c.name}
                    </button>
                    <button className="text-sm text-red-600" onClick={() => handleRemoveCalendar(c.id)}>
                      Löschen
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="col-span-2">
          {selectedCalendarId ? (
            <>
              {loadingEvents ? (
                <div>Lade Ereignisse...</div>
              ) : (
                <CalendarView events={eventsState} onCreate={handleCreateEvent} onUpdate={handleUpdateEvent} onRemove={handleRemoveEvent} />
              )}
            </>
          ) : (
            <div>Kein Kalender ausgewählt</div>
          )}
        </div>
      </div>
    </div>
  );
}
import React, { useEffect, useState } from 'react';
import { toast, Toaster } from 'sonner';
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
import CalendarView from './CalendarView';

export function CalendarPanel({ onClose }: { onClose: () => void }) {
  const [calendars, setCalendars] = useState<components['schemas']['CalendarOut'][]>([]);
  const [selectedCalendar, setSelectedCalendar] = useState<string | null>(null);
  const [events, setEvents] = useState<components['schemas']['EventOut'][]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [loadingCals, setLoadingCals] = useState(false);
  const [calError, setCalError] = useState<string | null>(null);
  const [eventsError, setEventsError] = useState<string | null>(null);
  const [newCalName, setNewCalName] = useState('');
  const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);
  const [editingCalendarName, setEditingCalendarName] = useState<string>('');
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [showCalendarView, setShowCalendarView] = useState(true);

  async function reloadCalendars() {
    setCalError(null);
    setLoadingCals(true);
    try {
      const c = await listCalendars();
      setCalendars(c || []);
      if (!selectedCalendar && c && c.length) setSelectedCalendar(c[0].id);
    } catch (err: any) {
      setCalError(err instanceof Error ? err.message : String(err));
      setCalendars([]);
    } finally {
      setLoadingCals(false);
    }
  }

  async function refreshEvents(calendarId?: string) {
    const calId = calendarId ?? selectedCalendar;
    if (!calId) {
      setEvents([]);
      return;
    }
    setEventsError(null);
    setLoadingEvents(true);
    try {
      const m = currentMonth || new Date();
      const start = new Date(m.getFullYear(), m.getMonth(), 1).toISOString();
      const end = new Date(m.getFullYear(), m.getMonth() + 1, 0, 23, 59, 59).toISOString();
      const ev = await listEvents(calId, { time_min: start, time_max: end });
      setEvents(ev || []);
    } catch (err: any) {
      setEventsError(err instanceof Error ? err.message : String(err));
      setEvents([]);
      toast.error('Ereignisse konnten nicht geladen werden: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setLoadingEvents(false);
    }
  }

  useEffect(() => {
    void reloadCalendars();
  }, []);

  useEffect(() => {
    if (!selectedCalendar) return;
    void refreshEvents(selectedCalendar);
  }, [selectedCalendar, currentMonth]);

  const handleAddCalendar = async () => {
    if (!newCalName.trim()) return;
    try {
      await createCalendar({ name: newCalName.trim() });
      setNewCalName('');
      void reloadCalendars();
      toast.success('Kalender erstellt');
    } catch (err: any) {
      toast.error('Kalender konnte nicht erstellt werden: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  const startEditingCalendar = (id: string, name: string) => {
    setEditingCalendarId(id);
    setEditingCalendarName(name);
  };

  const cancelEditCalendar = () => {
    setEditingCalendarId(null);
    setEditingCalendarName('');
  };

  const handleSaveCalendarEdit = async () => {
    if (!editingCalendarId) return;
    try {
      await patchCalendar(editingCalendarId, { name: editingCalendarName } as any);
      toast.success('Kalender aktualisiert');
      cancelEditCalendar();
      void reloadCalendars();
    } catch (err: any) {
      toast.error('Aktualisierung fehlgeschlagen: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleRemoveCalendar = async (id: string) => {
    if (!window.confirm('Kalender wirklich löschen?')) return;
    try {
      await deleteCalendar(id);
      toast.success('Kalender gelöscht');
      if (selectedCalendar === id) setSelectedCalendar(null);
      void reloadCalendars();
    } catch (err: any) {
      toast.error('Löschen fehlgeschlagen: ' + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleCreateEvent = async (payload: components['schemas']['EventCreate']) => {
    if (!selectedCalendar) return false;
    try {
      await createEvent(selectedCalendar, payload);
      void refreshEvents(selectedCalendar);
      return true;
    } catch (err: any) {
      toast.error('Ereignis konnte nicht erstellt werden: ' + (err instanceof Error ? err.message : String(err)));
      return false;
    }
  };

  const handleUpdateEvent = async (id: string, payload: components['schemas']['EventUpdate']) => {
    if (!selectedCalendar) return false;
    try {
      await patchEvent(selectedCalendar, id, payload);
      void refreshEvents(selectedCalendar);
      return true;
    } catch (err: any) {
      toast.error('Ereignis konnte nicht aktualisiert werden: ' + (err instanceof Error ? err.message : String(err)));
      return false;
    }
  };

  const handleRemoveEvent = async (id: string) => {
    if (!selectedCalendar) return false;
    try {
      await deleteEvent(selectedCalendar, id);
      void refreshEvents(selectedCalendar);
      return true;
    } catch (err: any) {
      toast.error('Ereignis konnte nicht gelöscht werden: ' + (err instanceof Error ? err.message : String(err)));
      return false;
    }
  };

  const prevMonth = () => setCurrentMonth((m) => new Date(m.getFullYear(), m.getMonth() - 1, 1));
  const nextMonth = () => setCurrentMonth((m) => new Date(m.getFullYear(), m.getMonth() + 1, 1));

  return (
    <div className="p-4">
      <Toaster position="bottom-right" />
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Kalenderverwaltung</h3>
        <div>
          <button className="mr-2 rounded px-2 py-1" onClick={onClose}>
            Schließen
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="col-span-1">
          <div className="mb-4">
            <h4 className="font-medium mb-2">Kalender</h4>
            <div className="flex gap-2">
              <input
                className="flex-1 rounded border px-2 py-1 text-sm"
                placeholder="Neuer Kalendername"
                value={newCalName}
                onChange={(e) => setNewCalName(e.target.value)}
              />
              <button className="px-3 py-1 bg-sky-600 text-white rounded" onClick={() => void handleAddCalendar()}>
                Hinzufügen
              </button>
            </div>
          </div>

          <div>
            {loadingCals ? (
              <div>Lade...</div>
            ) : calError ? (
              <div className="text-red-600">Fehler: {calError}</div>
            ) : (
              <ul className="space-y-2">
                {calendars.map((c) => (
                  <li key={c.id} className="flex items-center justify-between">
                    <button className={`text-left flex-1 ${selectedCalendar === c.id ? 'font-semibold' : ''}`} onClick={() => setSelectedCalendar(c.id)}>
                      {c.name}
                    </button>
                    <div className="flex items-center gap-2">
                      <button className="text-sm" onClick={() => startEditingCalendar(c.id, c.name)}>
                        Bearbeiten
                      </button>
                      <button className="text-sm text-red-600" onClick={() => void handleRemoveCalendar(c.id)}>
                        Löschen
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {editingCalendarId ? (
            <div className="mt-4">
              <h5 className="font-medium mb-1">Kalender bearbeiten</h5>
              <input
                className="w-full rounded border px-2 py-1 text-sm mb-2"
                value={editingCalendarName}
                onChange={(e) => setEditingCalendarName(e.target.value)}
              />
              <div className="flex gap-2 justify-end">
                <button className="px-3 py-1" onClick={cancelEditCalendar}>
                  Abbrechen
                </button>
                <button className="px-3 py-1 bg-sky-600 text-white rounded" onClick={() => void handleSaveCalendarEdit()}>
                  Speichern
                </button>
              </div>
            </div>
          ) : null}
        </div>

        <div className="col-span-2">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button className="px-2 py-1 rounded" onClick={prevMonth}>
                ‹
              </button>
              <div className="font-medium">{currentMonth.toLocaleString(undefined, { month: 'long', year: 'numeric' })}</div>
              <button className="px-2 py-1 rounded" onClick={nextMonth}>
                ›
              </button>
            </div>
            <div>
              <button className="px-3 py-1 rounded" onClick={() => setShowCalendarView((s) => !s)}>
                {showCalendarView ? 'Listenansicht' : 'Kalenderansicht'}
              </button>
            </div>
          </div>

          {showCalendarView ? (
            <CalendarView events={events} onCreate={handleCreateEvent} onUpdate={handleUpdateEvent} onRemove={handleRemoveEvent} />
          ) : (
            <div>
              {loadingEvents ? (
                <div>Lade Ereignisse...</div>
              ) : eventsError ? (
                <div className="text-red-600">Fehler: {eventsError}</div>
              ) : (
                <ul className="space-y-2">
                  {events.map((e) => (
                    <li key={e.id} className="flex items-center justify-between border rounded px-2 py-1">
                      <div>
                        <div className="font-medium">{e.title}</div>
                        <div className="text-sm text-slate-600">{new Date(e.start).toLocaleString()}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button className="text-sm" onClick={() => {/* handled in CalendarView */}}>
                          Bearbeiten
                        </button>
                        <button className="text-sm text-red-600" onClick={() => void handleRemoveEvent(e.id)}>
                          Löschen
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CalendarPanel;
