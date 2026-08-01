// F:\Kernschmied\frontend\src\components\settings\SettingsField.tsx

import { useEffect, useId, useMemo, useState } from "react";
import useConfigOptions from "../../hooks/useConfigApi";

import type { ChangeEvent, ReactNode } from "react";

import type { ConfigValue } from "../../contracts/config";

interface SettingsFieldProps {
  fieldKey: string;
  label: string;
  value: ConfigValue;
  path: string[];
  disabled?: boolean;
  description?: string;
  sensitive?: boolean;
  readOnly?: boolean;
  required?: boolean;
  placeholder?: string;
  minimum?: number;
  maximum?: number;
  step?: number;
  options?: SettingsFieldOption[];
  dynamicOptions?: {
    endpoint: string;
    depends_on?: string;
    dependency_parameter?: string;
  } | null;
  valuesByFullKey?: Record<string, ConfigValue> | null;
  onChange: (path: string[], value: ConfigValue) => void;
}

interface SettingsFieldOption {
  value: string | number | boolean;
  label: string;
  description?: string;
}

interface SettingsInputContainerProps {
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

type FieldKind =
  | "boolean"
  | "number"
  | "password"
  | "email"
  | "url"
  | "multiline"
  | "select"
  | "text"
  | "json";

export function SettingsField({
  fieldKey,
  label,
  value,
  path,
  disabled = false,
  description,
  sensitive,
  readOnly = false,
  required = false,
  placeholder,
  minimum,
  maximum,
  step,
  options,
  dynamicOptions = null,
  valuesByFullKey = null,
  onChange,
}: SettingsFieldProps) {
  const reactId = useId();

  const fieldId = useMemo(() => createFieldId(path, reactId), [path, reactId]);

  const effectiveDisabled = disabled || readOnly;

  const fieldKind = detectFieldKind({
    fieldKey,
    value,
    sensitive,
    options,
  });

  const [textDraft, setTextDraft] = useState(createTextDraft(value));

  const [complexDraft, setComplexDraft] = useState(formatComplexValue(value));

  const [validationError, setValidationError] = useState<string | null>(null);

  // Dynamic options state (component-local quick implementation)
  const {
    options: fetchedOptions,
    loading: optionsLoading,
    error: optionsError,
  } = useConfigOptions(
    dynamicOptions ?? null,
    (valuesByFullKey ?? null) as any,
  );

  useEffect(() => {
    setTextDraft(createTextDraft(value));

    setComplexDraft(formatComplexValue(value));

    setValidationError(null);
  }, [value]);

  if (fieldKind === "boolean") {
    const booleanValue = typeof value === "boolean" ? value : false;

    return (
      <div
        className={[
          "flex items-start justify-between gap-5 rounded-xl",
          "border border-slate-200 bg-white p-4",
          "dark:border-white/10 dark:bg-slate-900/40",
          effectiveDisabled ? "opacity-75" : "",
        ].join(" ")}
      >
        <div className="min-w-0 flex-1">
          <label
            htmlFor={fieldId}
            className="font-medium text-slate-900 dark:text-white"
          >
            {label}

            {required ? (
              <span
                className="ml-1 text-red-600 dark:text-red-400"
                aria-hidden="true"
              >
                *
              </span>
            ) : null}
          </label>

          {description ? (
            <p className="mt-1 text-sm leading-5 text-slate-600 dark:text-slate-400">
              {description}
            </p>
          ) : null}

          <FieldMetadata
            fieldKey={fieldKey}
            disabled={disabled}
            readOnly={readOnly}
          />
        </div>

        <button
          id={fieldId}
          type="button"
          role="switch"
          aria-checked={booleanValue}
          aria-label={label}
          disabled={effectiveDisabled}
          className={[
            "relative mt-0.5 inline-flex h-6 w-11 shrink-0",
            "rounded-full border-2 border-transparent",
            "transition-colors",
            "focus-visible:outline-none focus-visible:ring-2",
            "focus-visible:ring-blue-500 focus-visible:ring-offset-2",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "dark:focus-visible:ring-offset-slate-950",
            booleanValue ? "bg-blue-600" : "bg-slate-300 dark:bg-slate-700",
          ].join(" ")}
          onClick={() => {
            onChange(path, !booleanValue);
          }}
        >
          <span
            aria-hidden="true"
            className={[
              "pointer-events-none inline-block h-5 w-5",
              "rounded-full bg-white shadow ring-0",
              "transition-transform",
              booleanValue ? "translate-x-5" : "translate-x-0",
            ].join(" ")}
          />
        </button>
      </div>
    );
  }

  if (fieldKind === "select" && options) {
    const effectiveOptions = fetchedOptions ?? options;

    const dependencyMissing =
      Boolean(dynamicOptions?.depends_on) && fetchedOptions === null;

    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={fieldKey}
        label={label}
        description={description}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      >
        {dynamicOptions && dynamicOptions.endpoint ? (
          <div className="mb-2">
            {optionsLoading ? (
              <p className="text-sm text-slate-500">Lade Optionen…</p>
            ) : optionsError ? (
              <p className="text-sm text-amber-700">Fehler: {optionsError}</p>
            ) : dependencyMissing ? (
              <p className="text-sm text-slate-500">
                Bitte zuerst die abhängige Einstellung auswählen.
              </p>
            ) : null}
          </div>
        ) : null}

        <select
          id={fieldId}
          value={serializeOptionValue(value)}
          disabled={
            effectiveDisabled || Boolean(optionsLoading) || dependencyMissing
          }
          required={required}
          className={inputClassName}
          onChange={(event) => {
            const selectedOption = (effectiveOptions ?? []).find(
              (option) =>
                serializeOptionValue(option.value) === event.target.value,
            );

            if (!selectedOption) {
              return;
            }

            onChange(path, selectedOption.value);
          }}
        >
          {!required ? <option value="">Keine Auswahl</option> : null}

          {(effectiveOptions ?? []).map((option) => (
            <option
              key={serializeOptionValue(option.value)}
              value={serializeOptionValue(option.value)}
            >
              {option.label}
            </option>
          ))}
        </select>
      </SettingsInputContainer>
    );
  }

