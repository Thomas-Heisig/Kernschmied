import type { ChangeEvent, ReactNode } from "react";

import type { ConfigValue } from "../../contracts/config";

interface SettingsFieldProps {
  fieldKey: string;
  label: string;
  value: ConfigValue;
  path: string[];
  disabled?: boolean;

  onChange: (path: string[], value: ConfigValue) => void;
}

interface SettingsInputContainerProps {
  fieldId: string;
  fieldKey: string;
  label: string;
  children: ReactNode;
}

export function SettingsField({
  fieldKey,
  label,
  value,
  path,
  disabled = false,
  onChange,
}: SettingsFieldProps) {
  const fieldId = createFieldId(path);

  if (typeof value === "boolean") {
    return (
      <div className="flex items-start justify-between gap-5 rounded-xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-slate-900/40">
        <div className="min-w-0">
          <label
            htmlFor={fieldId}
            className="font-medium text-slate-900 dark:text-white"
          >
            {label}
          </label>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Schlüssel: {fieldKey}
          </p>
        </div>

        <input
          id={fieldId}
          type="checkbox"
          checked={value}
          disabled={disabled}
          className={[
            "mt-1 h-5 w-5 rounded",
            "border-slate-300 text-blue-600",
            "focus:ring-blue-500",
            "disabled:cursor-not-allowed",
            "disabled:opacity-50",
          ].join(" ")}
          onChange={(event) => {
            onChange(path, event.target.checked);
          }}
        />
      </div>
    );
  }

  if (typeof value === "number") {
    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={fieldKey}
        label={label}
      >
        <input
          id={fieldId}
          type="number"
          value={value}
          disabled={disabled}
          className={inputClassName}
          onChange={(event) => {
            handleNumberChange(event, path, onChange);
          }}
        />
      </SettingsInputContainer>
    );
  }

  if (typeof value === "string" || value === null) {
    return (
      <SettingsInputContainer
        fieldId={fieldId}
        fieldKey={fieldKey}
        label={label}
      >
        <input
          id={fieldId}
          type="text"
          value={value ?? ""}
          disabled={disabled}
          className={inputClassName}
          onChange={(event) => {
            onChange(path, event.target.value);
          }}
        />
      </SettingsInputContainer>
    );
  }

  return (
    <SettingsInputContainer fieldId={fieldId} fieldKey={fieldKey} label={label}>
      <textarea
        id={fieldId}
        rows={8}
        value={formatComplexValue(value)}
        disabled={disabled}
        spellCheck={false}
        className={[inputClassName, "resize-y font-mono text-xs"].join(" ")}
        onChange={(event) => {
          const parsedValue = parseComplexValue(event.target.value);

          if (parsedValue === undefined) {
            return;
          }

          onChange(path, parsedValue);
        }}
      />

      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
        Komplexer Wert im JSON-Format.
      </p>
    </SettingsInputContainer>
  );
}

function SettingsInputContainer({
  fieldId,
  fieldKey,
  label,
  children,
}: SettingsInputContainerProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-slate-900/40">
      <label
        htmlFor={fieldId}
        className="block font-medium text-slate-900 dark:text-white"
      >
        {label}
      </label>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        Schlüssel: {fieldKey}
      </p>

      <div className="mt-3">{children}</div>
    </div>
  );
}

function handleNumberChange(
  event: ChangeEvent<HTMLInputElement>,
  path: string[],
  onChange: (path: string[], value: ConfigValue) => void,
): void {
  const rawValue = event.target.value;

  if (rawValue.trim() === "") {
    return;
  }

  const numericValue = Number(rawValue);

  if (!Number.isFinite(numericValue)) {
    return;
  }

  onChange(path, numericValue);
}

function createFieldId(path: string[]): string {
  const normalizedPath = path
    .map((part) => part.replace(/[^a-zA-Z0-9_-]/g, "-"))
    .join("-");

  return `setting-${normalizedPath}`;
}

function formatComplexValue(value: ConfigValue): string {
  return JSON.stringify(value, null, 2);
}

function parseComplexValue(value: string): ConfigValue | undefined {
  try {
    const parsedValue = JSON.parse(value) as unknown;

    return isConfigValue(parsedValue) ? parsedValue : undefined;
  } catch {
    return undefined;
  }
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
  "disabled:cursor-not-allowed",
  "disabled:bg-slate-100",
  "disabled:opacity-70",
  "dark:border-white/10",
  "dark:bg-slate-950/60",
  "dark:text-white",
  "dark:disabled:bg-slate-900",
].join(" ");
