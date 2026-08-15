// F:\Kernschmied\frontend\src\components\workspace\SelectedNodeWorkspace.tsx

import { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import { resolveTemplate } from '../../utils/templateResolver';
import { Activity, Building2, FilePenLine, FileText, FolderKanban, Globe2, LayoutGrid, MessageSquare, Plus, Settings2, SlidersHorizontal, Trash2, Wrench } from 'lucide-react';
import { DynamicIcon } from '../../registry/iconRegistry';
import IconBadge from '../common/IconBadge';
import { getNodeTypeConfig } from '../../config/nodeTypeConfig';
import WorkspaceLayout from '../layout/WorkspaceLayout';

import { GenericChatView } from '../chat';
import { SettingsDialog } from '../settings';
import { WebsiteWorkspace } from '../websites';
import SchemaRenderer from '../schema/SchemaRenderer';
import WidgetBadges from '../widgets/WidgetBadges';
import WidgetsForNode from '../widgets/WidgetsForNode';
import CollapsibleWidgetPanel from '../widgets/CollapsibleWidgetPanel';
import SystemOverview from '../system/SystemOverview';
import UserNodeWorkspace from './UserNodeWorkspace';
import NodeWorkspaceOverview, { NodeWorkspaceAction } from './NodeWorkspaceOverview';
import RecentNodeSection from './RecentNodeSection';

/* ============================================================
 * TYPEN UND KONSTANTEN
 * ============================================================ */

export interface SelectedWorkspaceNode {
  id: string;
  name: string;
  type: string;
  metadata?: Record<string, unknown> | null;
  system_prompt?: string | null;
  effective_prompt?: string | null;
}

interface SelectedNodeWorkspaceProps {
  node: SelectedWorkspaceNode | (SelectedWorkspaceNode & Record<string, any>) | null;
  schema?: any;
  onUpdateHierarchyNode?: (id: string, payload: unknown) => Promise<void>;
  onNavigateToNode?: (nodeId: string) => void;
  onAction?: (action: string, node: any) => void;
}

const SETTINGS_NODE_TYPES = new Set<string>([
  'settings',
  'configuration',
  'system_config',
  'system-configuration',
]);

const SYSTEM_ROOT_NODE_TYPES = new Set<string>(['system', 'system_root', 'system-root']);

const CHAT_NODE_TYPES = new Set<string>(['chat', 'conversation']);

const WEBSITE_COLLECTION_NODE_TYPES = new Set<string>([
  'websites',
  'website_collection',
  'website-collection',
  'webseiten',
]);

const WEBSITE_NODE_TYPES = new Set<string>([
  'website',
  'webseite',
  'static_website',
  'static-website',
]);

const NODE_TYPE_ALIASES: Record<string, string> = {
  bereich: 'workspace',
  benutzer: 'user',
  benutzerkonto: 'user',
  projekt: 'project',
};

/* ============================================================
 * HAUPTKOMPONENTE
 * ============================================================ */

export function SelectedNodeWorkspace({
  node,
  schema,
  onUpdateHierarchyNode,
  onNavigateToNode,
  onAction,
}: SelectedNodeWorkspaceProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const normalizedType = node ? normalizeNodeType(node.type) : null;


  useEffect(() => {
    setIsSettingsOpen(normalizedType !== null && SETTINGS_NODE_TYPES.has(normalizedType));
  }, [normalizedType, node?.id]);

  if (!node || !normalizedType) {
    return <EmptyWorkspace />;
  }


  /* ----------------------------------------------------------
   * SYSTEM-ROOT
   * ---------------------------------------------------------- */
  if (SYSTEM_ROOT_NODE_TYPES.has(normalizedType)) {
    const cfg = getNodeTypeConfig('system');
    const children = Array.isArray((node as any).children) ? (node as any).children : [];

    return (
      <WorkspaceLayout
        icon={<IconBadge icon={<DynamicIcon name={cfg.icon ?? 'LayoutDashboard'} />} size={cfg.defaultSize} variant={cfg.variant} />}
        title={`System: ${node.name}`}
        widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
        background="white"
      >
        <div className="grid w-full grid-cols-1 gap-4">
          <NodeWorkspaceOverview
            eyebrow="Systemknoten"
            title={node.name}
            description="Zentrale Betriebsübersicht, Konfiguration, Prompt und registrierte Systemfunktionen."
            icon={<Activity />}
            metrics={[
              { label: 'Knotentyp', value: 'System' },
              { label: 'Unterknoten', value: children.length },
              { label: 'Status', value: String((node as any).status ?? 'Aktiv') },
            ]}
          />
          <RecentNodeSection
            nodes={children}
            acceptedTypes={['user', 'workspace', 'bereich', 'project', 'projekt', 'chat', 'conversation']}
            title="Zuletzt verwendet"
            description="Zuletzt geöffnete Inhalte aus der sichtbaren Systemhierarchie."
            onNavigateToNode={onNavigateToNode}
            includeDescendants
          />
          <CollapsibleWidgetPanel title="Systemübersicht" icon={<Activity size={19} />}>
            <SystemOverview />
          </CollapsibleWidgetPanel>

          <CollapsibleWidgetPanel
            title="Knotendaten"
            icon={<SlidersHorizontal size={19} />}
            defaultOpen={false}
          >
            <WorkspaceSettingsPanel node={node} onUpdateHierarchyNode={onUpdateHierarchyNode} />
          </CollapsibleWidgetPanel>

          <CollapsibleWidgetPanel title="Systemprompt" icon={<FileText size={19} />} defaultOpen={false}>
            <PromptEditor
              node={node}
              resolvedPrompt={(node as any)?.system_prompt ?? (node as any)?.metadata?.prompt}
              onUpdateHierarchyNode={onUpdateHierarchyNode}
            />
          </CollapsibleWidgetPanel>

          <CollapsibleWidgetPanel title="Systemwidgets" icon={<LayoutGrid size={19} />}>
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </CollapsibleWidgetPanel>
        </div>
      </WorkspaceLayout>
    );
  }

  /* ----------------------------------------------------------
   * SYSTEMEINSTELLUNGEN (inkl. System‑Root)
   * ---------------------------------------------------------- */
  if (SETTINGS_NODE_TYPES.has(normalizedType)) {
    const cfg = getNodeTypeConfig('system');
    return (
      <WorkspaceLayout
        icon={<IconBadge icon={<DynamicIcon name={cfg.icon ?? 'Circle'} />} size={cfg.defaultSize} variant={cfg.variant} />}
        title={`Einstellungen: ${node.name}`}
        widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
        background="white"
      >
        {isSettingsOpen ? (
          <SettingsDialog isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
        ) : (
          <SettingsClosedView onOpen={() => setIsSettingsOpen(true)} />
        )}
        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold text-text-soft dark:text-gray-300">Widgets</h3>
          <div className="max-h-[60vh] overflow-auto">
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </div>
        </div>
      </WorkspaceLayout>
    );
  }

  /* ----------------------------------------------------------
   * PERSÖNLICHER BENUTZERBEREICH
   * ---------------------------------------------------------- */
  if (normalizedType === 'user') {
    return (
      <UserNodeWorkspace
        node={node as any}
        onNavigateToNode={onNavigateToNode}
        onAction={onAction}
      />
    );
  }

  /* ----------------------------------------------------------
   * CHAT
   * ---------------------------------------------------------- */
  if (CHAT_NODE_TYPES.has(normalizedType)) {
    const children = Array.isArray((node as any).children) ? (node as any).children : [];
    const actions = Array.isArray((node as any).actions) ? (node as any).actions : [];
    return (
      <GenericChatView
        title={node.name}
        hierarchyNodeId={node.id}
        hierarchyNodeType={normalizedType}
        childNodes={children}
        onNavigateToNode={onNavigateToNode}
        canManageHistory={actions.includes('delete')}
      />
    );
  }

  /* ----------------------------------------------------------
   * PROJEKT (project / projekt)
   * ---------------------------------------------------------- */
  if (normalizedType === 'project' || normalizedType === 'projekt') {
    const cfg = getNodeTypeConfig('project');
    const actions = (node as any).actions ?? cfg.allowedActions ?? [];
    const children = Array.isArray((node as any).children) ? (node as any).children : [];
    const chatCount = children.filter((child: any) => CHAT_NODE_TYPES.has(normalizeNodeType(child?.type) ?? '')).length;

    return (
      <WorkspaceLayout
        icon={<IconBadge icon={<DynamicIcon name={cfg.icon ?? 'Folder'} />} size={cfg.defaultSize} variant={cfg.variant} />}
        title={`Projekt: ${node.name}`}
        widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
        background="white"
      >
        <div className="w-full space-y-4">
          <NodeWorkspaceOverview
            eyebrow="Projekt"
            title={node.name}
            description="Arbeitskontext für Chats, Projektprompt, Metadaten und angebundene Werkzeuge."
            icon={<FolderKanban />}
            actions={<>
              {actions.includes('rename') ? <NodeWorkspaceAction icon={<FilePenLine size={16} />} onClick={() => onAction?.('rename', node)}>Umbenennen</NodeWorkspaceAction> : null}
              {actions.includes('create_child') ? <NodeWorkspaceAction icon={<Plus size={16} />} onClick={() => onAction?.('create_child', node)}>Chat erstellen</NodeWorkspaceAction> : null}
              {actions.includes('edit_prompt') ? <NodeWorkspaceAction icon={<FileText size={16} />} onClick={() => onAction?.('edit_prompt', node)}>Prompt bearbeiten</NodeWorkspaceAction> : null}
              {actions.includes('toggle_tools') ? <NodeWorkspaceAction icon={<Wrench size={16} />} onClick={() => onAction?.('toggle_tools', node)}>Tools umschalten</NodeWorkspaceAction> : null}
              {actions.includes('delete') ? <NodeWorkspaceAction danger icon={<Trash2 size={16} />} onClick={() => onAction?.('delete', node)}>Löschen</NodeWorkspaceAction> : null}
            </>}
            metrics={[
              { label: 'Chats', value: chatCount, icon: <MessageSquare size={16} /> },
              { label: 'Zugriff', value: String((node as any).metadata?.access ?? 'Vererbt') },
              { label: 'Status', value: String((node as any).status ?? 'Aktiv') },
            ]}
          />
          <RecentNodeSection
            nodes={children}
            acceptedTypes={['chat', 'conversation']}
            title="Letzte Chats"
            description="Zuletzt geöffnete Chats in diesem Projekt."
            onNavigateToNode={onNavigateToNode}
          />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <CollapsibleWidgetPanel title="Projektprompt" icon={<FileText size={19} />}>
              <PromptEditor
                node={node}
                resolvedPrompt={(node as any)?.system_prompt ?? (node as any)?.metadata?.prompt}
                onUpdateHierarchyNode={onUpdateHierarchyNode}
              />
            </CollapsibleWidgetPanel>
            <CollapsibleWidgetPanel title="Projektdaten" icon={<Settings2 size={19} />}>
              <WorkspaceSettingsPanel node={node} onUpdateHierarchyNode={onUpdateHierarchyNode} />
            </CollapsibleWidgetPanel>
          </div>
          <CollapsibleWidgetPanel title="Projektwidgets" icon={<LayoutGrid size={19} />}>
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </CollapsibleWidgetPanel>
        </div>
      </WorkspaceLayout>
    );
  }

  /* ----------------------------------------------------------
   * BEREICH / WORKSPACE
   * ---------------------------------------------------------- */
  if (normalizedType === 'workspace' || normalizedType === 'bereich') {
    const cfg = getNodeTypeConfig(normalizedType);
    const actions = (node as any).actions ?? cfg.allowedActions ?? [];
    const resolvedIconName =
      (schema?.node_types?.[normalizedType]?.icon as string) ??
      (NODE_TYPE_ALIASES[normalizedType] && (schema?.node_types?.[NODE_TYPE_ALIASES[normalizedType]]?.icon as string)) ??
      cfg.icon ??
      'Building2';
    const children = Array.isArray((node as any).children) ? (node as any).children : [];
    const projectCount = children.filter((child: any) => ['project', 'projekt'].includes(normalizeNodeType(child?.type) ?? '')).length;
    const chatCount = children.filter((child: any) => CHAT_NODE_TYPES.has(normalizeNodeType(child?.type) ?? '')).length;

    return (
      <WorkspaceLayout
        icon={<IconBadge icon={<DynamicIcon name={resolvedIconName} />} size={cfg.defaultSize} variant={cfg.variant} />}
        title={`Bereich: ${node.name}`}
        widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
        background="white"
      >
        <div className="w-full space-y-4">
          <NodeWorkspaceOverview
            eyebrow="Bereich"
            title={node.name}
            description="Gemeinsamer Rahmen für Projekte, direkte Chats, Zugriffsregeln und Bereichsfunktionen."
            icon={<Building2 />}
            actions={actions.includes('create_child') ? <>
              <NodeWorkspaceAction icon={<Plus size={16} />} onClick={() => onAction?.('create_child', node)}>Projekt erstellen</NodeWorkspaceAction>
              <NodeWorkspaceAction icon={<MessageSquare size={16} />} onClick={() => onAction?.('create_chat', node)}>Chat erstellen</NodeWorkspaceAction>
            </> : null}
            metrics={[
              { label: 'Projekte', value: projectCount, icon: <FolderKanban size={16} /> },
              { label: 'Direkte Chats', value: chatCount, icon: <MessageSquare size={16} /> },
              { label: 'Zugriff', value: String((node as any).metadata?.access ?? 'Privat') },
            ]}
          />
          <RecentNodeSection
            nodes={children}
            acceptedTypes={['project', 'projekt']}
            title="Letzte Projekte"
            description="Zuletzt geöffnete Projekte in diesem Bereich."
            onNavigateToNode={onNavigateToNode}
          />
          <CollapsibleWidgetPanel title="Bereichsdaten" icon={<Settings2 size={19} />}>
            <WorkspaceSettingsPanel node={node} onUpdateHierarchyNode={onUpdateHierarchyNode} />
          </CollapsibleWidgetPanel>
          <CollapsibleWidgetPanel title="Bereichsprompt" icon={<FileText size={19} />}>
            <PromptEditor
              node={node}
              resolvedPrompt={(node as any)?.system_prompt ?? (node as any)?.metadata?.prompt}
              onUpdateHierarchyNode={onUpdateHierarchyNode}
            />
          </CollapsibleWidgetPanel>
          <CollapsibleWidgetPanel title="Bereichswidgets" icon={<LayoutGrid size={19} />}>
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </CollapsibleWidgetPanel>
        </div>
      </WorkspaceLayout>
    );
  }

  /* ----------------------------------------------------------
   * WEBSEITEN-SAMMLUNG
   * ---------------------------------------------------------- */
  if (WEBSITE_COLLECTION_NODE_TYPES.has(normalizedType)) {
    return <WebsiteCollectionView node={node} />;
  }

  /* ----------------------------------------------------------
   * EINZELNE WEBSEITE
   * ---------------------------------------------------------- */
  if (WEBSITE_NODE_TYPES.has(normalizedType)) {
    const cfg = getNodeTypeConfig('website');
    return (
      <WorkspaceLayout
        icon={<IconBadge icon={<DynamicIcon name={cfg.icon ?? 'Globe2'} />} size={cfg.defaultSize} variant={cfg.variant} />}
        title={`Webseite: ${node.name}`}
        widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
        background="slate"
      >
        <div className="w-full">
          <WebsiteWorkspace websiteId={node.id} title={node.name} embedded />
        </div>
      </WorkspaceLayout>
    );
  }

  /* ----------------------------------------------------------
   * SCHEMA-GESTEUERTE ANSICHT (wenn Schema vorhanden)
   * ---------------------------------------------------------- */
  if (schema && schema.node_types && schema.node_types[normalizedType]) {
    const nodeDef = schema.node_types[normalizedType];
    const cfg = getNodeTypeConfig(normalizedType);

    if (nodeDef && typeof nodeDef.type === 'string') {
      return (
        <WorkspaceLayout
          icon={<IconBadge icon={<DynamicIcon name={nodeDef.icon ?? cfg.icon ?? 'Circle'} />} size={cfg.defaultSize} variant={cfg.variant} />}
          title={nodeDef.label ?? node.name}
          widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
          background="slate"
        >
          <div className="w-full">
            <SchemaRenderer schema={nodeDef} context={{ nodeId: node.id }} />
          </div>
        </WorkspaceLayout>
      );
    }

    // Legacy / einfache Knotentyp-Beschreibung
    const def: any = nodeDef;
    const instancePrompt =
      (node as any)?.system_prompt ?? (node as any)?.effective_prompt ?? (node as any)?.metadata?.prompt;
    const resolvedPrompt = instancePrompt ?? def.system_prompt ?? def.effective_prompt ?? def.metadata?.prompt;

    return (
      <WorkspaceLayout
        icon={<IconBadge icon={def.icon ? <DynamicIcon name={def.icon} /> : <span />} size="lg" variant={def.color ? 'default' : 'primary'} />}
        title={def.label ?? node.type}
        widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
        background="slate"
      >
        <div className="w-full space-y-6">
          {def.description && (
            <p className="text-sm text-text-soft dark:text-gray-300">{def.description}</p>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-border-soft bg-white/70 p-3 dark:border-white/10 dark:bg-slate-900/40">
              <h3 className="text-xs font-semibold text-text-muted dark:text-gray-400">Erlaubte Aktionen</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {(Array.isArray(def.allowed_actions) ? def.allowed_actions : []).map((a: string) => (
                  <span key={a} className="rounded bg-surface-muted px-2 py-0.5 text-xs dark:bg-slate-800/50">
                    {a}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-border-soft bg-white/70 p-3 dark:border-white/10 dark:bg-slate-900/40">
              <h3 className="text-xs font-semibold text-text-muted dark:text-gray-400">Erlaubte Kindtypen</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {(Array.isArray(def.allowed_child_types) ? def.allowed_child_types : []).map((t: string) => (
                  <span key={t} className="rounded bg-surface-muted px-2 py-0.5 text-xs dark:bg-slate-800/50">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-border-soft bg-white/70 p-3 dark:border-white/10 dark:bg-slate-900/40">
            <h3 className="text-xs font-semibold text-text-muted dark:text-gray-400">Prompt</h3>
            <PromptEditor node={node} resolvedPrompt={resolvedPrompt} onUpdateHierarchyNode={onUpdateHierarchyNode} />
          </div>
          <div className="rounded-lg border border-border-soft bg-white/70 p-3 dark:border-white/10 dark:bg-slate-900/40">
            <h3 className="text-xs font-semibold text-text-muted dark:text-gray-400">Rohdefinition</h3>
            <div className="mt-2 max-h-48 overflow-auto rounded bg-surface-muted p-2 text-xs text-text-soft whitespace-pre-wrap dark:bg-slate-800/50 dark:text-gray-300">
              {JSON.stringify(def ?? {}, null, 2)}
            </div>
          </div>
        </div>
      </WorkspaceLayout>
    );
  }

  /* ----------------------------------------------------------
   * FALLBACK: Platzhalter für unbekannte Typen
   * ---------------------------------------------------------- */
  return <NodePlaceholder node={node} schema={schema} />;
}

/* ============================================================
 * PROMPT-EDITOR
 * ============================================================ */

function PromptEditor({
  node,
  resolvedPrompt,
  onUpdateHierarchyNode,
}: {
  node: SelectedWorkspaceNode | null | undefined;
  resolvedPrompt: string | null | undefined;
  onUpdateHierarchyNode?: (id: string, payload: unknown) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(resolvedPrompt ?? '');
  const [isSaving, setIsSaving] = useState(false);
  const [showResolvedModal, setShowResolvedModal] = useState(false);

  useEffect(() => {
    setValue(resolvedPrompt ?? '');
  }, [resolvedPrompt, node?.id]);

  if (!node) return <div className="text-xs text-text-muted dark:text-gray-400">Kein Prompt definiert.</div>;

  async function save() {
    if (!onUpdateHierarchyNode) return setEditing(false);
    setIsSaving(true);
    try {
      const payload: any = {
        system_prompt: value || null,
        prompt_enabled: !!value,
      };
      if ((node as any)?.prompt_mode !== undefined) payload.prompt_mode = (node as any).prompt_mode;
      if ((node as any)?.prompt_priority !== undefined) payload.prompt_priority = (node as any).prompt_priority;
      await onUpdateHierarchyNode((node as any).id, payload);
      setEditing(false);
    } catch (err) {
      // Fehler werden von der Parent-Komponente behandelt (Toast)
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mt-2 text-sm text-text-soft dark:text-gray-300">
      {!editing ? (
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            {value ? (
              <>
                <div className="max-h-28 overflow-auto rounded bg-surface-muted p-2 text-xs text-text-soft whitespace-pre-wrap dark:bg-slate-800/50 dark:text-gray-300">
                  {String(value)}
                </div>
                <div className="mt-2">
                  <div className="text-xs text-text-muted dark:text-gray-400">Aufgelöste Vorschau</div>
                  <div className="mt-1 max-h-20 overflow-auto rounded bg-surface-muted p-2 text-xs text-text-soft whitespace-pre-wrap dark:bg-slate-800/50 dark:text-gray-300">
                    {resolveTemplate(value, { system: { name: 'Kernschmied' } })}
                  </div>
                  <div className="mt-1">
                    <button
                      type="button"
                      className="inline-flex items-center rounded-lg border border-border-soft px-2 py-1 text-xs transition hover:bg-surface-hover dark:border-white/10"
                      onClick={() => setShowResolvedModal(true)}
                    >
                      Voll anzeigen
                    </button>
                    <Modal
                      isOpen={showResolvedModal}
                      title="Aufgelöster Prompt"
                      onClose={() => setShowResolvedModal(false)}
                      confirmLabel="Schließen"
                    >
                      <pre className="whitespace-pre-wrap">{resolveTemplate(value, { system: { name: 'Kernschmied' } })}</pre>
                    </Modal>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-xs text-text-muted dark:text-gray-400">Kein Prompt definiert.</div>
            )}
          </div>
          <div className="ml-4 flex shrink-0 flex-col gap-2">
            <button
              type="button"
              className="inline-flex items-center rounded-lg bg-primary px-2 py-1 text-xs text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow"
              onClick={() => setEditing(true)}
            >
              Bearbeiten
            </button>
          </div>
        </div>
      ) : (
        <div onMouseDown={(e) => e.stopPropagation()}>
          <textarea
            rows={6}
            className="w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              className="inline-flex items-center rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow disabled:opacity-50"
              onClick={() => void save()}
              disabled={isSaving}
            >
              {isSaving ? 'Speichern…' : 'Speichern'}
            </button>
            <button
              type="button"
              className="inline-flex items-center rounded-lg border border-border-soft px-3 py-1.5 text-sm font-medium text-text-soft transition hover:bg-surface-hover dark:border-white/10 dark:text-gray-300 dark:hover:bg-slate-800"
              onClick={() => {
                setEditing(false);
                setValue(resolvedPrompt ?? '');
              }}
              disabled={isSaving}
            >
              Abbrechen
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ============================================================
 * WORKSPACE SETTINGS PANEL (Metadaten)
 * ============================================================ */

function WorkspaceSettingsPanel({
  node,
  onUpdateHierarchyNode,
}: {
  node: SelectedWorkspaceNode | null | undefined;
  onUpdateHierarchyNode?: (id: string, payload: unknown) => Promise<void>;
}) {
  const [access, setAccess] = useState<string | null>((node as any)?.metadata?.access ?? null);
  const [channelUrl, setChannelUrl] = useState<string | null>((node as any)?.metadata?.channel_url ?? null);
  const [inviteList, setInviteList] = useState<string | null>(
    Array.isArray((node as any)?.metadata?.invite_list)
      ? ((node as any).metadata.invite_list as string[]).join(', ')
      : (node as any)?.metadata?.invite_list ?? null,
  );
  const [owner, setOwner] = useState<string | null>((node as any)?.metadata?.owner ?? null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setAccess((node as any)?.metadata?.access ?? null);
    setChannelUrl((node as any)?.metadata?.channel_url ?? null);
    setInviteList(
      Array.isArray((node as any)?.metadata?.invite_list)
        ? ((node as any).metadata.invite_list as string[]).join(', ')
        : (node as any)?.metadata?.invite_list ?? null,
    );
    setOwner((node as any)?.metadata?.owner ?? null);
  }, [node?.id]);

  async function save() {
    if (!node || !onUpdateHierarchyNode) return;
    setIsSaving(true);
    try {
      const metadata = {
        ...(node as any).metadata ?? {},
        access: access ?? undefined,
        channel_url: channelUrl ?? undefined,
        invite_list: inviteList ? inviteList.split(',').map((s) => s.trim()).filter(Boolean) : [],
        owner: owner ?? undefined,
      };
      await onUpdateHierarchyNode((node as any).id, { metadata });
    } catch (err) {
      // Parent behandelt Fehler
    } finally {
      setIsSaving(false);
    }
  }

  if (!node) return null;

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-semibold text-text-muted dark:text-gray-400">Zugriff</label>
        <select
          className="mt-2 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
          value={access ?? ''}
          onChange={(e) => setAccess(e.target.value || null)}
        >
          <option value="">(nicht gesetzt)</option>
          <option value="public">Public (Website-Kanal)</option>
          <option value="intern">Intern (angemeldete Nutzer / eingeladene)</option>
          <option value="private">Privat (Nur Owner)</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-semibold text-text-muted dark:text-gray-400">Channel-URL (optional)</label>
        <input
          type="text"
          className="mt-2 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
          value={channelUrl ?? ''}
          onChange={(e) => setChannelUrl(e.target.value || null)}
          placeholder="https://example.com/…"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-text-muted dark:text-gray-400">Eingeladene (Komma-getrennt)</label>
        <textarea
          rows={3}
          className="mt-2 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
          value={inviteList ?? ''}
          onChange={(e) => setInviteList(e.target.value || null)}
          placeholder="user1@example.com, user2@example.com"
        />
      </div>

      <div>
        <label className="block text-xs font-semibold text-text-muted dark:text-gray-400">Owner</label>
        <input
          type="text"
          className="mt-2 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
          value={owner ?? ''}
          onChange={(e) => setOwner(e.target.value || null)}
        />
      </div>

      <div>
        <button
          type="button"
          className="inline-flex items-center rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow disabled:opacity-50"
          onClick={() => void save()}
          disabled={isSaving}
        >
          {isSaving ? 'Speichern…' : 'Speichern'}
        </button>
      </div>
    </div>
  );
}

/* ============================================================
 * WEBSITE COLLECTION VIEW
 * ============================================================ */

interface WebsiteCollectionViewProps {
  node: SelectedWorkspaceNode;
}

function WebsiteCollectionView({ node }: WebsiteCollectionViewProps) {
  const titleId = createElementId('website-collection-title', node.id);
  const cfg = getNodeTypeConfig('website');

  return (
    <WorkspaceLayout
      icon={<IconBadge icon={<Globe2 />} size={cfg.defaultSize} variant={cfg.variant} />}
      title={`Webseiten: ${node.name}`}
      widgetBadges={<WidgetBadges nodeId={node.id} size="sm" />}
      background="slate"
    >
      <div className="w-full">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div aria-hidden="true">
                <IconBadge icon={<Globe2 />} size="lg" variant="primary" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-primary dark:text-primary">
                  Webseiten
                </p>
                <h1 id={titleId} className="truncate text-2xl font-semibold text-text dark:text-white">
                  {node.name}
                </h1>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-text-soft dark:text-gray-300">
              Hier werden die in Kernschmied registrierten Webseiten verwaltet. Wähle links eine Webseite aus, um ihre Vorschau zu öffnen und sie später zu bearbeiten.
            </p>
          </div>
          <button
            type="button"
            disabled
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow disabled:cursor-not-allowed disabled:opacity-50"
            title="Das Anlegen neuer Webseiten wird später über eine autorisierte Backend-Aktion bereitgestellt."
          >
            <Plus size={17} aria-hidden="true" />
            Webseite hinzufügen
          </button>
        </header>

        <div className="mt-8 rounded-2xl border border-dashed border-border-soft bg-white/70 p-8 text-center dark:border-white/15 dark:bg-slate-900/40">
          <IconBadge icon={<Globe2 />} size="lg" variant="default" className="mx-auto" />
          <h2 className="mt-4 text-base font-semibold text-text dark:text-white">
            Webseite in der Hierarchie auswählen
          </h2>
          <p className="mt-2 text-sm leading-6 text-text-soft dark:text-gray-300">
            Die vorhandenen Webseiten erscheinen als untergeordnete Knoten dieses Bereichs. Für die Vorschau wird der Knotentyp{' '}
            <code className="mx-1 rounded bg-surface-muted px-1.5 py-0.5 font-mono text-xs dark:bg-slate-800/50">
              website
            </code>{' '}
            verwendet.
          </p>
        </div>
      </div>
    </WorkspaceLayout>
  );
}

/* ============================================================
 * NODE PLACEHOLDER (Fallback für unbekannte Typen)
 * ============================================================ */

interface NodePlaceholderProps {
  node: SelectedWorkspaceNode;
  schema?: any;
}

function NodePlaceholder({ node, schema }: NodePlaceholderProps) {
  const titleId = createElementId('workspace-node-title', node.id);
  return (
    <section
      className="flex min-h-0 min-w-0 w-full flex-1 items-center justify-center overflow-auto bg-slate-50 p-6 dark:bg-slate-950/30 sm:p-8"
      aria-labelledby={titleId}
    >
      <div className="w-full max-w-2xl rounded-2xl border border-border-soft bg-white/80 p-6 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/50">
        <p className="text-xs font-semibold uppercase tracking-wider text-primary dark:text-primary">{node.type}</p>
        <h1 id={titleId} className="mt-2 text-xl font-semibold text-text dark:text-white">{node.name}</h1>
        <p className="mt-3 text-sm leading-6 text-text-soft dark:text-gray-300">
          {schema?.node_types?.[node.type]?.description ||
            'Für diesen Knotentyp wird künftig die passende schema-gesteuerte Ansicht über den zentralen SchemaRenderer dargestellt.'}
        </p>
        <dl className="mt-5 grid gap-3 rounded-xl bg-surface-muted p-4 text-sm dark:bg-white/5">
          <div className="flex min-w-0 gap-3">
            <dt className="w-20 shrink-0 font-medium text-text-muted dark:text-gray-400">ID</dt>
            <dd className="min-w-0 flex-1 wrap-break-words font-mono text-text dark:text-white">{node.id}</dd>
          </div>
          <div className="flex min-w-0 gap-3">
            <dt className="w-20 shrink-0 font-medium text-text-muted dark:text-gray-400">Typ</dt>
            <dd className="min-w-0 flex-1 wrap-break-words font-mono text-text dark:text-white">{node.type}</dd>
          </div>
        </dl>
        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold text-text-soft dark:text-gray-300">Widgets</h3>
          <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
        </div>
      </div>
    </section>
  );
}

/* ============================================================
 * LEERER ARBEITSBEREICH
 * ============================================================ */

function EmptyWorkspace() {
  return (
    <section
      className="flex min-h-0 min-w-0 w-full flex-1 items-center justify-center overflow-auto bg-slate-50 p-6 dark:bg-slate-950/30 sm:p-8"
      aria-labelledby="empty-workspace-title"
    >
      <div className="w-full text-center px-6 sm:px-8">
        <h1 id="empty-workspace-title" className="text-xl font-semibold text-text dark:text-white">
          Kein Bereich ausgewählt
        </h1>
        <p className="mt-2 text-sm leading-6 text-text-soft dark:text-gray-300">
          Wähle links einen Arbeitsbereich, ein Projekt, einen Chat, eine Webseite oder die Systemeinstellungen aus.
        </p>
      </div>
    </section>
  );
}

/* ============================================================
 * GESCHLOSSENE EINSTELLUNGEN
 * ============================================================ */

interface SettingsClosedViewProps {
  onOpen: () => void;
}

function SettingsClosedView({ onOpen }: SettingsClosedViewProps) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center p-6">
      <div className="text-center">
        <p className="text-sm text-text-muted dark:text-gray-400">Die Einstellungen wurden geschlossen.</p>
        <button
          type="button"
          className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 dark:bg-primary/80 dark:hover:bg-primary"
          onClick={onOpen}
        >
          Einstellungen öffnen
        </button>
      </div>
    </div>
  );
}

/* ============================================================
 * HILFSFUNKTIONEN
 * ============================================================ */

function normalizeNodeType(nodeType: string): string {
  return nodeType.trim().toLowerCase();
}

function createElementId(prefix: string, value: string): string {
  const normalized = value.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^[-_]+|[-_]+$/g, '');
  return normalized ? `${prefix}-${normalized}` : prefix;
}