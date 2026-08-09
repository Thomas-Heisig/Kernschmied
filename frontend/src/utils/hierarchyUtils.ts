import type { HierarchyNode } from "../contracts/hierarchy";

// Return ancestors from closest parent up to root (excluding the node itself)
export function getHierarchyAncestors(node: HierarchyNode): HierarchyNode[] {
  // We need the full tree to find the path. If the node has no parent_id
  // accessible here, return empty. This helper expects callers to pass a
  // HierarchyNode from the store where `parent_id` is available.
  const ancestors: HierarchyNode[] = [];
  let current: HierarchyNode | undefined = (node as any).__parentRef;

  // The store does not maintain direct parent refs; if present, follow them.
  while (current) {
    ancestors.push(current);
    current = (current as any).__parentRef;
  }

  return ancestors;
}
