import type { ComponentProps } from 'react';
import type { HierarchyNode } from '../contracts/hierarchy';

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
  bootstrap?: any | null;
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
  canPerformAction?: (action: string, node: any) => Promise<boolean> | boolean;
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
  bootstrap,
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
  canPerformAction,
  isHierarchyBusy,
  recentlyMovedNodeId,
}: AppWorkspaceProps) {
  function findPath(root: HierarchyNode | null | undefined, targetId: string | null | undefined): Array<{ id: string; name: string }> | null {
    if (!root || !targetId) return null;
    const path: Array<{ id: string; name: string }> = [];

    function dfs(node: HierarchyNode): boolean {
      path.push({ id: node.id, name: node.name });
      if (node.id === targetId) return true;
      if (node.children) {
        for (const c of node.children) {
          if (dfs(c)) return true;
        }
      }
      path.pop();
      return false;
    }

    // root may not be a HierarchyNode type here; coerce
    try {
      if ((root as any).id) {
        if (dfs(root as unknown as HierarchyNode)) return path;
      }
    } catch {
      return null;
    }

    return null;
  }

  const breadcrumbPath = selectedHierarchyNode ? findPath(root as any, selectedHierarchyNode.id) : null;
  function findNodeById(root: HierarchyNode | null | undefined, id: string | null | undefined): HierarchyNode | null {
    if (!root || !id) return null;

    function dfs(node: HierarchyNode): HierarchyNode | null {
      if (node.id === id) return node;
      if (node.children) {
        for (const c of node.children) {
          const res = dfs(c);
          if (res) return res;
        }
      }
      return null;
    }

    try {
      return dfs(root as HierarchyNode);
    } catch {
      return null;
    }
  }
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
          <AppContextSidebar
            node={selectedNode}
            schemaVersion={schema.schema_version}
            onAction={onAction}
            canPerformAction={canPerformAction}
            path={breadcrumbPath ?? undefined}
            onNavigateToNode={(id: string) => {
              const n = findNodeById(root as any, id);
              if (n) onSelectNode(n);
            }}
            systemInfo={bootstrap ?? undefined}
          />
        }
      >
        <SelectedNodeWorkspace
          node={selectedHierarchyNode ?? selectedNode}
          schema={schema}
          onUpdateHierarchyNode={onUpdateHierarchyNode}
        />
      </AppLayout>
      {isSettingsOpen ? (
        <SettingsDialog isOpen={isSettingsOpen} onClose={onCloseSettings} />
      ) : null}
      <DocumentationDialog isOpen={isDocumentationOpen} onClose={onCloseDocumentation} />
    </>
  );
}
