import {
  ArrowRight,
  Building2,
  Clock3,
  ChevronRight,
  FilePenLine,
  FolderKanban,
  KeyRound,
  LayoutDashboard,
  MessageSquare,
  MonitorSmartphone,
  Plus,
  Settings,
  ShieldCheck,
  Sparkles,
  UserRound,
  UsersRound,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { loadOwnHierarchyQuotas, type HierarchyQuotaStatus } from '../../api/hierarchy';
import { useAuth } from '../../auth/AuthProvider';
import { useUserPanels } from '../../auth/UserAccountPanels';
import { DynamicIcon } from '../../registry/iconRegistry';
import IconBadge from '../common/IconBadge';
import {
  readStoredNodeIds,
  RECENT_NODE_STORAGE_KEY,
} from '../hierarchy/quickAccessStorage';
import WorkspaceLayout from '../layout/WorkspaceLayout';
import WidgetBadges from '../widgets/WidgetBadges';
import WidgetsForNode from '../widgets/WidgetsForNode';
import NodeWorkspaceOverview, { NodeWorkspaceAction } from './NodeWorkspaceOverview';

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
const USER_WIDGET_PREFIXES = ['calendar', 'files'];

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
  const descendantEntries = useMemo(() => flattenVisibleDescendants(children), [children]);
  const availableAreas = children.filter((child) => isNodeType(child, 'workspace', 'bereich'));
  const availableProjects = descendantEntries.filter(({ node: child }) => isNodeType(child, 'project', 'projekt'));
  const availableChats = descendantEntries.filter(({ node: child }) => isNodeType(child, 'chat', 'conversation'));
  const nodesById = useMemo(
    () => new Map(descendantEntries.map((entry) => [entry.node.id, entry])),
    [descendantEntries],
  );
  const recentChats = readStoredNodeIds(RECENT_NODE_STORAGE_KEY)
    .map((id) => nodesById.get(id))
    .filter((entry): entry is VisibleNodeEntry => Boolean(entry && isNodeType(entry.node, 'chat', 'conversation')))
    .slice(0, 4);
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
      widgetBadges={<WidgetBadges nodeId={node.id} size="sm" allowedComponentTypePrefixes={USER_WIDGET_PREFIXES} />}
      background="white"
    >
      <div className="w-full space-y-7">
        <NodeWorkspaceOverview
          eyebrow="Persönlicher Arbeitsbereich"
          title={isOwnNode ? `Willkommen, ${user?.displayName ?? node.name}` : node.name}
          description={isOwnNode
            ? 'Dein Einstieg in Bereiche, Projekte, letzte Gespräche und persönliche Werkzeuge.'
            : 'Übersicht der freigegebenen Inhalte und Funktionen dieses Benutzerbereichs.'}
          icon={<UserRound />}
          actions={isOwnNode ? (
            <div className="flex flex-wrap gap-2" aria-label="Persönliche Aktionen">
              {node.actions?.includes('create_child') ? (
                <NodeWorkspaceAction icon={<Plus size={16} />} onClick={() => onAction?.('create_child', node)}>
                  Bereich erstellen
                </NodeWorkspaceAction>
              ) : null}
              {node.actions?.includes('edit_prompt') ? (
                <NodeWorkspaceAction icon={<FilePenLine size={16} />} onClick={() => onAction?.('edit_prompt', node)}>
                  Prompt bearbeiten
                </NodeWorkspaceAction>
              ) : null}
            </div>
          ) : isAdmin ? (
            <NodeWorkspaceAction icon={<UsersRound size={16} />} onClick={() => panels.openPanel('users')}>
              Benutzer verwalten
            </NodeWorkspaceAction>
          ) : null}
          details={isOwnNode && user ? (
            <dl className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <ProfileValue label="Benutzername" value={user.username} />
              <ProfileValue label="E-Mail" value={user.email ?? 'Nicht hinterlegt'} />
              <ProfileValue label="Zugriff" value={accessLabel} icon={<ShieldCheck size={15} />} />
            </dl>
          ) : null}
          metrics={[
            { label: 'Bereiche', value: availableAreas.length, icon: <Building2 size={17} /> },
            { label: 'Projekte', value: availableProjects.length, icon: <FolderKanban size={17} /> },
            { label: 'Chats', value: availableChats.length, icon: <MessageSquare size={17} /> },
            { label: 'Zuletzt aktiv', value: recentChats.length, icon: <Clock3 size={17} /> },
          ]}
        />

        {isOwnNode ? (
          <section aria-labelledby="quick-actions-title">
            <SectionHeading
              id="quick-actions-title"
              icon={<LayoutDashboard size={18} />}
              title="Meine Funktionen"
              description="Konto, Sicherheit und persönliche Einstellungen direkt öffnen."
            />
            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <DashboardAction icon={<UserRound />} label="Profil" description="Persönliche Daten" onClick={() => panels.openPanel('profile')} />
              <DashboardAction icon={<Settings />} label="Einstellungen" description="Darstellung & Verhalten" onClick={() => panels.openPanel('settings')} />
              <DashboardAction icon={<MonitorSmartphone />} label="Sitzungen" description="Angemeldete Geräte" onClick={() => panels.openPanel('sessions')} />
              {user?.passwordLoginAvailable ? (
                <DashboardAction icon={<KeyRound />} label="Passwort" description="Zugang absichern" onClick={() => panels.openPanel('change-password')} />
              ) : (
                <DashboardAction icon={<ShieldCheck />} label="Zugriff" description={accessLabel} />
              )}
            </div>
          </section>
        ) : null}

        {recentChats.length > 0 ? (
          <section aria-labelledby="recent-chats-title">
            <SectionHeading
              id="recent-chats-title"
              icon={<Clock3 size={18} />}
              title="Letzte Chats"
              description="Setze deine zuletzt geöffneten Gespräche direkt fort."
            />
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {recentChats.map((entry) => (
                <NodeCard
                  key={entry.node.id}
                  node={entry.node}
                  eyebrow={entry.path.join(' › ') || 'Chat'}
                  icon={<MessageSquare size={19} />}
                  onClick={() => onNavigateToNode?.(entry.node.id)}
                />
              ))}
            </div>
          </section>
        ) : null}

        <section aria-labelledby="available-projects-title">
          <SectionHeading
            id="available-projects-title"
            icon={<FolderKanban size={18} />}
            title="Verfügbare Projekte"
            description="Projekte aus deinen sichtbaren Bereichen."
          />
          {availableProjects.length > 0 ? (
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {availableProjects.slice(0, 6).map((entry) => (
                <NodeCard
                  key={entry.node.id}
                  node={entry.node}
                  eyebrow={entry.path.join(' › ') || 'Projekt'}
                  icon={<FolderKanban size={19} />}
                  onClick={() => onNavigateToNode?.(entry.node.id)}
                />
              ))}
            </div>
          ) : (
            <EmptyPanel text="In deinen verfügbaren Bereichen gibt es derzeit keine Projekte." />
          )}
        </section>

        <section aria-labelledby="available-areas-title">
          <SectionHeading
            id="available-areas-title"
            icon={<Building2 size={18} />}
            title="Verfügbare Bereiche"
            description="Alle Bereiche, die dir aktuell bereitgestellt wurden."
          />

          {availableAreas.length > 0 ? (
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {availableAreas.map((child) => (
                <NodeCard
                  key={child.id}
                  node={child}
                  eyebrow={labelForNodeType(child.type)}
                  icon={<DynamicIcon name={iconForNodeType(child.type)} className="h-5 w-5" />}
                  onClick={() => onNavigateToNode?.(child.id)}
                />
              ))}
            </div>
          ) : (
            <EmptyPanel text="Diesem Benutzer sind derzeit keine Bereiche zugeordnet." />
          )}
        </section>

        {isOwnNode && quotas?.limits && quotas.usage ? (
          <section aria-labelledby="usage-title">
            <SectionHeading
              id="usage-title"
              icon={<ShieldCheck size={18} />}
              title="Nutzung & Kontingente"
              description="Deine aktuell verwendeten Bereiche, Projekte und Chats."
            />
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3" aria-label="Eigene Nutzungslimits">
              <QuotaValue label="Bereiche" used={quotas.usage.workspace} limit={quotas.limits.workspace} />
              <QuotaValue label="Projekte" used={quotas.usage.project} limit={quotas.limits.project} />
              <QuotaValue label="Chats" used={quotas.usage.chat} limit={quotas.limits.chat} />
            </div>
          </section>
        ) : null}

        <section aria-labelledby="personal-widgets-title" className="rounded-2xl border border-border-soft bg-white p-5 shadow-sm dark:border-white/10 dark:bg-slate-900/40">
          <div className="flex items-center justify-between gap-4">
            <SectionHeading
              id="personal-widgets-title"
              icon={<Sparkles size={18} />}
              title="Widgets & Anbindungen"
              description="Persönliche Erweiterungen, Kalender, Favoriten und angebundene Funktionen."
            />
            <WidgetBadges nodeId={node.id} size="sm" allowedComponentTypePrefixes={USER_WIDGET_PREFIXES} />
          </div>
          <div className="mt-3">
            <WidgetsForNode
              nodeId={node.id}
              variant="workspace"
              showEmptyState={false}
              allowedComponentTypePrefixes={USER_WIDGET_PREFIXES}
            />
          </div>
        </section>
      </div>
    </WorkspaceLayout>
  );
}

