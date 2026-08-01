import { useEffect, useState, useCallback } from 'react';
import type { components } from '../api/openapi-types';
import {
  listEvents as apiListEvents,
  createEvent as apiCreateEvent,
  patchEvent as apiPatchEvent,
  deleteEvent as apiDeleteEvent,
} from '../api/fetchCalendarClient';

function getMonthRange(date: Date = new Date()) {
  const start = new Date(date.getFullYear(), date.getMonth(), 1).toISOString();
  const end = new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59).toISOString();
  return { start, end };
}

export function useEvents(calendarId: string | null) {
  const [events, setEvents] = useState<components['schemas']['EventOut'][]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!calendarId) {
      setEvents([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const { start, end } = getMonthRange();
      const ev = await apiListEvents(calendarId, { time_min: start, time_max: end });
      setEvents(ev || []);
    } catch (err: any) {
      setError(String(err));
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [calendarId]);

  const create = useCallback(async (payload: components['schemas']['EventCreate']) => {
    if (!calendarId) return false;
    try {
      await apiCreateEvent(calendarId, payload);
      await refresh();
      return true;
    } catch (err: any) {
      setError(String(err));
      return false;
    }
  }, [calendarId, refresh]);

  const update = useCallback(async (eventId: string, payload: components['schemas']['EventUpdate']) => {
    if (!calendarId) return false;
    try {
      await apiPatchEvent(calendarId, eventId, payload);
      await refresh();
      return true;
    } catch (err: any) {
      setError(String(err));
      return false;
    }
  }, [calendarId, refresh]);

  const remove = useCallback(async (eventId: string) => {
    if (!calendarId) return false;
    try {
      await apiDeleteEvent(calendarId, eventId);
      await refresh();
      return true;
    } catch (err: any) {
      setError(String(err));
      return false;
    }
  }, [calendarId, refresh]);

  useEffect(() => {
    void refresh();
  }, [calendarId]);

  return { events, loading, error, refresh, create, update, remove };
}
