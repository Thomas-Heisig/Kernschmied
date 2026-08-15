// F:\Kernschmied\frontend\src\components\schema\GenericTreeClean.tsx

import React, {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { ChevronDown, ChevronRight, MoreHorizontal, Star } from 'lucide-react';
import type { HierarchyNode } from '../../contracts/hierarchy';
import type { UISchema } from '../../contracts/schema';
import {
  getActionDefinition,
  hasActionHandler,
  filterSupportedActionKinds,
  executeRegisteredAction,
  listActionDefinitions,
  isActionEnabled,
} from '../../registry/actionRegistry';
import IconBadge from '../common/IconBadge';
import { DynamicIcon } from '../../registry/iconRegistry';
import { getNodeTypeConfig } from '../../config/nodeTypeConfig';

const DEFAULT_NODE_ICON = 'Circle';
const DEFAULT_VISIBLE_ACTION_COUNT = 2;
const INDENT_SIZE_PX = 16;
const BASE_INDENT_PX = 8;

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export interface GenericTreeProps {
  root: HierarchyNode;
  schema: UISchema;
  onSelect: (node: HierarchyNode) => void;
  selectedNodeId?: string | null;
  onAction?: (action: string, node: HierarchyNode) => void;
  onCreateChat?: (parentNodeId: string) => void;
  expandedNodeIds?: ReadonlySet<string>;
  onExpandedNodeIdsChange?: (expandedNodeIds: ReadonlySet<string>) => void;
  maxVisibleActions?: number;
  className?: string;
  renderLabel?: (node: HierarchyNode) => ReactNode;
  onNodeDrop?: (
    sourceId: string,
    targetId: string,
    dropInfo?: { parentId: string | null; position: number | null },
  ) => void;
  isBusy?: boolean;
  recentlyMovedNodeId?: string | null;
  filterText?: string | null;
  showArchived?: boolean;
  visibleNodeTypes?: ReadonlySet<string>;
  favoriteNodeIds?: ReadonlySet<string>;
  onToggleFavorite?: (node: HierarchyNode) => void;
}

function joinClassNames(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(' ');
}

function getChildren(node: HierarchyNode): readonly HierarchyNode[] {
  return Array.isArray(node.children) ? node.children : [];
}

function getNodeActions(node: HierarchyNode): readonly string[] {
  return Array.isArray(node.actions) ? node.actions : [];
}

function normalizeVisibleActionCount(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) return DEFAULT_VISIBLE_ACTION_COUNT;
  return Math.max(0, Math.floor(value));
}

function nodeMatchesFilter(node: HierarchyNode, filterText?: string | null): boolean {
  if (!filterText) return true;
  const q = String(filterText).trim().toLowerCase();
  if (!q) return true;

  if ((node.name ?? '').toLowerCase().includes(q)) return true;

  if (node.children && Array.isArray(node.children)) {
    for (const c of node.children) {
      if (nodeMatchesFilter(c, q)) return true;
    }
  }

  return false;
}

function nodeMatchesTypeFilter(node: HierarchyNode, visibleNodeTypes?: ReadonlySet<string>): boolean {
  if (!visibleNodeTypes || visibleNodeTypes.size === 0) return true;
  if (visibleNodeTypes.has(String(node.type).toLowerCase())) return true;
  return getChildren(node).some((child) => nodeMatchesTypeFilter(child, visibleNodeTypes));
}

function GenericTreeComponent({
  root,
  schema,
  onSelect,
  selectedNodeId = null,
  onAction,
  onCreateChat,
  expandedNodeIds,
  onExpandedNodeIdsChange,
  maxVisibleActions,
  className,
  renderLabel,
  onNodeDrop,
  isBusy = false,
  recentlyMovedNodeId = null,
  filterText,
  showArchived = false,
  visibleNodeTypes,
  favoriteNodeIds,
  onToggleFavorite,
}: GenericTreeProps) {
  const [internalExpanded, setInternalExpanded] = useState<Set<string>>(() => new Set([root.id]));
  const isControlled = expandedNodeIds !== undefined;
  const expanded = expandedNodeIds ?? internalExpanded;
  const visibleActionCount = useMemo(
    () => normalizeVisibleActionCount(maxVisibleActions),
    [maxVisibleActions],
  );

  useEffect(() => {
    if (isControlled) return;
    setInternalExpanded((s) => (s.has(root.id) ? s : new Set([root.id])));
  }, [isControlled, root.id]);

  const toggleExpanded = useCallback(
    (id: string) => {
      const next = new Set(expanded);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      if (!isControlled) setInternalExpanded(next);
      onExpandedNodeIdsChange?.(next);
    },
    [expanded, isControlled, onExpandedNodeIdsChange],
  );

  return (
    <div
      className={joinClassNames('min-w-0', className)}
      role="tree"
      aria-label="Anwendungshierarchie"
    >
      <TreeNode
        node={root}
        schema={schema}
        depth={0}
        selectedNodeId={selectedNodeId}
        expandedNodeIds={expanded}
        maxVisibleActions={visibleActionCount}
        onSelect={onSelect}
        onAction={onAction}
        onCreateChat={onCreateChat}
        onToggleExpanded={toggleExpanded}
        renderLabel={renderLabel}
        onNodeDrop={onNodeDrop}
        isBusy={isBusy}
        recentlyMovedNodeId={recentlyMovedNodeId}
        filterText={filterText}
        showArchived={showArchived}
        visibleNodeTypes={visibleNodeTypes}
        favoriteNodeIds={favoriteNodeIds}
        onToggleFavorite={onToggleFavorite}
      />
    </div>
  );
}

