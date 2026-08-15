import { Gauge } from 'lucide-react';

import type { AccessLevel, QuotaSetting } from './auth-api';

const ROLE_DEFAULTS: Record<AccessLevel, Record<QuotaKey, number | 'unlimited'>> = {
  guest: { workspace: 1, project: 2, chat: 5 },
  internal: { workspace: 5, project: 10, chat: 25 },
  admin: { workspace: 'unlimited', project: 'unlimited', chat: 'unlimited' },
};

type QuotaKey = 'workspace' | 'project' | 'chat';
type QuotaMode = 'default' | 'limit' | 'unlimited';

interface UserQuotaEditorProps {
  accessLevel: AccessLevel;
  workspaceQuota: QuotaSetting;
  projectQuota: QuotaSetting;
  chatQuota: QuotaSetting;
  disabled?: boolean;
  onWorkspaceQuotaChange: (value: QuotaSetting) => void;
  onProjectQuotaChange: (value: QuotaSetting) => void;
  onChatQuotaChange: (value: QuotaSetting) => void;
}

export default function UserQuotaEditor({
  accessLevel,
  workspaceQuota,
  projectQuota,
  chatQuota,
  disabled = false,
  onWorkspaceQuotaChange,
  onProjectQuotaChange,
  onChatQuotaChange,
}: UserQuotaEditorProps) {
  const adminUnlimited = accessLevel === 'admin';
  return (
    <fieldset className="sm:col-span-2 rounded-lg border border-border bg-surface-hover/35 p-4 dark:border-white/10 dark:bg-slate-900/35">
      <legend className="px-1 text-sm font-semibold">
        <span className="inline-flex items-center gap-2"><Gauge size={16} /> Hierarchie-Kontingente</span>
      </legend>
      <p className="text-xs text-text-muted">
        Rollenstandard übernehmen, ein festes Limit vergeben oder die Ressource unbegrenzt freigeben.
      </p>
      {adminUnlimited ? (
        <p className="mt-2 rounded-md bg-success/10 px-3 py-2 text-xs text-success">
          Administratoren besitzen unabhängig von Overrides unbegrenzte Hierarchienutzung.
        </p>
      ) : null}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <QuotaField
          label="Bereiche"
          quotaKey="workspace"
          value={workspaceQuota}
          accessLevel={accessLevel}
          disabled={disabled || adminUnlimited}
          onChange={onWorkspaceQuotaChange}
        />
        <QuotaField
          label="Projekte"
          quotaKey="project"
          value={projectQuota}
          accessLevel={accessLevel}
          disabled={disabled || adminUnlimited}
          onChange={onProjectQuotaChange}
        />
        <QuotaField
          label="Chats"
          quotaKey="chat"
          value={chatQuota}
          accessLevel={accessLevel}
          disabled={disabled || adminUnlimited}
          onChange={onChatQuotaChange}
        />
      </div>
    </fieldset>
  );
}

function QuotaField({
  label,
  quotaKey,
  value,
  accessLevel,
  disabled,
  onChange,
}: {
  label: string;
  quotaKey: QuotaKey;
  value: QuotaSetting;
  accessLevel: AccessLevel;
  disabled: boolean;
  onChange: (value: QuotaSetting) => void;
}) {
  const mode: QuotaMode = value === null ? 'default' : value === 'unlimited' ? 'unlimited' : 'limit';
  const roleDefault = ROLE_DEFAULTS[accessLevel][quotaKey];
  const defaultLabel = roleDefault === 'unlimited' ? 'unbegrenzt' : String(roleDefault);

  function updateMode(nextMode: QuotaMode) {
    if (nextMode === 'default') onChange(null);
    else if (nextMode === 'unlimited') onChange('unlimited');
    else onChange(typeof value === 'number' ? value : roleDefault === 'unlimited' ? 0 : roleDefault);
  }

  return (
    <div className="min-w-0">
      <label className="text-sm font-medium" htmlFor={`quota-mode-${quotaKey}`}>{label}</label>
      <select
        id={`quota-mode-${quotaKey}`}
        aria-label={`${label}-Kontingent`}
        value={mode}
        disabled={disabled}
        onChange={(event) => updateMode(event.target.value as QuotaMode)}
        className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 text-sm disabled:bg-surface-hover dark:border-white/10 dark:bg-slate-900"
      >
        <option value="default">Rollenstandard ({defaultLabel})</option>
        <option value="limit">Festes Limit</option>
        <option value="unlimited">Unbegrenzt</option>
      </select>
      {mode === 'limit' ? (
        <label className="mt-2 block text-xs text-text-muted">
          Maximale {label}
          <input
            type="number"
            min={0}
            step={1}
            value={value === 'unlimited' || value === null ? 0 : value}
            disabled={disabled}
            onChange={(event) => onChange(Math.max(0, Number.parseInt(event.target.value || '0', 10)))}
            className="mt-1 w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-text disabled:bg-surface-hover dark:border-white/10 dark:bg-slate-900 dark:text-white"
          />
        </label>
      ) : null}
    </div>
  );
}
