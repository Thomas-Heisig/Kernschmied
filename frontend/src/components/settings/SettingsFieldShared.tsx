import type { ChangeEvent, ReactNode } from 'react';
import type { ConfigValue } from '../../contracts/config';

export interface SettingsInputContainerProps {
  fieldId: string;
  fieldKey: string;
  label: string;
  children: ReactNode;
  description?: string;
  error?: string | null;
  required?: boolean;
  disabled?: boolean;
  readOnly?: boolean;
}

export function SettingsInputContainer({
  fieldId,
  fieldKey,
  label,
  children,
  description,
  error,
  required = false,
  disabled = false,
  readOnly = false,
}: SettingsInputContainerProps) {
  return (
    <div
      className={[
        'rounded-xl border border-slate-200 bg-white p-4',
        'dark:border-white/10 dark:bg-slate-900/40',
        disabled || readOnly ? 'opacity-75' : '',
      ].join(' ')}
    >
      <label htmlFor={fieldId} className="block font-medium text-slate-900 dark:text-white">
        {label}

        {required ? (
          <span className="ml-1 text-red-600 dark:text-red-400" aria-hidden="true">
            *
          </span>
        ) : null}
      </label>

      {description ? (
        <p className="mt-1 text-sm leading-5 text-slate-600 dark:text-slate-400">{description}</p>
      ) : null}

      <FieldMetadata fieldKey={fieldKey} disabled={disabled} readOnly={readOnly} />

      <div className="mt-3">{children}</div>

      {error ? (
        <p
          id={`${fieldId}-error`}
          className="mt-2 text-sm font-medium text-red-700 dark:text-red-300"
          role="alert"
        >
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function FieldMetadata({
  fieldKey,
  disabled,
  readOnly,
}: {
  fieldKey: string;
  disabled: boolean;
  readOnly: boolean;
}) {
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
      <code className="rounded bg-slate-100 px-2 py-1 text-slate-500 dark:bg-white/5 dark:text-slate-400">
        {fieldKey}
      </code>

      {readOnly ? (
        <span className="rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
          Schreibgeschützt
        </span>
      ) : null}

      {disabled && !readOnly ? (
        <span className="rounded-full bg-amber-100 px-2 py-1 font-medium text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">
          Deaktiviert
        </span>
      ) : null}
    </div>
  );
}

export function serializeOptionValue(value: ConfigValue): string {
  if (value === null) {
    return '';
  }

  return JSON.stringify(value);
}

export const inputClassName = [
  'block w-full rounded-lg',
  'border border-slate-300',
  'bg-white px-3 py-2',
  'text-sm text-slate-900',
  'shadow-sm outline-none',
  'transition',
  'placeholder:text-slate-400',
  'focus:border-blue-500',
  'focus:ring-2',
  'focus:ring-blue-500/20',
  'invalid:border-red-400',
  'disabled:cursor-not-allowed',
  'disabled:bg-slate-100',
  'disabled:opacity-70',
  'dark:border-white/10',
  'dark:bg-slate-950/60',
  'dark:text-white',
  'dark:invalid:border-red-500',
  'dark:disabled:bg-slate-900',
].join(' ');

export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export function isValidHttpUrl(value: string): boolean {
  try {
    const parsedUrl = new URL(value.trim());

    return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:';
  } catch {
    return false;
  }
}

export function includesAny(value: string, candidates: string[]): boolean {
  return candidates.some((candidate) => value.includes(candidate));
}
