// F:\Kernschmied\frontend\src\components\workspace\SelectedNodeWorkspace.tsx

import { useEffect, useState } from 'react';
import Modal from '../ui/Modal';
import { resolveTemplate } from '../../utils/templateResolver';
import { Globe2, Plus } from 'lucide-react';
import { DynamicIcon } from '../../registry/iconRegistry';

import { GenericChatView } from '../chat';
import { SettingsDialog } from '../settings';
import { WebsiteWorkspace } from '../websites';
import SchemaRenderer from '../schema/SchemaRenderer';
import WidgetBadges from '../widgets/WidgetBadges';
import WidgetsForNode from '../widgets/WidgetsForNode';

/* ============================================================
 * Typen und Konstanten
 * ============================================================ */

export interface SelectedWorkspaceNode {
  id: string;
  name: string;
  type: string;
  // optionally include metadata/prompt fields when the full HierarchyNode is passed
  metadata?: Record<string, unknown> | null;
  system_prompt?: string | null;
  effective_prompt?: string | null;
}

interface SelectedNodeWorkspaceProps {
  // the caller may pass either a minimal node or the full HierarchyNode
  node: SelectedWorkspaceNode | (SelectedWorkspaceNode & Record<string, any>) | null;
  schema?: any;
  onUpdateHierarchyNode?: (id: string, payload: unknown) => Promise<void>;
}

const SETTINGS_NODE_TYPES = new Set<string>([
  'settings',
  'configuration',
  'system_config',
  'system-configuration',
]);

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

/* ============================================================
 * Hauptkomponente
 * ============================================================ */

