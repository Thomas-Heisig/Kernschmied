import React from 'react';
import { Check, RefreshCw, Save, RotateCcw } from 'lucide-react';

interface Props {
  isDirty: boolean;
  isSaving: boolean;
  onSave: () => void;
  onReload: () => void;
  onReset: () => void;
}

export default function SettingsToolbar({ isDirty, isSaving, onSave, onReload, onReset }: Props) {
  return (
    <div className="flex items-center gap-2">
      <button type="button" className="btn" onClick={onReload}>
        <RefreshCw size={15} />
        <span>Neu laden</span>
      </button>

      <button type="button" className="btn" onClick={onReset}>
        <RotateCcw size={15} />
        <span>Zurücksetzen</span>
      </button>

      <button type="button" className="btn-primary" disabled={!isDirty || isSaving} onClick={onSave}>
        <Save size={15} />
        <span>{isSaving ? 'Speichern …' : 'Speichern'}</span>
      </button>
    </div>
  );
}
