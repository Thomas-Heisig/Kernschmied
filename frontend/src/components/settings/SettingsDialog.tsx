// F:\Kernschmied\frontend\src\components\settings\SettingsDialog.tsx

import { useEffect, useId, useRef, useState } from 'react';

import type { KeyboardEvent as ReactKeyboardEvent, MouseEvent as ReactMouseEvent } from 'react';

import { Menu, Settings, X } from 'lucide-react';

import { useSystemConfig } from '../../hooks/useSystemConfig';
import { SettingsContent } from './SettingsContent';
import { SettingsSidebar } from './SettingsSidebar';

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const SETTINGS_CATALOG_KEY = 'settings-catalog';

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const dialogId = useId();
  const titleId = `${dialogId}-title`;
  const descriptionId = `${dialogId}-description`;

  const dialogRef = useRef<HTMLElement | null>(null);

  const closeButtonRef = useRef<HTMLButtonElement | null>(null);

  const previouslyFocusedElementRef = useRef<HTMLElement | null>(null);

  const config = useSystemConfig();

  const [activeKey, setActiveKey] = useState<string | null>(SETTINGS_CATALOG_KEY);

  const [showJson, setShowJson] = useState(false);

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const [showCloseConfirmation, setShowCloseConfirmation] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    setActiveKey(SETTINGS_CATALOG_KEY);

    setShowJson(false);
    setIsSidebarOpen(false);
    setShowCloseConfirmation(false);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    previouslyFocusedElementRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = 'hidden';

    const focusTimeout = window.setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 0);

    function handleDocumentKeyDown(event: KeyboardEvent): void {
      if (event.key === 'Escape') {
        event.preventDefault();

        if (showCloseConfirmation) {
          setShowCloseConfirmation(false);
          return;
        }

        if (isSidebarOpen) {
          setIsSidebarOpen(false);
          return;
        }

        requestClose();
        return;
      }

      if (event.key === 'Tab') {
        trapFocus(event, dialogRef.current);
      }
    }

    window.addEventListener('keydown', handleDocumentKeyDown);

    return () => {
      window.clearTimeout(focusTimeout);

      document.body.style.overflow = previousOverflow;

      window.removeEventListener('keydown', handleDocumentKeyDown);

      previouslyFocusedElementRef.current?.focus();
    };
  }, [isOpen, isSidebarOpen, showCloseConfirmation, config.isDirty]);

  if (!isOpen) {
    return null;
  }

  function requestClose(): void {
    if (config.isDirty && !showCloseConfirmation) {
      setShowCloseConfirmation(true);
      return;
    }

    onClose();
  }

  function handleConfirmDiscard(): void {
    config.reset();
    setShowCloseConfirmation(false);
    onClose();
  }

  function handleCancelClose(): void {
    setShowCloseConfirmation(false);
    closeButtonRef.current?.focus();
  }

  function handleBackdropMouseDown(event: ReactMouseEvent<HTMLDivElement>): void {
    if (event.target !== event.currentTarget) {
      return;
    }

    requestClose();
  }

  function handleDialogKeyDown(event: ReactKeyboardEvent<HTMLElement>): void {
    if (event.key === 'Escape') {
      event.stopPropagation();
    }
  }

  function handleSelectKey(key: string | null): void {
    setActiveKey(key);
    setShowJson(false);
    setIsSidebarOpen(false);
  }

  function handleSelectJson(): void {
    setShowJson(true);
    setActiveKey(null);
    setIsSidebarOpen(false);
  }

  const currentTitle = getCurrentViewTitle({
    activeKey,
    showJson,
  });

  return (
    <div
      className={[
        'fixed inset-0 z-50 flex items-center justify-center',
        'bg-slate-950/55 p-0 backdrop-blur-sm',
        'sm:p-4 lg:p-8',
      ].join(' ')}
      role="presentation"
      onMouseDown={handleBackdropMouseDown}
    >
      <section
        ref={dialogRef}
        className={[
          'relative flex min-h-0 w-full flex-col overflow-hidden',
          'border border-slate-200 bg-white shadow-2xl',
          'dark:border-white/10 dark:bg-slate-950',
          'h-dvh rounded-none',
          'sm:h-[min(92vh,960px)] sm:max-w-7xl sm:rounded-2xl',
        ].join(' ')}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onKeyDown={handleDialogKeyDown}
        onMouseDown={(event) => {
          event.stopPropagation();
        }}
      >
        <header
          className={[
            'flex min-h-16 shrink-0 items-center justify-between gap-4',
            'border-b border-slate-200 bg-white px-4',
            'dark:border-white/10 dark:bg-slate-950',
            'sm:px-5',
          ].join(' ')}
        >
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              className={[
                'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
                'text-slate-600 transition-colors',
                'hover:bg-slate-100 hover:text-slate-950',
                'focus-visible:outline-none focus-visible:ring-2',
                'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
                'dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
                'dark:focus-visible:ring-offset-slate-950',
                'md:hidden',
              ].join(' ')}
              aria-label="Einstellungsnavigation öffnen"
              aria-expanded={isSidebarOpen}
              aria-controls={`${dialogId}-sidebar`}
              onClick={() => {
                setIsSidebarOpen((current) => !current);
              }}
            >
              <Menu size={20} aria-hidden="true" />
            </button>

            <span
              className={[
                'hidden h-9 w-9 shrink-0 items-center justify-center rounded-lg',
                'bg-blue-50 text-blue-700',
                'dark:bg-blue-500/10 dark:text-blue-300',
                'sm:inline-flex',
              ].join(' ')}
              aria-hidden="true"
            >
              <Settings size={19} />
            </span>

            <div className="min-w-0">
              <h1
                id={titleId}
                className="truncate text-base font-semibold text-slate-950 dark:text-white"
              >
                Systemeinstellungen
              </h1>

              <p id={descriptionId} className="truncate text-xs text-slate-500 dark:text-slate-400">
                {currentTitle}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            {config.isDirty ? (
              <span
                className={[
                  'hidden rounded-full bg-amber-100 px-2.5 py-1',
                  'text-xs font-medium text-amber-800',
                  'dark:bg-amber-500/15 dark:text-amber-300',
                  'sm:inline-flex',
                ].join(' ')}
              >
                Nicht gespeichert
              </span>
            ) : null}

            <button
              ref={closeButtonRef}
              type="button"
              className={[
                'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
                'text-slate-600 transition-colors',
                'hover:bg-slate-100 hover:text-slate-950',
                'focus-visible:outline-none focus-visible:ring-2',
                'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
                'dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
                'dark:focus-visible:ring-offset-slate-950',
              ].join(' ')}
              aria-label="Einstellungen schließen"
              title="Schließen"
              onClick={requestClose}
            >
              <X size={19} aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="relative flex min-h-0 flex-1 overflow-hidden">
          {isSidebarOpen ? (
            <button
              type="button"
              className="absolute inset-0 z-20 bg-slate-950/35 md:hidden"
              aria-label="Navigation schließen"
              onClick={() => {
                setIsSidebarOpen(false);
              }}
            />
          ) : null}

          <aside
            id={`${dialogId}-sidebar`}
            className={[
              'absolute inset-y-0 left-0 z-30',
              'transform transition-transform duration-200',
              'md:static md:z-auto md:translate-x-0',
              isSidebarOpen ? 'translate-x-0' : '-translate-x-full',
            ].join(' ')}
          >
            <SettingsSidebar
                values={config.values}
                groups={config.groups}
              activeKey={activeKey}
              isJsonActive={showJson}
              onSelectKey={handleSelectKey}
              onSelectJson={handleSelectJson}
            />
          </aside>

          <main
            className={[
              'min-w-0 flex-1 overflow-y-auto',
              'bg-slate-50/60',
              'dark:bg-slate-950/30',
            ].join(' ')}
          >
            <SettingsContent activeKey={activeKey} showJson={showJson} config={config} allowLegacyValuesFallback={false} />
          </main>
        </div>

        {showCloseConfirmation ? (
          <CloseConfirmation
            isSaving={config.isSaving}
            onCancel={handleCancelClose}
            onDiscard={handleConfirmDiscard}
          />
        ) : null}
      </section>
    </div>
  );
}