export function SelectedNodeWorkspace({ node, schema, onUpdateHierarchyNode }: SelectedNodeWorkspaceProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const normalizedType = node ? normalizeNodeType(node.type) : null;

  /*
   * Wird ein Einstellungsknoten ausgewählt, öffnet sich der Dialog
   * automatisch. Beim Wechsel zu einem anderen Knotentyp wird er
   * geschlossen.
   */
  useEffect(() => {
    setIsSettingsOpen(normalizedType !== null && SETTINGS_NODE_TYPES.has(normalizedType));
  }, [normalizedType, node?.id]);

  if (!node || !normalizedType) {
    return <EmptyWorkspace />;
  }

  /* ----------------------------------------------------------
   * Systemeinstellungen
   * ---------------------------------------------------------- */

  if (SETTINGS_NODE_TYPES.has(normalizedType)) {
    return (
      <section
        className={[
          'flex min-h-0 min-w-0',
          'w-full flex-1 flex-col',
          'overflow-hidden',
          'bg-slate-50',
          'dark:bg-slate-950/30',
        ].join(' ')}
        aria-label={`Einstellungen: ${node.name}`}
      >
        {isSettingsOpen ? (
          <SettingsDialog
            isOpen={isSettingsOpen}
            onClose={() => {
              setIsSettingsOpen(false);
            }}
          />
        ) : (
          <SettingsClosedView
            onOpen={() => {
              setIsSettingsOpen(true);
            }}
          />
        )}
        <div className="absolute right-4 top-4">
          <WidgetBadges nodeId={(node as any).id} />
        </div>

        <div className="mx-auto w-full max-w-6xl mt-6">
          <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
          <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
        </div>
      </section>
    );
  }

  /* ----------------------------------------------------------
   * Chat
   * ---------------------------------------------------------- */

    if (CHAT_NODE_TYPES.has(normalizedType)) {
    return (
      <section
        className={[
          'flex min-h-0 min-w-0',
          'w-full flex-1',
          'overflow-hidden',
          'bg-white',
          'dark:bg-slate-950',
        ].join(' ')}
        aria-label={`Chat: ${node.name}`}
      >
        <div className="absolute right-6 top-6 z-20">
          <WidgetBadges nodeId={(node as any).id} />
        </div>
        <div className="w-full">
          <GenericChatView title={node.name} hierarchyNodeId={node.id} hierarchyNodeType={normalizedType} />

          <div className="mt-6 px-6">
            <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </div>
        </div>
      </section>
    );
  }

  /* ----------------------------------------------------------
   * Workspace / Bereich - spezielle Einstellungen
   * ---------------------------------------------------------- */
  if (normalizedType === 'workspace' || normalizedType === 'bereich') {
    return (
      <section
        className={['flex min-h-0 min-w-0', 'w-full flex-1', 'overflow-auto', 'bg-white', 'dark:bg-slate-950',].join(' ')}
        aria-label={`Workspace: ${node.name}`}
      >
        <div className="mx-auto w-full max-w-4xl p-6">
          <h2 className="text-lg font-semibold">Bereich: {node.name}</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">Spezielle Einstellungen für diesen Bereich.</p>

          <WorkspaceSettingsPanel node={node} onUpdateHierarchyNode={onUpdateHierarchyNode} />

          <div className="mt-6">
            {/* Prompt editor, falls vorhanden */}
            <div className="rounded-lg border bg-white p-3">
              <h3 className="text-xs font-semibold text-slate-500">Prompt</h3>
              <PromptEditor
                node={node}
                resolvedPrompt={(node as any)?.metadata?.prompt ?? (node as any)?.system_prompt}
                onUpdateHierarchyNode={onUpdateHierarchyNode}
              />
            </div>
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
              <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
            </div>
          </div>
        </div>
      </section>
    );
  }


  /* ----------------------------------------------------------
   * Webseiten-Sammlung
   * ---------------------------------------------------------- */

  if (WEBSITE_COLLECTION_NODE_TYPES.has(normalizedType)) {
    return <WebsiteCollectionView node={node} />;
  }

  /* ----------------------------------------------------------
   * Einzelne Webseite
   * ---------------------------------------------------------- */

  if (WEBSITE_NODE_TYPES.has(normalizedType)) {
    return (
      <section className={[ 'flex min-h-0 min-w-0', 'w-full flex-1', 'overflow-auto', 'bg-slate-50 p-6', 'dark:bg-slate-950/30', 'sm:p-8', ].join(' ')} aria-label={`Website: ${node.name}`}>
        <div className="mx-auto w-full max-w-6xl">
          <WebsiteWorkspace websiteId={node.id} title={node.name} />
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </div>
        </div>
      </section>
    );
  }

  /* ----------------------------------------------------------
   * Noch nicht unterstützter Knotentyp
   * ---------------------------------------------------------- */
  if (WEBSITE_COLLECTION_NODE_TYPES.has(normalizedType)) {
    return <WebsiteCollectionView node={node} />;
  }

  if (WEBSITE_NODE_TYPES.has(normalizedType)) {
    return (
      <section className={[ 'flex min-h-0 min-w-0', 'w-full flex-1', 'overflow-auto', 'bg-slate-50 p-6', 'dark:bg-slate-950/30', 'sm:p-8', ].join(' ')} aria-label={`Website: ${node.name}`}>
        <div className="mx-auto w-full max-w-6xl">
          <WebsiteWorkspace websiteId={node.id} title={node.name} />
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
            <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
          </div>
        </div>
      </section>
    );
  }

  // If the schema provides a node definition for this type, render the SchemaRenderer
  if (schema && schema.node_types && schema.node_types[normalizedType]) {
    const nodeDef = schema.node_types[normalizedType];

    // If the node type definition looks like a UI component (has `.type`),
    // render it via the SchemaRenderer. Otherwise treat it as a simple
    // node-type descriptor (label/icon/allowed_actions) and render a
    // friendly card view.
    if (nodeDef && typeof nodeDef.type === 'string') {
      return (
        <section
          className={[
            'flex min-h-0 min-w-0',
            'w-full flex-1',
            'overflow-auto',
            'bg-slate-50 p-6',
            'dark:bg-slate-950/30',
            'sm:p-8',
          ].join(' ')}
          aria-label={`Schema view: ${node.name}`}
        >
            <div className="absolute right-6 top-6 z-20">
              <WidgetBadges nodeId={(node as any).id} />
            </div>
          <div className="mx-auto w-full max-w-6xl">
            <SchemaRenderer schema={nodeDef} context={{ nodeId: node.id }} />
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
              <WidgetsForNode nodeId={node.id} />
            </div>
          </div>
        </section>
      );
    }

    // Node-type descriptor (legacy/simple shape) -> render card
    const def: any = nodeDef;
    // Prefer prompt stored on the node instance; fall back to the node-type definition
    const instancePrompt = (node as any)?.system_prompt ?? (node as any)?.effective_prompt ??
      (node as any)?.metadata?.prompt;
    const resolvedPrompt =
      instancePrompt ?? def.system_prompt ?? def.effective_prompt ?? def.metadata?.prompt;
    return (
      <section
        className={[
          'flex min-h-0 min-w-0',
          'w-full flex-1',
          'overflow-auto',
          'bg-slate-50 p-6',
          'dark:bg-slate-950/30',
          'sm:p-8',
        ].join(' ')}
        aria-label={`Node type: ${node.name}`}
      >
        <div className="absolute right-6 top-6 z-20">
          <WidgetBadges nodeId={(node as any).id} />
        </div>
        <div className="mx-auto w-full max-w-4xl">
          <div className="flex items-center gap-4">
            <div
              className={[
                'flex h-14 w-14 items-center justify-center rounded-lg border',
                'bg-white text-2xl',
              ].join(' ')}
              style={def.color ? { backgroundColor: def.color } : undefined}
            >
              {/* Icon name may be provided */}
              {def.icon ? <DynamicIcon name={def.icon} size={28} /> : <span />}
            </div>

            <div>
              <h2 className="text-lg font-semibold">{def.label ?? node.type}</h2>
              {def.description ? (
                <p className="text-sm text-slate-600 dark:text-slate-400">{def.description}</p>
              ) : null}
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-4">
            <div className="rounded-lg border bg-white p-3">
              <h3 className="text-xs font-semibold text-slate-500">Erlaubte Aktionen</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {(Array.isArray(def.allowed_actions) ? def.allowed_actions : []).map(
                  (a: string) => (
                    <span key={a} className="rounded bg-slate-100 px-2 py-0.5 text-xs">
                      {a}
                    </span>
                  ),
                )}
              </div>
            </div>

            <div className="rounded-lg border bg-white p-3">
              <h3 className="text-xs font-semibold text-slate-500">Erlaubte Kindtypen</h3>
              <div className="mt-2 flex flex-wrap gap-2">
                {(Array.isArray(def.allowed_child_types) ? def.allowed_child_types : []).map(
                  (t: string) => (
                    <span key={t} className="rounded bg-slate-100 px-2 py-0.5 text-xs">
                      {t}
                    </span>
                  ),
                )}
              </div>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
                    <div className="rounded-lg border bg-white p-3">
                      <h3 className="text-xs font-semibold text-slate-500">Prompt</h3>
                      <PromptEditor
                        node={node}
                        resolvedPrompt={resolvedPrompt}
                        onUpdateHierarchyNode={onUpdateHierarchyNode}
                      />
                    </div>

            <div className="rounded-lg border bg-white p-3">
              <h3 className="text-xs font-semibold text-slate-500">Rohdefinition</h3>
              <div className="mt-2 max-h-48 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-800 whitespace-pre-wrap wrap-break-word">
                {JSON.stringify(def ?? {}, null, 2)}
              </div>
            </div>
            <div className="rounded-lg border bg-white p-3">
              <h3 className="text-xs font-semibold text-slate-500">Widgets</h3>
              <div className="mt-2">
                <WidgetsForNode nodeId={node.id} />
              </div>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return <NodePlaceholder node={node} schema={schema} />;
}
// Inline prompt editor component
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

  if (!node) return <div className="text-xs text-slate-400">Kein Prompt definiert.</div>;

  async function save() {
    if (!onUpdateHierarchyNode) return setEditing(false);
    setIsSaving(true);
    try {
      const metadata = { ...(node as any).metadata ?? {}, prompt: value || null };
      await onUpdateHierarchyNode((node as any).id, { metadata });
      setEditing(false);
    } catch (err) {
      // ignore — the toast flow in parent will handle errors
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="mt-2 text-sm text-slate-700">
      {!editing ? (
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            {value ? (
                  <>
                    <div className="max-h-28 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-800 whitespace-pre-wrap wrap-break-word">
                      {String(value)}
                    </div>

                    <div className="mt-2">
                      <div className="text-xs text-slate-500">Aufgelöste Vorschau</div>
                      <div className="mt-1 max-h-20 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-800 whitespace-pre-wrap">
                        {resolveTemplate(value, { system: { name: 'Kernschmied' } })}
                      </div>
                      <div className="mt-1">
                        <button
                          type="button"
                          className="inline-flex items-center rounded border px-2 py-1 text-xs"
                          onClick={() => setShowResolvedModal(true)}
                        >
                          Voll anzeigen
                        </button>
                        <Modal isOpen={showResolvedModal} title="Aufgelöster Prompt" onClose={() => setShowResolvedModal(false)} confirmLabel="Schließen">
                          <pre className="whitespace-pre-wrap">{resolveTemplate(value, { system: { name: 'Kernschmied' } })}</pre>
                        </Modal>
                      </div>
                    </div>
                  </>
            ) : (
              <div className="text-xs text-slate-400">Kein Prompt definiert.</div>
            )}
          </div>

          <div className="ml-4 flex shrink-0 flex-col gap-2">
            <button
              type="button"
              className="inline-flex items-center rounded bg-primary px-2 py-1 text-xs text-white"
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
            className="w-full rounded border border-border px-2 py-1 text-sm"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />

          <div className="mt-2 flex gap-2">
            <button
              type="button"
              className="inline-flex items-center rounded bg-primary px-3 py-1 text-sm text-white"
              onClick={() => void save()}
              disabled={isSaving}
            >
              {isSaving ? 'Speichern…' : 'Speichern'}
            </button>

            <button
              type="button"
              className="inline-flex items-center rounded border px-3 py-1 text-sm"
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

function WorkspaceSettingsPanel({
  node,
  onUpdateHierarchyNode,
}: {
  node: SelectedWorkspaceNode | null | undefined;
  onUpdateHierarchyNode?: (id: string, payload: unknown) => Promise<void>;
}) {
  const [access, setAccess] = useState<string | null>(
    (node as any)?.metadata?.access ?? null,
  );
  const [channelUrl, setChannelUrl] = useState<string | null>(
    (node as any)?.metadata?.channel_url ?? null,
  );
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
      } as Record<string, unknown>;

      await onUpdateHierarchyNode((node as any).id, { metadata });
    } catch (err) {
      // parent toasts handle errors
    } finally {
      setIsSaving(false);
    }
  }

  if (!node) return null;

  return (
    <div className="mt-4 grid gap-4">
      <div className="rounded-lg border bg-white p-4">
        <label className="block text-xs font-semibold text-slate-500">Zugriff</label>
        <select
          className="mt-2 w-full rounded border px-2 py-1"
          value={access ?? ''}
          onChange={(e) => setAccess(e.target.value || null)}
        >
          <option value="">(nicht gesetzt)</option>
          <option value="public">Public (Website-Kanal)</option>
          <option value="intern">Intern (angemeldete Nutzer / eingeladene)</option>
          <option value="private">Privat (Nur Owner)</option>
        </select>
      </div>

      <div className="rounded-lg border bg-white p-4">
        <label className="block text-xs font-semibold text-slate-500">Channel-URL (optional)</label>
        <input
          type="text"
          className="mt-2 w-full rounded border px-2 py-1"
          value={channelUrl ?? ''}
          onChange={(e) => setChannelUrl(e.target.value || null)}
          placeholder="https://example.com/…"
        />
      </div>

      <div className="rounded-lg border bg-white p-4">
        <label className="block text-xs font-semibold text-slate-500">Eingeladene (Komma-getrennt)</label>
        <textarea
          rows={3}
          className="mt-2 w-full rounded border px-2 py-1"
          value={inviteList ?? ''}
          onChange={(e) => setInviteList(e.target.value || null)}
          placeholder="user1@example.com, user2@example.com"
        />
      </div>

      <div className="rounded-lg border bg-white p-4">
        <label className="block text-xs font-semibold text-slate-500">Owner</label>
        <input
          type="text"
          className="mt-2 w-full rounded border px-2 py-1"
          value={owner ?? ''}
          onChange={(e) => setOwner(e.target.value || null)}
        />
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          className="inline-flex items-center rounded bg-primary px-3 py-1 text-sm text-white"
          onClick={() => void save()}
          disabled={isSaving}
        >
          {isSaving ? 'Speichern…' : 'Speichern'}
        </button>
      </div>
    </div>
  );
}
function NodePlaceholder({ node, schema }: NodePlaceholderProps & { schema?: any }) {
  const titleId = createElementId('workspace-node-title', node.id);

  return (
    <section
      className={[
        'flex min-h-0 min-w-0',
        'w-full flex-1',
        'items-center justify-center',
        'overflow-auto',
        'bg-slate-50 p-6',
        'dark:bg-slate-950/30',
        'sm:p-8',
      ].join(' ')}
      aria-labelledby={titleId}
    >
      <div
        className={[
          'w-full max-w-xl',
          'rounded-2xl',
          'border border-slate-200',
          'bg-white p-6',
          'shadow-sm',
          'dark:border-white/10',
          'dark:bg-slate-900/50',
        ].join(' ')}
      >
        <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
          {node.type}
        </p>

        <h1 id={titleId} className="mt-2 text-xl font-semibold text-slate-950 dark:text-white">
          {node.name}
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-400">
          {/** prefer schema-driven description if available */}
          {schema &&
          schema.node_types &&
          schema.node_types[node.type] &&
          schema.node_types[node.type].description
            ? schema.node_types[node.type].description
            : 'Für diesen Knotentyp wird künftig die passende schema-gesteuerte Ansicht über den zentralen SchemaRenderer dargestellt.'}
        </p>

        <dl className="mt-5 grid gap-3 rounded-xl bg-slate-100 p-4 text-sm dark:bg-white/5">
          <div className="flex min-w-0 gap-3">
            <dt className="w-20 shrink-0 font-medium text-slate-500 dark:text-slate-400">ID</dt>

            <dd className="min-w-0 flex-1 wrap-break-words font-mono text-slate-800 dark:text-slate-200">
              {node.id}
            </dd>
          </div>

          <div className="flex min-w-0 gap-3">
            <dt className="w-20 shrink-0 font-medium text-slate-500 dark:text-slate-400">Typ</dt>

            <dd className="min-w-0 flex-1 wrap-break-words font-mono text-slate-800 dark:text-slate-200">
              {node.type}
            </dd>
          </div>
        </dl>
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-slate-500 mb-2">Widgets</h3>
          <WidgetsForNode nodeId={node.id} variant="workspace" showEmptyState={false} />
        </div>
      </div>
    </section>
  );
}

/* ============================================================
 * Leerer Arbeitsbereich
 * ============================================================ */

function EmptyWorkspace() {
  return (
    <section
      className={[
        'flex min-h-0 min-w-0',
        'w-full flex-1',
        'items-center justify-center',
        'overflow-auto',
        'bg-slate-50 p-6',
        'dark:bg-slate-950/30',
        'sm:p-8',
      ].join(' ')}
      aria-labelledby="empty-workspace-title"
    >
      <div className="w-full max-w-md text-center">
        <h1
          id="empty-workspace-title"
          className="text-xl font-semibold text-slate-950 dark:text-white"
        >
          Kein Bereich ausgewählt
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
          Wähle links einen Arbeitsbereich, ein Projekt, einen Chat, eine Webseite oder die
          Systemeinstellungen aus.
        </p>
      </div>
    </section>
  );
}

/* ============================================================
 * Webseiten-Sammlung
 * ============================================================ */

interface WebsiteCollectionViewProps {
  node: SelectedWorkspaceNode;
}

function WebsiteCollectionView({ node }: WebsiteCollectionViewProps) {
  const titleId = createElementId('website-collection-title', node.id);

  return (
    <section
      className={[
        'flex min-h-0 min-w-0',
        'w-full flex-1 flex-col',
        'overflow-auto',
        'bg-slate-50',
        'p-6',
        'dark:bg-slate-950/30',
        'sm:p-8',
      ].join(' ')}
      aria-labelledby={titleId}
    >
      <div className="mx-auto w-full max-w-6xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div
                className={[
                  'flex h-11 w-11 shrink-0',
                  'items-center justify-center',
                  'rounded-xl',
                  'border border-blue-200',
                  'bg-blue-50',
                  'text-blue-600',
                  'dark:border-blue-400/20',
                  'dark:bg-blue-500/10',
                  'dark:text-blue-400',
                ].join(' ')}
                aria-hidden="true"
              >
                <Globe2 size={22} />
              </div>

              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                  Webseiten
                </p>

                <h1
                  id={titleId}
                  className="truncate text-2xl font-semibold text-slate-950 dark:text-white"
                >
                  {node.name}
                </h1>
              </div>
            </div>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-400">
              Hier werden die in Kernschmied registrierten Webseiten verwaltet. Wähle links eine
              Webseite aus, um ihre Vorschau zu öffnen und sie später zu bearbeiten.
            </p>
          </div>

          <button
            type="button"
            disabled
            className={[
              'inline-flex shrink-0',
              'items-center justify-center',
              'gap-2 rounded-xl',
              'bg-blue-600',
              'px-4 py-2.5',
              'text-sm font-semibold',
              'text-white shadow-sm',
              'transition',
              'disabled:cursor-not-allowed',
              'disabled:opacity-50',
            ].join(' ')}
            title="Das Anlegen neuer Webseiten wird später über eine autorisierte Backend-Aktion bereitgestellt."
          >
            <Plus size={17} aria-hidden="true" />
            Webseite hinzufügen
          </button>
        </header>

        <div
          className={[
            'mt-8 rounded-2xl',
            'border border-dashed',
            'border-slate-300',
            'bg-white/70',
            'p-8 text-center',
            'dark:border-white/15',
            'dark:bg-slate-900/40',
          ].join(' ')}
        >
          <Globe2
            size={36}
            className="mx-auto text-slate-400 dark:text-slate-500"
            aria-hidden="true"
          />

          <h2 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">
            Webseite in der Hierarchie auswählen
          </h2>

          <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-600 dark:text-slate-400">
            Die vorhandenen Webseiten erscheinen als untergeordnete Knoten dieses Bereichs. Für die
            Vorschau wird der Knotentyp
            <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs dark:bg-white/10">
              website
            </code>
            verwendet.
          </p>
        </div>
      </div>
    </section>
  );
}

/* ============================================================
 * Platzhalter für unbekannte Knotentypen
 * ============================================================ */

interface NodePlaceholderProps {
  node: SelectedWorkspaceNode;
}

/* ============================================================
 * Geschlossene Einstellungen
 * ============================================================ */

interface SettingsClosedViewProps {
  onOpen: () => void;
}

function SettingsClosedView({ onOpen }: SettingsClosedViewProps) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center p-6">
      <div className="text-center">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Die Einstellungen wurden geschlossen.
        </p>

        <button
          type="button"
          className={[
            'mt-3 rounded-lg',
            'bg-blue-600',
            'px-4 py-2',
            'text-sm font-medium',
            'text-white',
            'transition',
            'hover:bg-blue-700',
            'focus-visible:outline-none',
            'focus-visible:ring-2',
            'focus-visible:ring-blue-500',
            'focus-visible:ring-offset-2',
            'dark:focus-visible:ring-offset-slate-950',
          ].join(' ')}
          onClick={onOpen}
        >
          Einstellungen öffnen
        </button>
      </div>
    </div>
  );
}

/* ============================================================
 * Hilfsfunktionen
 * ============================================================ */

function normalizeNodeType(nodeType: string): string {
  return nodeType.trim().toLowerCase();
}

function createElementId(prefix: string, value: string): string {
  const normalizedValue = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^[-_]+|[-_]+$/g, '');

  return normalizedValue ? `${prefix}-${normalizedValue}` : prefix;
}
