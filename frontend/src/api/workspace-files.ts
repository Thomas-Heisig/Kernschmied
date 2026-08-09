import type { WorkspaceFile, FilesListResponse } from "../contracts/workspace-files";
import type { HierarchyNode } from "../contracts/hierarchy";
import { createMockWorkspaceFilesForNode, MOCK_WORKSPACE_FILES_BY_NODE } from "../mocks/workspace-files";

export interface LoadWorkspaceFilesOptions {
  node: HierarchyNode;
  includeInherited?: boolean;
  ancestors?: HierarchyNode[];
  signal?: AbortSignal;
}

export const WORKSPACE_FILES_MODE: 'mock' | 'api' = 'mock';

export async function loadWorkspaceFiles(options: LoadWorkspaceFilesOptions): Promise<FilesListResponse> {
  const { node, includeInherited = false, ancestors = [], signal } = options;

  if (WORKSPACE_FILES_MODE === 'api') {
    // future real API call
    return {
      schemaVersion: '1.0',
      nodeId: node.id,
      items: [],
    };
  }

  // mock mode: deterministic generation
  // explicit mapping first
  const explicit = MOCK_WORKSPACE_FILES_BY_NODE[node.id];
  let items: WorkspaceFile[] = explicit ? explicit.map((f) => ({ ...f })) : createMockWorkspaceFilesForNode(node);

  if (includeInherited && Array.isArray(ancestors) && ancestors.length > 0) {
    for (const anc of ancestors) {
      const ancFiles = MOCK_WORKSPACE_FILES_BY_NODE[anc.id] ?? createMockWorkspaceFilesForNode(anc);
      // mark as inherited
      const marked = ancFiles.map((f) => ({ ...f, inherited: true, inheritedFromNodeId: anc.id, inheritedFromNodeName: anc.name }));
      items = items.concat(marked);
    }
  }

  // respect AbortSignal with tiny delay
  await new Promise<void>((resolve, reject) => {
    const t = setTimeout(() => resolve(), 80 + (items.length % 100));
    if (signal) {
      signal.addEventListener('abort', () => {
        clearTimeout(t);
        reject(new DOMException('Aborted', 'AbortError'));
      });
    }
  });

  return {
    schemaVersion: '1.0',
    nodeId: node.id,
    items,
  };
}
