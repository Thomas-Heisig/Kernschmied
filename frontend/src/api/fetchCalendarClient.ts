/* Typed, lightweight fetch wrapper using generated OpenAPI types (types-only).
   Replaces the handwritten calendarClient. */

import type { components } from './openapi-types';

const BASE = (window as any).__API_BASE__ || '/api/v1';

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

export async function listCalendars(): Promise<components['schemas']['CalendarOut'][]> {
  return request<components['schemas']['CalendarOut'][]>(`/calendars`);
}

export async function getCalendar(id: string): Promise<components['schemas']['CalendarOut']> {
  return request<components['schemas']['CalendarOut']>(`/calendars/${id}`);
}

export async function createCalendar(
  payload: components['schemas']['CalendarCreate'],
): Promise<components['schemas']['CalendarOut']> {
  return request<components['schemas']['CalendarOut']>(`/calendars/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function patchCalendar(
  id: string,
  payload: components['schemas']['CalendarUpdate'],
): Promise<components['schemas']['CalendarOut']> {
  return request<components['schemas']['CalendarOut']>(`/calendars/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteCalendar(id: string): Promise<void> {
  return request<void>(`/calendars/${id}`, { method: 'DELETE' });
}

export async function listEvents(
  calendarId: string,
  params?: { time_min?: string; time_max?: string },
): Promise<components['schemas']['EventOut'][]> {
  const q = params ? `?${new URLSearchParams(params as any).toString()}` : '';
  return request<components['schemas']['EventOut'][]>(`/calendars/${calendarId}/events${q}`);
}

export async function createEvent(
  calendarId: string,
  payload: components['schemas']['EventCreate'],
): Promise<components['schemas']['EventOut']> {
  return request<components['schemas']['EventOut']>(`/calendars/${calendarId}/events`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getEvent(
  calendarId: string,
  eventId: string,
): Promise<components['schemas']['EventOut']> {
  return request<components['schemas']['EventOut']>(`/calendars/${calendarId}/events/${eventId}`);
}

export async function patchEvent(
  calendarId: string,
  eventId: string,
  payload: components['schemas']['EventUpdate'],
): Promise<components['schemas']['EventOut']> {
  return request<components['schemas']['EventOut']>(`/calendars/${calendarId}/events/${eventId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteEvent(calendarId: string, eventId: string): Promise<void> {
  return request<void>(`/calendars/${calendarId}/events/${eventId}`, { method: 'DELETE' });
}

export async function selectDate(payload: components['schemas']['CalendarSelectionIn']) {
  return request<components['schemas']['CalendarSelectionOut']>(`/calendar/selection`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export default {
  listCalendars,
  getCalendar,
  listEvents,
  createEvent,
  selectDate,
};
