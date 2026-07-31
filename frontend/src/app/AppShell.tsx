import { useCallback, useState } from "react";

import { AppErrorScreen } from "../components/errors";
import { AppLoadingScreen } from "../components/status";
import {
  selectExpandedNodeIds,
  selectHierarchyRoot,
  selectSelectedNode,
  selectSelectedNodeId,
} from "../store";
import { useTheme } from "../theme";
import { AppWorkspace } from "./AppWorkspace";
import { useAppBootstrap } from "./useAppBootstrap";

export function AppShell() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDocumentationOpen, setIsDocumentationOpen] = useState(false);

  const {
    state,
    reloadApplication,
    selectHierarchyNode,
    replaceExpandedNodeIds,
  } = useAppBootstrap();

  const { theme, toggleTheme } = useTheme();

  const handleOpenSettings = useCallback((): void => {
    setIsSettingsOpen(true);
  }, []);

  const handleCloseSettings = useCallback((): void => {
    setIsSettingsOpen(false);
  }, []);

  const handleOpenDocumentation = useCallback((): void => {
    setIsDocumentationOpen(true);
  }, []);

  const handleCloseDocumentation = useCallback((): void => {
    setIsDocumentationOpen(false);
  }, []);

  if (state.status === "idle" || state.status === "loading") {
    return <AppLoadingScreen />;
  }

  if (state.status === "error") {
    return (
      <AppErrorScreen
        message={
          state.error?.message ?? "Die Anwendung konnte nicht geladen werden."
        }
        requestId={state.error?.requestId}
        onRetry={reloadApplication}
      />
    );
  }

  const schema = state.schema;
  const root = selectHierarchyRoot(state);

  if (!schema || !root) {
    return (
      <AppErrorScreen
        message="Das UI-Schema oder die Hierarchie ist nicht verfügbar."
        onRetry={reloadApplication}
      />
    );
  }

  const selectedHierarchyNode = selectSelectedNode(state);
  const selectedNode = selectedHierarchyNode
    ? {
        id: selectedHierarchyNode.id,
        name: selectedHierarchyNode.name,
        type: selectedHierarchyNode.type,
      }
    : null;

  return (
    <AppWorkspace
      schema={schema}
      root={root}
      selectedNode={selectedNode}
      selectedNodeId={selectSelectedNodeId(state)}
      expandedNodeIds={selectExpandedNodeIds(state)}
      theme={theme}
      isSettingsOpen={isSettingsOpen}
      isDocumentationOpen={isDocumentationOpen}
      onSelectNode={selectHierarchyNode}
      onExpandedNodeIdsChange={replaceExpandedNodeIds}
      onToggleTheme={toggleTheme}
      onOpenSettings={handleOpenSettings}
      onCloseSettings={handleCloseSettings}
      onOpenDocumentation={handleOpenDocumentation}
      onCloseDocumentation={handleCloseDocumentation}
    />
  );
}
