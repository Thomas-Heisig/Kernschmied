import type { ComponentProps } from 'react';

import { DocumentationDialog } from '../components/documentation';
import { AppContextSidebar, AppHierarchySidebar, AppLayout } from '../components/layout';
import { SettingsDialog } from '../components/settings';
import { SelectedNodeWorkspace } from '../components/workspace';

type HierarchySidebarProps = ComponentProps<typeof AppHierarchySidebar>;
type ContextSidebarProps = ComponentProps<typeof AppContextSidebar>;
type LayoutProps = ComponentProps<typeof AppLayout>;

interface AppWorkspaceProps {
  schema: HierarchySidebarProps['schema'];
  root: HierarchySidebarProps['root'];
  selectedNode: ContextSidebarProps['node'];
  selectedNodeId: HierarchySidebarProps['selectedNodeId'];
  expandedNodeIds: HierarchySidebarProps['expandedNodeIds'];
  theme: LayoutProps['theme'];
  applicationVersion?: string;
  environment?: string;
  userName?: string;
  isSettingsOpen: boolean;
  isDocumentationOpen: boolean;
  onSelectNode: HierarchySidebarProps['onSelect'];
  onExpandedNodeIdsChange: HierarchySidebarProps['onExpandedNodeIdsChange'];
  onToggleTheme: LayoutProps['onToggleTheme'];
  onOpenSettings: () => void;
  onCloseSettings: () => void;
  onOpenDocumentation: () => void;
  onCloseDocumentation: () => void;
  onCreateHierarchyNode?: (parentId: string) => Promise<void>;
  onMoveHierarchyNode?: (
    id: string,
    newParentId: string | null,
    position?: number | null,
  ) => Promise<void>;
  onUpdateHierarchyNode?: (id: string, payload: unknown) => Promise<void>;
  onDeleteHierarchyNode?: (id: string) => Promise<void>;
  isHierarchyBusy?: boolean;
  recentlyMovedNodeId?: string | null;
  onAction?: (action: string, node: any) => void;
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
  isDocumentationOpen,
  onSelectNode,
  onExpandedNodeIdsChange,
  onToggleTheme,
  onOpenSettings,
  onCloseSettings,
  onOpenDocumentation,
  onCloseDocumentation,
  onCreateHierarchyNode,
  onMoveHierarchyNode,
  onUpdateHierarchyNode,
  onDeleteHierarchyNode,
  onAction,
  isHierarchyBusy,
  recentlyMovedNodeId,
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
        onOpenDocumentation={onOpenDocumentation}
        hierarchySidebar={
          <AppHierarchySidebar
            root={root}
            schema={schema}
            selectedNodeId={selectedNodeId}
            expandedNodeIds={expandedNodeIds}
            onSelect={onSelectNode}
            onExpandedNodeIdsChange={onExpandedNodeIdsChange}
            onCreateChat={(id) => {
              void onCreateHierarchyNode?.(id);
            }}
            onNodeDrop={(sourceId, targetId, dropInfo) => {
              // If dropInfo.position is provided, forward it as the insertion index
              if (dropInfo && typeof dropInfo.position === 'number') {
                void onMoveHierarchyNode?.(sourceId, dropInfo.parentId ?? null, dropInfo.position);
              } else if (dropInfo) {
                // append as child
                void onMoveHierarchyNode?.(sourceId, dropInfo.parentId ?? null);
              } else {
                void onMoveHierarchyNode?.(sourceId, targetId);
              }
            }}
            isBusy={isHierarchyBusy}
            onAction={onAction}
            recentlyMovedNodeId={recentlyMovedNodeId}
          />
        }
        contextSidebar={
          <AppContextSidebar node={selectedNode} schemaVersion={schema.schema_version} />
        }
      >
        <SelectedNodeWorkspace node={selectedNode} schema={schema} />
      </AppLayout>
      <SettingsDialog isOpen={isSettingsOpen} onClose={onCloseSettings} />
      <DocumentationDialog isOpen={isDocumentationOpen} onClose={onCloseDocumentation} />
    </>
  );
}
