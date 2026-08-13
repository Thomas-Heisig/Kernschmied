import React from 'react';
import CalendarPanel from '../calendar/CalendarPanel';

export default function CalendarWidget({ nodeId, configuration }: { nodeId?: string; configuration?: any }) {
  // For the first iteration we simply render the existing CalendarPanel.
  // In future we can scope calendars/events to `nodeId` + `configuration`.
  return (
    <div className="rounded border border-border-soft px-3 py-2 bg-white/60 dark:bg-slate-900/40">
      <div className="mb-2 text-sm font-semibold">Kalender</div>
      <CalendarPanel onClose={() => { /* no-op inside widget */ }} />
    </div>
  );
}
