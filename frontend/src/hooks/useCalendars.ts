import { useEffect, useState, useCallback } from 'react';
import type { components } from '../api/openapi-types';
import { listCalendars, createCalendar, patchCalendar, deleteCalendar } from '../api/fetchCalendarClient';

export function useCalendars() {
  const [calendars, setCalendars] = useState<components['schemas']['CalendarOut'][]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const c = await listCalendars();
      setCalendars(c || []);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const addCalendar = useCallback(async (name: string) => {
    try {
      const created = await createCalendar({ name });
      setCalendars((prev) => (created ? [created, ...prev] : prev));
      return true;
    } catch (err) {
      setError(String(err));
      return false;
    }
  }, []);

  const updateCalendar = useCallback(async (id: string, name: string) => {
    try {
      const patched = await patchCalendar(id, { name });
      setCalendars((prev) => prev.map((c) => (c.id === id ? patched : c)));
      return true;
    } catch (err) {
      setError(String(err));
      return false;
    }
  }, []);

  const removeCalendar = useCallback(async (id: string) => {
    try {
      await deleteCalendar(id);
      setCalendars((prev) => prev.filter((c) => c.id !== id));
      return true;
    } catch (err) {
      setError(String(err));
      return false;
    }
  }, []);

  return { calendars, loading, error, addCalendar, updateCalendar, removeCalendar, reload };
}

export default useCalendars;
