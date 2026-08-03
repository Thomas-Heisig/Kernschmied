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
  // full hierarchy node (may include metadata) when available
  selectedHierarchyNode?: any | null;
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
  onOpenCalendar?: () => void;
  onCreatePublicWorkspace?: () => void;
  onCreateInternWorkspace?: () => void;
  onCreateUser?: () => void;
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
  selectedHierarchyNode,
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
  onOpenCalendar,
  onCreateHierarchyNode,
  onCreatePublicWorkspace,
  onCreateInternWorkspace,
  onCreateUser,
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
        onOpenCalendar={onOpenCalendar}
      onCreatePublicWorkspace={onCreatePublicWorkspace}
      onCreateInternWorkspace={onCreateInternWorkspace}
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
            onCreatePublicWorkspace={onCreatePublicWorkspace}
            onCreateInternWorkspace={onCreateInternWorkspace}
            onCreateUser={onCreateUser}
          />
        }
        contextSidebar={
          <AppContextSidebar node={selectedNode} schemaVersion={schema.schema_version} />
        }
      >
        <SelectedNodeWorkspace
          node={selectedHierarchyNode ?? selectedNode}
          schema={schema}
          onUpdateHierarchyNode={onUpdateHierarchyNode}
        />
      </AppLayout>
      <SettingsDialog isOpen={isSettingsOpen} onClose={onCloseSettings} />
      <DocumentationDialog isOpen={isDocumentationOpen} onClose={onCloseDocumentation} />
    </>
  );
}
