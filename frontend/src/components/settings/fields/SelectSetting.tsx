import React from 'react';
import type { ConfigValue, ConfigEntryResponse } from '../../../contracts/config';
import useConfigOptions from '../../../hooks/useConfigApi';
import {
  SettingsInputContainer,
  serializeOptionValue,
  inputClassName,
} from '../SettingsFieldShared';

interface Props {
  entry: ConfigEntryResponse;
  path: string[];
  value: ConfigValue;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  valuesByFullKey?: Record<string, ConfigValue> | null;
  onChange: (path: string[], value: ConfigValue) => void;
}

export default function SelectSetting({
  entry,
  path,
  value,
  disabled = false,
  readOnly = false,
  required = false,
  valuesByFullKey = null,
  onChange,
}: Props) {
  const fieldId = ['setting', entry.full_key].join('-').replace(/[^a-zA-Z0-9_-]/g, '-');

  // Map backend ConfigDynamicOptionsResponse -> hook DynamicOptionsSpec
  const dynamicSpec = entry.ui.dynamic_options
    ? {
        endpoint: entry.ui.dynamic_options.endpoint ?? '',
        depends_on: entry.ui.dynamic_options.depends_on ?? undefined,
        dependency_parameter: entry.ui.dynamic_options.dependency_parameter ?? undefined,
      }
    : null;

  const {
    options: fetchedOptions,
    loading: optionsLoading,
    error: optionsError,
  } = useConfigOptions(dynamicSpec, valuesByFullKey ?? null);

  const effectiveOptions = fetchedOptions ?? entry.ui.options ?? [];

  const dependencyMissing =
    Boolean(entry.ui.dynamic_options?.depends_on) && fetchedOptions === null;

  return (
    <SettingsInputContainer
      fieldId={fieldId}
      fieldKey={entry.full_key}
      label={entry.display_name}
      description={entry.description}
      required={required}
      disabled={disabled}
      readOnly={readOnly}
    >
      {entry.ui.dynamic_options && entry.ui.dynamic_options.endpoint ? (
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
        disabled={disabled || readOnly || Boolean(optionsLoading) || dependencyMissing}
        required={required}
        className={inputClassName}
        onChange={(event) => {
          const selected = (effectiveOptions ?? []).find(
            (o) => serializeOptionValue(o.value) === event.target.value,
          );

          if (!selected) return;

          onChange(path, selected.value);
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
