import { useCallback, useEffect, useState } from 'react';
import type { components } from '../api/openapi-types';
import { listEvents, createEvent, patchEvent, deleteEvent } from '../api/fetchCalendarClient';

export function useEvents(calendarId: string | null, month: Date) {
  const [events, setEvents] = useState<components['schemas']['EventOut'][]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchForMonth = useCallback(async () => {
    if (!calendarId) {
      setEvents([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const start = new Date(month.getFullYear(), month.getMonth(), 1, 0, 0, 0, 0).toISOString();
      const end = new Date(month.getFullYear(), month.getMonth() + 1, 0, 23, 59, 59, 999).toISOString();
      const ev = await listEvents(calendarId, { time_min: start, time_max: end });
      setEvents(ev || []);
    } catch (err) {
      setError(String(err));
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [calendarId, month]);

  useEffect(() => {
    void fetchForMonth();
  }, [fetchForMonth]);

  const refresh = useCallback(async () => {
    await fetchForMonth();
  }, [fetchForMonth]);

  const create = useCallback(
    async (payload: components['schemas']['EventCreate']) => {
      if (!calendarId) return false;
      try {
        await createEvent(calendarId, payload);
        await fetchForMonth();
        return true;
      } catch (err) {
        setError(String(err));
        return false;
      }
    },
    [calendarId, fetchForMonth],
  );

  const update = useCallback(
    async (id: string, payload: components['schemas']['EventUpdate']) => {
      if (!calendarId) return false;
      try {
        await patchEvent(calendarId, id, payload);
        await fetchForMonth();
        return true;
      } catch (err) {
        setError(String(err));
        return false;
      }
    },
    [calendarId, fetchForMonth],
  );

  const remove = useCallback(
    async (id: string) => {
      if (!calendarId) return false;
      try {
        await deleteEvent(calendarId, id);
        await fetchForMonth();
        return true;
      } catch (err) {
        setError(String(err));
        return false;
      }
    },
    [calendarId, fetchForMonth],
  );

  return { events, loading, error, create, update, remove, refresh };
}

export default useEvents;
