// F:\Kernschmied\frontend\src\components\schema\UnsupportedSchemaComponent.tsx

import React, { memo } from 'react';
import { AlertTriangle } from 'lucide-react';
import IconBadge from '../common/IconBadge';

export interface UnsupportedProps {
  /** Der nicht unterstützte Schema‑Typ (z. B. 'unknown_component') */
  type?: string;
  /** Die vollständige Schema‑Definition (für Debug‑Zwecke) */
  definition?: any;
}

/**
 * Fallback‑Komponente für nicht unterstützte Schema‑Typen.
 * Wird im SchemaRenderer verwendet, wenn kein Renderer registriert ist.
 */
function UnsupportedSchemaComponent({ type, definition }: UnsupportedProps) {
  const isDevelopment = import.meta.env.DEV;

  return (
    <div
      className="rounded-xl border border-danger/20 bg-danger-soft p-4 text-sm text-danger dark:border-danger/30 dark:bg-danger/10"
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <div aria-hidden="true">
          <IconBadge icon={<AlertTriangle />} size="lg" variant="danger" />
        </div>

        <div className="min-w-0 flex-1">
          <h4 className="font-semibold text-danger dark:text-danger">
            Nicht unterstützter Schema‑Typ
          </h4>

          <p className="mt-1 text-text-soft dark:text-gray-300">
            {type ? (
              <>
                Der vom Backend gelieferte Typ <code className="font-mono">{type}</code> wird von dieser
                Anwendung nicht unterstützt.
              </>
            ) : (
              'Der vom Backend gelieferte Schema‑Typ wird von dieser Anwendung nicht unterstützt.'
            )}
          </p>

          {isDevelopment && definition !== undefined && (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs font-medium text-text-muted hover:text-text dark:text-gray-400 dark:hover:text-white">
                Debug‑Informationen
              </summary>
              <pre className="mt-2 max-h-60 overflow-auto rounded-lg border border-border-soft bg-slate-900 p-3 text-xs text-slate-100 dark:border-white/5">
                {JSON.stringify(definition ?? {}, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

export default memo(UnsupportedSchemaComponent);