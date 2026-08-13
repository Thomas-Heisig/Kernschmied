import React, { useMemo, useState, useEffect } from 'react';
import { updateHierarchyNode } from '../../api/hierarchy';
import type { HierarchyNode } from '../../contracts/hierarchy';
import { ApiError } from '../../api/client';
import widgetsApi from '../../api/widgets';
import fetchWidgetsClient from '../../api/fetchWidgetsClient';
import fetchToolsClient, { putNodeToolPolicy } from '../../api/fetchToolsClient';
import SettingsJsonEditor from '../settings/SettingsJsonEditor';

export default function NodeEditorDialog({
  isOpen,
  node,
  nodeTypes,
  onClose,
  onSaved,
}: {
  isOpen: boolean;
  node: HierarchyNode | null;
  nodeTypes: Record<string, any>;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(node?.name ?? '');
  const [type, setType] = useState(node?.type ?? '');
  const [activeTab, setActiveTab] = useState<'general' | 'structure' | 'widgets' | 'prompts' | 'tools'>('general');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  

  // keep initial values in sync when node changes
  // Structure tab: override state
  const [useOverride, setUseOverride] = useState<boolean>(false);
  const [overrideChildTypes, setOverrideChildTypes] = useState<string[]>([]);

  React.useEffect(() => {
    setName(node?.name ?? '');
    setType(node?.type ?? '');
    setError(null);
    const metaHierarchy = (node as any)?.metadata?.hierarchy;
    setUseOverride(Boolean(metaHierarchy?.allowed_child_types));
    setOverrideChildTypes(metaHierarchy?.allowed_child_types?.map((s: string) => String(s)) ?? []);
  }, [node]);

  // Widgets tab state
  const [registryWidgets, setRegistryWidgets] = useState<any[] | null>(null);
  const [effectiveWidgets, setEffectiveWidgets] = useState<any[] | null>(null);
  const [widgetSearch, setWidgetSearch] = useState('');
  const [widgetFilter, setWidgetFilter] = useState<'all' | 'active' | 'available' | 'disabled'>('all');
  const [widgetStatusMsg, setWidgetStatusMsg] = useState<string | null>(null);
  // Prompts tab state
  const [promptsLocal, setPromptsLocal] = useState<string | null>(null);
  const [promptsChain, setPromptsChain] = useState<any[] | null>(null);
  const [resolvedPrompt, setResolvedPrompt] = useState<any | null>(null);
  const [promptSaving, setPromptSaving] = useState(false);
  const [promptError, setPromptError] = useState<string | null>(null);
  // Tools tab state
  const [toolsRegistry, setToolsRegistry] = useState<any[] | null>(null);
  const [nodeToolPolicy, setNodeToolPolicy] = useState<Record<string, boolean> | null>(null);
  const [nodeToolConfigs, setNodeToolConfigs] = useState<Record<string, any> | null>(null);
  const [effectiveToolIds, setEffectiveToolIds] = useState<string[] | null>(null);
  const [toolSearch, setToolSearch] = useState('');
  const [toolFilter, setToolFilter] = useState<'all' | 'active' | 'inherited' | 'available' | 'disabled'>('all');
  const [toolStatusMsg, setToolStatusMsg] = useState<string | null>(null);
  const [configEditorKind, setConfigEditorKind] = useState<'tool' | 'widget' | null>(null);
  const [configEditorKey, setConfigEditorKey] = useState<string | null>(null);
  const [configEditorValue, setConfigEditorValue] = useState('');
  const [configEditorError, setConfigEditorError] = useState<string | null>(null);
  const [configEditorCopied, setConfigEditorCopied] = useState(false);

  useEffect(() => {
    if (!isOpen || !node) return;
    if (activeTab !== 'widgets') return;
    let mounted = true;
    (async () => {
      try {
        const [regResp, eff] = await Promise.all([fetchWidgetsClient.listRegistry(), widgetsApi.loadEffectiveWidgets(node.id)]);
        if (!mounted) return;
        const rr: any = regResp as any;
        setRegistryWidgets(Array.isArray(rr) ? rr : (rr.items ?? rr));
        setEffectiveWidgets(Array.isArray(eff) ? eff : (eff as any));
      } catch (e) {
        console.error('Failed loading widgets', e);
        if (mounted) setWidgetStatusMsg('Fehler beim Laden der Widgets');
      }
    })();
    return () => {
      mounted = false;
    };
  }, [isOpen, node, activeTab]);

  useEffect(() => {
    if (!isOpen || !node) return;
    if (activeTab !== 'tools') return;

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
        console.error('Failed loading tools', e);
        if (mounted) setToolStatusMsg('Fehler beim Laden der Werkzeuge');
      }
    })();

    return () => { mounted = false; };
  }, [isOpen, node, activeTab]);

  useEffect(() => {
    if (!isOpen || !node) return;
    if (activeTab !== 'prompts') return;

    let mounted = true;
    (async () => {
      try {
        const client = await import('../../api/fetchPromptClient');
        const ctx = await client.loadPromptContext(node.id);
        if (!mounted) return;
        setPromptsLocal(ctx.local_prompt ?? null);
        setPromptsChain(ctx.sources ?? []);
        setResolvedPrompt({ system_prompt: ctx.effective_prompt ?? '' , fragments: [] });
      } catch (e) {
        console.error('Failed loading prompts', e);
        if (mounted) setPromptError('Der effektive Prompt konnte nicht aufgelöst werden.');
      }
    })();

    return () => {
      mounted = false;
    };
  }, [isOpen, node, activeTab]);

  const typeOptions = useMemo(() => {
    return Object.keys(nodeTypes ?? {}).map((k) => ({ id: k, def: nodeTypes[k] }));
  }, [nodeTypes]);

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

  if (!isOpen || !node) return null;

  async function handleSave() {
    setIsSaving(true);
    setError(null);
    try {
      const payload: any = { name, type };
      if (useOverride) {
        payload.metadata = { ...(node as any).metadata, hierarchy: { allowed_child_types: overrideChildTypes } };
      }
      await updateHierarchyNode(node!.id, payload);
      await onSaved();
    } catch (err: unknown) {
      const maybe = err as any;
      const code = maybe?.code;
      if ((err instanceof ApiError) || code === 'HIERARCHY_NODE_TYPE_CHANGE_INVALID') {
        const details = (err instanceof ApiError) ? (err as any).details : maybe.details;
        const invalid = details?.invalid_children as Array<any> | undefined;
        if (invalid && invalid.length > 0) {
          const list = invalid.map((c) => `${c.id} (${c.type})`).join(', ');
          setError(`Typwechsel nicht möglich: inkompatible Kinder: ${list}`);
        } else {
          setError((err instanceof Error ? (err as Error).message : null) ?? 'Typwechsel nicht möglich');
        }
      } else {
        const msg = err instanceof Error ? err.message : 'Fehler beim Speichern';
        setError(msg);
      }
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative z-50 w-[90%] max-w-2xl rounded bg-white p-4 dark:bg-slate-900">
        <h2 className="text-lg font-semibold mb-2">Knoten bearbeiten</h2>

        <div className="mb-3">
          <nav className="flex gap-2">
            <button
              className={`px-3 py-1 rounded ${activeTab === 'general' ? 'bg-slate-200' : ''}`}
              onClick={() => setActiveTab('general')}
            >
              Allgemein
            </button>
            <button
              className={`px-3 py-1 rounded ${activeTab === 'structure' ? 'bg-slate-200' : ''}`}
              onClick={() => setActiveTab('structure')}
            >
              Struktur
            </button>
            <button
              className={`px-3 py-1 rounded ${activeTab === 'widgets' ? 'bg-slate-200' : ''}`}
              onClick={() => setActiveTab('widgets')}
            >
              Widgets
            </button>
            <button
              className={`px-3 py-1 rounded ${activeTab === 'tools' ? 'bg-slate-200' : ''}`}
              onClick={() => setActiveTab('tools')}
            >
              Werkzeuge
            </button>
          </nav>
        </div>

        {activeTab === 'general' && (
          <div className="space-y-3">
            <div>
              <label className="block mb-1">Name</label>
              <input className="w-full border px-2 py-1" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="block mb-1">Typ</label>
              <select className="w-full border px-2 py-1" value={type} onChange={(e) => setType(e.target.value)}>
                {typeOptions.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.def?.label ?? t.id}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {configEditorKind && configEditorKey && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="max-w-3xl w-full">
              <div className="rounded-xl bg-white p-4 dark:bg-slate-900">
                <div className="flex items-start justify-between">
                  <h3 className="text-lg font-medium">Konfiguration: {configEditorKey}</h3>
                  <div className="flex gap-2">
                    <button onClick={() => { setConfigEditorKind(null); setConfigEditorKey(null); }} className="px-3 py-1 border rounded">Schließen</button>
                  </div>
                </div>

                <div className="mt-4">
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
                          // Load current node state and prepare payload that preserves
                          // existing enabled/disabled lists and writes configurations
                          // into the canonical tool_policy.configurations property.
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
                                case 'TOOL_CONFIGURATION_INVALID':
                                  setConfigEditorError('Die Werkzeugkonfiguration ist ungültig.');
                                  return;
                                case 'TOOL_NOT_AUTHORIZED':
                                  setConfigEditorError('Sie dürfen dieses Werkzeug nicht konfigurieren.');
                                  return;
                                case 'TOOL_NOT_REGISTERED':
                                  setConfigEditorError('Das Werkzeug ist nicht mehr registriert.');
                                  return;
                                default:
                                  setConfigEditorError(String(e.message ?? 'Fehler beim Speichern'));
                                  return;
                              }
                            }
                            setConfigEditorError(String(e?.message ?? 'Fehler beim Speichern'));
                            return;
                          }

                          // refresh local state
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
                          // legacy widget metadata editing remains unchanged
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
          </div>
        )}

        {activeTab === 'structure' && (
          <div className="space-y-3">
            <div>
              <label className="block mb-1 font-medium">Parent</label>
              {node.parent_id ? (
                <div className="text-sm">
                  <div>ID: {node.parent_id}</div>
                  <div>Name: {(node as any).parent_name ?? '—'}</div>
                  <div>Typ: {(node as any).parent_type ?? '—'}</div>
                </div>
              ) : (
                <div className="text-sm">Kein übergeordneter Knoten</div>
              )}
            </div>

            <div>
              <label className="block mb-1 font-medium">Aktueller Knotentyp</label>
              <div className="text-sm">{type}</div>
            </div>

            <div>
              <label className="block mb-1 font-medium">Erlaubte Kindtypen</label>
              <div className="flex gap-2 flex-wrap">
                {(allowedChildTypesForSelected ?? []).map((t: string) => (
                  <span key={t} className="px-2 py-0.5 bg-slate-100 rounded text-sm">
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label className="block mb-1 font-medium">Erlaubte Aktionen</label>
              <div className="flex gap-2 flex-wrap">
                {(currentTypeDef?.allowed_actions ?? []).map((a: string) => (
                  <span key={a} className="px-2 py-0.5 bg-slate-100 rounded text-sm">
                    {a}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <label className="block mb-1 font-medium">Flags (read-only)</label>
              <div className="text-sm space-y-1">
                <div>selectable: {String(Boolean(currentTypeDef?.selectable))}</div>
                <div>draggable: {String(Boolean(currentTypeDef?.draggable))}</div>
                <div>droppable: {String(Boolean(currentTypeDef?.droppable))}</div>
                <div>expandable: {String(Boolean(currentTypeDef?.expandable))}</div>
              </div>
            </div>

            <div className="pt-2">
              <label className="block font-medium mb-1">Kindtypen für diesen Knoten einschränken</label>
              <div className="flex items-center gap-2">
                <input id="useOverride" type="checkbox" checked={useOverride} onChange={(e) => setUseOverride(e.target.checked)} />
                <label htmlFor="useOverride">Eigene Einschränkung verwenden</label>
              </div>

              {useOverride && (
                <div className="mt-2">
                  <div className="text-sm mb-1">Wähle erlaubte Kindtypen (nur Einschränken):</div>
                  <div className="flex gap-2 flex-wrap">
                    {(allowedChildTypesForSelected ?? []).map((t: string) => {
                      const checked = overrideChildTypes.includes(t);
                      return (
                        <label key={t} className="inline-flex items-center gap-2 px-2 py-1 border rounded">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) setOverrideChildTypes((s) => Array.from(new Set([...s, t])));
                              else setOverrideChildTypes((s) => s.filter((x) => x !== t));
                            }}
                          />
                          <span className="text-sm">{t}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {incompatibleChildren.length > 0 && (
              <div className="mt-2 text-red-700">
                <strong>Warnung:</strong> Dieser Typwechsel würde inkompatible Kinder erzeugen:
                <ul className="list-disc pl-6">
                  {incompatibleChildren.map((c) => (
                    <li key={c.id}>{`${(c as any).name ?? c.id} — ${c.type}`}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'widgets' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input className="border px-2 py-1 flex-1" placeholder="Search widgets..." value={widgetSearch} onChange={(e) => setWidgetSearch(e.target.value)} />
              <select value={widgetFilter} onChange={(e) => setWidgetFilter(e.target.value as any)} className="border px-2 py-1">
                <option value="all">Alle</option>
                <option value="active">Aktiv</option>
                <option value="available">Verfügbar</option>
                <option value="disabled">Deaktiviert</option>
              </select>
            </div>

            <div>
              {widgetStatusMsg ? <div className="text-sm text-red-600">{widgetStatusMsg}</div> : null}
              <div className="max-h-64 overflow-auto border rounded">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="p-2 text-left">Name</th>
                      <th className="p-2">Kategorie</th>
                      <th className="p-2">Herkunft</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(registryWidgets ?? []).filter((r: any) => {
                      const name = String(r.name ?? r.id ?? '');
                      if (widgetSearch && !name.toLowerCase().includes(widgetSearch.toLowerCase())) return false;
                      return true;
                    }).map((r: any) => {
                      const name = String(r.name ?? r.id ?? '');
                      const eff = (effectiveWidgets ?? []).find((e: any) => String(e.id) === name || String(e.name) === name);
                      const status = eff ? 'Aktiv' : 'Verfügbar';
                      if (widgetFilter === 'active' && !eff) return null;
                      if (widgetFilter === 'available' && eff) return null;
                      if (widgetFilter === 'disabled' && !(eff && eff.enabled === false)) return null;
                      const category = (r.metadata && (r.metadata.category as string)) ?? r.type ?? '';
                      return (
                        <tr key={name} className="border-t">
                          <td className="p-2">{r.label ?? name}</td>
                          <td className="p-2">{category}</td>
                          <td className="p-2">{eff ? 'Geerbt/zugewiesen' : 'Registry'}</td>
                          <td className="p-2">{status}</td>
                          <td className="p-2">
                            <div className="flex gap-2">
                              {!eff && (
                                <button className="px-2 py-1 bg-green-600 text-white rounded" onClick={async () => {
                                  // activate
                                  try {
                                    const existing = (node as any).widget_assignments ?? [];
                                    const key = name;
                                    const next = Array.isArray(existing) ? [...existing] : [];
                                    // remove any existing with same key
                                    const filtered = next.filter((a: any) => String(a.id ?? a.widget_id ?? a.name) !== key);
                                    filtered.push({ name: key, enabled: true, inherit: false, position: 1000, configuration: {} });
                                    await fetchWidgetsClient.setNodeAssignments(node.id, { assignments: filtered });
                                    // reload effective
                                    const eff2 = await widgetsApi.loadEffectiveWidgets(node.id);
                                    setEffectiveWidgets(eff2);
                                    setWidgetStatusMsg('Widget aktiviert');
                                    setTimeout(() => setWidgetStatusMsg(null), 2500);
                                  } catch (e) {
                                    setWidgetStatusMsg('Fehler beim Aktivieren');
                                  }
                                }}>Aktivieren</button>
                              )}
                              {eff && (
                                <button className="px-2 py-1 bg-red-600 text-white rounded" onClick={async () => {
                                  try {
                                    const existing = (node as any).widget_assignments ?? [];
                                    const key = String(r.name ?? r.id ?? '');
                                    const next = Array.isArray(existing) ? [...existing] : [];
                                    // if relational assignment exists, remove it; else create disabled override
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
                                }}>Deaktivieren</button>
                              )}
                              <button className="px-2 py-1 border rounded" onClick={async () => {
                                try {
                                  const nodeResp = await fetchToolsClient.getNode(node.id);
                                  const existingMeta = (nodeResp?.metadata ?? {}) as any;
                                  const widgetsMeta = existingMeta.widgets ?? {};
                                  const key = String(r.name ?? r.id ?? '');
                                  const initial = widgetsMeta[key] ? JSON.stringify(widgetsMeta[key], null, 2) : '{}';
                                  setConfigEditorKind('widget');
                                  setConfigEditorKey(key);
                                  setConfigEditorValue(initial);
                                  setConfigEditorError(null);
                                } catch (e) {
                                  setWidgetStatusMsg('Fehler beim Laden der Konfiguration');
                                  setTimeout(() => setWidgetStatusMsg(null), 2500);
                                }
                              }}>Konfigurieren</button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tools' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input className="border px-2 py-1 flex-1" placeholder="Search tools..." value={toolSearch} onChange={(e) => setToolSearch(e.target.value)} />
              <select value={toolFilter} onChange={(e) => setToolFilter(e.target.value as any)} className="border px-2 py-1">
                <option value="all">Alle</option>
                <option value="active">Aktiv</option>
                <option value="inherited">Geerbt</option>
                <option value="available">Verfügbar</option>
                <option value="disabled">Deaktiviert</option>
              </select>
            </div>

            <div>
              {toolStatusMsg ? <div className="text-sm text-red-600">{toolStatusMsg}</div> : null}
              <div className="max-h-64 overflow-auto border rounded">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="p-2 text-left">Name</th>
                      <th className="p-2">Kategorie</th>
                      <th className="p-2">Herkunft</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(toolsRegistry ?? []).filter((t: any) => {
                      const name = String(t.name ?? t.id ?? '');
                      if (toolSearch && !name.toLowerCase().includes(toolSearch.toLowerCase())) return false;
                      return true;
                    }).map((t: any) => {
                      const name = String(t.name ?? t.id ?? '');
                      const category = t.category ?? (t.metadata && t.metadata.category) ?? '';
                      // derive status from node.tool_policy
                      const policy = nodeToolPolicy ?? ((node as any).tool_policy ?? {});
                      const explicit = Object.prototype.hasOwnProperty.call(policy, name);
                      const isActive = explicit ? Boolean(policy[name]) : (effectiveToolIds?.includes(name) ?? false);
                      const isInherited = !explicit && (effectiveToolIds?.includes(name) ?? false);
                      const status = isActive ? 'Aktiv' : isInherited ? 'Geerbt' : 'Verfügbar';
                      if (toolFilter === 'active' && !isActive) return null;
                      if (toolFilter === 'available' && isActive) return null;
                      if (toolFilter === 'disabled' && t.enabled !== true) return null;

                      return (
                        <tr key={name} className="border-t">
                          <td className="p-2">{t.display_name ?? name}</td>
                          <td className="p-2">{category}</td>
                          <td className="p-2">{isInherited ? 'Geerbt' : 'Registry'}</td>
                          <td className="p-2">{status}</td>
                          <td className="p-2">
                            <div className="flex gap-2">
                              {!isActive && (
                                <button className="px-2 py-1 bg-green-600 text-white rounded" onClick={async () => {
                                  try {
                                    const existing = nodeToolPolicy ?? ((node as any).tool_policy ?? {});
                                    const next = { ...(existing || {}) };
                                    next[name] = true;
                                    await putNodeToolPolicy(node.id, { tool_policy: next });
                                    // refresh local state
                                    const nodeResp2 = await fetchToolsClient.getNode(node.id);
                                    const eff2 = await fetchToolsClient.getNodeEffectiveTools(node.id).catch(() => null);
                                    setNodeToolPolicy((nodeResp2 as any)?.tool_policy ?? {});
                                    setEffectiveToolIds(Array.isArray(eff2) ? eff2 : (eff2?.effective_tool_ids ?? null));
                                    setToolStatusMsg('Werkzeug aktiviert');
                                    setTimeout(() => setToolStatusMsg(null), 2500);
                                  } catch (e) {
                                    if (e instanceof ApiError) {
                                      switch (e.code) {
                                        case 'TOOL_NOT_REGISTERED':
                                          setToolStatusMsg('Werkzeug nicht registriert');
                                          break;
                                        case 'TOOL_NOT_ENABLED':
                                          setToolStatusMsg('Werkzeug ist deaktiviert');
                                          break;
                                        case 'TOOL_NOT_AUTHORIZED':
                                          setToolStatusMsg('Keine Berechtigung für dieses Werkzeug');
                                          break;
                                        case 'TOOL_CONFIGURATION_INVALID':
                                          setToolStatusMsg('Werkzeugkonfiguration ungültig');
                                          break;
                                        default:
                                          setToolStatusMsg('Fehler beim Aktivieren');
                                      }
                                    } else {
                                      setToolStatusMsg('Fehler beim Aktivieren');
                                    }
                                  }
                                }}>Aktivieren</button>
                              )}
                              {isActive && (
                                <button className="px-2 py-1 bg-red-600 text-white rounded" onClick={async () => {
                                  try {
                                    const existing = nodeToolPolicy ?? ((node as any).tool_policy ?? {});
                                    const next = { ...(existing || {}) };
                                    // disable locally by explicit false
                                    next[name] = false;
                                    await putNodeToolPolicy(node.id, { tool_policy: next });
                                    const nodeResp2 = await fetchToolsClient.getNode(node.id);
                                    const eff2 = await fetchToolsClient.getNodeEffectiveTools(node.id).catch(() => null);
                                    setNodeToolPolicy((nodeResp2 as any)?.tool_policy ?? {});
                                    setEffectiveToolIds(Array.isArray(eff2) ? eff2 : (eff2?.effective_tool_ids ?? null));
                                    setToolStatusMsg('Werkzeug deaktiviert');
                                    setTimeout(() => setToolStatusMsg(null), 2500);
                                  } catch (e) {
                                    if (e instanceof ApiError) {
                                      switch (e.code) {
                                        case 'TOOL_NOT_REGISTERED':
                                          setToolStatusMsg('Werkzeug nicht registriert');
                                          break;
                                        case 'TOOL_NOT_ENABLED':
                                          setToolStatusMsg('Werkzeug ist deaktiviert');
                                          break;
                                        case 'TOOL_NOT_AUTHORIZED':
                                          setToolStatusMsg('Keine Berechtigung für dieses Werkzeug');
                                          break;
                                        default:
                                          setToolStatusMsg('Fehler beim Deaktivieren');
                                      }
                                    } else {
                                      setToolStatusMsg('Fehler beim Deaktivieren');
                                    }
                                  }
                                }}>Deaktivieren</button>
                              )}
                              <button className="px-2 py-1 border rounded" onClick={async () => {
                                try {
                                  const nodeResp = await fetchToolsClient.getNode(node.id);
                                  // Prefer canonical tool_policy.configurations, fall back to legacy metadata.tools
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
                                  setTimeout(() => setToolStatusMsg(null), 2500);
                                }
                              }}>{t.configuration_schema || (nodeToolConfigs && nodeToolConfigs[name]) ? 'Konfigurieren' : 'Rohkonfiguration bearbeiten'}</button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'prompts' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold">Lokaler Prompt</h3>
              <textarea className="w-full border p-2 mt-2" rows={6} value={promptsLocal ?? ''} onChange={(e) => setPromptsLocal(e.target.value)} />
              <div className="flex gap-2 justify-end mt-2">
                <button className="px-3 py-1 border rounded" onClick={async () => {
                  // discard: reset to node value
                  setPromptsLocal((node as any).system_prompt ?? '');
                }} disabled={promptSaving}>Zurücksetzen</button>
                <button className="px-3 py-1 bg-green-600 text-white rounded" onClick={async () => {
                  setPromptSaving(true);
                  setPromptError(null);
                    try {
                    const client = await import('../../api/fetchPromptClient');
                    await client.saveLocalPrompt(node.id, promptsLocal ?? null);
                    // reload prompt context
                    const ctx = await client.loadPromptContext(node.id);
                    setPromptsLocal(ctx.local_prompt ?? null);
                    setPromptsChain(ctx.sources ?? []);
                    setResolvedPrompt({ system_prompt: ctx.effective_prompt ?? '' });
                    setPromptError(null);
                  } catch (e) {
                    console.error('Failed saving prompt', e);
                    setPromptError('Fehler beim Speichern des Prompts.');
                  } finally {
                    setPromptSaving(false);
                  }
                }} disabled={promptSaving || (promptsLocal === ((node as any).system_prompt ?? null))}>Prompt speichern</button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold">Geerbte Prompt-Quellen</h3>
              <div className="mt-2 space-y-1">
                {(promptsChain ?? []).map((c: any) => (
                  <div key={c.id} className="p-2 border rounded">
                    <div className="flex justify-between text-sm">
                      <div>
                        <strong>{c.name ?? c.id}</strong> <span className="text-text-soft">{c.type}</span>
                      </div>
                      <div className="text-xs text-gray-500">{c.system_prompt ? `${String(c.system_prompt).length} Zeichen` : '0 Zeichen'}</div>
                    </div>
                    {c.system_prompt ? (
                      <details className="mt-2"><summary className="text-xs text-blue-600">Prompt anzeigen</summary><pre className="whitespace-pre-wrap mt-1 text-sm">{c.system_prompt}</pre></details>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold">Effektiver Prompt</h3>
              <div className="mt-2">
                <textarea readOnly className="w-full border p-2 bg-slate-50" rows={8} value={resolvedPrompt?.system_prompt ?? ''} />
                <div className="flex items-center justify-between text-xs text-gray-600 mt-1">
                  <div>Effektive Länge: {String((resolvedPrompt?.system_prompt ?? '').length)}</div>
                  <div className="flex gap-2">
                    <button className="px-2 py-1 border rounded" onClick={async () => {
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
                    }}>Neu auflösen</button>
                    {import.meta.env.DEV ? (
                      <button className="px-2 py-1 border rounded" onClick={() => {
                        // show debug info in console
                        console.info('prompt-debug', { nodeId: node.id, resolved: resolvedPrompt });
                      }}>Debug</button>
                    ) : null}
                  </div>
                </div>
                {promptError ? <div className="text-red-600 mt-2">{promptError}</div> : null}
              </div>
            </div>
          </div>
        )}

        <div className="flex gap-2 justify-end pt-2">
          <button
            className="px-3 py-1 border rounded"
            onClick={() => {
              // confirm discard if dirty
              const isDirty =
                name !== (node?.name ?? '') || type !== (node?.type ?? '') ||
                (useOverride && JSON.stringify(overrideChildTypes) !== JSON.stringify(((node as any)?.metadata?.hierarchy?.allowed_child_types) ?? []));
              if (isDirty) {
                if (!window.confirm('Nicht gespeicherte Änderungen verwerfen?')) return;
              }
              onClose();
            }}
            disabled={isSaving}
          >
            Abbrechen
          </button>
          <button
            className="px-3 py-1 bg-blue-600 text-white rounded"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'Speichern…' : 'Speichern'}
          </button>
        </div>
        {error && <div className="text-red-600 mt-2">{error}</div>}
      </div>
    </div>
  );
}
