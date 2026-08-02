import React from 'react';
import { Search, X } from 'lucide-react';

export default function SettingsSearch({
  value,
  resultCount,
  onChange,
  onClear,
}: {
  value: string;
  resultCount?: number;
  onChange: (value: string) => void;
  onClear: () => void;
}) {
  return (
    <div className="mt-4 flex max-w-2xl items-center gap-2">
      <div className="relative min-w-0 flex-1">
        <Search
          size={16}
          aria-hidden="true"
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />

        <input
          type="search"
          value={value}
          placeholder="Einstellungen durchsuchen …"
          aria-label="Einstellungen durchsuchen"
          className={[
            'block w-full rounded-lg border border-slate-300',
            'bg-white py-2 pl-9 pr-10 text-sm text-slate-900',
            'outline-none transition',
            'placeholder:text-slate-400',
            'focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20',
            'dark:border-white/10 dark:bg-slate-900 dark:text-white',
          ].join(' ')}
          onChange={(event) => {
            onChange(event.target.value);
          }}
        />

        {value ? (
          <button
            type="button"
            className={[
              'absolute right-1.5 top-1/2 inline-flex h-7 w-7',
              '-translate-y-1/2 items-center justify-center rounded-md',
              'text-slate-400 transition hover:bg-slate-100 hover:text-slate-700',
              'dark:hover:bg-white/10 dark:hover:text-white',
            ].join(' ')}
            aria-label="Suche löschen"
            onClick={onClear}
          >
            <X size={15} aria-hidden="true" />
          </button>
        ) : null}
      </div>

      {resultCount !== undefined ? (
        <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 dark:bg-white/10 dark:text-slate-300">
          {resultCount}
        </span>
      ) : null}
    </div>
  );
}
