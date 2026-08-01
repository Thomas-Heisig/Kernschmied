import React, { useState } from 'react';
import type { ConfigValue, ConfigEntryResponse } from '../../../contracts/config';
import { SettingsInputContainer, inputClassName } from '../SettingsFieldShared';

interface Props {
  entry: ConfigEntryResponse;
  path: string[];
  value: ConfigValue;
  disabled?: boolean;
  readOnly?: boolean;
  required?: boolean;
  minimum?: number;
  maximum?: number;
  step?: number;
  onChange: (path: string[], value: ConfigValue) => void;
}

function inferNumberStep(value: number, fieldKey: string): number {
  const normalizedKey = fieldKey.toLowerCase();

  if (
    Number.isInteger(value) &&
    ![
      'temperature',
      'top_p',
      'penalty',
      'ratio',
      'rate',
      'percent',
      'percentage',
      'threshold',
    ].some((c) => normalizedKey.includes(c))
  ) {
    return 1;
  }

  return 0.01;
}

export default function NumberSetting({
  entry,
  path,
  value,
  disabled = false,
  readOnly = false,
  required = false,
  minimum,
  maximum,
  step,
  onChange,
}: Props) {
  const numericValue = typeof value === 'number' ? value : 0;

  const [textDraft, setTextDraft] = useState(String(numericValue));
  const [validationError, setValidationError] = useState<string | null>(null);

  const fieldId = ['setting', entry.full_key].join('-').replace(/[^a-zA-Z0-9_-]/g, '-');

  function handleNumberChange(event: React.ChangeEvent<HTMLInputElement>) {
    const rawValue = event.target.value;

    setTextDraft(rawValue);

    if (rawValue.trim() === '') {
      setValidationError('Eine leere Zahl kann nicht gespeichert werden.');
      return;
    }

    const numeric = Number(rawValue);

    if (!Number.isFinite(numeric)) {
      setValidationError('Bitte eine gültige Zahl eingeben.');
      return;
    }

    if (minimum !== undefined && numeric < minimum) {
      setValidationError(`Der Wert darf nicht kleiner als ${minimum} sein.`);
      return;
    }

    if (maximum !== undefined && numeric > maximum) {
      setValidationError(`Der Wert darf nicht größer als ${maximum} sein.`);
      return;
    }

    setValidationError(null);

    onChange(path, numeric);
  }

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
        type="number"
        value={textDraft}
        disabled={disabled || readOnly}
        required={required}
        min={minimum}
        max={maximum}
        step={step ?? inferNumberStep(numericValue, entry.key)}
        placeholder={entry.ui.placeholder ?? undefined}
        aria-invalid={validationError !== null}
        aria-describedby={validationError ? `${fieldId}-error` : undefined}
        className={inputClassName}
        onChange={handleNumberChange}
        onBlur={() => {
          if (textDraft.trim() === '') {
            setTextDraft(String(numericValue));
          }
        }}
      />
    </SettingsInputContainer>
  );
}
