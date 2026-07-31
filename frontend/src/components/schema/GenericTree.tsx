// F:\Kernschmied\frontend\src\components\schema\GenericTree.tsx

import {
  memo,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import type { HierarchyNode } from "../../contracts/hierarchy";
import type { UISchema } from "../../contracts/schema";
import { isKnownActionKind } from "../../registry/actionRegistry";
import { DynamicIcon } from "../../registry/iconRegistry";

const DEFAULT_NODE_ICON = "Circle";
const UNKNOWN_NODE_ICON = "CircleHelp";

const DEFAULT_VISIBLE_ACTION_COUNT = 2;
const INDENT_SIZE_PX = 16;
const BASE_INDENT_PX = 8;

// Hilfsfunktion: Prüft, ob ein Wert ein Objekt ist (und nicht null/Array)
function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export interface GenericTreeProps {
  root: HierarchyNode;
  schema: UISchema;
  onSelect: (node: HierarchyNode) => void;

  /**
   * Aktuell ausgewählter Knoten.
   */
  selectedNodeId?: string | null;

  /**
   * Wird aufgerufen, wenn eine bekannte Aktion angefordert wird.
   *
   * GenericTree führt Aktionen niemals selbst aus. Die tatsächliche
   * Ausführung und Autorisierung erfolgen außerhalb der Darstellung.
   */
  onAction?: (action: string, node: HierarchyNode) => void;

  /**
   * Wird aufgerufen, wenn für einen Projektknoten ein neuer Chat erstellt werden soll.
   */
  onCreateChat?: (parentNodeId: string) => void;

  /**
   * Kontrollierte Menge aufgeklappter Knoten.
   *
   * Wird dieser Wert nicht übergeben, verwaltet GenericTree den
   * Aufklappzustand intern.
   */
  expandedNodeIds?: ReadonlySet<string>;

  /**
   * Wird aufgerufen, wenn sich der Aufklappzustand ändert.
   */
  onExpandedNodeIdsChange?: (expandedNodeIds: ReadonlySet<string>) => void;

  /**
   * Maximale Anzahl direkt sichtbarer Aktionen je Knoten.
   */
  maxVisibleActions?: number;

  /**
   * Zusätzliche CSS-Klassen für den äußeren Baum.
   */
  className?: string;

  /**
   * Optionaler Renderer für Knotennamen.
   */
  renderLabel?: (node: HierarchyNode) => ReactNode;
}

interface TreeNodeProps {
  node: HierarchyNode;
  schema: UISchema;
  depth: number;
  selectedNodeId: string | null;
  expandedNodeIds: ReadonlySet<string>;
  maxVisibleActions: number;
  onSelect: (node: HierarchyNode) => void;
  onAction?: (action: string, node: HierarchyNode) => void;
  onCreateChat?: (parentNodeId: string) => void;
  onToggleExpanded: (nodeId: string) => void;
  renderLabel?: (node: HierarchyNode) => ReactNode;
}

function joinClassNames(
  ...values: Array<string | false | null | undefined>
): string {
  return values.filter(Boolean).join(" ");
}

function getChildren(node: HierarchyNode): readonly HierarchyNode[] {
  return Array.isArray(node.children) ? node.children : [];
}

function hasChildren(node: HierarchyNode): boolean {
  return getChildren(node).length > 0;
}

function getNodeActions(node: HierarchyNode): readonly string[] {
  return Array.isArray(node.actions) ? node.actions : [];
}

function normalizeVisibleActionCount(value: number | undefined): number {
  if (value === undefined || !Number.isFinite(value)) {
    return DEFAULT_VISIBLE_ACTION_COUNT;
  }

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
}: GenericTreeProps) {
  const [internalExpandedNodeIds, setInternalExpandedNodeIds] = useState<
    Set<string>
  >(() => new Set([root.id]));

  const isControlled = expandedNodeIds !== undefined;

  const effectiveExpandedNodeIds = expandedNodeIds ?? internalExpandedNodeIds;

  const visibleActionCount = useMemo(
    () => normalizeVisibleActionCount(maxVisibleActions),
    [maxVisibleActions],
  );

  useEffect(() => {
    if (isControlled) {
      return;
    }

    setInternalExpandedNodeIds((currentExpandedNodeIds) => {
      if (currentExpandedNodeIds.has(root.id)) {
        return currentExpandedNodeIds;
      }

      return new Set([root.id]);
    });
  }, [isControlled, root.id]);

  const handleToggleExpanded = useCallback(
    (nodeId: string) => {
      const nextExpandedNodeIds = new Set(effectiveExpandedNodeIds);

      if (nextExpandedNodeIds.has(nodeId)) {
        nextExpandedNodeIds.delete(nodeId);
      } else {
        nextExpandedNodeIds.add(nodeId);
      }

      if (!isControlled) {
        setInternalExpandedNodeIds(nextExpandedNodeIds);
      }

      onExpandedNodeIdsChange?.(nextExpandedNodeIds);
    },
    [effectiveExpandedNodeIds, isControlled, onExpandedNodeIdsChange],
  );

  return (
    <div
      className={joinClassNames("min-w-0", className)}
      role="tree"
      aria-label="Anwendungshierarchie"
    >
      <TreeNode
        node={root}
        schema={schema}
        depth={0}
        selectedNodeId={selectedNodeId}
        expandedNodeIds={effectiveExpandedNodeIds}
        maxVisibleActions={visibleActionCount}
        onSelect={onSelect}
        onAction={onAction}
        onCreateChat={onCreateChat}
        onToggleExpanded={handleToggleExpanded}
        renderLabel={renderLabel}
      />
    </div>
  );
}

