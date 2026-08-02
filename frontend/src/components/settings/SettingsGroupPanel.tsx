import React from 'react';

import type { ConfigValue } from '../../contracts/config';

interface Props {
  sectionKey: string;
  sectionValue: ConfigValue;
}

export default function SettingsGroupPanel({ sectionKey, sectionValue }: Props) {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold">{sectionKey}</h3>
      <pre className="mt-2 whitespace-pre-wrap text-sm">{JSON.stringify(sectionValue, null, 2)}</pre>
    </div>
  );
}
