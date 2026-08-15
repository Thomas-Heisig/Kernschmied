import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { updateHierarchyNode } from '../../api/hierarchy';
import type { HierarchyNode } from '../../contracts/hierarchy';
import { ApiError } from '../../api/client';
import widgetsApi from '../../api/widgets';
import fetchWidgetsClient from '../../api/fetchWidgetsClient';
import fetchToolsClient, { putNodeToolPolicy } from '../../api/fetchToolsClient';
import SettingsJsonEditor from '../settings/SettingsJsonEditor';
import IconBadge from '../common/IconBadge';
import {
  X,
  Settings,
  Layers,
  Puzzle,
  Wrench,
  MessageSquare,
  Save,
  RefreshCw,
  Plus,
  Minus,
  Copy,
  AlertCircle,
} from 'lucide-react';

type TabId = 'general' | 'structure' | 'widgets' | 'prompts' | 'tools';

interface NodeEditorDialogProps {
  isOpen: boolean;
  node: HierarchyNode | null;
  nodeTypes: Record<string, any>;
  onClose: () => void;
  onSaved: () => void;
  initialTab?: TabId;
}

export default function NodeEditorDialog({
  isOpen,
  node,
  nodeTypes,
  onClose,
  onSaved,
  initialTab = 'general',
}: NodeEditorDialogProps) {
  // State (behält alle bestehenden States)
  const [name, setName] = useState(node?.name ?? '');
  const [type, setType] = useState(node?.type ?? '');
  const [activeTab, setActiveTab] = useState<TabId>('general');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // UI metadata (Allgemein)
  const [uiLabel, setUiLabel] = useState('');
  const [uiIcon, setUiIcon] = useState('');
  const [uiColor, setUiColor] = useState('');
  const [uiVisibility, setUiVisibility] = useState('');
  const [uiSelectable, setUiSelectable] = useState(false);
  const [uiDraggable, setUiDraggable] = useState(false);
  const [uiDroppable, setUiDroppable] = useState(false);
  const [uiExpandable, setUiExpandable] = useState(false);
  const [accessVisibility, setAccessVisibility] = useState('');
  const [assignedUserIds, setAssignedUserIds] = useState('');

  const [useDefaultLabel, setUseDefaultLabel] = useState(true);
  const [useDefaultIcon, setUseDefaultIcon] = useState(true);
  const [useDefaultColor, setUseDefaultColor] = useState(true);
  const [useDefaultVisibility, setUseDefaultVisibility] = useState(true);
  const [useDefaultSelectable, setUseDefaultSelectable] = useState(true);
  const [useDefaultDraggable, setUseDefaultDraggable] = useState(true);
  const [useDefaultDroppable, setUseDefaultDroppable] = useState(true);
  const [useDefaultExpandable, setUseDefaultExpandable] = useState(true);

  // Structure tab
  const [useOverride, setUseOverride] = useState(false);
  const [overrideChildTypes, setOverrideChildTypes] = useState<string[]>([]);

  // Widgets tab
  const [registryWidgets, setRegistryWidgets] = useState<any[] | null>(null);
  const [effectiveWidgets, setEffectiveWidgets] = useState<any[] | null>(null);
  const [widgetSearch, setWidgetSearch] = useState('');
  const [widgetFilter, setWidgetFilter] = useState<'all' | 'active' | 'available' | 'disabled'>('all');
  const [widgetStatusMsg, setWidgetStatusMsg] = useState<string | null>(null);

  // Prompts tab
  const [promptsLocal, setPromptsLocal] = useState<string | null>(null);
  const [promptsChain, setPromptsChain] = useState<any[] | null>(null);
  const [resolvedPrompt, setResolvedPrompt] = useState<any | null>(null);
  const [promptSaving, setPromptSaving] = useState(false);
  const [promptError, setPromptError] = useState<string | null>(null);

  // Tools tab
  const [toolsRegistry, setToolsRegistry] = useState<any[] | null>(null);
  const [nodeToolPolicy, setNodeToolPolicy] = useState<Record<string, boolean> | null>(null);
  const [nodeToolConfigs, setNodeToolConfigs] = useState<Record<string, any> | null>(null);
  const [effectiveToolIds, setEffectiveToolIds] = useState<string[] | null>(null);
  const [toolSearch, setToolSearch] = useState('');
  const [toolFilter, setToolFilter] = useState<'all' | 'active' | 'inherited' | 'available' | 'disabled'>('all');
  const [toolStatusMsg, setToolStatusMsg] = useState<string | null>(null);

  // Config editor state
  const [configEditorKind, setConfigEditorKind] = useState<'tool' | 'widget' | null>(null);
  const [configEditorKey, setConfigEditorKey] = useState<string | null>(null);
  const [configEditorValue, setConfigEditorValue] = useState('');
  const [configEditorError, setConfigEditorError] = useState<string | null>(null);
  const [configEditorCopied, setConfigEditorCopied] = useState(false);

  // ---- Lifecycle ----
  useEffect(() => {
    setName(node?.name ?? '');
    setType(node?.type ?? '');
    setError(null);
    const metaHierarchy = (node as any)?.metadata?.hierarchy;
    setUseOverride(Boolean(metaHierarchy?.allowed_child_types));
    setOverrideChildTypes(metaHierarchy?.allowed_child_types?.map((s: string) => String(s)) ?? []);
    const metaUI = (node as any)?.metadata?.ui ?? {};
    setUiLabel(metaUI.label ?? '');
    setUiIcon(metaUI.icon ?? '');
    setUiColor(metaUI.color ?? '');
    setUiVisibility(metaUI.visibility ?? '');
    setUiSelectable(Boolean(metaUI.selectable));
    setUiDraggable(Boolean(metaUI.draggable));
    setUiDroppable(Boolean(metaUI.droppable));
    setUiExpandable(Boolean(metaUI.expandable));
    setUseDefaultLabel(!Object.prototype.hasOwnProperty.call(metaUI, 'label'));
    setUseDefaultIcon(!Object.prototype.hasOwnProperty.call(metaUI, 'icon'));
    setUseDefaultColor(!Object.prototype.hasOwnProperty.call(metaUI, 'color'));
    setUseDefaultVisibility(!Object.prototype.hasOwnProperty.call(metaUI, 'visibility'));
    setUseDefaultSelectable(!Object.prototype.hasOwnProperty.call(metaUI, 'selectable'));
    setUseDefaultDraggable(!Object.prototype.hasOwnProperty.call(metaUI, 'draggable'));
    setUseDefaultDroppable(!Object.prototype.hasOwnProperty.call(metaUI, 'droppable'));
    setUseDefaultExpandable(!Object.prototype.hasOwnProperty.call(metaUI, 'expandable'));
    const metadata = (node as any)?.metadata ?? {};
    setAccessVisibility(String(metadata.visibility ?? ''));
    setAssignedUserIds(
      Array.isArray(metadata.assigned_user_ids)
        ? metadata.assigned_user_ids.map(String).join(', ')
        : '',
    );
  }, [node]);

  useEffect(() => {
    if (isOpen) setActiveTab(initialTab);
  }, [isOpen, initialTab]);

  // ---- Data fetching (Widgets, Tools, Prompts) ----
  useEffect(() => {
    if (!isOpen || !node || activeTab !== 'widgets') return;
    let mounted = true;
    (async () => {
      try {
        const [regResp, eff] = await Promise.all([fetchWidgetsClient.listRegistry(), widgetsApi.loadEffectiveWidgets(node.id)]);
        if (!mounted) return;
        const rr: any = regResp as any;
        setRegistryWidgets(Array.isArray(rr) ? rr : (rr.items ?? rr));
        setEffectiveWidgets(Array.isArray(eff) ? eff : (eff as any));
      } catch (e) {
        if (mounted) setWidgetStatusMsg('Fehler beim Laden der Widgets');
      }
    })();
    return () => { mounted = false; };
  }, [isOpen, node, activeTab]);

  useEffect(() => {
    if (!isOpen || !node || activeTab !== 'tools') return;
    let mounted = true;
    (async () => {
      try {
        const reg = await fetchToolsClient.listRegistry({ include_disabled: true, include_unavailable: true });
        const nodeResp = await fetchToolsClient.getNode(node.id);
        const eff = await fetchToolsClient.getNodeEffectiveTools(node.id).catch(() => null);
        if (!mounted) return;
        const items = Array.isArray(reg) ? reg : (reg.items ?? reg);
        setToolsRegistry(items);
        const respAny: any = nodeResp as any;
        setNodeToolPolicy(respAny?.tool_policy ?? {});
        const metaTools = (respAny?.metadata ?? {}).tools ?? {};
        const policyConfigs = (respAny?.tool_policy ?? {}).configurations ?? {};
        setNodeToolConfigs({ ...(metaTools ?? {}), ...(policyConfigs ?? {}) });
        setEffectiveToolIds(Array.isArray(eff) ? eff : (eff?.effective_tool_ids ?? null));
        setToolStatusMsg(null);
      } catch (e) {
        if (mounted) setToolStatusMsg('Fehler beim Laden der Werkzeuge');
      }
    })();
    return () => { mounted = false; };
  }, [isOpen, node, activeTab]);

  useEffect(() => {
    if (!isOpen || !node || activeTab !== 'prompts') return;
    let mounted = true;
    (async () => {
      try {
        const client = await import('../../api/fetchPromptClient');
        const ctx = await client.loadPromptContext(node.id);
        if (!mounted) return;
        setPromptsLocal(ctx.local_prompt ?? null);
        setPromptsChain(ctx.sources ?? []);
        setResolvedPrompt({ system_prompt: ctx.effective_prompt ?? '', fragments: [] });
      } catch (e) {
        if (mounted) setPromptError('Der effektive Prompt konnte nicht aufgelöst werden.');
      }
    })();
    return () => { mounted = false; };
  }, [isOpen, node, activeTab]);

  // ---- Derived state ----
  const typeOptions = useMemo(() => Object.keys(nodeTypes ?? {}).map((k) => ({ id: k, def: nodeTypes[k] })), [nodeTypes]);
  const currentTypeDef = useMemo(() => nodeTypes?.[type] ?? null, [nodeTypes, type]);
  const directChildren = node?.children ?? [];
  const allowedChildTypesForSelected = useMemo(() => {
    if (!currentTypeDef) return [] as string[];
    return (currentTypeDef.allowed_child_types ?? []).map((s: string) => String(s));
  }, [currentTypeDef]);
  const incompatibleChildren = useMemo(() => {
    const allowed = useOverride ? overrideChildTypes : allowedChildTypesForSelected;
    if (!allowed || allowed.length === 0) return [] as HierarchyNode[];
    return (directChildren as HierarchyNode[]).filter((c) => !allowed.includes(c.type));
  }, [directChildren, allowedChildTypesForSelected, useOverride, overrideChildTypes]);

  // ---- Handlers ----
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setError(null);
    try {
      const payload: any = { name, type };
      const existingMeta = (node as any)?.metadata ?? {};
      const nextMeta = { ...(existingMeta || {}) } as any;

      // hierarchy override
      if (useOverride) {
        nextMeta.hierarchy = { ...(nextMeta.hierarchy ?? {}), allowed_child_types: overrideChildTypes };
      } else if (nextMeta.hierarchy && nextMeta.hierarchy.allowed_child_types !== undefined) {
        const copy = { ...(nextMeta.hierarchy || {}) };
        delete copy.allowed_child_types;
        if (Object.keys(copy).length === 0) delete nextMeta.hierarchy;
        else nextMeta.hierarchy = copy;
      }

      // UI metadata overrides
      const uiObj: any = { ...(nextMeta.ui ?? {}) };
      const setUiField = (key: string, value: any, useDefault: boolean) => {
        if (useDefault) {
          if (uiObj && Object.prototype.hasOwnProperty.call(uiObj, key)) delete uiObj[key];
        } else {
          uiObj[key] = value;
        }
      };
      setUiField('label', uiLabel || null, useDefaultLabel);
      setUiField('icon', uiIcon || null, useDefaultIcon);
      setUiField('color', uiColor || null, useDefaultColor);
      setUiField('visibility', uiVisibility || null, useDefaultVisibility);
      setUiField('selectable', uiSelectable, useDefaultSelectable);
      setUiField('draggable', uiDraggable, useDefaultDraggable);
      setUiField('droppable', uiDroppable, useDefaultDroppable);
      setUiField('expandable', uiExpandable, useDefaultExpandable);

      if (Object.keys(uiObj).length === 0) {
        if (nextMeta.ui !== undefined) delete nextMeta.ui;
      } else {
        nextMeta.ui = uiObj;
      }

      if (accessVisibility) nextMeta.visibility = accessVisibility;
      else delete nextMeta.visibility;

      const normalizedAssignments = assignedUserIds
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean);
      if (normalizedAssignments.length > 0) {
        nextMeta.assigned_user_ids = [...new Set(normalizedAssignments)];
      } else {
        delete nextMeta.assigned_user_ids;
      }

      const metaChanged = JSON.stringify(existingMeta || {}) !== JSON.stringify(nextMeta || {});
      if (metaChanged) payload.metadata = nextMeta;
      await updateHierarchyNode(node!.id, payload);
      await onSaved();
    } catch (err: unknown) {
      const maybe = err as any;
      if ((err instanceof ApiError) || maybe?.code === 'HIERARCHY_NODE_TYPE_CHANGE_INVALID') {
        const details = (err instanceof ApiError) ? (err as any).details : maybe.details;
        const invalid = details?.invalid_children as Array<any> | undefined;
        if (invalid && invalid.length > 0) {
          const list = invalid.map((c) => `${c.id} (${c.type})`).join(', ');
          setError(`Typwechsel nicht möglich: inkompatible Kinder: ${list}`);
        } else {
          setError((err instanceof Error ? (err as Error).message : null) ?? 'Typwechsel nicht möglich');
        }
      } else {
        setError(err instanceof Error ? err.message : 'Fehler beim Speichern');
      }
    } finally {
      setIsSaving(false);
    }
  }, [name, type, node, useOverride, overrideChildTypes, uiLabel, uiIcon, uiColor, uiVisibility, uiSelectable, uiDraggable, uiDroppable, uiExpandable, accessVisibility, assignedUserIds, useDefaultLabel, useDefaultIcon, useDefaultColor, useDefaultVisibility, useDefaultSelectable, useDefaultDraggable, useDefaultDroppable, useDefaultExpandable, onSaved]);

  const handleClose = useCallback(() => {
    const isDirty =
      name !== (node?.name ?? '') ||
      type !== (node?.type ?? '') ||
      (useOverride && JSON.stringify(overrideChildTypes) !== JSON.stringify(((node as any)?.metadata?.hierarchy?.allowed_child_types) ?? []));
    if (isDirty && !window.confirm('Nicht gespeicherte Änderungen verwerfen?')) return;
    onClose();
  }, [name, type, node, useOverride, overrideChildTypes, onClose]);

  // ---- Tab configuration ----
  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    { id: 'general', label: 'Allgemein', icon: <Settings size={16} /> },
    { id: 'structure', label: 'Struktur', icon: <Layers size={16} /> },
    { id: 'widgets', label: 'Widgets', icon: <Puzzle size={16} /> },
    { id: 'tools', label: 'Werkzeuge', icon: <Wrench size={16} /> },
    { id: 'prompts', label: 'Prompts', icon: <MessageSquare size={16} /> },
  ];

  if (!isOpen || !node) return null;

  // ---- Render helpers ----
  const renderTabButton = (tab: typeof tabs[0]) => {
    const isActive = activeTab === tab.id;
    return (
      <button
        key={tab.id}
        role="tab"
        aria-selected={isActive}
        className={[
          'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition',
          isActive
            ? 'bg-primary text-white shadow-sm'
            : 'text-text-soft hover:bg-surface-hover hover:text-text dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
        ].join(' ')}
        onClick={() => setActiveTab(tab.id)}
      >
        <IconBadge icon={tab.icon} size="sm" variant={isActive ? 'primary' : 'default'} />
        {tab.label}
      </button>
    );
  };

  const renderInput = (label: string, value: string, onChange: (v: string) => void, disabled?: boolean, placeholder?: string) => (
    <div>
      <label className="block text-sm font-medium text-text-soft dark:text-gray-300">{label}</label>
      <input
        className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
      />
    </div>
  );

  const renderSelect = (label: string, value: string, options: { value: string; label: string }[], onChange: (v: string) => void, disabled?: boolean) => (
    <div>
      <label className="block text-sm font-medium text-text-soft dark:text-gray-300">{label}</label>
      <select
        className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 disabled:opacity-60 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );

  const renderCheckbox = (label: string, checked: boolean, onChange: (v: boolean) => void, disabled?: boolean) => (
    <label className="inline-flex items-center gap-2 text-sm text-text-soft dark:text-gray-300">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        disabled={disabled}
        className="rounded border-border-soft text-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10"
      />
      {label}
    </label>
  );

  // ---- Render ----
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm" role="presentation" onClick={handleClose}>
      <div
        className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border-soft bg-white shadow-2xl dark:border-white/10 dark:bg-slate-900"
        role="dialog"
        aria-modal="true"
        aria-labelledby="node-editor-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Kopf */}
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border-soft bg-white/95 px-6 py-4 backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/95">
          <h2 id="node-editor-title" className="text-lg font-semibold text-text dark:text-white">
            Knoten bearbeiten
          </h2>
          <button
            type="button"
            className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
            onClick={handleClose}
            aria-label="Dialog schließen"
          >
            <IconBadge icon={<X />} size="sm" variant="default" />
          </button>
        </header>

        {/* Tabs */}
        <div className="border-b border-border-soft px-6 pt-4 dark:border-white/10" role="tablist">
          <div className="flex flex-wrap gap-1">{tabs.map(renderTabButton)}</div>
        </div>

        {/* Inhalt */}
        <div className="p-6">
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-danger/20 bg-danger-soft px-4 py-2 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          {/* General */}
          {activeTab === 'general' && (
            <div className="space-y-4">
              {renderInput('Name', name, setName)}
              {renderSelect('Typ', type, typeOptions.map((t) => ({ value: t.id, label: t.def?.label ?? t.id })), setType)}

              <div className="border-t border-border-soft pt-4 dark:border-white/10">
                <h3 className="mb-3 text-sm font-medium text-text-soft dark:text-gray-300">Anzeige (lokale Overrides)</h3>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {renderInput('Label', uiLabel, setUiLabel, useDefaultLabel)}
                  <div>
                    {renderInput('Icon', uiIcon, setUiIcon, useDefaultIcon)}
                    {renderCheckbox('Standard verwenden', useDefaultIcon, setUseDefaultIcon)}
                  </div>
                  <div>
                    {renderInput('Farbe', uiColor, setUiColor, useDefaultColor)}
                    {renderCheckbox('Standard verwenden', useDefaultColor, setUseDefaultColor)}
                  </div>
                  <div>
                    {renderSelect('Sichtbarkeit', uiVisibility, [
                      { value: '', label: '(Standard)' },
                      { value: 'public', label: 'public' },
                      { value: 'authenticated', label: 'authenticated' },
                      { value: 'private', label: 'private' },
                    ], setUiVisibility, useDefaultVisibility)}
                    {renderCheckbox('Standard verwenden', useDefaultVisibility, setUseDefaultVisibility)}
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-4">
                  {renderCheckbox('selectable', uiSelectable, setUiSelectable, useDefaultSelectable)}
                  {renderCheckbox('draggable', uiDraggable, setUiDraggable, useDefaultDraggable)}
                  {renderCheckbox('droppable', uiDroppable, setUiDroppable, useDefaultDroppable)}
                  {renderCheckbox('expandable', uiExpandable, setUiExpandable, useDefaultExpandable)}
                </div>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-text-muted">
                  {renderCheckbox('Standard selectable', useDefaultSelectable, setUseDefaultSelectable)}
                  {renderCheckbox('Standard draggable', useDefaultDraggable, setUseDefaultDraggable)}
                  {renderCheckbox('Standard droppable', useDefaultDroppable, setUseDefaultDroppable)}
                  {renderCheckbox('Standard expandable', useDefaultExpandable, setUseDefaultExpandable)}
                </div>
              </div>

              <div className="border-t border-border-soft pt-4 dark:border-white/10">
                <h3 className="mb-1 text-sm font-medium text-text-soft dark:text-gray-300">Datenzugriff</h3>
                <p className="mb-3 text-xs text-text-muted">Bestimmt serverseitig, welche angemeldeten Benutzer diesen Knoten und seine Kinder sehen dürfen.</p>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {renderSelect('Zugriffsstufe', accessVisibility, [
                    { value: '', label: 'Nur im eigenen Unterbaum' },
                    { value: 'private', label: 'Privat / nur Eigentümer' },
                    { value: 'assigned', label: 'Nur zugewiesene Benutzer' },
                    { value: 'internal', label: 'Intern / alle angemeldeten Benutzer' },
                    { value: 'public', label: 'Öffentlich freigegeben' },
                  ], setAccessVisibility)}
                  {renderInput('Zugewiesene Benutzer-IDs', assignedUserIds, setAssignedUserIds)}
                </div>
                <p className="mt-2 text-xs text-text-muted">Mehrere IDs mit Komma trennen. Zuweisungen gelten auch für untergeordnete Projekte und Chats.</p>
              </div>
            </div>
          )}

          {/* Structure */}
          {activeTab === 'structure' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Parent</h3>
                {node.parent_id ? (
                  <div className="mt-1 rounded-lg border border-border-soft bg-surface-muted px-4 py-2 text-sm dark:border-white/10 dark:bg-slate-800/50">
                    <div>ID: <code className="font-mono">{node.parent_id}</code></div>
                    <div>Name: {(node as any).parent_name ?? '—'}</div>
                    <div>Typ: {(node as any).parent_type ?? '—'}</div>
                  </div>
                ) : (
                  <div className="mt-1 text-sm text-text-muted">Kein übergeordneter Knoten</div>
                )}
              </div>

              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Aktueller Knotentyp</h3>
                <div className="mt-1 text-sm">{type}</div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Erlaubte Kindtypen</h3>
                <div className="mt-1 flex flex-wrap gap-1">
                  {allowedChildTypesForSelected.map((t: string) => (
                    <span key={t} className="rounded bg-surface-muted px-2 py-0.5 text-sm dark:bg-slate-800/50">{t}</span>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Erlaubte Aktionen</h3>
                <div className="mt-1 flex flex-wrap gap-1">
                  {(currentTypeDef?.allowed_actions ?? []).map((a: string) => (
                    <span key={a} className="rounded bg-surface-muted px-2 py-0.5 text-sm dark:bg-slate-800/50">{a}</span>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Flags (read-only)</h3>
                <div className="mt-1 space-y-0.5 text-sm">
                  <div>selectable: {String(Boolean(currentTypeDef?.selectable))}</div>
                  <div>draggable: {String(Boolean(currentTypeDef?.draggable))}</div>
                  <div>droppable: {String(Boolean(currentTypeDef?.droppable))}</div>
                  <div>expandable: {String(Boolean(currentTypeDef?.expandable))}</div>
                </div>
              </div>

              <div className="border-t border-border-soft pt-4 dark:border-white/10">
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Kindtypen für diesen Knoten einschränken</h3>
                <div className="mt-2 flex items-center gap-2">
                  {renderCheckbox('Eigene Einschränkung verwenden', useOverride, setUseOverride)}
                </div>
                {useOverride && (
                  <div className="mt-3">
                    <div className="mb-1 text-sm text-text-soft">Wähle erlaubte Kindtypen (nur Einschränken):</div>
                    <div className="flex flex-wrap gap-2">
                      {allowedChildTypesForSelected.map((t: string) => {
                        const checked = overrideChildTypes.includes(t);
                        return (
                          <label key={t} className="inline-flex items-center gap-2 rounded-lg border border-border-soft px-3 py-1.5 text-sm dark:border-white/10">
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={(e) => {
                                if (e.target.checked) setOverrideChildTypes((s) => Array.from(new Set([...s, t])));
                                else setOverrideChildTypes((s) => s.filter((x) => x !== t));
                              }}
                              className="rounded border-border-soft text-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10"
                            />
                            {t}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {incompatibleChildren.length > 0 && (
                <div className="rounded-lg border border-danger/20 bg-danger-soft px-4 py-3 text-sm text-danger dark:border-danger/30 dark:bg-danger/10">
                  <strong>Warnung:</strong> Dieser Typwechsel würde inkompatible Kinder erzeugen:
                  <ul className="ml-6 list-disc">
                    {incompatibleChildren.map((c) => (
                      <li key={c.id}>{`${(c as any).name ?? c.id} — ${c.type}`}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Widgets */}
          {activeTab === 'widgets' && (
            <div className="space-y-4">
              <div className="flex flex-col gap-2 sm:flex-row">
                {renderInput('Suche', widgetSearch, setWidgetSearch, false, 'Widgets durchsuchen…')}
                {renderSelect('Filter', widgetFilter, [
                  { value: 'all', label: 'Alle' },
                  { value: 'active', label: 'Aktiv' },
                  { value: 'available', label: 'Verfügbar' },
                  { value: 'disabled', label: 'Deaktiviert' },
                ], (v) => setWidgetFilter(v as any))}
              </div>

              {widgetStatusMsg && <div className="text-sm text-danger">{widgetStatusMsg}</div>}

              <div className="overflow-x-auto rounded-lg border border-border-soft dark:border-white/10">
                <table className="w-full text-sm">
                  <thead className="bg-surface-muted dark:bg-slate-800/50">
                    <tr>
                      <th className="p-3 text-left">Name</th>
                      <th className="p-3">Kategorie</th>
                      <th className="p-3">Herkunft</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(registryWidgets ?? [])
                      .filter((r: any) => {
                        const name = String(r.name ?? r.id ?? '');
                        if (widgetSearch && !name.toLowerCase().includes(widgetSearch.toLowerCase())) return false;
                        return true;
                      })
                      .map((r: any) => {
                        const name = String(r.name ?? r.id ?? '');
                        const eff = (effectiveWidgets ?? []).find((e: any) => String(e.id) === name || String(e.name) === name);
                        const status = eff ? 'Aktiv' : 'Verfügbar';
                        if (widgetFilter === 'active' && !eff) return null;
                        if (widgetFilter === 'available' && eff) return null;
                        if (widgetFilter === 'disabled' && !(eff && eff.enabled === false)) return null;
                        const category = (r.metadata && (r.metadata.category as string)) ?? r.type ?? '';
                        return (
                          <tr key={name} className="border-t border-border-soft dark:border-white/10">
                            <td className="p-3">{r.label ?? name}</td>
                            <td className="p-3 text-center">{category}</td>
                            <td className="p-3 text-center">{eff ? 'Geerbt/zugewiesen' : 'Registry'}</td>
                            <td className="p-3 text-center">{status}</td>
                            <td className="p-3">
                              <div className="flex flex-wrap gap-1.5">
                                {!eff && (
                                  <button
                                    className="inline-flex items-center gap-1 rounded-lg bg-success px-2.5 py-1 text-xs font-medium text-white transition hover:bg-success-hover"
                                    onClick={async () => {
                                      try {
                                        const existing = (node as any).widget_assignments ?? [];
                                        const key = name;
                                        const next = Array.isArray(existing) ? [...existing] : [];
                                        const filtered = next.filter((a: any) => String(a.id ?? a.widget_id ?? a.name) !== key);
                                        filtered.push({ name: key, enabled: true, inherit: false, position: 1000, configuration: {} });
                                        await fetchWidgetsClient.setNodeAssignments(node.id, { assignments: filtered });
                                        const eff2 = await widgetsApi.loadEffectiveWidgets(node.id);
                                        setEffectiveWidgets(eff2);
                                        setWidgetStatusMsg('Widget aktiviert');
                                        setTimeout(() => setWidgetStatusMsg(null), 2500);
                                      } catch (e) {
                                        setWidgetStatusMsg('Fehler beim Aktivieren');
                                      }
                                    }}
                                  >
                                    <Plus size={12} /> Aktivieren
                                  </button>
                                )}
                                {eff && (
                                  <button
                                    className="inline-flex items-center gap-1 rounded-lg bg-danger px-2.5 py-1 text-xs font-medium text-white transition hover:bg-danger-hover"
                                    onClick={async () => {
                                      try {
                                        const existing = (node as any).widget_assignments ?? [];
                                        const key = name;
                                        const next = Array.isArray(existing) ? [...existing] : [];
                                        const hasRel = next.some((a: any) => String(a.id ?? a.widget_id ?? a.name) === key);
                                        let filtered: any[] = [];
                                        if (hasRel) {
                                          filtered = next.filter((a: any) => String(a.id ?? a.widget_id ?? a.name) !== key);
                                        } else {
                                          filtered = [...next, { name: key, enabled: false, inherit: false }];
                                        }
                                        await fetchWidgetsClient.setNodeAssignments(node.id, { assignments: filtered });
                                        const eff2 = await widgetsApi.loadEffectiveWidgets(node.id);
                                        setEffectiveWidgets(eff2);
                                        setWidgetStatusMsg('Widget deaktiviert');
                                        setTimeout(() => setWidgetStatusMsg(null), 2500);
                                      } catch (e) {
                                        setWidgetStatusMsg('Fehler beim Deaktivieren');
                                      }
                                    }}
                                  >
                                    <Minus size={12} /> Deaktivieren
                                  </button>
                                )}
                                <button
                                  className="inline-flex items-center gap-1 rounded-lg border border-border-soft px-2.5 py-1 text-xs font-medium transition hover:bg-surface-hover dark:border-white/10"
                                  onClick={async () => {
                                    try {
                                      const nodeResp = await fetchToolsClient.getNode(node.id);
                                      const existingMeta = (nodeResp?.metadata ?? {}) as any;
                                      const widgetsMeta = existingMeta.widgets ?? {};
                                      const key = name;
                                      const initial = widgetsMeta[key] ? JSON.stringify(widgetsMeta[key], null, 2) : '{}';
                                      setConfigEditorKind('widget');
                                      setConfigEditorKey(key);
                                      setConfigEditorValue(initial);
                                      setConfigEditorError(null);
                                    } catch (e) {
                                      setWidgetStatusMsg('Fehler beim Laden der Konfiguration');
                                    }
                                  }}
                                >
                                  <Settings size={12} /> Konfigurieren
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Tools */}
          {activeTab === 'tools' && (
            <div className="space-y-4">
              <div className="flex flex-col gap-2 sm:flex-row">
                {renderInput('Suche', toolSearch, setToolSearch, false, 'Werkzeuge durchsuchen…')}
                {renderSelect('Filter', toolFilter, [
                  { value: 'all', label: 'Alle' },
                  { value: 'active', label: 'Aktiv' },
                  { value: 'inherited', label: 'Geerbt' },
                  { value: 'available', label: 'Verfügbar' },
                  { value: 'disabled', label: 'Deaktiviert' },
                ], (v) => setToolFilter(v as any))}
              </div>

              {toolStatusMsg && <div className="text-sm text-danger">{toolStatusMsg}</div>}

              <div className="overflow-x-auto rounded-lg border border-border-soft dark:border-white/10">
                <table className="w-full text-sm">
                  <thead className="bg-surface-muted dark:bg-slate-800/50">
                    <tr>
                      <th className="p-3 text-left">Name</th>
                      <th className="p-3">Kategorie</th>
                      <th className="p-3">Herkunft</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(toolsRegistry ?? [])
                      .filter((t: any) => {
                        const name = String(t.name ?? t.id ?? '');
                        if (toolSearch && !name.toLowerCase().includes(toolSearch.toLowerCase())) return false;
                        return true;
                      })
                      .map((t: any) => {
                        const name = String(t.name ?? t.id ?? '');
                        const category = t.category ?? (t.metadata && t.metadata.category) ?? '';
                        const policy = nodeToolPolicy ?? ((node as any).tool_policy ?? {});
                        const explicit = Object.prototype.hasOwnProperty.call(policy, name);
                        const isActive = explicit ? Boolean(policy[name]) : (effectiveToolIds?.includes(name) ?? false);
                        const isInherited = !explicit && (effectiveToolIds?.includes(name) ?? false);
                        const status = isActive ? 'Aktiv' : isInherited ? 'Geerbt' : 'Verfügbar';
                        if (toolFilter === 'active' && !isActive) return null;
                        if (toolFilter === 'available' && isActive) return null;
                        if (toolFilter === 'disabled' && t.enabled !== true) return null;

                        return (
                          <tr key={name} className="border-t border-border-soft dark:border-white/10">
                            <td className="p-3">{t.display_name ?? name}</td>
                            <td className="p-3 text-center">{category}</td>
                            <td className="p-3 text-center">{isInherited ? 'Geerbt' : 'Registry'}</td>
                            <td className="p-3 text-center">{status}</td>
                            <td className="p-3">
                              <div className="flex flex-wrap gap-1.5">
                                {!isActive && (
                                  <button
                                    className="inline-flex items-center gap-1 rounded-lg bg-success px-2.5 py-1 text-xs font-medium text-white transition hover:bg-success-hover"
                                    onClick={async () => {
                                      try {
                                        const existing = nodeToolPolicy ?? ((node as any).tool_policy ?? {});
                                        const next = { ...(existing || {}) };
                                        next[name] = true;
                                        await putNodeToolPolicy(node.id, { tool_policy: next });
                                        const nodeResp2 = await fetchToolsClient.getNode(node.id);
                                        const eff2 = await fetchToolsClient.getNodeEffectiveTools(node.id).catch(() => null);
                                        setNodeToolPolicy((nodeResp2 as any)?.tool_policy ?? {});
                                        setEffectiveToolIds(Array.isArray(eff2) ? eff2 : (eff2?.effective_tool_ids ?? null));
                                        setToolStatusMsg('Werkzeug aktiviert');
                                        setTimeout(() => setToolStatusMsg(null), 2500);
                                      } catch (e) {
                                        if (e instanceof ApiError) {
                                          switch (e.code) {
                                            case 'TOOL_NOT_REGISTERED': setToolStatusMsg('Werkzeug nicht registriert'); break;
                                            case 'TOOL_NOT_ENABLED': setToolStatusMsg('Werkzeug ist deaktiviert'); break;
                                            case 'TOOL_NOT_AUTHORIZED': setToolStatusMsg('Keine Berechtigung'); break;
                                            case 'TOOL_CONFIGURATION_INVALID': setToolStatusMsg('Konfiguration ungültig'); break;
                                            default: setToolStatusMsg('Fehler beim Aktivieren');
                                          }
                                        } else {
                                          setToolStatusMsg('Fehler beim Aktivieren');
                                        }
                                      }
                                    }}
                                  >
                                    <Plus size={12} /> Aktivieren
                                  </button>
                                )}
                                {isActive && (
                                  <button
                                    className="inline-flex items-center gap-1 rounded-lg bg-danger px-2.5 py-1 text-xs font-medium text-white transition hover:bg-danger-hover"
                                    onClick={async () => {
                                      try {
                                        const existing = nodeToolPolicy ?? ((node as any).tool_policy ?? {});
                                        const next = { ...(existing || {}) };
                                        next[name] = false;
                                        await putNodeToolPolicy(node.id, { tool_policy: next });
                                        const nodeResp2 = await fetchToolsClient.getNode(node.id);
                                        const eff2 = await fetchToolsClient.getNodeEffectiveTools(node.id).catch(() => null);
                                        setNodeToolPolicy((nodeResp2 as any)?.tool_policy ?? {});
                                        setEffectiveToolIds(Array.isArray(eff2) ? eff2 : (eff2?.effective_tool_ids ?? null));
                                        setToolStatusMsg('Werkzeug deaktiviert');
                                        setTimeout(() => setToolStatusMsg(null), 2500);
                                      } catch (e) {
                                        setToolStatusMsg('Fehler beim Deaktivieren');
                                      }
                                    }}
                                  >
                                    <Minus size={12} /> Deaktivieren
                                  </button>
                                )}
                                <button
                                  className="inline-flex items-center gap-1 rounded-lg border border-border-soft px-2.5 py-1 text-xs font-medium transition hover:bg-surface-hover dark:border-white/10"
                                  onClick={async () => {
                                    try {
                                      const nodeResp = await fetchToolsClient.getNode(node.id);
                                      const existingPolicy = (nodeResp?.tool_policy ?? {}) as any;
                                      const configs = existingPolicy.configurations ?? {};
                                      const legacyTools = (nodeResp?.metadata ?? {}).tools ?? {};
                                      const initialObj = configs[name] ?? legacyTools[name] ?? {};
                                      const initial = Object.keys(initialObj).length ? JSON.stringify(initialObj, null, 2) : '{}';
                                      setConfigEditorKind('tool');
                                      setConfigEditorKey(name);
                                      setConfigEditorValue(initial);
                                      setConfigEditorError(null);
                                    } catch (e) {
                                      setToolStatusMsg('Fehler beim Laden der Konfiguration');
                                    }
                                  }}
                                >
                                  <Settings size={12} /> Konfigurieren
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Prompts */}
          {activeTab === 'prompts' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Lokaler Prompt</h3>
                <textarea
                  className="mt-1 w-full rounded-lg border border-border-soft bg-white px-3 py-2 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:focus:ring-primary/20"
                  rows={6}
                  value={promptsLocal ?? ''}
                  onChange={(e) => setPromptsLocal(e.target.value)}
                />
                <div className="mt-2 flex justify-end gap-2">
                  <button
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border-soft px-3 py-1.5 text-sm font-medium transition hover:bg-surface-hover dark:border-white/10"
                    onClick={() => setPromptsLocal((node as any).system_prompt ?? '')}
                    disabled={promptSaving}
                  >
                    <RefreshCw size={14} /> Zurücksetzen
                  </button>
                  <button
                    className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow disabled:opacity-50"
                    onClick={async () => {
                      setPromptSaving(true);
                      setPromptError(null);
                      try {
                        const client = await import('../../api/fetchPromptClient');
                        await client.saveLocalPrompt(node.id, promptsLocal ?? null);
                        const ctx = await client.loadPromptContext(node.id);
                        setPromptsLocal(ctx.local_prompt ?? null);
                        setPromptsChain(ctx.sources ?? []);
                        setResolvedPrompt({ system_prompt: ctx.effective_prompt ?? '' });
                        setPromptError(null);
                      } catch (e) {
                        setPromptError('Fehler beim Speichern des Prompts.');
                      } finally {
                        setPromptSaving(false);
                      }
                    }}
                    disabled={promptSaving || (promptsLocal === ((node as any).system_prompt ?? null))}
                  >
                    <Save size={14} /> {promptSaving ? 'Speichern…' : 'Prompt speichern'}
                  </button>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Geerbte Prompt-Quellen</h3>
                <div className="mt-2 space-y-1">
                  {(promptsChain ?? []).map((c: any) => (
                    <div key={c.id} className="rounded-lg border border-border-soft p-3 dark:border-white/10">
                      <div className="flex justify-between text-sm">
                        <div>
                          <strong className="text-text dark:text-white">{c.name ?? c.id}</strong>
                          <span className="ml-2 text-text-muted">{c.type}</span>
                        </div>
                        <div className="text-xs text-text-muted">{c.system_prompt ? `${String(c.system_prompt).length} Zeichen` : '0 Zeichen'}</div>
                      </div>
                      {c.system_prompt && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-xs text-primary hover:underline">Prompt anzeigen</summary>
                          <pre className="mt-1 whitespace-pre-wrap rounded bg-surface-muted p-2 text-sm dark:bg-slate-800/50">{c.system_prompt}</pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-text-soft dark:text-gray-300">Effektiver Prompt</h3>
                <div className="mt-2">
                  <textarea
                    readOnly
                    className="w-full rounded-lg border border-border-soft bg-surface-muted px-3 py-2 text-sm text-text dark:border-white/10 dark:bg-slate-800/50 dark:text-white"
                    rows={8}
                    value={resolvedPrompt?.system_prompt ?? ''}
                  />
                  <div className="mt-1 flex flex-wrap items-center justify-between gap-2 text-xs text-text-muted">
                    <span>Effektive Länge: {String((resolvedPrompt?.system_prompt ?? '').length)}</span>
                    <div className="flex gap-2">
                      <button
                        className="inline-flex items-center gap-1 rounded-lg border border-border-soft px-2.5 py-1 text-xs transition hover:bg-surface-hover dark:border-white/10"
                        onClick={async () => {
                          try {
                            const client = await import('../../api/fetchPromptClient');
                            const ctx = await client.loadPromptContext(node.id);
                            setPromptsLocal(ctx.local_prompt ?? null);
                            setPromptsChain(ctx.sources ?? []);
                            setResolvedPrompt({ system_prompt: ctx.effective_prompt ?? '' });
                            setPromptError(null);
                          } catch (e) {
                            setPromptError('Der effektive Prompt konnte nicht aufgelöst werden.');
                          }
                        }}
                      >
                        <RefreshCw size={12} /> Neu auflösen
                      </button>
                      {import.meta.env.DEV && (
                        <button
                          className="inline-flex items-center gap-1 rounded-lg border border-border-soft px-2.5 py-1 text-xs transition hover:bg-surface-hover dark:border-white/10"
                          onClick={() => console.info('prompt-debug', { nodeId: node.id, resolved: resolvedPrompt })}
                        >
                          Debug
                        </button>
                      )}
                    </div>
                  </div>
                  {promptError && <div className="mt-2 text-sm text-danger">{promptError}</div>}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="sticky bottom-0 flex items-center justify-end gap-3 border-t border-border-soft bg-white/95 px-6 py-4 backdrop-blur-sm dark:border-white/10 dark:bg-slate-900/95">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border-soft px-4 py-2 text-sm font-medium transition hover:bg-surface-hover dark:border-white/10 dark:hover:bg-slate-800"
            onClick={handleClose}
            disabled={isSaving}
          >
            Abbrechen
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow disabled:opacity-50"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'Speichern…' : 'Speichern'}
          </button>
        </footer>
      </div>

      {/* Config Editor Modal */}
      {configEditorKind && configEditorKey && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
          <div className="max-w-3xl w-full rounded-2xl border border-border-soft bg-white shadow-2xl dark:border-white/10 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-border-soft px-6 py-4 dark:border-white/10">
              <h3 className="text-lg font-semibold text-text dark:text-white">
                Konfiguration: {configEditorKey}
              </h3>
              <button
                type="button"
                className="rounded-lg p-1.5 text-text-muted transition hover:bg-surface-hover hover:text-text dark:text-gray-400 dark:hover:bg-slate-800 dark:hover:text-white"
                onClick={() => { setConfigEditorKind(null); setConfigEditorKey(null); }}
              >
                <IconBadge icon={<X />} size="sm" variant="default" />
              </button>
            </div>
            <div className="p-6">
              <SettingsJsonEditor
                value={configEditorValue}
                error={configEditorError}
                disabled={false}
                isDirty={true}
                copied={configEditorCopied}
                onChange={(v) => setConfigEditorValue(v)}
                onApply={async () => {
                  try {
                    const parsed = JSON.parse(configEditorValue);
                    if (configEditorKind === 'tool') {
                      const nodeResp = await fetchToolsClient.getNode(node.id);
                      const existingPolicy = (nodeResp?.tool_policy ?? {}) as any;
                      const nextPolicy = { ...(existingPolicy || {}) } as any;
                      nextPolicy.configurations = { ...(nextPolicy.configurations ?? {}) };
                      nextPolicy.configurations[configEditorKey] = parsed;

                      try {
                        await putNodeToolPolicy(node.id, { tool_policy: nextPolicy });
                      } catch (e: any) {
                        if (e instanceof ApiError) {
                          switch (e.code) {
                            case 'TOOL_CONFIGURATION_INVALID': setConfigEditorError('Die Werkzeugkonfiguration ist ungültig.'); return;
                            case 'TOOL_NOT_AUTHORIZED': setConfigEditorError('Sie dürfen dieses Werkzeug nicht konfigurieren.'); return;
                            case 'TOOL_NOT_REGISTERED': setConfigEditorError('Das Werkzeug ist nicht mehr registriert.'); return;
                            default: setConfigEditorError(String(e.message ?? 'Fehler beim Speichern')); return;
                          }
                        }
                        setConfigEditorError(String(e?.message ?? 'Fehler beim Speichern'));
                        return;
                      }

                      const nodeResp2 = await fetchToolsClient.getNode(node.id);
                      const eff2 = await fetchToolsClient.getNodeEffectiveTools(node.id).catch(() => null);
                      const nr: any = nodeResp2 as any;
                      setNodeToolPolicy(nr?.tool_policy ?? {});
                      const metaTools2 = (nr?.metadata ?? {}).tools ?? {};
                      const policyConfigs2 = (nr?.tool_policy ?? {}).configurations ?? {};
                      setNodeToolConfigs({ ...(metaTools2 ?? {}), ...(policyConfigs2 ?? {}) });
                      setEffectiveToolIds(Array.isArray(eff2) ? eff2 : (eff2?.effective_tool_ids ?? null));
                      setToolStatusMsg('Konfiguration gespeichert');
                      setTimeout(() => setToolStatusMsg(null), 2500);
                      setConfigEditorKind(null);
                      setConfigEditorKey(null);
                    } else if (configEditorKind === 'widget') {
                      const nodeResp = await fetchToolsClient.getNode(node.id);
                      const existingMeta = (nodeResp?.metadata ?? {}) as any;
                      const widgetsMeta = existingMeta.widgets ?? {};
                      widgetsMeta[configEditorKey] = parsed;
                      existingMeta.widgets = widgetsMeta;
                      await fetchToolsClient.updateNode(node.id, { metadata: existingMeta });
                      setToolStatusMsg('Konfiguration gespeichert');
                      setTimeout(() => setToolStatusMsg(null), 2500);
                      setConfigEditorKind(null);
                      setConfigEditorKey(null);
                    }
                  } catch (err: any) {
                    setConfigEditorError(String(err?.message ?? err ?? 'Ungültiges JSON'));
                  }
                }}
                onFormat={() => {
                  try {
                    const parsed = JSON.parse(configEditorValue);
                    setConfigEditorValue(JSON.stringify(parsed, null, 2));
                    setConfigEditorError(null);
                  } catch (e) {
                    setConfigEditorError('Ungültiges JSON');
                  }
                }}
                onReset={() => {
                  setConfigEditorValue('{}');
                  setConfigEditorError(null);
                }}
                onCopy={async () => {
                  try {
                    await navigator.clipboard.writeText(configEditorValue);
                    setConfigEditorCopied(true);
                    setTimeout(() => setConfigEditorCopied(false), 2000);
                  } catch (_) {}
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}