import { useCallback, useEffect } from 'react';

import { useAppSchema } from '../hooks/useAppSchema';
import { useAppStoreCommands, useAppStoreState } from '../store';
import type {
  HierarchyNodeCreate,
  HierarchyNodeUpdate,
  HierarchyTree,
} from '../contracts/hierarchy';

export function useAppBootstrap() {
  const { schema, hierarchyTree, error, isLoading, reload, reloadHierarchy } = useAppSchema();

  const state = useAppStoreState();

  const { beginLoading, setLoadedData, setError, selectHierarchyNode, replaceExpandedNodeIds } =
    useAppStoreCommands();

  // Hierarchie-Mutationen
  const createHierarchyNode = useCallback(
    async (payloadOrParentId: string | (HierarchyNodeCreate & Record<string, unknown>)) => {
      const { createHierarchyNode: apiCreate } = await import('../api/hierarchy');
      let payload: HierarchyNodeCreate;
      if (typeof payloadOrParentId === 'string') {
        // called with parentId only -> create a default chat node
        payload = {
          type: 'chat',
          name: 'Neuer Knoten',
          parent_id: payloadOrParentId || null,
          // default empty policy/config
          tool_policy: {},
          config_overrides: {},
          metadata: {},
        } as unknown as HierarchyNodeCreate;
      } else {
        payload = payloadOrParentId as HierarchyNodeCreate;
      }
      // Create node and ensure UI selects the newly created node after reload.
      const created = await apiCreate(payload as any);
      try {
        await reloadHierarchy();
      } catch {
        // ignore reload errors here – selection may still be useful
      }

      // If the API returned the created node id, select it in the UI state.
      try {
        const id = (created as any)?.id;
        if (id && typeof selectHierarchyNode === 'function') {
          selectHierarchyNode(id);
        }
      } catch {
        // silent fallback
      }
    },
    [reloadHierarchy, selectHierarchyNode],
  );

  const updateHierarchyNode = useCallback(
    async (id: string, payload: unknown) => {
      const { updateHierarchyNode: apiUpdate } = await import('../api/hierarchy');
      await apiUpdate(id, payload as HierarchyNodeUpdate);
      void reloadHierarchy();
    },
    [reloadHierarchy],
  );

  const moveHierarchyNode = useCallback(
    async (id: string, newParentId: string | null, position?: number | null) => {
      if (position === undefined || position === null) {
        const { moveHierarchyNode: apiMove } = await import('../api/hierarchy');
        await apiMove(id, newParentId);
      } else {
        const { reorderHierarchy } = await import('../api/hierarchy');
        await reorderHierarchy([{ id, new_parent_id: newParentId, new_position: position }]);
      }

      void reloadHierarchy();
    },
    [reloadHierarchy],
  );

  const deleteHierarchyNode = useCallback(
    async (id: string) => {
      const { deleteHierarchyNode: apiDelete } = await import('../api/hierarchy');
      await apiDelete(id);
      void reloadHierarchy();
    },
    [reloadHierarchy],
  );

  useEffect(() => {
    if (!isLoading) {
      return;
    }

    beginLoading();
  }, [beginLoading, isLoading]);

  useEffect(() => {
    if (!schema || !hierarchyTree) {
      return;
    }

    setLoadedData(schema, hierarchyTree as HierarchyTree);
  }, [hierarchyTree, schema, setLoadedData]);

  useEffect(() => {
    if (!error) {
      return;
    }

    setError(error);
  }, [error, setError]);

  const reloadApplication = useCallback((): void => {
    void reload();
  }, [reload]);

  return {
    state,
    reloadApplication,
    selectHierarchyNode,
    replaceExpandedNodeIds,
    createHierarchyNode,
    updateHierarchyNode,
    moveHierarchyNode,
    deleteHierarchyNode,
  };
}
