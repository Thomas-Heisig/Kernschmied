/// <reference types="vitest" />
import { describe, it, beforeEach, afterEach, expect, vi } from 'vitest';
import { sendSelectedDateIfOptIn } from '../../../lib/calendar';

describe('sendSelectedDateIfOptIn opt-in behavior', () => {
  const realFetch = (globalThis as any).fetch;

  beforeEach(() => {
    // clear localStorage key
    localStorage.removeItem('calendar.saveSelection');
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = realFetch;
  });

  it('does not call fetch when opt-in is false', async () => {
    localStorage.setItem('calendar.saveSelection', 'false');

    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({}) }));
    (globalThis as any).fetch = fetchMock;

    await sendSelectedDateIfOptIn(new Date());

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('calls fetch when opt-in is true', async () => {
    localStorage.setItem('calendar.saveSelection', 'true');

    const fetchMock = vi.fn(async (url: string, opts: any) => ({ ok: true, json: async () => ({}) }));
    (globalThis as any).fetch = fetchMock;

    const now = new Date();
    await sendSelectedDateIfOptIn(now);

    expect(fetchMock).toHaveBeenCalled();
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/v1/calendar/selection');
    expect(opts.method).toBe('POST');
    const body = JSON.parse(opts.body);
    expect(body.selected).toBe(now.toISOString());
  });
});
