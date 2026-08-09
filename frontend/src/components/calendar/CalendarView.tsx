import React, { useMemo, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
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

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmEventId, setConfirmEventId] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

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
        <div className="text-sm">Soll das Ereignis wirklich gelöscht werden?</div>
      </Modal>
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{ left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay' }}
        events={fcEvents}
        editable
        selectable
        dateClick={handleDateClick}
        eventClick={handleEventClick}
        eventDrop={handleEventDrop}
        height="auto"
      />

      {editing ? (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <div className="bg-white p-4 rounded w-full max-w-md">
            <h4 className="font-semibold mb-2">Ereignis bearbeiten</h4>
            <input
              className="w-full rounded border px-2 py-1 text-sm mb-2"
              value={editing.title}
              onChange={(e) => setEditing({ ...editing, title: e.target.value })}
            />
            <textarea
              className="w-full rounded border px-2 py-1 text-sm mb-2"
              rows={3}
              value={editing.description ?? ''}
              onChange={(e) => setEditing({ ...editing, description: e.target.value })}
            />
            <div className="flex items-center gap-4 mb-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={!!editing.all_day}
                  onChange={(e) => setEditing({ ...editing, all_day: e.target.checked })}
                />
                Ganztägig
              </label>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="datetime-local"
                className="w-full rounded border px-2 py-1 text-sm"
                value={new Date(editing.start).toISOString().slice(0, 16)}
                onChange={(e) => setEditing({ ...editing, start: new Date(e.target.value).toISOString() })}
              />
              <input
                type="datetime-local"
                className="w-full rounded border px-2 py-1 text-sm"
                value={new Date(editing.end).toISOString().slice(0, 16)}
                onChange={(e) => setEditing({ ...editing, end: new Date(e.target.value).toISOString() })}
              />
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <button className="px-3 py-1" onClick={() => setEditing(null)}>
                Abbrechen
              </button>
              <button className="px-3 py-1 bg-sky-600 text-white rounded" onClick={() => void handleSaveEdit()}>
                Speichern
              </button>
              <button
                className="px-3 py-1 text-red-600"
                onClick={() => {
                  setEditing(null);
                  requestRemove(editing.id);
                }}
              >
                Löschen
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
