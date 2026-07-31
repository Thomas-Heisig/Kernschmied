import type { ComponentProps } from "react";

import {
  AppContextSidebar,
  AppHierarchySidebar,
  AppLayout,
} from "../components/layout";
import { SettingsDialog } from "../components/settings";
import { SelectedNodeWorkspace } from "../components/workspace";

type HierarchySidebarProps = ComponentProps<typeof AppHierarchySidebar>;

type ContextSidebarProps = ComponentProps<typeof AppContextSidebar>;

type LayoutProps = ComponentProps<typeof AppLayout>;

interface AppWorkspaceProps {
  schema: HierarchySidebarProps["schema"];
  root: HierarchySidebarProps["root"];

  selectedNode: ContextSidebarProps["node"];

  selectedNodeId: HierarchySidebarProps["selectedNodeId"];

  expandedNodeIds: HierarchySidebarProps["expandedNodeIds"];

  theme: LayoutProps["theme"];

  applicationVersion?: string;
  environment?: string;
  userName?: string;

  isSettingsOpen: boolean;

  onSelectNode: HierarchySidebarProps["onSelect"];

  onExpandedNodeIdsChange: HierarchySidebarProps["onExpandedNodeIdsChange"];

  onToggleTheme: LayoutProps["onToggleTheme"];

  onOpenSettings: () => void;
  onCloseSettings: () => void;
}

export function AppWorkspace({
  schema,
  root,
  selectedNode,
  selectedNodeId,
  expandedNodeIds,
  theme,
  applicationVersion,
  environment,
  userName,
  isSettingsOpen,
  onSelectNode,
  onExpandedNodeIdsChange,
  onToggleTheme,
  onOpenSettings,
  onCloseSettings,
}: AppWorkspaceProps) {
  return (
    <>
      <AppLayout
        theme={theme}
        schemaVersion={schema.schema_version}
        applicationVersion={applicationVersion}
        environment={environment}
        userName={userName}
        onToggleTheme={onToggleTheme}
        onOpenSettings={onOpenSettings}
        hierarchySidebar={
          <AppHierarchySidebar
            root={root}
            schema={schema}
            selectedNodeId={selectedNodeId}
            expandedNodeIds={expandedNodeIds}
            onSelect={onSelectNode}
            onExpandedNodeIdsChange={onExpandedNodeIdsChange}
          />
        }
        contextSidebar={
          <AppContextSidebar
            node={selectedNode}
            schemaVersion={schema.schema_version}
          />
        }
      >
        <SelectedNodeWorkspace node={selectedNode} />
      </AppLayout>

      <SettingsDialog isOpen={isSettingsOpen} onClose={onCloseSettings} />
    </>
  );
}
