import React, { useState } from "react";
import type { ConfigValue, ConfigEntryResponse } from "../../../contracts/config";
import { SettingsInputContainer, inputClassName } from "../SettingsFieldShared";

type ComplexParseResult =
  | { ok: true; value: ConfigValue }
  | { ok: false; error: string };

function parseComplexValue(value: string): ComplexParseResult {
  if (value.trim() === "") {
    return { ok: false, error: "Der JSON-Wert darf nicht leer sein." };
  }

  try {
    const parsed = JSON.parse(value) as unknown;

    // minimal validation: allow object/array/primitive
    return { ok: true, value: parsed as ConfigValue };
  } catch {
    return { ok: false, error: "Der Wert enthält kein gültiges JSON." };
  }
}

function formatComplexValue(value: ConfigValue): string {
  if (typeof value !== "object" || value === null) return "";
  return JSON.stringify(value, null, 2);
}

export default function JsonSetting({ entry, path, value, disabled = false, readOnly = false, onChange }: {
  entry: ConfigEntryResponse;
  path: string[];
  value: ConfigValue;
  disabled?: boolean;
  readOnly?: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}) {
  const [complexDraft, setComplexDraft] = useState(formatComplexValue(value));
  const [validationError, setValidationError] = useState<string | null>(null);

  const fieldId = ["setting", entry.full_key].join("-").replace(/[^a-zA-Z0-9_-]/g, "-");

  return (
    <SettingsInputContainer
      fieldId={fieldId}
      fieldKey={entry.full_key}
      label={entry.display_name}
      description={entry.description}
      error={validationError}
      disabled={disabled}
      readOnly={readOnly}
    >
      <textarea
        id={fieldId}
        rows={10}
        value={complexDraft}
        disabled={disabled || readOnly}
        spellCheck={false}
        aria-invalid={validationError !== null}
        aria-describedby={validationError ? `${fieldId}-error` : undefined}
        className={[inputClassName, "resize-y font-mono text-xs leading-5"].join(" ")}
        onChange={(event) => {
          const next = event.target.value;
          setComplexDraft(next);

          const parsed = parseComplexValue(next);
          if (!parsed.ok) {
            setValidationError(parsed.error);
            return;
          }

          setValidationError(null);
          onChange(path, parsed.value);
        }}
        onBlur={() => {
          const parsed = parseComplexValue(complexDraft);
          if (!parsed.ok) return;
          setComplexDraft(formatComplexValue(parsed.value));
        }}
      />

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-500 dark:text-slate-400">Komplexer Wert im JSON-Format.</p>

        <button
          type="button"
          disabled={disabled || readOnly}
          className={[
            "rounded-md border border-slate-300 px-2.5 py-1",
            "text-xs font-medium text-slate-600 transition",
            "hover:bg-slate-50",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "dark:border-white/10 dark:text-slate-300",
            "dark:hover:bg-white/5",
          ].join(" ")}
          onClick={() => {
            const parsed = parseComplexValue(complexDraft);
            if (!parsed.ok) {
              setValidationError(parsed.error);
              return;
            }

            setComplexDraft(formatComplexValue(parsed.value));
            setValidationError(null);
          }}
        >
          JSON formatieren
        </button>
      </div>
    </SettingsInputContainer>
  );
}
