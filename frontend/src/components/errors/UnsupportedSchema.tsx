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
        "rounded-lg",
        "border",
        "border-amber-400",
        "bg-amber-50",
        "p-4",
        "text-sm",
        "text-amber-900",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      role="alert"
      aria-live="polite"
    >
      <h3 className="mb-2 font-semibold">
        {title}
      </h3>

      <p className="mb-2">
        Für den vom Backend gelieferten Schema-Typ existiert
        derzeit keine registrierte React-Komponente.
      </p>

      <div className="rounded bg-white/70 px-3 py-2">
        <span className="font-medium">Schema-Typ:</span>{" "}
        <code className="font-mono">{kind}</code>
      </div>

      {message && (
        <p className="mt-3">
          {message}
        </p>
      )}

      {isDevelopment && schema !== undefined && (
        <details className="mt-4">
          <summary className="cursor-pointer font-medium">
            Debug-Informationen
          </summary>

          <pre className="mt-2 overflow-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
            {JSON.stringify(schema, null, 2)}
          </pre>
        </details>
      )}
    </section>
  );
}

export const UnsupportedSchema = memo(UnsupportedSchemaComponent);