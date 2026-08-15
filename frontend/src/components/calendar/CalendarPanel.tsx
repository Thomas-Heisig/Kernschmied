// F:\Kernschmied\frontend\src\components\calendar\CalendarPanel.tsx

import React, { useEffect, useState } from 'react';
import { Plus, Trash2, X } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import { useToast } from '../ui/ToastProvider';
import Modal from '../ui/Modal';
import type { components } from '../../api/openapi-types';
import CalendarView from './CalendarView';
import * as api from '../../api/fetchCalendarClient';

export default function CalendarPanel({ onClose }: { onClose: () => void }) {
  const [calendarsState, setCalendarsState] = useState<components['schemas']['CalendarOut'][]>([]);
  const [selectedCalendarId, setSelectedCalendarId] = useState<string | null>(null);
  const [eventsState, setEventsState] = useState<components['schemas']['EventOut'][]>([]);
  const [loadingCals, setLoadingCals] = useState(false);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [newCalName, setNewCalName] = useState('');

  const { push } = useToast();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmActionId, setConfirmActionId] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  const loadCalendars = async () => {
    setLoadingCals(true);
    try {
      const c = await api.listCalendars();
      setCalendarsState(c || []);
      if (!selectedCalendarId && c && c.length) setSelectedCalendarId(c[0].id);
    } catch (err) {
      push('error', 'Kalender konnten nicht geladen werden');
    } finally {
      setLoadingCals(false);
    }
  };

  const loadEvents = async (calendarId: string | null) => {
    if (!calendarId) return setEventsState([]);
    setLoadingEvents(true);
    try {
      const start = new Date();
      const end = new Date();
      end.setMonth(end.getMonth() + 1);
      const events = await api.listEvents(calendarId, {
        time_min: start.toISOString(),
        time_max: end.toISOString(),
      });
      setEventsState(events || []);
    } catch (err) {
      push('error', 'Ereignisse konnten nicht geladen werden');
    } finally {
      setLoadingEvents(false);
    }
  };

  useEffect(() => {
    void loadCalendars();
  }, []);

  useEffect(() => {
    void loadEvents(selectedCalendarId);
  }, [selectedCalendarId]);

  const handleAddCalendar = async () => {
    if (!newCalName.trim()) return;
    try {
      await api.createCalendar({ name: newCalName.trim() } as any);
      setNewCalName('');
      void loadCalendars();
      push('success', 'Kalender erstellt');
    } catch (err) {
      push('error', 'Kalender konnte nicht erstellt werden');
    }
  };

  const handleRemoveCalendar = async (id: string) => {
    setConfirmActionId(id);
    setConfirmOpen(true);
  };

  async function confirmRemoveCalendar() {
    if (!confirmActionId) return;
    setIsConfirming(true);
    try {
      await api.deleteCalendar(confirmActionId);
      push('success', 'Kalender gelöscht');
      if (selectedCalendarId === confirmActionId) setSelectedCalendarId(null);
      void loadCalendars();
    } catch (err) {
      push('error', 'Löschen fehlgeschlagen');
    } finally {
      setIsConfirming(false);
      setConfirmOpen(false);
      setConfirmActionId(null);
    }
  }

  const handleCreateEvent = async (payload: components['schemas']['EventCreate']) => {
    if (!selectedCalendarId) return false;
    try {
      await api.createEvent(selectedCalendarId, payload);
      void loadEvents(selectedCalendarId);
      push('success', 'Ereignis erstellt');
      return true;
    } catch (err) {
      push('error', 'Ereignis konnte nicht erstellt werden');
      return false;
    }
  };

  const handleUpdateEvent = async (id: string, payload: components['schemas']['EventUpdate']) => {
    if (!selectedCalendarId) return false;
    try {
      await api.patchEvent(selectedCalendarId, id, payload);
      void loadEvents(selectedCalendarId);
      push('success', 'Ereignis aktualisiert');
      return true;
    } catch (err) {
      push('error', 'Aktualisierung fehlgeschlagen');
      return false;
    }
  };

  const handleRemoveEvent = async (id: string) => {
    if (!selectedCalendarId) return false;
    try {
      await api.deleteEvent(selectedCalendarId, id);
      void loadEvents(selectedCalendarId);
      push('success', 'Ereignis gelöscht');
      return true;
    } catch (err) {
      push('error', 'Löschen fehlgeschlagen');
      return false;
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full max-h-[90vh] overflow-auto bg-white p-6 shadow-2xl dark:bg-slate-900"
        role="dialog"
        aria-modal="true"
        aria-labelledby="calendar-panel-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Kopfzeile */}
        <div className="flex items-center justify-between mb-6">
          <h3 id="calendar-panel-title" className="text-lg font-semibold text-text dark:text-white">
            Kalenderverwaltung
          </h3>
          <button
            type="button"
            className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
            onClick={onClose}
            aria-label="Kalender schließen"
            title="Schließen"
          >
            <IconBadge icon={<X />} size="sm" variant="default" />
          </button>
        </div>

        {/* Inhalt: 2 Spalten */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {/* Linke Spalte: Kalenderliste + Hinzufügen */}
          <div className="space-y-4">
            <div>
              <label htmlFor="new-calendar-name" className="sr-only">
                Neuer Kalendername
              </label>
              <div className="flex gap-2">
                <input
                  id="new-calendar-name"
                  className="flex-1 rounded-lg border border-border-soft bg-surface-muted px-3 py-2 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
                  placeholder="Neuer Kalendername"
                  value={newCalName}
                  onChange={(e) => setNewCalName(e.target.value)}
                />
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 dark:bg-primary/80 dark:hover:bg-primary"
                  onClick={handleAddCalendar}
                  disabled={!newCalName.trim()}
                  aria-label="Kalender hinzufügen"
                >
                  <IconBadge icon={<Plus />} size="sm" variant="default" />
                  <span>Hinzufügen</span>
                </button>
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted dark:text-gray-500">
                Kalender
              </h4>
              {loadingCals ? (
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
                  Lade…
                </div>
              ) : (
                <ul className="space-y-1.5">
                  {calendarsState.map((c) => {
                    const isActive = selectedCalendarId === c.id;
                    return (
                      <li
                        key={c.id}
                        className={[
                          'flex items-center gap-2 rounded-lg px-3 py-2 transition-colors',
                          isActive
                            ? 'bg-primary-soft dark:bg-primary/20'
                            : 'hover:bg-surface-hover dark:hover:bg-slate-800',
                        ].join(' ')}
                      >
                        <button
                          type="button"
                          className={[
                            'flex-1 truncate text-left text-sm font-medium',
                            isActive ? 'text-primary dark:text-primary' : 'text-text-soft dark:text-gray-300',
                          ].join(' ')}
                          onClick={() => setSelectedCalendarId(c.id)}
                        >
                          {c.name}
                        </button>
                        <button
                          type="button"
                          className="rounded p-1 text-text-muted transition hover:bg-danger-soft hover:text-danger focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-danger dark:text-gray-400 dark:hover:bg-danger/10 dark:hover:text-danger"
                          onClick={() => handleRemoveCalendar(c.id)}
                          aria-label={`Kalender "${c.name}" löschen`}
                          title="Kalender löschen"
                        >
                          <IconBadge icon={<Trash2 />} size="sm" variant="default" />
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          {/* Rechte Spalte: CalendarView */}
          <div className="md:col-span-2">
            {selectedCalendarId ? (
              loadingEvents ? (
                <div className="flex items-center justify-center py-12 text-text-muted">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-primary/60" />
                  <span className="ml-2">Lade Ereignisse…</span>
                </div>
              ) : (
                <CalendarView
                  events={eventsState}
                  onCreate={handleCreateEvent}
                  onUpdate={handleUpdateEvent}
                  onRemove={handleRemoveEvent}
                />
              )
            ) : (
              <div className="flex h-full min-h-50 items-center justify-center rounded-xl border border-dashed border-border-soft text-sm text-text-muted dark:border-white/10">
                Kein Kalender ausgewählt
              </div>
            )}
          </div>
        </div>

        {/* Bestätigungsmodal */}
        <Modal
          isOpen={confirmOpen}
          title="Kalender löschen"
          onClose={() => setConfirmOpen(false)}
          onConfirm={() => void confirmRemoveCalendar()}
          confirmLabel="Löschen"
          confirmDisabled={isConfirming}
        >
          <div className="text-sm text-text-soft dark:text-gray-300">
            Soll der Kalender wirklich gelöscht werden?
          </div>
        </Modal>
      </div>
    </div>
  );
}