  if (fieldKind === "number") {
    const numericValue = typeof value === "number" ? value : 0;

    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={fieldKey}
        label={label}
        description={description}
        error={validationError}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      >
        <input
          id={fieldId}
          type="number"
          value={textDraft}
          disabled={effectiveDisabled}
          required={required}
          min={minimum}
          max={maximum}
          step={step ?? inferNumberStep(numericValue, fieldKey)}
          placeholder={placeholder}
          aria-invalid={validationError !== null}
          aria-describedby={validationError ? `${fieldId}-error` : undefined}
          className={inputClassName}
          onChange={(event) => {
            handleNumberChange({
              event,
              path,
              minimum,
              maximum,
              setDraft: setTextDraft,
              setError: setValidationError,
              onChange,
            });
          }}
          onBlur={() => {
            if (textDraft.trim() === "") {
              setTextDraft(String(numericValue));
            }
          }}
        />
      </SettingsInputContainer>
    );
  }

  if (
    fieldKind === "text" ||
    fieldKind === "password" ||
    fieldKind === "email" ||
    fieldKind === "url"
  ) {
    const inputType =
      fieldKind === "password"
        ? "password"
        : fieldKind === "email"
          ? "email"
          : fieldKind === "url"
            ? "url"
            : "text";

    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={fieldKey}
        label={label}
        description={description}
        error={validationError}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      >
        <input
          id={fieldId}
          type={inputType}
          value={textDraft}
          disabled={effectiveDisabled}
          required={required}
          placeholder={placeholder ?? inferPlaceholder(fieldKind, fieldKey)}
          autoComplete={fieldKind === "password" ? "new-password" : "off"}
          spellCheck={fieldKind === "text"}
          aria-invalid={validationError !== null}
          aria-describedby={validationError ? `${fieldId}-error` : undefined}
          className={inputClassName}
          onChange={(event) => {
            const nextValue = event.target.value;

            setTextDraft(nextValue);

            const error = validateTextValue({
              value: nextValue,
              fieldKind,
              required,
            });

            setValidationError(error);

            if (error === null) {
              onChange(path, nextValue);
            }
          }}
        />

        {fieldKind === "password" ? (
          <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
            Sensible Werte sollten nur als Secret-Referenz und nicht als
            Klartext gespeichert werden.
          </p>
        ) : null}
      </SettingsInputContainer>
    );
  }

  if (fieldKind === "multiline") {
    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={fieldKey}
        label={label}
        description={description}
        error={validationError}
        required={required}
        disabled={disabled}
        readOnly={readOnly}
      >
        <textarea
          id={fieldId}
          rows={6}
          value={textDraft}
          disabled={effectiveDisabled}
          required={required}
          placeholder={placeholder}
          spellCheck
          aria-invalid={validationError !== null}
          aria-describedby={validationError ? `${fieldId}-error` : undefined}
          className={[inputClassName, "resize-y leading-6"].join(" ")}
          onChange={(event) => {
            const nextValue = event.target.value;

            setTextDraft(nextValue);

            const error =
              required && nextValue.trim() === ""
                ? "Dieses Feld darf nicht leer sein."
                : null;

            setValidationError(error);

            if (error === null) {
              onChange(path, nextValue);
            }
          }}
        />
      </SettingsInputContainer>
    );
  }

  return (
    <SettingsInputContainer
      fieldId={fieldId}
      fieldKey={fieldKey}
      label={label}
      description={description}
      error={validationError}
      required={required}
      disabled={disabled}
      readOnly={readOnly}
    >
      <textarea
        id={fieldId}
        rows={10}
        value={complexDraft}
        disabled={effectiveDisabled}
        spellCheck={false}
        aria-invalid={validationError !== null}
        aria-describedby={validationError ? `${fieldId}-error` : undefined}
        className={[
          inputClassName,
          "resize-y font-mono text-xs leading-5",
        ].join(" ")}
        onChange={(event) => {
          const nextDraft = event.target.value;

          setComplexDraft(nextDraft);

          const parsedResult = parseComplexValue(nextDraft);

          if (!parsedResult.ok) {
            setValidationError(parsedResult.error);
            return;
          }

          setValidationError(null);

          onChange(path, parsedResult.value);
        }}
        onBlur={() => {
          const parsedResult = parseComplexValue(complexDraft);

          if (!parsedResult.ok) {
            return;
          }

          setComplexDraft(formatComplexValue(parsedResult.value));
        }}
      />

      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Komplexer Wert im JSON-Format.
        </p>

        <button
          type="button"
          disabled={effectiveDisabled}
          className={[
            "rounded-md border border-slate-300 px-2.5 py-1",
            "text-xs font-medium text-slate-600 transition",
            "hover:bg-slate-50",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "dark:border-white/10 dark:text-slate-300",
            "dark:hover:bg-white/5",
          ].join(" ")}
          onClick={() => {
            const parsedResult = parseComplexValue(complexDraft);

            if (!parsedResult.ok) {
              setValidationError(parsedResult.error);
              return;
            }

            setComplexDraft(formatComplexValue(parsedResult.value));

            setValidationError(null);
          }}
        >
          JSON formatieren
        </button>
      </div>
    </SettingsInputContainer>
  );
}

