/* Auto-generated lightweight TypeScript client for Calendar API
   Uses fetch and returns parsed JSON. Adjust baseUrl if needed. */

const BASE = (window as any).__API_BASE__ || '/api/v1';

export type CalendarCreate = { name: string; color?: string | null; description?: string | null };
export type CalendarOut = {
  id: string;
  name: string;
  color?: string | null;
  description?: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
};

export type EventCreate = {
  title: string;
  description?: string | null;
  start: string;
  end: string;
  all_day?: boolean;
};
export type EventOut = {
  id: string;
  calendar_id: string;
  title: string;
  description?: string | null;
  start: string;
  end: string;
  all_day: boolean;
  created_at: string;
  updated_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  if (res.status === 204) {
    return undefined as unknown as T;
  }
  return (await res.json()) as T;
}

export const calendarClient = {
  listCalendars: async (): Promise<CalendarOut[]> => request(`/calendars`),
  createCalendar: async (payload: CalendarCreate): Promise<CalendarOut> =>
    request(`/calendars`, { method: 'POST', body: JSON.stringify(payload) }),
  getCalendar: async (id: string): Promise<CalendarOut> => request(`/calendars/${id}`),
  patchCalendar: async (id: string, payload: Partial<CalendarCreate>): Promise<CalendarOut> =>
    request(`/calendars/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteCalendar: async (id: string): Promise<void> =>
    request(`/calendars/${id}`, { method: 'DELETE' }),

  listEvents: async (
    calendarId: string,
    params?: { time_min?: string; time_max?: string },
  ): Promise<EventOut[]> => {
    const q = params ? `?${new URLSearchParams(params as any).toString()}` : '';
    return request(`/calendars/${calendarId}/events${q}`);
  },
  createEvent: async (calendarId: string, payload: EventCreate): Promise<EventOut> =>
    request(`/calendars/${calendarId}/events`, { method: 'POST', body: JSON.stringify(payload) }),
  getEvent: async (calendarId: string, eventId: string): Promise<EventOut> =>
    request(`/calendars/${calendarId}/events/${eventId}`),
  patchEvent: async (
    calendarId: string,
    eventId: string,
    payload: Partial<EventCreate>,
  ): Promise<EventOut> =>
    request(`/calendars/${calendarId}/events/${eventId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  deleteEvent: async (calendarId: string, eventId: string): Promise<void> =>
    request(`/calendars/${calendarId}/events/${eventId}`, { method: 'DELETE' }),
};

export default calendarClient;