function QuotaValue({ label, used, limit }: { label: string; used: number; limit: number }) {
  const percentage = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div className="rounded-xl border border-border-soft bg-white p-4 shadow-sm dark:border-white/10 dark:bg-slate-900/50">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium text-text dark:text-gray-200">{label}</span>
        <strong className="text-text dark:text-white">{used}/{limit}</strong>
      </div>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div className="h-full rounded-full bg-emerald-600 dark:bg-emerald-400" style={{ width: `${percentage}%` }} />
      </div>
      <p className="mt-2 text-xs text-text-muted dark:text-gray-400">{limit - used > 0 ? `${limit - used} verfügbar` : 'Kontingent ausgeschöpft'}</p>
    </div>
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
    <div className="rounded-lg border border-slate-200 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/25">
      <dt className="text-[11px] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="mt-1 flex items-center gap-1.5 truncate text-sm font-medium text-slate-950 dark:text-white">
        {icon}
        {value}
      </dd>
    </div>
  );
}

function SectionHeading({
  id,
  icon,
  title,
  description,
}: {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-w-0 items-start gap-3">
      <span className="mt-0.5 text-emerald-700 dark:text-emerald-300">{icon}</span>
      <span className="min-w-0">
        <h2 id={id} className="text-base font-semibold text-slate-950 dark:text-white">{title}</h2>
        <p className="mt-0.5 text-sm text-slate-600 dark:text-gray-400">{description}</p>
      </span>
    </div>
  );
}

