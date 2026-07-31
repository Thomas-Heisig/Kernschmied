import { useCallback, useEffect } from "react";

import { useAppSchema } from "../hooks/useAppSchema";
import { useAppStoreCommands, useAppStoreState } from "../store";

export function useAppBootstrap() {
  const { schema, hierarchyTree, error, isLoading, reload } = useAppSchema();

  const state = useAppStoreState();

  const {
    beginLoading,
    setLoadedData,
    setError,
    selectHierarchyNode,
    replaceExpandedNodeIds,
  } = useAppStoreCommands();

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
  };
}
