import React, {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from 'react';
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
import { DynamicIcon } from '../../registry/iconRegistry';

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
      />
    </div>
  );
}

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
  } = props;
  const nodeDef = isPlainObject(schema.node_types?.[node.type])
    ? schema.node_types[node.type]
    : undefined;
  const children = useMemo(() => getChildren(node), [node]);
  const hasChildren = children.length > 0;
  const isExpanded = hasChildren && expandedNodeIds.has(node.id);
  const isSelected = selectedNodeId === node.id;
  const iconName = typeof nodeDef?.icon === 'string' ? nodeDef.icon : undefined;

  const supported = useMemo(() => filterSupportedActionKinds(getNodeActions(node)), [node]);
  const effective =
    supported.length > 0
      ? supported
      : listActionDefinitions()
          .map((d) => d.kind)
          .filter(isActionEnabled);
  const visible = effective.slice(0, maxVisibleActions);
  const overflow = effective.slice(maxVisibleActions);

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
          e.dataTransfer.getData("application/x-kernschmied-node") ||
          e.dataTransfer.getData("text/plain");
        if (!source || !onNodeDrop || source === node.id) return;

        // Determine drop position: before / inside / after based on pointer
        const rect = (e.currentTarget as Element).getBoundingClientRect();
        const y = e.clientY - rect.top;
        const h = rect.height || 1;
        const pct = y / h;

        // top 25% -> before, bottom 25% -> after, otherwise inside
        let dropInfo: { parentId: string | null; position: number | null } | undefined;
        if (pct < 0.25) {
          dropInfo = { parentId: node.parent_id ?? null, position: node.sort_order ?? 0 };
        } else if (pct > 0.75) {
          dropInfo = { parentId: node.parent_id ?? null, position: (node.sort_order ?? 0) + 1 };
        } else {
          // inside -> append as child (position null meaning append)
          dropInfo = { parentId: node.id, position: null };
        }

        onNodeDrop(source, node.id, dropInfo);
      } catch {}
    },
    [node.id, onNodeDrop],
  );

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
          'flex items-center gap-2 px-2 py-1 rounded',
          isSelected ? 'bg-primary-soft' : '',
        )}
        style={{ paddingLeft: BASE_INDENT_PX + depth * INDENT_SIZE_PX }}
      >
        <button
          type="button"
          onClick={() => hasChildren && onToggleExpanded(node.id)}
          className={joinClassNames(hasChildren ? '' : 'opacity-0')}
        >
          {hasChildren ? '▶' : null}
        </button>
        <button
          type="button"
          onClick={() => onSelect(node)}
          onKeyDown={(e) => {
            if ((e as KeyboardEvent).key === 'Enter') onSelect(node);
          }}
          className="flex-1 text-left"
        >
          <DynamicIcon name={iconName ?? DEFAULT_NODE_ICON} />{' '}
          <span className="ml-2 truncate">{renderLabel ? renderLabel(node) : node.name}</span>
        </button>

        <div className="relative ml-2" ref={menuRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpen((s) => !s);
            }}
            className="p-1 rounded"
          >
            {' '}
            <DynamicIcon name="MoreHorizontal" size={16} />{' '}
          </button>
          {menuOpen ? (
            <div className="absolute right-0 mt-2 w-56 bg-white shadow z-10 border border-border dark:bg-slate-900">
              <div className="p-1">
                {/* Primary (non-destructive) actions */}
                {effective
                  .filter((a) => !(getActionDefinition(a)?.destructive ?? false))
                  .map((action: string) => {
                    const def = getActionDefinition(action)!;
                    const disabled = !hasActionHandler(action) && !onAction;
                    return (
                      <button
                        key={action}
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
                          'w-full text-left px-3 py-2 flex items-center gap-2',
                          disabled ? 'opacity-50' : 'hover:bg-surface-hover',
                        )}
                      >
                        {def.icon ? <DynamicIcon name={def.icon} size={14} /> : null}
                        <span className="ml-1">{def.label}</span>
                      </button>
                    );
                  })}

                {/* Separator + destructive actions */}
                {effective.some((a) => getActionDefinition(a)?.destructive) ? (
                  <div className="my-1 h-px bg-slate-100 dark:bg-white/5" />
                ) : null}

                {effective
                  .filter((a) => getActionDefinition(a)?.destructive)
                  .map((action: string) => {
                    const def = getActionDefinition(action)!;
                    const disabled = !hasActionHandler(action) && !onAction;
                    return (
                      <button
                        key={action}
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
                          'w-full text-left px-3 py-2 flex items-center gap-2',
                          disabled ? 'opacity-50 text-slate-400' : 'hover:bg-surface-hover',
                        )}
                        style={{ color: disabled ? undefined : '#dc2626' }}
                      >
                        {def.icon ? <DynamicIcon name={def.icon} size={14} /> : null}
                        <span className="ml-1">{def.label}</span>
                      </button>
                    );
                  })}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {hasChildren && isExpanded ? (
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
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export const GenericTree = memo(GenericTreeComponent);
export default GenericTree;
