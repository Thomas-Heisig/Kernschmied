// F:\Kernschmied\frontend\src\components\calendar\CalendarView.tsx

import React, { useMemo, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { X, Save, Trash2 } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import type { components } from '../../api/openapi-types';
import { useToast } from '../ui/ToastProvider';
import Modal from '../ui/Modal';

type Props = {
  events: components['schemas']['EventOut'][];
  onCreate: (payload: components['schemas']['EventCreate']) => Promise<boolean>;
  onUpdate: (id: string, payload: components['schemas']['EventUpdate']) => Promise<boolean>;
  onRemove: (id: string) => Promise<boolean>;
};

export default function CalendarView({ events, onCreate, onUpdate, onRemove }: Props) {
  const { push } = useToast();
  const fcEvents = useMemo(
    () =>
      events.map((e) => ({
        id: e.id,
        title: e.title,
        start: e.start,
        end: e.end,
        allDay: !!e.all_day,
      })),
    [events],
  );

  const [editing, setEditing] = useState<components['schemas']['EventOut'] | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmEventId, setConfirmEventId] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  async function handleEventDrop(arg: any) {
    try {
      const id = arg.event.id;
      const start = arg.event.start?.toISOString();
      const end = arg.event.end?.toISOString() ?? arg.event.start?.toISOString();
      if (!start || !end) return;
      const payload: components['schemas']['EventUpdate'] = {
        title: arg.event.title,
        start,
        end,
        all_day: !!arg.event.allDay,
      };
      const ok = await onUpdate(id, payload);
      if (ok) push('success', 'Ereignis verschoben');
    } catch (err: any) {
      push('error', 'Verschieben fehlgeschlagen: ' + String(err));
    }
  }

  function handleEventClick(clickInfo: any) {
    const id = clickInfo.event.id;
    const ev = events.find((e) => e.id === id) || null;
    if (ev) setEditing(ev);
  }

  function handleDateClick(arg: any) {
    const start = arg.date;
    const end = new Date(start.getTime() + 60 * 60 * 1000);
    const now = new Date().toISOString();
    const newEv = {
      id: '__new',
      calendar_id: '',
      title: 'Neues Ereignis',
      description: '',
      start: start.toISOString(),
      end: end.toISOString(),
      all_day: false,
      created_at: now,
      updated_at: now,
    } as components['schemas']['EventOut'];
    setEditing(newEv);
  }

  async function handleSaveEdit() {
    if (!editing) return;
    try {
      if (editing.id === '__new') {
        const createPayload: components['schemas']['EventCreate'] = {
          title: editing.title,
          description: editing.description ?? '',
          start: editing.start,
          end: editing.end,
          all_day: editing.all_day ?? false,
        };
        const ok = await onCreate(createPayload);
        if (ok) {
          push('success', 'Ereignis erstellt');
          setEditing(null);
        }
      } else {
        const payload: components['schemas']['EventUpdate'] = {
          title: editing.title,
          description: editing.description ?? undefined,
          start: editing.start,
          end: editing.end,
          all_day: editing.all_day ?? false,
        };
        const ok = await onUpdate(editing.id, payload);
        if (ok) {
          push('success', 'Ereignis gespeichert');
          setEditing(null);
        }
      }
    } catch (err: any) {
      push('error', 'Speichern fehlgeschlagen: ' + String(err));
    }
  }

  function requestRemove(id: string) {
    setConfirmEventId(id);
    setConfirmOpen(true);
  }

  async function confirmRemove() {
    if (!confirmEventId) return;
    setIsConfirming(true);
    try {
      const ok = await onRemove(confirmEventId);
      if (ok) push('success', 'Ereignis gelöscht');
      else push('error', 'Löschen fehlgeschlagen');
    } catch (err: any) {
      push('error', 'Löschen fehlgeschlagen: ' + String(err));
    } finally {
      setIsConfirming(false);
      setConfirmOpen(false);
      setConfirmEventId(null);
    }
  }

  return (
    <div>
      <Modal
        isOpen={confirmOpen}
        title="Ereignis löschen"
        onClose={() => setConfirmOpen(false)}
        onConfirm={() => void confirmRemove()}
        confirmLabel="Löschen"
        confirmDisabled={isConfirming}
      >
        <div className="text-sm text-text-soft dark:text-gray-300">
          Soll das Ereignis wirklich gelöscht werden?
        </div>
      </Modal>

      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay',
        }}
        events={fcEvents}
        editable
        selectable
        dateClick={handleDateClick}
        eventClick={handleEventClick}
        eventDrop={handleEventDrop}
        height="auto"
      />

      {/* Bearbeitungsmodal (verbessert) */}
      {editing && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
          role="presentation"
          onClick={(e) => {
            if (e.target === e.currentTarget) setEditing(null);
          }}
        >
          <div
            className="w-full max-w-lg rounded-2xl border border-border-soft bg-white p-6 shadow-2xl dark:border-white/10 dark:bg-slate-900"
            role="dialog"
            aria-modal="true"
            aria-labelledby="event-editor-title"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Kopfzeile */}
            <div className="flex items-center justify-between mb-4">
              <h4 id="event-editor-title" className="text-lg font-semibold text-text dark:text-white">
                {editing.id === '__new' ? 'Neues Ereignis' : 'Ereignis bearbeiten'}
              </h4>
              <button
                type="button"
                className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
                onClick={() => setEditing(null)}
                aria-label="Schließen"
                title="Schließen"
              >
                <IconBadge icon={<X />} size="sm" variant="default" />
              </button>
            </div>

            {/* Formularfelder */}
            <div className="space-y-4">
              <div>
                <label htmlFor="event-title" className="block text-sm font-medium text-text-soft dark:text-gray-300">
                  Titel
                </label>
                <input
                  id="event-title"
                  className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                  value={editing.title}
                  onChange={(e) => setEditing({ ...editing, title: e.target.value })}
                />
              </div>

              <div>
                <label htmlFor="event-description" className="block text-sm font-medium text-text-soft dark:text-gray-300">
                  Beschreibung
                </label>
                <textarea
                  id="event-description"
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                  value={editing.description ?? ''}
                  onChange={(e) => setEditing({ ...editing, description: e.target.value })}
                />
              </div>

              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-text-soft dark:text-gray-300">
                  <input
                    type="checkbox"
                    checked={!!editing.all_day}
                    onChange={(e) => setEditing({ ...editing, all_day: e.target.checked })}
                    className="rounded border-border-soft text-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10"
                  />
                  Ganztägig
                </label>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="event-start" className="block text-sm font-medium text-text-soft dark:text-gray-300">
                    Start
                  </label>
                  <input
                    id="event-start"
                    type="datetime-local"
                    className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                    value={new Date(editing.start).toISOString().slice(0, 16)}
                    onChange={(e) => setEditing({ ...editing, start: new Date(e.target.value).toISOString() })}
                  />
                </div>
                <div>
                  <label htmlFor="event-end" className="block text-sm font-medium text-text-soft dark:text-gray-300">
                    Ende
                  </label>
                  <input
                    id="event-end"
                    type="datetime-local"
                    className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                    value={new Date(editing.end).toISOString().slice(0, 16)}
                    onChange={(e) => setEditing({ ...editing, end: new Date(e.target.value).toISOString() })}
                  />
                </div>
              </div>
            </div>

            {/* Aktionsleiste */}
            <div className="mt-6 flex flex-wrap items-center justify-end gap-2">
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-lg border border-border-soft px-4 py-2 text-sm font-medium text-text-soft transition hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:border-white/10 dark:text-gray-300 dark:hover:bg-slate-800"
                onClick={() => setEditing(null)}
              >
                Abbrechen
              </button>

              {editing.id !== '__new' && (
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-danger px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-danger-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger focus-visible:ring-offset-2 dark:bg-danger/80 dark:hover:bg-danger"
                  onClick={() => {
                    const id = editing.id;
                    setEditing(null);
                    requestRemove(id);
                  }}
                  aria-label="Ereignis löschen"
                >
                  <IconBadge icon={<Trash2 />} size="sm" variant="default" />
                  <span>Löschen</span>
                </button>
              )}

              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:bg-primary/80 dark:hover:bg-primary"
                onClick={() => void handleSaveEdit()}
              >
                <IconBadge icon={<Save />} size="sm" variant="default" />
                <span>Speichern</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}