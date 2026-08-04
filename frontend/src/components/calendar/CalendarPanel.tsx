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
