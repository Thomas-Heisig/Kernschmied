// F:\Kernschmied\frontend\src\components\errors\UnsupportedSchema.tsx

import { memo } from "react";

export interface UnsupportedSchemaProps {
  /**
   * Typ aus dem Backend-Schema.
   * Beispiele:
   *  - ui.form
   *  - ui.table
   *  - custom.my_component
   */
  kind: string;

  /**
   * Optionaler Anzeigename.
   */
  title?: string;

  /**
   * Optionaler zusätzlicher Hinweis.
   */
  message?: string;

  /**
   * Vollständiges Schema für Debugzwecke.
   * Wird nur im Development angezeigt.
   */
  schema?: unknown;

  /**
   * Zusätzliche CSS-Klassen.
   */
  className?: string;
}

function UnsupportedSchemaComponent({
  kind,
  title = "Nicht unterstützte UI-Komponente",
  message,
  schema,
  className,
}: UnsupportedSchemaProps) {
  const isDevelopment = import.meta.env.DEV;

  return (
    <section
      className={[
        "animate-fade-in",
        "rounded-xl",
        "border",
        "border-warning/30",
        "bg-warning-soft",
        "p-4",
        "text-sm",
        "text-warning",
        "dark:border-warning/20",
        "dark:bg-warning-soft/20",
        "dark:text-warning",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      role="alert"
      aria-live="polite"
    >
      <h3 className="mb-2 font-semibold text-warning dark:text-warning">
        {title}
      </h3>

      <p className="mb-2 text-text-soft dark:text-gray-300">
        Für den vom Backend gelieferten Schema-Typ existiert derzeit keine
        registrierte React-Komponente.
      </p>

      <div className="rounded-lg bg-surface-muted px-3 py-2 text-text dark:bg-slate-800/60 dark:text-gray-200">
        <span className="font-medium">Schema-Typ:</span>{" "}
        <code className="font-mono text-warning dark:text-warning/80">
          {kind}
        </code>
      </div>

      {message && (
        <p className="mt-3 text-text-soft dark:text-gray-300">{message}</p>
      )}

      {isDevelopment && schema !== undefined && (
        <details className="mt-4">
          <summary className="cursor-pointer font-medium text-text-soft dark:text-gray-300 hover:text-text dark:hover:text-white">
            Debug-Informationen
          </summary>

          <pre className="mt-2 max-h-60 overflow-auto rounded-lg border border-border-soft bg-slate-900 p-3 text-xs text-slate-100 dark:border-white/5">
            {JSON.stringify(schema, null, 2)}
          </pre>
        </details>
      )}
    </section>
  );
}

export const UnsupportedSchema = memo(UnsupportedSchemaComponent);