function DashboardAction({
  icon,
  label,
  description,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  onClick?: () => void;
}) {
  const content = (
    <>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200 [&>svg]:h-4 [&>svg]:w-4">{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-slate-950 dark:text-white">{label}</span>
        <span className="mt-0.5 block truncate text-xs text-slate-600 dark:text-gray-400">{description}</span>
      </span>
      {onClick ? <ChevronRight size={16} className="text-slate-400" /> : null}
    </>
  );
  const classes = 'flex min-w-0 items-center gap-3 rounded-xl border border-slate-200 bg-white p-3 text-left shadow-sm transition dark:border-white/10 dark:bg-slate-900/50';

  return onClick ? (
    <button type="button" onClick={onClick} className={`${classes} hover:border-emerald-300 hover:bg-emerald-50/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/20`}>
      {content}
    </button>
  ) : (
    <div className={classes}>{content}</div>
  );
}

function NodeCard({
  node,
  eyebrow,
  icon,
  onClick,
}: {
  node: UserWorkspaceNode;
  eyebrow: string;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex min-w-0 items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-white/10 dark:bg-slate-900/50 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/20"
      aria-label={`${node.name} öffnen`}
    >
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">{icon}</span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-semibold text-slate-950 dark:text-white">{node.name}</span>
        <span className="mt-1 block truncate text-xs text-slate-600 dark:text-gray-400">{eyebrow}</span>
      </span>
      <ArrowRight size={17} className="shrink-0 text-slate-400 transition group-hover:text-emerald-700 dark:group-hover:text-emerald-300" />
    </button>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return (
    <div className="mt-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-sm text-slate-600 dark:border-white/15 dark:bg-slate-900/30 dark:text-gray-400">
      {text}
    </div>
  );
}

interface VisibleNodeEntry {
  node: UserWorkspaceNode;
  path: string[];
}

function flattenVisibleDescendants(
  nodes: UserWorkspaceNode[],
  path: string[] = [],
): VisibleNodeEntry[] {
  return nodes.flatMap((child) => {
    const entry = { node: child, path };
    return [entry, ...flattenVisibleDescendants(child.children ?? [], [...path, child.name])];
  });
}

function isNodeType(node: UserWorkspaceNode, ...types: string[]): boolean {
  const normalized = node.type.trim().toLowerCase();
  return types.includes(normalized);
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
