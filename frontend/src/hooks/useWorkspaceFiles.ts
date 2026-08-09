import { useEffect, useRef, useState } from "react";
import type { WorkspaceFile, FilesListResponse } from "../contracts/workspace-files";
import type { HierarchyNode } from "../contracts/hierarchy";
import { loadWorkspaceFiles } from "../api/workspace-files";
import { useAppStoreState } from "../store/AppStore";

interface UseWorkspaceFilesOptions {
  node?: HierarchyNode | null;
  includeInherited?: boolean;
}

interface UseWorkspaceFilesResult {
  files: WorkspaceFile[];
  isLoading: boolean;
  error: string | null;
  reload: () => Promise<void>;
}

export function useWorkspaceFiles(options: UseWorkspaceFilesOptions): UseWorkspaceFilesResult {
  const { node = null, includeInherited = false } = options;

  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const appState = useAppStoreState();

  const abortRef = useRef<AbortController | null>(null);
  const generationRef = useRef(0);

  async function doLoad(currentGen: number, signal?: AbortSignal) {
    if (!node) return;

    try {
      let ancestors: typeof node[] = [];
      if (includeInherited) {
        const { hierarchyTree } = appState;
        if (hierarchyTree && hierarchyTree.root && node) {
          const path: HierarchyNode[] = [];
          const targetId = node.id;
          function dfs(root: HierarchyNode): boolean {
            if (root.id === targetId) return true;
            for (const c of root.children ?? []) {
              if (dfs(c)) {
                path.push(root);
                return true;
              }
            }
            return false;
          }

          const rootNode = hierarchyTree.root as HierarchyNode;
          dfs(rootNode);
          ancestors = path; // closest parent first
        }
      }

      const res: FilesListResponse = await loadWorkspaceFiles({ node, includeInherited, ancestors, signal });
      if (generationRef.current !== currentGen) return;
      setFiles(res.items ?? []);
      setError(null);
    } catch (err: any) {
      if (err && err.name === "AbortError") return;
      setError(String(err?.message || err));
    } finally {
      if (generationRef.current === currentGen) setLoading(false);
    }
  }

  useEffect(() => {
    generationRef.current += 1;
    const gen = generationRef.current;

    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }

    if (!node) {
      setFiles([]);
      setError(null);
      setLoading(false);
      return;
    }

    const ac = new AbortController();
    abortRef.current = ac;
    setLoading(true);
    setError(null);

    void doLoad(gen, ac.signal);

    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
        abortRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node?.id, includeInherited]);

  const reload = async () => {
    generationRef.current += 1;
    const gen = generationRef.current;
    if (abortRef.current) abortRef.current.abort();
    const ac = new AbortController();
    abortRef.current = ac;
    setLoading(true);
    setError(null);
    await doLoad(gen, ac.signal);
  };

  return { files, isLoading, error, reload };
}