function CloseConfirmation({
  isSaving,
  onCancel,
  onDiscard,
}: {
  isSaving: boolean;
  onCancel: () => void;
  onDiscard: () => void;
}) {
  const cancelButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    cancelButtonRef.current?.focus();
  }, []);

  return (
    <div
      className={[
        'absolute inset-0 z-50 flex items-center justify-center',
        'bg-slate-950/50 p-4 backdrop-blur-sm',
      ].join(' ')}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="settings-close-confirmation-title"
      aria-describedby="settings-close-confirmation-description"
    >
      <div
        className={[
          'w-full max-w-md rounded-2xl border border-slate-200',
          'bg-white p-5 shadow-2xl',
          'dark:border-white/10 dark:bg-slate-900',
        ].join(' ')}
      >
        <h2
          id="settings-close-confirmation-title"
          className="text-lg font-semibold text-slate-950 dark:text-white"
        >
          Änderungen verwerfen?
        </h2>

        <p
          id="settings-close-confirmation-description"
          className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400"
        >
          Es gibt nicht gespeicherte Änderungen. Beim Schließen werden diese Änderungen verworfen.
        </p>

        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            ref={cancelButtonRef}
            type="button"
            className={secondaryButtonClassName}
            onClick={onCancel}
          >
            Weiter bearbeiten
          </button>

          <button
            type="button"
            className={dangerButtonClassName}
            disabled={isSaving}
            onClick={onDiscard}
          >
            Änderungen verwerfen
          </button>
        </div>
      </div>
    </div>
  );
}

