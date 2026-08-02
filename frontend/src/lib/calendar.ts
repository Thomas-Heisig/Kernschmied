const DEFAULT_FETCH_TIMEOUT = 5000;

function isDevMode(): boolean {
  try {
    // Vite / import.meta.env
    if (typeof (import.meta as any) !== 'undefined' && (import.meta as any).env && (import.meta as any).env.MODE !== 'production') {
      return true;
    }

    // Node / SSR environments via globalThis
    const g = globalThis as any;
    if (g && g.process && g.process.env && g.process.env.NODE_ENV !== 'production') {
      return true;
    }
  } catch {
    // ignore
  }
  return false;
}

export async function sendSelectedDate(date: Date, timeoutMs = DEFAULT_FETCH_TIMEOUT) {
  // basic validation
  if (!(date instanceof Date) || isNaN(date.getTime())) {
    const msg = 'sendSelectedDate: invalid date provided';
    if (isDevMode()) console.warn(msg, date);
    return null;
  }

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch('/api/v1/calendar/selection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected: date.toISOString() }),
      signal: controller.signal,
    });

    if (!res.ok) {
      // Not fatal; backend may not implement this yet
      throw new Error(`${res.status} ${res.statusText}`);
    }

    return res.json();
  } catch (e) {
    // swallow; integration point prepared
    if (isDevMode()) console.warn('sendSelectedDate failed:', e);
    return null;
  } finally {
    clearTimeout(id);
  }
}

export function shouldSendSelection(): boolean {
  try {
    const v = localStorage.getItem('calendar.saveSelection');
    if (v === null) return true;
    return v === 'true';
  } catch {
    return true;
  }
}

export async function sendSelectedDateIfOptIn(date: Date) {
  if (!shouldSendSelection()) return null;
  return sendSelectedDate(date);
}
