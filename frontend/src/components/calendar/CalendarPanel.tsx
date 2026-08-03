import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
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
  const [newCalName, setNewCalName] = useState('');
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventStart, setNewEventStart] = useState('');
  const [newEventEnd, setNewEventEnd] = useState('');
  const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);
  const [editingCalendarName, setEditingCalendarName] = useState<string>('');
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [showCalendarView, setShowCalendarView] = useState(true);

  // Use domain hooks for calendars and events; they encapsulate API operations
  const { calendars, loading: loadingCals, error: calError, addCalendar, updateCalendar, removeCalendar, reload } = useCalendars();
  const { events, loading: loadingEvents, error: eventsError, create: createEventHook, update: updateEventHook, remove: removeEventHook, refresh: refreshEvents } = useEvents(
    selectedCalendar,
    currentMonth,
  );

  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [editingEventTitle, setEditingEventTitle] = useState('');
  const [editingEventStartInput, setEditingEventStartInput] = useState('');
  const [editingEventEndInput, setEditingEventEndInput] = useState('');

  const toInputLocal = (iso: string) => {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  useEffect(() => {
    if (!selectedCalendar && calendars && calendars.length) setSelectedCalendar(calendars[0].id);
  }, [calendars]);

  // initialize new event start/end to next full hour and +1h
  useEffect(() => {
    const toLocalInput = (d: Date) => {
      const pad = (n: number) => String(n).padStart(2, '0');
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    };

    const now = new Date();
    const next = new Date(now);
    next.setHours(now.getHours() + 1, 0, 0, 0);
    const end = new Date(next.getTime() + 60 * 60 * 1000);
    setNewEventStart(toLocalInput(next));
    setNewEventEnd(toLocalInput(end));
  }, []);

  useEffect(() => {
    if (!selectedCalendar) return;
    // events are handled by useEvents hook; refresh when selectedCalendar or month changes
    void refreshEvents();
  }, [selectedCalendar, currentMonth, refreshEvents]);

  return (
    <div className="p-4">
      <Toaster position="bottom-right" />
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Kalenderverwaltung</h3>
        <div>
          <button className="mr-2 rounded px-2 py-1" onClick={onClose}>
            Schließen
          </button>
