export async function sendSelectedDate(date: Date) {
  try {
    const res = await fetch('/api/v1/calendar/selection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected: date.toISOString() }),
    });

    if (!res.ok) {
      // Not fatal; backend may not implement this yet
      throw new Error(`${res.status} ${res.statusText}`);
    }

    return res.json();
  } catch (e) {
    // swallow; integration point prepared
    return null;
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