// ============================================================
// TREE NODE (verbessert)
// ============================================================

function TreeNode(props: any) {
  const {
    node,
    schema,
    depth,
    selectedNodeId,
    expandedNodeIds,
    maxVisibleActions,
    onSelect,
    onAction,
    onCreateChat,
    onToggleExpanded,
    renderLabel,
    onNodeDrop,
    isBusy,
    recentlyMovedNodeId,
    filterText,
    showArchived = false,
    visibleNodeTypes,
    favoriteNodeIds,
    onToggleFavorite,
  } = props;

  // Node‑Type‑Lookup (unverändert)
  const lookupNodeType = (k: string | undefined) =>
    k && isPlainObject(schema.node_types?.[k]) ? schema.node_types[k] : undefined;

  let nodeDef = lookupNodeType(node.id) ?? lookupNodeType(node.type);

  if (!nodeDef && typeof node.type === 'string') {
    const t = String(node.type).trim().toLowerCase();
    const aliases: Record<string, string> = {
      bereich: 'workspace',
      benutzer: 'user',
      benutzerkonto: 'user',
      user: 'user',
      workspace: 'workspace',
      projekt: 'project',
      projektname: 'project',
      project: 'project',
    };
    const mapped = aliases[t];
    if (mapped) nodeDef = lookupNodeType(mapped);
  }

  const children = useMemo(() => getChildren(node), [node]);
  const hasChildren = children.length > 0;
  const isExpanded = hasChildren && expandedNodeIds.has(node.id);
  const isSelected = selectedNodeId === node.id;
  const iconName = typeof nodeDef?.icon === 'string' ? nodeDef.icon : undefined;

  // Aktionen
  const supported = useMemo(() => filterSupportedActionKinds(getNodeActions(node)), [node]);
  const effective =
    supported.length > 0
      ? supported
      : listActionDefinitions()
          .map((d) => d.kind)
          .filter(isActionEnabled);
  const visible = effective.slice(0, maxVisibleActions);
  const overflow = effective.slice(maxVisibleActions);

  // Dropdown‑Menu (verbessert)
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!menuOpen) return;
      if (!menuRef.current) return;
      if (!menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    }
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [menuOpen]);

  // Drag & Drop (unverändert)
  const handleDragStart = useCallback(
    (e: React.DragEvent) => {
      try {
        e.dataTransfer.setData('application/x-kernschmied-node', node.id);
        e.dataTransfer.effectAllowed = 'move';
      } catch {}
    },
    [node.id],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    try {
      e.dataTransfer.dropEffect = 'move';
    } catch {}
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      try {
        const source =
          e.dataTransfer.getData('application/x-kernschmied-node') ||
          e.dataTransfer.getData('text/plain');
        if (!source || !onNodeDrop || source === node.id) return;

        const rect = (e.currentTarget as Element).getBoundingClientRect();
        const y = e.clientY - rect.top;
        const h = rect.height || 1;
        const pct = y / h;

        let dropInfo: { parentId: string | null; position: number | null } | undefined;
        if (pct < 0.25) {
          dropInfo = { parentId: node.parent_id ?? null, position: node.sort_order ?? 0 };
        } else if (pct > 0.75) {
          dropInfo = { parentId: node.parent_id ?? null, position: (node.sort_order ?? 0) + 1 };
        } else {
          dropInfo = { parentId: node.id, position: null };
        }

        onNodeDrop(source, node.id, dropInfo);
      } catch {}
    },
    [node.id, onNodeDrop],
  );

  // Archivierte Knoten ausblenden
  if (!showArchived && node.metadata?.archived) {
    return null;
  }

  // Wenn Filter aktiv ist und weder dieser Knoten noch ein Kind matcht -> ausblenden
  if (filterText && !nodeMatchesFilter(node, filterText)) {
    return null;
  }

  if (!nodeMatchesTypeFilter(node, visibleNodeTypes)) {
    return null;
  }

  const cfg = getNodeTypeConfig(String(node.type ?? ''));
  const icon = iconName ?? cfg.icon ?? DEFAULT_NODE_ICON;
  const isMoved = recentlyMovedNodeId === node.id;
  const isFavorite = favoriteNodeIds?.has(node.id) ?? false;
  const unreadCount = Number(node.metadata?.unread_count ?? node.metadata?.unreadCount ?? 0);
  const hasStatus = Boolean(node.status) || unreadCount > 0 || Boolean(node.metadata?.changed);

  return (
    <div
      role="treeitem"
      aria-level={depth + 1}
      aria-selected={isSelected}
      aria-expanded={hasChildren ? isExpanded : undefined}
      draggable
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <div
        className={joinClassNames(
          'flex items-center gap-1.5 rounded-lg px-2 py-1.5 transition-colors min-w-0',
          isSelected
            ? 'bg-primary-soft dark:bg-primary/20'
            : 'hover:bg-surface-hover dark:hover:bg-slate-800',
          isMoved ? 'ring-2 ring-primary/50 animate-pulse' : '',
          node.metadata?.archived ? 'opacity-60' : '',
        )}
        style={{ paddingLeft: BASE_INDENT_PX + depth * INDENT_SIZE_PX }}
      >
        {hasChildren ? (
          <button
            type="button"
            draggable={false}
            onClick={() => onToggleExpanded(node.id)}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-text-muted hover:bg-white/70 hover:text-text dark:hover:bg-slate-700"
            aria-label={isExpanded ? `${node.name} einklappen` : `${node.name} ausklappen`}
          >
            {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
          </button>
        ) : (
          <span className="h-7 w-7 shrink-0" aria-hidden="true" />
        )}

        {/* Haupt‑Button: Icon + Label */}
        <button
          type="button"
          onClick={() => onSelect(node)}
          className="flex flex-1 items-center gap-2 min-w-0 text-left"
        >
          <IconBadge
            icon={<DynamicIcon name={String(icon)} />}
            size={cfg.defaultSize}
            variant={cfg.variant as any}
          />

          <span
            className={joinClassNames(
              'truncate text-sm text-text dark:text-white',
              node.metadata?.archived ? 'italic' : '',
            )}
            title={String(node.name ?? '')}
          >
            {renderLabel ? renderLabel(node) : node.name}
          </span>

          {unreadCount > 0 ? (
            <span className="min-w-5 rounded-full bg-primary px-1.5 py-0.5 text-center text-[10px] font-semibold text-white" title={`${unreadCount} ungelesen`}>
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          ) : hasStatus ? (
            <span className="h-2 w-2 shrink-0 rounded-full bg-warning" title={String(node.status ?? 'Geändert')} />
          ) : null}

          {isBusy && isSelected && (
            <span className="ml-auto h-2 w-2 animate-pulse rounded-full bg-primary/60" />
          )}
        </button>

        <button
          type="button"
          draggable={false}
          onClick={(event) => {
            event.stopPropagation();
            onToggleFavorite?.(node);
          }}
          className={joinClassNames(
            'rounded-md p-1 transition-colors hover:bg-surface-hover',
            isFavorite ? 'text-warning' : 'text-text-subtle opacity-40 hover:opacity-100',
          )}
          aria-label={isFavorite ? `${node.name} aus Favoriten entfernen` : `${node.name} zu Favoriten hinzufügen`}
          aria-pressed={isFavorite}
          title={isFavorite ? 'Favorit entfernen' : 'Als Favorit markieren'}
        >
          <Star size={14} fill={isFavorite ? 'currentColor' : 'none'} />
        </button>

        {/* "Mehr"‑Button + Dropdown */}
        <div className="relative ml-auto" ref={menuRef}>
          <button
            type="button"
            draggable={false}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            aria-label="Weitere Aktionen"
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((s) => !s);
            }}
            className={joinClassNames(
              'rounded-lg p-1.5 transition-colors',
              menuOpen
                ? 'bg-surface-hover text-text dark:text-white'
                : 'text-text-muted hover:bg-surface-hover hover:text-text dark:text-gray-400 dark:hover:bg-slate-700 dark:hover:text-white',
            )}
          >
            <IconBadge icon={<MoreHorizontal />} size="sm" variant="default" />
          </button>

          {menuOpen && (
            <div
              className="absolute right-0 mt-2 w-56 rounded-xl border border-border-soft bg-white p-1.5 shadow-2xl dark:border-white/10 dark:bg-slate-900"
              role="menu"
              onMouseDown={(e) => e.stopPropagation()}
            >
              {/* Nicht‑destruktive Aktionen */}
              {effective
                .filter((a) => !(getActionDefinition(a)?.destructive ?? false))
                .map((action: string) => {
                  const def = getActionDefinition(action);
                  const disabled = !hasActionHandler(action) && !onAction;

                  if (!def) {
                    return (
                      <button
                        key={action}
                        type="button"
                        draggable={false}
                        disabled
                        className="w-full cursor-not-allowed rounded-lg px-3 py-2 text-left text-sm text-text-muted opacity-50 dark:text-gray-500"
                      >
                        {action}
                      </button>
                    );
                  }

                  return (
                    <button
                      key={action}
                      type="button"
                      draggable={false}
                      disabled={disabled}
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setMenuOpen(false);
                        if (onAction) {
                          onAction(action, node);
                        } else {
                          void executeRegisteredAction(action, {
                            target: node,
                            payload: undefined,
                          });
                        }
                      }}
                      className={joinClassNames(
                        'w-full rounded-lg px-3 py-2 text-left text-sm transition-colors',
                        disabled
                          ? 'cursor-not-allowed text-text-muted opacity-50'
                          : 'text-text hover:bg-surface-hover dark:text-gray-200 dark:hover:bg-slate-800',
                      )}
                    >
                      <span className="flex items-center gap-2.5">
                        {def.icon && <DynamicIcon name={def.icon} size={14} />}
                        {def.label}
                      </span>
                    </button>
                  );
                })}

              {/* Trennlinie + destruktive Aktionen */}
              {effective.some((a) => getActionDefinition(a)?.destructive) && (
                <div className="my-1.5 h-px bg-border-soft dark:bg-white/10" />
              )}

              {effective
                .filter((a) => getActionDefinition(a)?.destructive)
                .map((action: string) => {
                  const def = getActionDefinition(action);
                  const disabled = !hasActionHandler(action) && !onAction;

                  if (!def) {
                    return (
                      <button
                        key={action}
                        type="button"
                        draggable={false}
                        disabled
                        className="w-full cursor-not-allowed rounded-lg px-3 py-2 text-left text-sm text-text-muted opacity-50 dark:text-gray-500"
                      >
                        {action}
                      </button>
                    );
                  }

                  return (
                    <button
                      key={action}
                      type="button"
                      draggable={false}
                      disabled={disabled}
                      onClick={(ev) => {
                        ev.stopPropagation();
                        setMenuOpen(false);
                        if (onAction) {
                          onAction(action, node);
                        } else {
                          void executeRegisteredAction(action, {
                            target: node,
                            payload: undefined,
                          });
                        }
                      }}
                      className={joinClassNames(
                        'w-full rounded-lg px-3 py-2 text-left text-sm transition-colors',
                        disabled
                          ? 'cursor-not-allowed text-text-muted opacity-50'
                          : 'text-danger hover:bg-danger-soft dark:text-danger dark:hover:bg-danger/10',
                      )}
                    >
                      <span className="flex items-center gap-2.5">
                        {def.icon && <DynamicIcon name={def.icon} size={14} />}
                        {def.label}
                      </span>
                    </button>
                  );
                })}
            </div>
          )}
        </div>
      </div>

      {/* Kinder (rekursiv) */}
      {hasChildren && isExpanded && (
        <div role="group">
          {children.map((c) => (
            <TreeNode
              key={c.id}
              node={c}
              schema={schema}
              depth={depth + 1}
              selectedNodeId={selectedNodeId}
              expandedNodeIds={expandedNodeIds}
              maxVisibleActions={maxVisibleActions}
              onSelect={onSelect}
              onAction={onAction}
              onCreateChat={onCreateChat}
              onToggleExpanded={onToggleExpanded}
              renderLabel={renderLabel}
              onNodeDrop={onNodeDrop}
              isBusy={isBusy}
              recentlyMovedNodeId={recentlyMovedNodeId}
              filterText={filterText}
              showArchived={showArchived}
              visibleNodeTypes={visibleNodeTypes}
              favoriteNodeIds={favoriteNodeIds}
              onToggleFavorite={onToggleFavorite}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export const GenericTree = memo(GenericTreeComponent);
export default GenericTree;