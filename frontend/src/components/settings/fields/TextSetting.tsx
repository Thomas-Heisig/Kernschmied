import React, { useState, useEffect } from "react";
import type { ConfigValue, ConfigEntryResponse } from "../../../contracts/config";
import { SettingsInputContainer, inputClassName, isValidEmail, isValidHttpUrl } from "../SettingsFieldShared";

interface Props {
  entry: ConfigEntryResponse;
  path: string[];
  value: ConfigValue;
  kind?: "text" | "password" | "email" | "url" | "multiline";
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}

export default function TextSetting({
  entry,
  path,
  value,
  kind = "text",
  disabled = false,
  readOnly = false,
  required = false,
  onChange,
}: Props) {
  const [textDraft, setTextDraft] = useState(() => (typeof value === "string" ? value : value === null ? "" : String(value)));
  const [validationError, setValidationError] = useState<string | null>(null);

  useEffect(() => {
    setTextDraft(typeof value === "string" ? value : value === null ? "" : String(value));
    setValidationError(null);
  }, [value]);

  const fieldId = ["setting", entry.full_key].join("-").replace(/[^a-zA-Z0-9_-]/g, "-");

  function validateText(next: string): string | null {
    if (required && next.trim() === "") {
      return "Dieses Feld darf nicht leer sein.";
    }

    if (next.trim() === "") {
      return null;
    }

    if (kind === "email" && !isValidEmail(next)) {
      return "Bitte eine gültige E-Mail-Adresse eingeben.";
    }

    if (kind === "url" && !isValidHttpUrl(next)) {
      return "Bitte eine gültige HTTP- oder HTTPS-Adresse eingeben.";
    }

    return null;
  }

  if (kind === "multiline") {
    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={entry.full_key}
        label={entry.display_name}
        description={entry.description}
        error={validationError}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      >
        <textarea
          id={fieldId}
          rows={6}
          value={textDraft}
          disabled={disabled || readOnly}
          required={required}
          placeholder={entry.ui.placeholder ?? undefined}
          spellCheck
          aria-invalid={validationError !== null}
          aria-describedby={validationError ? `${fieldId}-error` : undefined}
          className={[inputClassName, "resize-y leading-6"].join(" ")}
          onChange={(event) => {
            const nextValue = event.target.value;

            setTextDraft(nextValue);

            const error = required && nextValue.trim() === "" ? "Dieses Feld darf nicht leer sein." : null;

            setValidationError(error);

            if (error === null) {
              onChange(path, nextValue);
            }
          }}
        />
      </SettingsInputContainer>
    );
  }

  const inputType = kind === "password" ? "password" : kind === "email" ? "email" : kind === "url" ? "url" : "text";

  return (
    <SettingsInputContainer
      fieldId={fieldId}
      fieldKey={entry.full_key}
      label={entry.display_name}
      description={entry.description}
      error={validationError}
      required={required}
      disabled={disabled}
      readOnly={readOnly}
    >
      <input
        id={fieldId}
        type={inputType}
        value={textDraft}
        disabled={disabled || readOnly}
        required={required}
        placeholder={entry.ui.placeholder ?? undefined}
        autoComplete={kind === "password" ? "new-password" : "off"}
        spellCheck={kind === "text"}
        aria-invalid={validationError !== null}
        aria-describedby={validationError ? `${fieldId}-error` : undefined}
        className={inputClassName}
        onChange={(event) => {
          const nextValue = event.target.value;

          setTextDraft(nextValue);

          const error = validateText(nextValue);

          setValidationError(error);

          if (error === null) {
            onChange(path, nextValue);
          }
        }}
      />

      {kind === "password" ? (
        <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
          Sensible Werte sollten nur als Secret-Referenz und nicht als Klartext gespeichert werden.
        </p>
      ) : null}
    </SettingsInputContainer>
  );
}
