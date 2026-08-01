import React from "react";
import type { ConfigValue, ConfigEntryResponse } from "../../../contracts/config";
import { SettingsInputContainer, FieldMetadata } from "../SettingsFieldShared";

interface Props {
  entry: ConfigEntryResponse;
  path: string[];
  value: ConfigValue;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}

export default function BooleanSetting({
  entry,
  path,
  value,
  disabled = false,
  readOnly = false,
  required = false,
  onChange,
}: Props) {
  const fieldId = ["setting", entry.full_key].join("-").replace(/[^a-zA-Z0-9_-]/g, "-");

  const effectiveDisabled = disabled || readOnly;

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
        <label htmlFor={fieldId} className="font-medium text-slate-900 dark:text-white">
          {entry.display_name}
          {required ? (
            <span className="ml-1 text-red-600 dark:text-red-400" aria-hidden="true">
              *
            </span>
          ) : null}
        </label>

        {entry.description ? (
          <p className="mt-1 text-sm leading-5 text-slate-600 dark:text-slate-400">
            {entry.description}
          </p>
        ) : null}

        <FieldMetadata fieldKey={entry.full_key} disabled={disabled} readOnly={readOnly} />
      </div>

      <button
        id={fieldId}
        type="button"
        role="switch"
        aria-checked={booleanValue}
        aria-label={entry.display_name}
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
