import React from 'react';
import type { ConfigEntryResponse } from '../../contracts/config';
import { SettingsInputContainer } from './SettingsFieldShared';

export default function UnsupportedSetting({
  entry,
  path,
}: {
  entry: ConfigEntryResponse;
  path: string[];
}) {
  const fieldId = ['setting', entry.full_key].join('-').replace(/[^a-zA-Z0-9_-]/g, '-');

  return (
    <SettingsInputContainer fieldId={fieldId} fieldKey={entry.full_key} label={entry.display_name}>
      <p className="text-sm text-slate-500">
        Komponenten vom Typ "{entry.ui.component}" werden derzeit nicht unterstützt.
      </p>
    </SettingsInputContainer>
  );
}