function SettingsInputContainer({
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
        "rounded-xl border border-slate-200 bg-white p-4",
        "dark:border-white/10 dark:bg-slate-900/40",
        disabled || readOnly ? "opacity-75" : "",
      ].join(" ")}
    >
      <label
        htmlFor={fieldId}
        className="block font-medium text-slate-900 dark:text-white"
      >
        {label}

        {required ? (
          <span
            className="ml-1 text-red-600 dark:text-red-400"
            aria-hidden="true"
          >
            *
          </span>
        ) : null}
      </label>

      {description ? (
        <p className="mt-1 text-sm leading-5 text-slate-600 dark:text-slate-400">
          {description}
        </p>
      ) : null}

      <FieldMetadata
        fieldKey={fieldKey}
        disabled={disabled}
        readOnly={readOnly}
      />

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

function FieldMetadata({
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

function handleNumberChange({
  event,
  path,
  minimum,
  maximum,
  setDraft,
  setError,
  onChange,
}: {
  event: ChangeEvent<HTMLInputElement>;
  path: string[];
  minimum?: number;
  maximum?: number;
  setDraft: (value: string) => void;
  setError: (value: string | null) => void;
  onChange: (path: string[], value: ConfigValue) => void;
}): void {
  const rawValue = event.target.value;

  setDraft(rawValue);

  if (rawValue.trim() === "") {
    setError("Eine leere Zahl kann nicht gespeichert werden.");
    return;
  }

  const numericValue = Number(rawValue);

  if (!Number.isFinite(numericValue)) {
    setError("Bitte eine gültige Zahl eingeben.");
    return;
  }

  if (minimum !== undefined && numericValue < minimum) {
    setError(`Der Wert darf nicht kleiner als ${minimum} sein.`);
    return;
  }

  if (maximum !== undefined && numericValue > maximum) {
    setError(`Der Wert darf nicht größer als ${maximum} sein.`);
    return;
  }

  setError(null);

  onChange(path, numericValue);
}

function detectFieldKind({
  fieldKey,
  value,
  sensitive,
  options,
}: {
  fieldKey: string;
  value: ConfigValue;
  sensitive?: boolean;
  options?: SettingsFieldOption[];
}): FieldKind {
  if (options !== undefined && options.length > 0) {
    return "select";
  }

  if (typeof value === "boolean") {
    return "boolean";
  }

  if (typeof value === "number") {
    return "number";
  }

  if (typeof value === "object" && value !== null) {
    return "json";
  }

  const normalizedKey = fieldKey.toLowerCase();

  if (
    sensitive === true ||
    includesAny(normalizedKey, [
      "password",
      "passwort",
      "secret",
      "token",
      "api_key",
      "apikey",
      "credential",
    ])
  ) {
    return "password";
  }

  if (includesAny(normalizedKey, ["email", "e_mail", "mail_address"])) {
    return "email";
  }

  if (
    includesAny(normalizedKey, [
      "url",
      "uri",
      "endpoint",
      "base_url",
      "webhook",
    ])
  ) {
    return "url";
  }

  if (
    includesAny(normalizedKey, [
      "description",
      "beschreibung",
      "prompt",
      "instruction",
      "anweisung",
      "template",
      "vorlage",
      "content",
      "inhalt",
      "message",
      "nachricht",
      "reason",
      "begründung",
      "notes",
      "notizen",
    ])
  ) {
    return "multiline";
  }

  return "text";
}

function validateTextValue({
  value,
  fieldKind,
  required,
}: {
  value: string;
  fieldKind: FieldKind;
  required: boolean;
}): string | null {
  if (required && value.trim() === "") {
    return "Dieses Feld darf nicht leer sein.";
  }

  if (value.trim() === "") {
    return null;
  }

  if (fieldKind === "email" && !isValidEmail(value)) {
    return "Bitte eine gültige E-Mail-Adresse eingeben.";
  }

  if (fieldKind === "url" && !isValidHttpUrl(value)) {
    return "Bitte eine gültige HTTP- oder HTTPS-Adresse eingeben.";
  }

  return null;
}

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

function isValidHttpUrl(value: string): boolean {
  try {
    const parsedUrl = new URL(value.trim());

    return parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:";
  } catch {
    return false;
  }
}

function inferPlaceholder(
  fieldKind: FieldKind,
  fieldKey: string,
): string | undefined {
  if (fieldKind === "email") {
    return "name@beispiel.de";
  }

  if (fieldKind === "url") {
    return "https://example.org";
  }

  if (fieldKind === "password") {
    return "Secret-Referenz oder geschützter Wert";
  }

  if (fieldKey.toLowerCase().includes("timezone")) {
    return "Europe/Berlin";
  }

  return undefined;
}

function inferNumberStep(value: number, fieldKey: string): number {
  const normalizedKey = fieldKey.toLowerCase();

  if (
    Number.isInteger(value) &&
    !includesAny(normalizedKey, [
      "temperature",
      "top_p",
      "penalty",
      "ratio",
      "rate",
      "percent",
      "percentage",
      "threshold",
    ])
  ) {
    return 1;
  }

  return 0.01;
}

function createFieldId(path: string[], reactId: string): string {
  const normalizedPath = path
    .map((part) => part.replace(/[^a-zA-Z0-9_-]/g, "-"))
    .join("-");

  const normalizedReactId = reactId.replace(/[^a-zA-Z0-9_-]/g, "");

  return ["setting", normalizedPath || "root", normalizedReactId].join("-");
}

function createTextDraft(value: ConfigValue): string {
  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number") {
    return String(value);
  }

  if (value === null) {
    return "";
  }

  return "";
}

function formatComplexValue(value: ConfigValue): string {
  if (typeof value !== "object" || value === null) {
    return "";
  }

  return JSON.stringify(value, null, 2);
}

type ComplexParseResult =
  | {
      ok: true;
      value: ConfigValue;
    }
  | {
      ok: false;
      error: string;
    };

function parseComplexValue(value: string): ComplexParseResult {
  if (value.trim() === "") {
    return {
      ok: false,
      error: "Der JSON-Wert darf nicht leer sein.",
    };
  }

  let parsedValue: unknown;

  try {
    parsedValue = JSON.parse(value) as unknown;
  } catch {
    return {
      ok: false,
      error: "Der Wert enthält kein gültiges JSON.",
    };
  }

  if (!isConfigValue(parsedValue)) {
    return {
      ok: false,
      error: "Das JSON enthält einen nicht unterstützten Konfigurationswert.",
    };
  }

  return {
    ok: true,
    value: parsedValue,
  };
}

function isConfigValue(value: unknown): value is ConfigValue {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return true;
  }

  if (typeof value === "number") {
    return Number.isFinite(value);
  }

  if (Array.isArray(value)) {
    return value.every(isConfigValue);
  }

  if (typeof value === "object" && value !== null) {
    return Object.values(value).every(isConfigValue);
  }

  return false;
}

function serializeOptionValue(value: ConfigValue): string {
  if (value === null) {
    return "";
  }

  return JSON.stringify(value);
}

function includesAny(value: string, candidates: string[]): boolean {
  return candidates.some((candidate) => value.includes(candidate));
}

const inputClassName = [
  "block w-full rounded-lg",
  "border border-slate-300",
  "bg-white px-3 py-2",
  "text-sm text-slate-900",
  "shadow-sm outline-none",
  "transition",
  "placeholder:text-slate-400",
  "focus:border-blue-500",
  "focus:ring-2",
  "focus:ring-blue-500/20",
  "invalid:border-red-400",
  "disabled:cursor-not-allowed",
  "disabled:bg-slate-100",
  "disabled:opacity-70",
  "dark:border-white/10",
  "dark:bg-slate-950/60",
  "dark:text-white",
  "dark:invalid:border-red-500",
  "dark:disabled:bg-slate-900",
].join(" ");
