import { useCallback, useEffect } from 'react';

import { useAppSchema } from '../hooks/useAppSchema';
import { useAppStoreCommands, useAppStoreState } from '../store';

export function useAppBootstrap() {
  const { schema, hierarchyTree, error, isLoading, reload, reloadHierarchy } = useAppSchema();

  const state = useAppStoreState();

  const { beginLoading, setLoadedData, setError, selectHierarchyNode, replaceExpandedNodeIds } =
    useAppStoreCommands();

  // Hierarchie-Mutationen
  const createHierarchyNode = useCallback(
    async (payload: unknown) => {
      const { createHierarchyNode: apiCreate } = await import('../api/hierarchy');
      await apiCreate(payload as any);
      void reloadHierarchy();
    },
    [reloadHierarchy],
  );

  const updateHierarchyNode = useCallback(
    async (id: string, payload: unknown) => {
      const { updateHierarchyNode: apiUpdate } = await import('../api/hierarchy');
      await apiUpdate(id, payload as any);
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

    setLoadedData(schema, hierarchyTree);
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