function TreeNodeComponent({
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
}: TreeNodeProps) {
  const nodeDefinitionRaw = schema.node_types[node.type];

  // Sicherstellen, dass nodeDefinitionRaw ein Objekt ist
  const nodeDefinition = isPlainObject(nodeDefinitionRaw)
    ? nodeDefinitionRaw
    : undefined;

  const children = useMemo(() => getChildren(node), [node]);

  const nodeHasChildren = children.length > 0;

  const isExpanded = nodeHasChildren && expandedNodeIds.has(node.id);

  const isSelected = selectedNodeId === node.id;

  const isKnownNodeType = nodeDefinition !== undefined;

  const knownActions = useMemo(() => {
    if (!onAction) {
      return [];
    }

    return getNodeActions(node)
      .filter(isKnownActionKind)
      .slice(0, maxVisibleActions);
  }, [maxVisibleActions, node, onAction]);

  const handleSelect = useCallback(() => {
    onSelect(node);
  }, [node, onSelect]);

  const handleToggle = useCallback(() => {
    if (!nodeHasChildren) {
      return;
    }

    onToggleExpanded(node.id);
  }, [node.id, nodeHasChildren, onToggleExpanded]);

  const handleSelectKeyDown = useCallback(
    (event: KeyboardEvent<HTMLButtonElement>) => {
      if (event.key === "ArrowRight") {
        event.preventDefault();

        if (nodeHasChildren && !isExpanded) {
          onToggleExpanded(node.id);
        }

        return;
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();

        if (nodeHasChildren && isExpanded) {
          onToggleExpanded(node.id);
        }

        return;
      }

      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        onSelect(node);
      }
    },
    [isExpanded, node, nodeHasChildren, onSelect, onToggleExpanded],
  );

  const renderedLabel = renderLabel ? renderLabel(node) : node.name;

  // Sichere Extraktion von icon und color
  const iconName = isPlainObject(nodeDefinition?.icon)
    ? undefined
    : typeof nodeDefinition?.icon === "string"
      ? nodeDefinition.icon
      : undefined;

  const color =
    typeof nodeDefinition?.color === "string"
      ? nodeDefinition.color
      : undefined;

  // Prüfen, ob der Knoten ein Projekt ist (für "Neuer Chat"-Button)
  const isProject = node.type === "project";

  return (
    <div
      role="treeitem"
      aria-level={depth + 1}
      aria-selected={isSelected}
      aria-expanded={nodeHasChildren ? isExpanded : undefined}
    >
      <div
        className={joinClassNames(
          "group flex min-w-0 items-center gap-1 rounded-md",
          "px-2 py-1 transition-colors duration-fast",
          // Selektion
          isSelected
            ? "bg-primary-soft text-text dark:bg-primary/20 dark:text-white"
            : "text-text-soft hover:bg-surface-hover dark:text-gray-300 dark:hover:bg-slate-800/60",
        )}
        style={{
          paddingLeft: BASE_INDENT_PX + depth * INDENT_SIZE_PX,
        }}
      >
        {/* Toggle-Button (Pfeil) */}
        <button
          type="button"
          className={joinClassNames(
            "flex h-6 w-6 shrink-0 items-center justify-center",
            "rounded text-text-muted dark:text-gray-500",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
            nodeHasChildren
              ? "hover:bg-surface-hover hover:text-text dark:hover:bg-slate-700/60 dark:hover:text-white"
              : "pointer-events-none opacity-0",
          )}
          onClick={handleToggle}
          tabIndex={nodeHasChildren ? 0 : -1}
          aria-label={
            nodeHasChildren
              ? isExpanded
                ? `${node.name} einklappen`
                : `${node.name} ausklappen`
              : undefined
          }
          aria-hidden={!nodeHasChildren}
        >
          <span
            aria-hidden="true"
            className={joinClassNames(
              "text-xs transition-transform duration-fast",
              isExpanded && "rotate-90",
            )}
          >
            ▶
          </span>
        </button>

        {/* Haupt-Button: Icon + Name */}
        <button
          type="button"
          className={joinClassNames(
            "flex min-w-0 flex-1 items-center gap-2",
            "rounded-sm text-left",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1",
          )}
          onClick={handleSelect}
          onKeyDown={handleSelectKeyDown}
          title={
            isKnownNodeType
              ? node.name
              : `${node.name} – unbekannter Knotentyp: ${node.type}`
          }
        >
          <DynamicIcon
            name={
              iconName ??
              (isKnownNodeType ? DEFAULT_NODE_ICON : UNKNOWN_NODE_ICON)
            }
            color={color}
          />

          <span className="min-w-0 flex-1 truncate">{renderedLabel}</span>

          {!isKnownNodeType && (
            <span
              className={joinClassNames(
                "shrink-0 rounded",
                "border border-warning/30",
                "bg-warning-soft px-1.5 py-0.5",
                "text-[10px] font-medium",
                "text-warning",
                "dark:border-warning/20",
                "dark:bg-warning/10",
                "dark:text-warning",
              )}
              title={`Nicht unterstützter Knotentyp: ${node.type}`}
            >
              Nicht unterstützt
            </span>
          )}
        </button>

        {/* "Neuer Chat"-Button für Projektknoten */}
        {isProject && onCreateChat && (
          <button
            type="button"
            className={joinClassNames(
              "shrink-0 rounded",
              "bg-primary px-2 py-1",
              "text-xs font-medium text-white",
              "transition-colors duration-fast",
              "hover:bg-primary-hover",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1",
              "dark:bg-primary/80 dark:hover:bg-primary",
            )}
            onClick={(event) => {
              event.stopPropagation();
              onCreateChat(node.id);
            }}
            aria-label={`Neuen Chat in ${node.name} erstellen`}
            title={`Neuen Chat in ${node.name} erstellen`}
          >
            Neuer Chat
          </button>
        )}

        {/* Aktionen-Buttons (nur bei Hover sichtbar) */}
        {knownActions.length > 0 && (
          <div
            className={joinClassNames(
              "flex shrink-0 items-center gap-1",
              "opacity-0 transition-opacity duration-fast",
              "group-hover:opacity-100",
              "group-focus-within:opacity-100",
            )}
            aria-label={`Aktionen für ${node.name}`}
          >
            {knownActions.map((action) => (
              <button
                key={action}
                type="button"
                className={joinClassNames(
                  "rounded px-1.5 py-1",
                  "text-xs text-text-muted",
                  "hover:bg-surface-hover hover:text-text",
                  "dark:text-gray-400 dark:hover:bg-slate-700/60 dark:hover:text-white",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                )}
                title={action}
                aria-label={`${action}: ${node.name}`}
                onClick={(event) => {
                  event.stopPropagation();

                  onAction?.(action, node);
                }}
              >
                {action}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Kinder (rekursiv) */}
      {nodeHasChildren && isExpanded && (
        <div role="group">
          {children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
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
            />
          ))}
        </div>
      )}
    </div>
  );
}

const TreeNode = memo(TreeNodeComponent);

export const GenericTree = memo(GenericTreeComponent);
