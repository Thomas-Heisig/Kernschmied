import React from 'react';

import type { ConfigGroupResponse } from '../../contracts/config';

interface Props {
  groups?: ConfigGroupResponse[] | null;
  activeKey: string | null;
  onSelect: (key: string) => void;
}

export default function SettingsGroupList({ groups, activeKey, onSelect }: Props) {
  if (!groups || groups.length === 0) {
    return <div className="px-4 py-2 text-sm text-muted">Keine Bereiche</div>;
  }

  return (
    <ul className="divide-y">
      {groups.map((g) => (
        <li key={g.id}>
          <button
            type="button"
            className={`w-full text-left px-4 py-2 ${activeKey === g.id ? 'bg-amber-100' : ''}`}
            onClick={() => onSelect(g.id)}
          >
            <div className="font-medium">{g.title ?? g.id}</div>
            {g.description ? <div className="text-xs text-muted">{g.description}</div> : null}
          </button>
        </li>
      ))}
    </ul>
  );
}
