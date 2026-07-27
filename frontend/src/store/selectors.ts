// F:\Kernschmied\frontend\src\store\selectors.ts

import type { HierarchyNode } from "../contracts/hierarchy";
import type { NodeTypeDefinition } from "../contracts/schema";
import type { AppStoreState } from "./AppStore";

export function selectSchema(
  state: AppStoreState,
) {
  return state.schema;
}

export function selectHierarchyTree(
  state: AppStoreState,
) {
  return state.hierarchyTree;
}

export function selectHierarchyRoot(
  state: AppStoreState,
): HierarchyNode | null {
  return state.hierarchyTree?.root ?? null;
}

export function selectSelectedNodeId(
  state: AppStoreState,
): string | null {
  return state.selectedNodeId;
}

export function selectSelectedNode(
  state: AppStoreState,
): HierarchyNode | null {
  const root = selectHierarchyRoot(state);

  if (!root || !state.selectedNodeId) {
    return null;
  }

  return findHierarchyNode(
    root,
    state.selectedNodeId,
  );
}

export function selectSelectedNodeTypeDefinition(
  state: AppStoreState,
): NodeTypeDefinition | null {
  const schema = state.schema;
  const node = selectSelectedNode(state);

  if (!schema || !node) {
    return null;
  }

  return schema.node_types[node.type] ?? null;
}

export function selectExpandedNodeIds(
  state: AppStoreState,
): ReadonlySet<string> {
  return state.expandedNodeIds;
}

export function selectAppIsReady(
  state: AppStoreState,
): boolean {
  return (
    state.status === "ready" &&
    state.schema !== null &&
    state.hierarchyTree !== null
  );
}

export function selectAppIsLoading(
  state: AppStoreState,
): boolean {
  return state.status === "loading";
}

export function selectSchemaRevision(
  state: AppStoreState,
): number | null {
  return state.schema?.revision ?? null;
}

export function selectHierarchyRevision(
  state: AppStoreState,
): number | null {
  return state.hierarchyTree?.revision ?? null;
}

export function findHierarchyNode(
  root: HierarchyNode,
  nodeId: string,
): HierarchyNode | null {
  const stack: HierarchyNode[] = [root];
  const visitedNodeIds = new Set<string>();

  while (stack.length > 0) {
    const node = stack.pop();

    if (!node || visitedNodeIds.has(node.id)) {
      continue;
    }

    if (node.id === nodeId) {
      return node;
    }

    visitedNodeIds.add(node.id);

    for (
      let index = node.children.length - 1;
      index >= 0;
      index -= 1
    ) {
      const child = node.children[index];

      if (child) {
        stack.push(child);
      }
    }
  }

  return null;
}

export function findHierarchyPath(
  root: HierarchyNode,
  nodeId: string,
): HierarchyNode[] {
  const stack: Array<{
    node: HierarchyNode;
    path: HierarchyNode[];
  }> = [
    {
      node: root,
      path: [],
    },
  ];

  const visitedNodeIds = new Set<string>();

  while (stack.length > 0) {
    const entry = stack.pop();

    if (
      !entry ||
      visitedNodeIds.has(entry.node.id)
    ) {
      continue;
    }

    const currentPath = [
      ...entry.path,
      entry.node,
    ];

    if (entry.node.id === nodeId) {
      return currentPath;
    }

    visitedNodeIds.add(entry.node.id);

    for (
      let index = entry.node.children.length - 1;
      index >= 0;
      index -= 1
    ) {
      const child = entry.node.children[index];

      if (child) {
        stack.push({
          node: child,
          path: currentPath,
        });
      }
    }
  }

  return [];
}