function getCurrentViewTitle({
  activeKey,
  showJson,
}: {
  activeKey: string | null;
  showJson: boolean;
}): string {
  if (showJson) {
    return 'Direkte Bearbeitung der Konfiguration als JSON';
  }

  if (activeKey === SETTINGS_CATALOG_KEY) {
    return 'Settings-Katalog und vorbereitete Systemressourcen';
  }

  if (activeKey === null) {
    return 'Alle verfügbaren Konfigurationswerte';
  }

  return formatTitle(activeKey);
}

function formatTitle(value: string): string {
  return value.replace(/[_-]+/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

function trapFocus(event: KeyboardEvent, container: HTMLElement | null): void {
  if (!container) {
    return;
  }

  const focusableElements = Array.from(
    container.querySelectorAll<HTMLElement>(
      [
        'a[href]',
        'button:not([disabled])',
        'input:not([disabled])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        '[tabindex]:not([tabindex="-1"])',
      ].join(','),
    ),
  ).filter(
    (element) => !element.hasAttribute('hidden') && element.getAttribute('aria-hidden') !== 'true',
  );

  if (focusableElements.length === 0) {
    event.preventDefault();
    container.focus();
    return;
  }

  const firstElement = focusableElements[0];

  const lastElement = focusableElements[focusableElements.length - 1];

  if (!firstElement || !lastElement) {
    return;
  }

  const activeElement = document.activeElement;

  if (event.shiftKey && activeElement === firstElement) {
    event.preventDefault();
    lastElement.focus();
    return;
  }

  if (!event.shiftKey && activeElement === lastElement) {
    event.preventDefault();
    firstElement.focus();
  }
}

const secondaryButtonClassName = [
  'rounded-lg border border-slate-300 bg-white px-3.5 py-2',
  'text-sm font-medium text-slate-700 transition',
  'hover:bg-slate-50',
  'focus-visible:outline-none focus-visible:ring-2',
  'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
  'dark:border-white/10 dark:bg-white/5 dark:text-slate-200',
  'dark:hover:bg-white/10 dark:focus-visible:ring-offset-slate-900',
].join(' ');

const dangerButtonClassName = [
  'rounded-lg bg-red-600 px-3.5 py-2',
  'text-sm font-medium text-white transition',
  'hover:bg-red-700',
  'focus-visible:outline-none focus-visible:ring-2',
  'focus-visible:ring-red-500 focus-visible:ring-offset-2',
  'disabled:cursor-not-allowed disabled:opacity-50',
  'dark:focus-visible:ring-offset-slate-900',
].join(' ');
