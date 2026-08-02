import React from 'react';
import { Check, Clipboard } from 'lucide-react';

const secondaryButtonClassName = [
  'inline-flex items-center justify-center gap-2 rounded-lg',
  'border border-slate-300 bg-white px-3.5 py-2',
  'text-sm font-medium text-slate-700 transition',
  'hover:bg-slate-50',
  'focus-visible:outline-none focus-visible:ring-2',
  'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
  'disabled:cursor-not-allowed disabled:opacity-50',
  'dark:border-white/10 dark:bg-white/5 dark:text-slate-200',
  'dark:hover:bg-white/10 dark:focus-visible:ring-offset-slate-950',
].join(' ');

const primaryButtonClassName = [
  'inline-flex items-center justify-center gap-2 rounded-lg',
  'bg-blue-600 px-4 py-2 text-sm font-medium text-white',
  'transition hover:bg-blue-700',
  'focus-visible:outline-none focus-visible:ring-2',
  'focus-visible:ring-blue-500 focus-visible:ring-offset-2',
  'disabled:cursor-not-allowed disabled:opacity-50',
  'dark:focus-visible:ring-offset-slate-950',
].join(' ');

export default function SettingsJsonEditor({
  value,
  error,
  disabled,
  isDirty,
  copied,
  onChange,
  onApply,
  onFormat,
  onReset,
  onCopy,
}: {
  value: string;
  error: string | null;
  disabled: boolean;
  isDirty: boolean;
  copied: boolean;
  onChange: (value: string) => void;
  onApply: () => void;
  onFormat: () => void;
  onReset: () => void;
  onCopy: () => void;
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900/50">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="font-semibold text-slate-950 dark:text-white">JSON-Konfiguration</h2>

            {isDirty ? <span className="rounded-full px-2.5 py-1 text-xs font-medium bg-amber-100 text-amber-800">Bearbeitet</span> : null}
          </div>

          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            Es werden ausschließlich gültige Kernschmied-Konfigurationswerte übernommen. Zusätzliche
            Felder können vom Backend abgelehnt werden.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className={secondaryButtonClassName}
            disabled={disabled}
            onClick={onCopy}
          >
            {copied ? (
              <Check size={15} aria-hidden="true" />
            ) : (
              <Clipboard size={15} aria-hidden="true" />
            )}

            <span>{copied ? 'Kopiert' : 'Kopieren'}</span>
          </button>

          <button
            type="button"
            className={secondaryButtonClassName}
            disabled={disabled}
            onClick={onFormat}
          >
            Formatieren
          </button>

          <button
            type="button"
            className={secondaryButtonClassName}
            disabled={disabled || !isDirty}
            onClick={onReset}
          >
            Zurücksetzen
          </button>

          <button
            type="button"
            className={primaryButtonClassName}
            disabled={disabled || !isDirty}
            onClick={onApply}
          >
            JSON übernehmen
          </button>
        </div>
      </div>

      <textarea
        rows={30}
        value={value}
        disabled={disabled}
        spellCheck={false}
        aria-label="JSON-Konfiguration"
        aria-invalid={error !== null}
        aria-describedby={error ? 'settings-json-error' : 'settings-json-help'}
        className={[
          'mt-5 block w-full resize-y rounded-xl border',
          error ? 'border-red-400' : 'border-slate-300',
          'bg-slate-950 p-4 font-mono text-sm leading-6 text-slate-100',
          'outline-none transition',
          'focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',
          'disabled:cursor-not-allowed disabled:opacity-60',
          'dark:border-white/10',
        ].join(' ')}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />

      <p id="settings-json-help" className="mt-3 text-xs text-slate-500 dark:text-slate-400">
        Änderungen werden erst nach „JSON übernehmen“ in den lokalen Konfigurationsentwurf
        übernommen. Das Speichern erfolgt anschließend über die Hauptaktion „Speichern“.
      </p>

      {error ? (
        <p
          id="settings-json-error"
          className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm font-medium text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </section>
  );
}
