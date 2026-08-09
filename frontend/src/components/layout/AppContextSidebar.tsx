// F:\Kernschmied\frontend\src\components\layout\AppContextSidebar.tsx

import { useEffect, useState, useRef } from 'react';
import { resolveTemplate } from '../../utils/templateResolver';
import { useToast } from '../ui/ToastProvider';
import Modal from '../ui/Modal';
import { apiGet } from '../../api/client';
import { DynamicIcon } from '../../registry/iconRegistry';
import WorkspaceFilesSection from '../files/WorkspaceFilesSection';

const statusColorMap: Record<string, string> = {
  active: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  archived: 'bg-gray-200 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  blocked: 'bg-gray-300 text-gray-700 dark:bg-gray-900 dark:text-gray-300',
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  completed: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  default: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

interface ContextNode {
  id: string;
  name: string;
  type: string;

  // optional additional fields available from the API
  actions?: string[];
  parent_id?: string | null;
  sort_order?: number | null;
  selectable?: boolean | null;
  disabled?: boolean | null;
  status?: string | null;
  metadata?: Record<string, unknown> | null;
  revision?: number | null;
}

interface AppContextSidebarProps {
  node: ContextNode | null;
  schemaVersion?: string;
  defaultOpen?: boolean;
  onAction?: (action: string, node: ContextNode) => Promise<void> | void;
  canPerformAction?: (action: string, node: ContextNode) => Promise<boolean> | boolean;
  path?: Array<{ id: string; name: string }> | undefined;
  onNavigateToNode?: (id: string) => void;
  systemInfo?: any;
}

export function AppContextSidebar({
  node,
  schemaVersion,
  defaultOpen = false,
  onAction,
  canPerformAction,
  path,
  onNavigateToNode,
  systemInfo,
}: AppContextSidebarProps) {
  const [open, setOpen] = useState(defaultOpen);

  function toggleSidebar(): void {
    setOpen((currentOpen) => !currentOpen);
  }

  const toggleLabel = open ? 'Kontextleiste einklappen' : 'Kontextleiste ausklappen';

  const { push } = useToast();

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [isConfirming, setIsConfirming] = useState(false);

  function openConfirm(action: string) {
    setPendingAction(action);
    setConfirmOpen(true);
  }

  async function handleConfirm(node: ContextNode) {
    if (!pendingAction) return;
    setIsConfirming(true);
    try {
      await (onAction ? onAction(pendingAction, node) : Promise.resolve());
      push('success', `Aktion '${pendingAction}' erfolgreich ausgeführt.`);
    } catch (err) {
      push('error', err instanceof Error ? err.message : String(err));
    } finally {
      setIsConfirming(false);
      setConfirmOpen(false);
      setPendingAction(null);
    }
  }

  return (
    <aside
      className={[
        'flex h-full min-h-0 shrink-0 flex-col',
        'border-l border-border',
        'bg-white/80 shadow-glass backdrop-blur-md',
        'transition-[width] duration-200 ease-out',
        'dark:border-white/10 dark:bg-slate-800/80',
        open ? 'w-80' : 'w-12',
      ].join(' ')}
      aria-label="Kontextinformationen"
      data-state={open ? 'open' : 'collapsed'}
    >
      <header
        className={[
          'flex shrink-0 border-b border-border',
          'dark:border-white/10',
          open
            ? 'min-h-16 items-center justify-between gap-3 px-4 py-3'
            : 'h-12 items-center justify-center px-1',
        ].join(' ')}
      >
        {open ? (
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold tracking-wide text-text uppercase dark:text-white">
              Kontext
            </h2>

            <p className="mt-1 truncate text-xs text-text-muted dark:text-gray-400">
              Informationen zum ausgewählten Bereich
            </p>
          </div>
        ) : null}

        <button
          type="button"
          onClick={toggleSidebar}
          className={[
            'inline-flex h-9 w-9 shrink-0',
            'items-center justify-center rounded-lg',
            'text-text-muted transition',
            'hover:bg-surface-hover hover:text-text',
            'focus-visible:outline-none',
            'focus-visible:ring-2',
            'focus-visible:ring-primary',
            'dark:text-gray-400',
            'dark:hover:bg-slate-700/70',
            'dark:hover:text-white',
          ].join(' ')}
          aria-label={toggleLabel}
          aria-expanded={open}
          title={toggleLabel}
        >
          <ContextToggleIcon open={open} />
        </button>
      </header>

      {open ? (
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          {node ? (
            <>
              <ContextContent
                node={node}
                schemaVersion={schemaVersion}
                onAction={onAction}
                onRequestAction={openConfirm}
                canPerformAction={canPerformAction}
                path={path}
                onNavigateToNode={onNavigateToNode}
                systemInfo={systemInfo}
              />
              <Modal
                isOpen={confirmOpen && !!pendingAction && !!node}
                title={`Aktion: ${pendingAction ?? ''}`}
                onClose={() => setConfirmOpen(false)}
                onConfirm={() => void handleConfirm(node!)}
                confirmLabel="Ausführen"
                confirmDisabled={isConfirming}
              >
                <div className="text-sm">Soll die Aktion <strong>{pendingAction}</strong> für <strong>{node.name}</strong> wirklich ausgeführt werden?</div>
              </Modal>
            </>
          ) : (
            <EmptyContext />
          )}
        </div>
      ) : (
        <button
          type="button"
          onClick={toggleSidebar}
          className={[
            'flex min-h-0 flex-1',
            'items-center justify-center',
            'text-text-subtle transition',
            'hover:bg-surface-hover hover:text-text',
            'focus-visible:outline-none',
            'focus-visible:ring-2',
            'focus-visible:ring-inset',
            'focus-visible:ring-primary',
            'dark:text-gray-500',
            'dark:hover:bg-slate-800',
            'dark:hover:text-gray-300',
          ].join(' ')}
          aria-label="Kontextleiste ausklappen"
          title="Kontextleiste ausklappen"
        >
          <span
            className={[
              'select-none text-[10px]',
              'font-semibold tracking-[0.18em]',
              'uppercase',
              '[writing-mode:vertical-rl]',
            ].join(' ')}
            aria-hidden="true"
          >
            Kontext
          </span>
        </button>
      )}
    </aside>
  );
}

interface ContextContentProps {
  node: ContextNode;
  schemaVersion?: string;
  onAction?: (action: string, node: ContextNode) => Promise<void> | void;
  onRequestAction?: (action: string) => void;
  canPerformAction?: (action: string, node: ContextNode) => Promise<boolean> | boolean;
  path?: Array<{ id: string; name: string }> | undefined;
  onNavigateToNode?: (id: string) => void;
  systemInfo?: any;
}
function ContextContent({ node, schemaVersion, onAction, onRequestAction, canPerformAction, path, onNavigateToNode, systemInfo }: ContextContentProps) {
  const [canMap, setCanMap] = useState<Record<string, boolean | undefined>>({});
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [measuring, setMeasuring] = useState(false);
  const pingController = useRef<AbortController | null>(null);
  const [promptModalOpen, setPromptModalOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function run() {
      if (!Array.isArray(node.actions) || !canPerformAction) return;
      const next: Record<string, boolean | undefined> = {};
      for (const a of node.actions) {
        try {
          // allow sync or async check
          const ok = await Promise.resolve(canPerformAction(a, node));
          next[a] = Boolean(ok);
        } catch {
          next[a] = false;
        }
      }

      if (mounted) setCanMap(next);
    }

    void run();
    return () => {
      mounted = false;
    };
  }, [node, canPerformAction]);

  useEffect(() => {
    // measure latency once when node/context shown
    void measureLatency();
    return () => {
      if (pingController.current) pingController.current.abort();
    };
  }, [node]);

  async function measureLatency() {
    try {
      if (pingController.current) pingController.current.abort();
    } catch {}

    const controller = new AbortController();
    pingController.current = controller;
    setMeasuring(true);
    const start = performance.now();
    try {
      await apiGet('/health', { signal: controller.signal });
      const d = Math.max(0, Math.round(performance.now() - start));
      setLatencyMs(d);
    } catch (err) {
      setLatencyMs(null);
    } finally {
      setMeasuring(false);
      pingController.current = null;
    }
  }
  return (
    <div className="space-y-5 p-4">
      {path && path.length > 0 ? (
        <div className="mb-2 text-xs text-text-muted dark:text-gray-400">
          {path.map((p, idx) => {
            const isLast = idx === path.length - 1;
            return (
              <span key={p.id} className="inline-flex items-center">
                <button
                  type="button"
                  onClick={() => !isLast && onNavigateToNode?.(p.id)}
                  className={[
                    'text-xs px-1',
                    isLast ? 'font-semibold text-text' : 'text-text-muted hover:underline',
                  ].join(' ')}
                >
                  {p.name}
                </button>
                {!isLast ? <span className="mx-1 text-text-muted">/</span> : null}
              </span>
            );
          })}
        </div>
      ) : null}
      <ContextSection title="Ausgewählter Knoten" defaultOpen={true}>
        <div className="px-3 py-2">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="truncate text-sm font-semibold text-text">{node.name}</h3>
              <div className="mt-1 text-xs text-text-muted">{node.type}</div>
              {(() => {
                const desc = (node as any).description ?? (node.metadata && (node.metadata.description ?? node.metadata.desc));
                if (!desc) return null;
                return <p className="mt-2 text-sm text-text-muted">{String(desc)}</p>;
              })()}
            </div>

            <div className="shrink-0 text-right">
              {(() => {
                const created = (node.metadata && (node.metadata.created_at ?? node.metadata.createdAt)) as string | undefined | null;
                if (!created) return null;
                const d = new Date(created);
                return <div className="text-xs text-text-muted">Erstellt: {Number.isFinite(d.getTime()) ? d.toLocaleDateString() : String(created)}</div>;
              })()}

              <div className="mt-2">
                <div className="text-xs">Status</div>
                <div className="text-sm font-medium">{node.status ?? 'aktiv'}</div>
              </div>
            </div>
          </div>
        </div>
      </ContextSection>

      <ContextSection title="Schema">
        <ContextValue label="UI-Schema" value={schemaVersion ?? 'Nicht verfügbar'} mono />
      </ContextSection>

      <ContextSection title="Details">
        <ContextValue label="Status" value={node.status ?? '—'} />

        <ContextValue label="Eltern-ID" value={node.parent_id ?? '—'} mono />

        <ContextValue label="Sortierung" value={
          node.sort_order !== undefined && node.sort_order !== null ? String(node.sort_order) : '—'
        } mono />

        <ContextValue label="Auswählbar" value={
          node.selectable === undefined || node.selectable === null ? 'default' : String(node.selectable)
        } />

        <ContextValue label="Deaktiviert" value={
          node.disabled === undefined || node.disabled === null ? 'false' : String(node.disabled)
        } />

        <ContextValue label="Revision" value={node.revision !== undefined && node.revision !== null ? String(node.revision) : '—'} />
      </ContextSection>

      {Array.isArray(node.actions) && node.actions.length > 0 ? (
        <ContextSection title="Aktionen">
          <div className="px-3 py-2">
            <div className="flex flex-col gap-2">
              {node.actions.map((a) => (
                <button
                  key={a}
                  type="button"
                  onClick={() => onRequestAction?.(a)}
                  className="rounded border border-border px-3 py-1 text-sm text-left hover:bg-surface-hover"
                  disabled={!onAction || canMap[a] === false}
                  title={canMap[a] === false ? 'Nicht autorisiert' : undefined}
                  aria-disabled={canMap[a] === false}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>
        </ContextSection>
      ) : null}

      <ContextSection title="Teilnehmer">
        {(() => {
          const parts = node.metadata && (node.metadata.participants ?? node.metadata.users ?? node.metadata.participant);
          if (!parts) return <div className="px-3 py-2 text-xs text-text-muted">Keine Teilnehmer</div>;
          if (Array.isArray(parts)) {
            return (
              <div className="px-3 py-2">
                <div className="flex flex-wrap gap-2">
                  {parts.map((p: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 rounded bg-surface px-2 py-0.5 text-[12px]">
                      <div className="h-6 w-6 flex items-center justify-center rounded-full bg-white/30 text-[12px]">{typeof p === 'string' ? (p[0] ?? '?') : typeof p === 'object' && p !== null && p.name ? String((p as any).name)[0] : '?'}</div>
                      <div className="min-w-0 truncate">{typeof p === 'string' ? p : typeof p === 'object' && p !== null && 'name' in p ? String((p as any).name) : String(p)}</div>
                    </div>
                  ))}
                </div>
              </div>
            );
          }

          return <div className="px-3 py-2 text-xs text-text-muted">{String(parts)}</div>;
        })()}
      </ContextSection>

      {node.metadata && Object.keys(node.metadata).length > 0 ? (
        <ContextSection title="Metadaten">
          <div className="space-y-2 px-3 py-2">
            {(() => {
              const linked = node.metadata && (node.metadata.linked_resources ?? node.metadata.links ?? node.metadata.linked);
              if (!linked || !Array.isArray(linked) || linked.length === 0) return null;
              const items = linked.slice(0, 3);
              return (
                <div className="mb-2">
                  <div className="text-xs text-text-muted dark:text-gray-400 mb-2">Verknüpfte Ressourcen</div>
                  <div className="flex flex-col gap-2">
                    {items.map((it: any, i: number) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => {
                          if (it.id && onNavigateToNode) onNavigateToNode(it.id);
                        }}
                        aria-label={String(it.name ?? it.title ?? it.id ?? 'Ressource')}
                        className="w-full rounded border border-border px-2 py-2 text-sm hover:bg-surface-hover focus:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      >
                        <div className="grid grid-cols-[auto_1fr_auto] items-center gap-3">
                          <div className="flex items-center justify-center h-8 w-8 shrink-0 rounded-md bg-surface">
                            {it.icon ? (
                              <img src={String(it.icon)} alt="" className="h-5 w-5" />
                            ) : (
                              <DynamicIcon name={String(it.type ?? 'Circle')} size={18} />
                            )}
                          </div>

                          <div className="min-w-0">
                            <div className="truncate text-sm font-medium text-text">{it.name ?? it.title ?? it.id ?? 'Unbenannt'}</div>
                            {it.type ? (
                              <div className="text-[11px] text-text-muted mt-0.5 truncate">{String(it.type)}</div>
                            ) : null}
                          </div>

                          <div className="ml-2 flex items-center justify-end">
                            {it.status ? (
                              (() => {
                                const key = String(it.status).toLowerCase();
                                const cls = statusColorMap[key] ?? statusColorMap.default;
                                return (
                                  <span className={`inline-flex items-center justify-center shrink-0 rounded-full px-2 py-0.5 text-[11px] ${cls}`}>{String(it.status)}</span>
                                );
                              })()
                            ) : null}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })()}
            {Object.entries(node.metadata).map(([k, v]) => (
              <div key={k} className="flex items-start justify-between gap-4 border-b border-border-soft py-1 last:border-b-0 dark:border-white/10">
                <dt className="shrink-0 text-xs text-text-muted dark:text-gray-500">{k}</dt>
                <dd className="min-w-0 break-all text-right text-xs text-text-soft dark:text-gray-300 font-mono">{renderMetadataValue(v)}</dd>
              </div>
            ))}
          </div>
        </ContextSection>
      ) : null}

      <ContextSection title="Prompt">
        {(() => {
          const prompt = (node as any).system_prompt ?? (node as any).effective_prompt ?? (node.metadata && (node.metadata.prompt ?? null));
          if (!prompt) return <div className="px-3 py-2 text-xs text-text-muted">Kein Prompt definiert.</div>;
          const snippet = String(prompt).length > 250 ? String(prompt).slice(0, 250) + '…' : String(prompt);
          return (
            <div className="px-3 py-2">
              <div className="text-sm text-text wrap-break-word">{snippet}</div>
              <div className="mt-2">
                <button
                  type="button"
                  className="inline-flex items-center rounded border px-2 py-1 text-xs"
                  onClick={() => setPromptModalOpen(true)}
                >
                  Voll anzeigen
                </button>
                <Modal isOpen={promptModalOpen} title="Vollständiger Prompt" onClose={() => setPromptModalOpen(false)} confirmLabel="Schließen">
                  <pre className="whitespace-pre-wrap">{resolveTemplate(String(prompt), { system: { name: 'Kernschmied' } })}</pre>
                </Modal>
              </div>
            </div>
          );
        })()}
      </ContextSection>

        <ContextSection title="Dateien">
          <div className="px-3 py-2">
            <WorkspaceFilesSection selectedNode={node} />
          </div>
        </ContextSection>
      {systemInfo ? (
        <div className="px-3 py-3 border-t border-border text-xs text-text-muted dark:border-white/10">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[13px] font-medium">System</div>
            <div className="flex items-center gap-2">
              <div className="text-right text-[12px] text-text-soft">
                {systemInfo.apiVersion ? <div>API: {systemInfo.apiVersion}</div> : null}
                {systemInfo.requestId ? <div>Req: {systemInfo.requestId}</div> : null}
              </div>
              <button
                type="button"
                onClick={() => void measureLatency()}
                className="inline-flex items-center gap-2 rounded px-2 py-1 text-xs hover:bg-surface-hover"
                title="Latenz erneut messen"
              >
                {measuring ? 'Messe…' : 'Ping'}
              </button>
            </div>
          </div>
          <div className="mt-2 text-[12px] text-text-muted">
            {systemInfo.model ? <div>Modell: {systemInfo.model}</div> : null}
            {systemInfo.temperature !== undefined ? <div>Temperatur: {String(systemInfo.temperature)}</div> : null}
            {latencyMs !== null ? (
              <div>Latenz: {String(latencyMs)}ms</div>
            ) : (
              systemInfo.latency !== undefined ? <div>Latenz: {String(systemInfo.latency)}ms</div> : null
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function renderMetadataValue(value: unknown): string {
  if (value === null || value === undefined) return '—';

  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

interface ContextSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function ContextSection({ title, children, defaultOpen = false }: ContextSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-wide text-text-muted uppercase dark:text-gray-500">{title}</h3>
        <button
          type="button"
          onClick={() => setOpen((s) => !s)}
          className="inline-flex items-center justify-center rounded px-2 py-1 text-xs text-text-muted hover:bg-surface-hover"
          aria-expanded={open}
        >
          {open ? '▾' : '▸'}
        </button>
      </div>

      {open ? (
        <dl className="overflow-hidden rounded-xl border border-border-soft bg-white/70 dark:border-white/10 dark:bg-slate-900/40">
          {children}
        </dl>
      ) : null}
    </section>
  );
}

interface ContextValueProps {
  label: string;
  value: string;
  mono?: boolean;
}

function ContextValue({ label, value, mono = false }: ContextValueProps) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border-soft px-3 py-2.5 last:border-b-0 dark:border-white/10">
      <dt className="shrink-0 text-xs text-text-muted dark:text-gray-500">{label}</dt>

      <dd
        className={[
          'min-w-0 break-all text-right text-xs',
          'text-text-soft dark:text-gray-300',
          mono ? 'font-mono' : 'font-medium',
        ].join(' ')}
      >
        {value}
      </dd>
    </div>
  );
}

function EmptyContext() {
  return (
    <div className="p-4">
      <div className="rounded-xl border border-dashed border-border-soft bg-white/50 p-4 text-sm text-text-muted dark:border-white/10 dark:bg-slate-900/30 dark:text-gray-400">
        Wähle einen Eintrag aus der Hierarchie aus, um weitere Informationen anzuzeigen.
      </div>
    </div>
  );
}

interface ContextToggleIconProps {
  open: boolean;
}

function ContextToggleIcon({ open }: ContextToggleIconProps) {
  return (
    <svg
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="16" rx="2" strokeWidth="1.8" />

      <path d="M15 4v16" strokeWidth="1.8" />

      {open ? (
        <path d="m10 9 3 3-3 3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
      ) : (
        <path d="m13 9-3 3 3 3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
      )}
    </svg>
  );
}
