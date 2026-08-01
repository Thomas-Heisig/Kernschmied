import { useEffect, useState, useCallback } from 'react';
import type { components } from '../api/openapi-types';
import {
  listCalendars,
  createCalendar,
  patchCalendar,
  deleteCalendar,
} from '../api/fetchCalendarClient';

export function useCalendars() {
  const [calendars, setCalendars] = useState<components['schemas']['CalendarOut'][]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const c = await listCalendars();
      setCalendars(c || []);
    } catch (err: any) {
      setError(String(err));
      setCalendars([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const addCalendar = useCallback(async (name: string) => {
    try {
      await createCalendar({ name });
      await reload();
      return true;
    } catch (err: any) {
      setError(String(err));
      return false;
    }
  }, [reload]);

  const updateCalendar = useCallback(async (id: string, name: string) => {
    try {
      await patchCalendar(id, { name } as components['schemas']['CalendarUpdate']);
      await reload();
      return true;
    } catch (err: any) {
      setError(String(err));
      return false;
    }
  }, [reload]);

  const removeCalendar = useCallback(async (id: string) => {
    try {
      await deleteCalendar(id);
      await reload();
      return true;
    } catch (err: any) {
      setError(String(err));
      return false;
    }
  }, [reload]);

  useEffect(() => {
    void reload();
  }, []);

  return { calendars, loading, error, reload, addCalendar, updateCalendar, removeCalendar };
}
