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
