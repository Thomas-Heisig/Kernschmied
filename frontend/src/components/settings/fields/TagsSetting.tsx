import React from "react";
import type { ConfigValue, ConfigEntryResponse } from "../../../contracts/config";
import { SettingsInputContainer, serializeOptionValue, inputClassName } from "../SettingsFieldShared";

interface Props {
  entry: ConfigEntryResponse;
  path: string[];
  value: ConfigValue;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  onChange: (path: string[], value: ConfigValue) => void;
}

export default function TagsSetting({ entry, path, value, disabled = false, readOnly = false, required = false, onChange }: Props) {
  const fieldId = ["setting", entry.full_key].join("-").replace(/[^a-zA-Z0-9_-]/g, "-");

  const selected = Array.isArray(value) ? value : [];

  const options = entry.ui.options ?? [];

  function toggleOption(optValue: unknown) {
    const str = serializeOptionValue(optValue as ConfigValue);
    const found = selected.find((s) => serializeOptionValue(s as ConfigValue) === str);

    let next: ConfigValue[];

    if (found === undefined) {
      next = [...selected, optValue as ConfigValue];
    } else {
      next = selected.filter((s) => serializeOptionValue(s as ConfigValue) !== str) as ConfigValue[];
    }

    onChange(path, next as ConfigValue);
  }

  return (
    <SettingsInputContainer fieldId={fieldId} fieldKey={entry.full_key} label={entry.display_name} description={entry.description} required={required} disabled={disabled} readOnly={readOnly}>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const isSelected = selected.some((s) => serializeOptionValue(s as ConfigValue) === serializeOptionValue(opt.value));

          return (
            <button key={serializeOptionValue(opt.value)} type="button" disabled={disabled || readOnly} onClick={() => toggleOption(opt.value)} className={["rounded-full px-3 py-1 border", isSelected ? "bg-blue-600 text-white" : "bg-white"].join(" ")}>
              {opt.label}
            </button>
          );
        })}
      </div>
    </SettingsInputContainer>
  );
}
