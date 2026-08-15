import {
  Building2,
  ChevronRight,
  KeyRound,
  MonitorSmartphone,
  Plus,
  Settings,
  ShieldCheck,
  UserRound,
  UsersRound,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { loadOwnHierarchyQuotas, type HierarchyQuotaStatus } from '../../api/hierarchy';
import { useAuth } from '../../auth/AuthProvider';
import { useUserPanels } from '../../auth/UserAccountPanels';
import { DynamicIcon } from '../../registry/iconRegistry';
import IconBadge from '../common/IconBadge';
import WorkspaceLayout from '../layout/WorkspaceLayout';
import WidgetBadges from '../widgets/WidgetBadges';
import WidgetsForNode from '../widgets/WidgetsForNode';

interface UserWorkspaceNode {
  id: string;
  name: string;
  type: string;
  metadata?: Record<string, unknown> | null;
  actions?: string[];
  children?: UserWorkspaceNode[];
}

interface UserNodeWorkspaceProps {
  node: UserWorkspaceNode;
  onNavigateToNode?: (nodeId: string) => void;
  onAction?: (action: string, node: UserWorkspaceNode) => void;
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrator',
  guest: 'Gast',
  user: 'Intern',
  internal: 'Intern',
  intern: 'Intern',
};

export default function UserNodeWorkspace({
  node,
  onNavigateToNode,
  onAction,
}: UserNodeWorkspaceProps) {
  const { user } = useAuth();
  const panels = useUserPanels();
  const metadata = node.metadata ?? {};
  const entityId = String(metadata.entity_id ?? metadata.user_id ?? '');
  const isOwnNode = Boolean(
    user && (entityId === user.id || node.id === `user-${user.id}`),
  );
  const isAdmin = Boolean(user?.roles.some((role) => role.toLowerCase() === 'admin'));
  const children = node.children ?? [];
  const [quotas, setQuotas] = useState<HierarchyQuotaStatus | null>(null);
  const accessLabel = user
    ? user.roles.map((role) => ROLE_LABELS[role.toLowerCase()] ?? role).join(', ') || 'Benutzer'
    : 'Benutzer';

  useEffect(() => {
    if (!isOwnNode || isAdmin) {
      setQuotas(null);
      return;
    }
    let active = true;
    void loadOwnHierarchyQuotas()
      .then((result) => {
        if (active) setQuotas(result);
      })
      .catch(() => {
        if (active) setQuotas(null);
      });
    return () => {
      active = false;
    };
  }, [children.length, isAdmin, isOwnNode, node.id]);

  return (
    <WorkspaceLayout
      icon={<IconBadge icon={<UserRound />} size="md" variant="secondary" />}
      title={`${isOwnNode ? 'Mein Bereich' : 'Benutzerbereich'}: ${node.name}`}
      widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
      background="white"
    >
      <div className="w-full space-y-8">
        <section
          aria-labelledby="personal-overview-title"
          className="border-b border-border-soft pb-6 dark:border-white/10"
        >
          <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
            <div>
              <h2 id="personal-overview-title" className="text-lg font-semibold text-text dark:text-white">
                {isOwnNode ? `Willkommen, ${user?.displayName ?? node.name}` : node.name}
              </h2>
              <p className="mt-1 max-w-2xl text-sm text-text-muted dark:text-gray-400">
                {isOwnNode
                  ? 'Hier verwaltest du dein Profil, deine persönlichen Einstellungen und deine verfügbaren Bereiche.'
                  : 'Übersicht des Benutzerbereichs und seiner zugeordneten Inhalte.'}
              </p>
            </div>

            {isOwnNode ? (
              <div className="flex flex-wrap gap-2" aria-label="Persönliche Aktionen">
                {node.actions?.includes('create_child') ? (
                  <ActionButton icon={<Plus size={16} />} onClick={() => onAction?.('create_child', node)}>
                    Bereich erstellen
                  </ActionButton>
                ) : null}
                <ActionButton icon={<UserRound size={16} />} onClick={() => panels.openPanel('profile')}>
                  Profil
                </ActionButton>
                <ActionButton icon={<Settings size={16} />} onClick={() => panels.openPanel('settings')}>
                  Einstellungen
                </ActionButton>
                <ActionButton icon={<MonitorSmartphone size={16} />} onClick={() => panels.openPanel('sessions')}>
                  Sitzungen
                </ActionButton>
                {user?.passwordLoginAvailable ? (
                  <ActionButton icon={<KeyRound size={16} />} onClick={() => panels.openPanel('change-password')}>
                    Passwort
                  </ActionButton>
                ) : null}
              </div>
            ) : isAdmin ? (
              <ActionButton icon={<UsersRound size={16} />} onClick={() => panels.openPanel('users')}>
                Benutzer verwalten
              </ActionButton>
            ) : null}
          </div>

          {isOwnNode && user ? (
            <dl className="mt-6 grid grid-cols-1 gap-x-8 gap-y-4 text-sm sm:grid-cols-2 xl:grid-cols-3">
              <ProfileValue label="Benutzername" value={user.username} />
              <ProfileValue label="E-Mail" value={user.email ?? 'Nicht hinterlegt'} />
              <ProfileValue label="Zugriff" value={accessLabel} icon={<ShieldCheck size={15} />} />
            </dl>
          ) : null}

          {isOwnNode && quotas?.limits && quotas.usage ? (
            <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3" aria-label="Eigene Nutzungslimits">
              <QuotaValue label="Bereiche" used={quotas.usage.workspace} limit={quotas.limits.workspace} />
              <QuotaValue label="Projekte" used={quotas.usage.project} limit={quotas.limits.project} />
              <QuotaValue label="Chats" used={quotas.usage.chat} limit={quotas.limits.chat} />
            </div>
          ) : null}
        </section>

        <section aria-labelledby="available-areas-title">
          <div className="flex items-center gap-2">
            <Building2 size={18} className="text-text-muted" />
            <h2 id="available-areas-title" className="text-base font-semibold text-text dark:text-white">
              Verfügbare Bereiche
            </h2>
          </div>

          {children.length > 0 ? (
            <div className="mt-3 divide-y divide-border-soft border-y border-border-soft dark:divide-white/10 dark:border-white/10">
              {children.map((child) => (
                <button
                  key={child.id}
                  type="button"
                  className="flex w-full items-center gap-3 px-2 py-3 text-left transition hover:bg-surface-hover dark:hover:bg-slate-900/60"
                  onClick={() => onNavigateToNode?.(child.id)}
                >
                  <DynamicIcon name={iconForNodeType(child.type)} className="h-5 w-5 shrink-0 text-text-muted" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-text dark:text-white">{child.name}</span>
                    <span className="block text-xs text-text-muted dark:text-gray-400">{labelForNodeType(child.type)}</span>
                  </span>
                  <ChevronRight size={17} className="shrink-0 text-text-muted" />
                </button>
              ))}
            </div>
          ) : (
            <p className="mt-3 border-y border-border-soft py-5 text-sm text-text-muted dark:border-white/10 dark:text-gray-400">
              Diesem Benutzer sind derzeit keine Bereiche zugeordnet.
            </p>
          )}
        </section>

        <section aria-labelledby="personal-widgets-title">
          <h2 id="personal-widgets-title" className="text-base font-semibold text-text dark:text-white">
            Persönliche Widgets
          </h2>
          <div className="mt-3">
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </div>
        </section>
      </div>
    </WorkspaceLayout>
  );
}

function QuotaValue({ label, used, limit }: { label: string; used: number; limit: number }) {
  return (
    <div className="rounded-md bg-surface-muted px-3 py-2 text-sm dark:bg-slate-800/60">
      <span className="text-text-muted dark:text-gray-400">{label}</span>{' '}
      <strong className="text-text dark:text-white">{used}/{limit}</strong>
    </div>
  );
}

function ActionButton({
  icon,
  children,
  onClick,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-2 rounded-md border border-border-soft px-3 py-2 text-sm font-medium text-text-soft transition hover:bg-surface-hover dark:border-white/10 dark:text-gray-200 dark:hover:bg-slate-800"
    >
      {icon}
      {children}
    </button>
  );
}

function ProfileValue({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-text-muted dark:text-gray-400">{label}</dt>
      <dd className="mt-1 flex items-center gap-1.5 text-text dark:text-gray-200">
        {icon}
        {value}
      </dd>
    </div>
  );
}

function iconForNodeType(type: string): string {
  const normalized = type.trim().toLowerCase();
  if (normalized === 'project' || normalized === 'projekt') return 'Folder';
  if (normalized === 'chat' || normalized === 'conversation') return 'MessageSquare';
  return 'Building2';
}

function labelForNodeType(type: string): string {
  const normalized = type.trim().toLowerCase();
  if (normalized === 'project' || normalized === 'projekt') return 'Projekt';
  if (normalized === 'chat' || normalized === 'conversation') return 'Chat';
  return 'Bereich';
}
