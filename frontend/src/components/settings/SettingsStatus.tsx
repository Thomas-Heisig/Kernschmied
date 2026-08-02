import React from 'react';

interface Props {
  revision?: string | null;
  isLoading: boolean;
}

export default function SettingsStatus({ revision, isLoading }: Props) {
  return (
    <div className="text-sm text-muted">
      {isLoading ? 'Lade…' : revision ? `Revision: ${revision}` : 'Keine Revision'}
    </div>
  );
}
