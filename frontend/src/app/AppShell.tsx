import { useCallback, useState } from 'react';
import { useAppStoreCommands } from '../store';

import { AppErrorScreen } from '../components/errors';
import { AppLoadingScreen } from '../components/status';
import { ToastProvider, useToast } from '../components/ui/ToastProvider';
import HierarchyActionModal from '../components/ui/HierarchyActionModal';
import { SettingsDialog } from '../components/settings';
import { DocumentationDialog } from '../components/documentation';
import {
  selectExpandedNodeIds,
  selectHierarchyRoot,
  selectSelectedNode,
  selectSelectedNodeId,
} from '../store';
import { useTheme } from '../theme';
import { AppWorkspace } from './AppWorkspace';
import { useAppBootstrap } from './useAppBootstrap';

export function AppShell() {
  return (
    <ToastProvider>
      <AppShellContent />
    </ToastProvider>
  );
}

function AppShellContent() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDocumentationOpen, setIsDocumentationOpen] = useState(false);

  const {
    state,
    reloadApplication,
    selectHierarchyNode,
    replaceExpandedNodeIds,
    createHierarchyNode,
    updateHierarchyNode,
    moveHierarchyNode,
    deleteHierarchyNode,
  } = useAppBootstrap();

  const { theme, toggleTheme } = useTheme();

  const { push } = useToast();
  const { replaceHierarchy } = useAppStoreCommands();

  // Modal state for hierarchy actions (declare hooks early to preserve Hooks order)
  const [modalOpen, setModalOpen] = useState(false);
  const [modalKind, setModalKind] = useState<string | null>(null);
  const [modalNode, setModalNode] = useState<any | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [recentlyMovedNodeId, setRecentlyMovedNodeId] = useState<string | null>(null);

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

  if (state.status === 'idle' || state.status === 'loading') {
    return <AppLoadingScreen />;
  }

  if (state.status === 'error') {
    return (
      <AppErrorScreen
        message={state.error?.message ?? 'Die Anwendung konnte nicht geladen werden.'}
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

  function openModalFor(action: string, node: any) {
    setModalKind(action);
    setModalNode(node);
    setModalOpen(true);
  }

  const handleMoveHierarchyNode = async (
    id: string,
    newParentId: string | null,
    position?: number | null,
  ) => {
    setIsMutating(true);

    const prev = state.hierarchyTree;

    if (!prev) {
      setIsMutating(false);
      push('error', 'Keine Hierarchie geladen.');
      return;
    }

    // Build optimistic tree
    try {
      const optimistic = moveNodeInTree(prev, id, newParentId, position ?? null);
      replaceHierarchy(optimistic);
    } catch (err: unknown) {
      // If optimistic transform fails, abort
      push(
        'error',
        err instanceof Error ? err.message : 'Fehler beim Anwenden der lokalen Änderung',
      );
      setIsMutating(false);
      return;
    }

    try {
      await moveHierarchyNode?.(id, newParentId, position ?? null);
      push('success', 'Verschoben.');
      setRecentlyMovedNodeId(id);
      window.setTimeout(() => setRecentlyMovedNodeId(null), 900);
    } catch (err: unknown) {
      // revert
      if (prev) replaceHierarchy(prev);
      push('error', err instanceof Error ? err.message : 'Fehler beim Verschieben');
    } finally {
      setIsMutating(false);
    }
  };

  function moveNodeInTree(
    hierarchy: any,
    nodeId: string,
    newParentId: string | null,
    insertPosition: number | null = null,
  ) {
    const clone = JSON.parse(JSON.stringify(hierarchy));

    // Find and remove node
    let nodeToMove: any = null;

    function removeNode(parent: any) {
      if (!parent.children) return false;
      for (let i = 0; i < parent.children.length; i++) {
        const c = parent.children[i];
        if (c.id === nodeId) {
          nodeToMove = parent.children.splice(i, 1)[0];
          return true;
        }
        if (removeNode(c)) return true;
      }
      return false;
    }

    if (clone.root.id === nodeId) {
      throw new Error('Root-Knoten kann nicht verschoben werden.');
    }

    if (!removeNode(clone.root)) {
      throw new Error('Knoten nicht gefunden.');
    }

    if (!nodeToMove) throw new Error('Knoten konnte nicht entfernt werden.');

    // insert into new parent
    if (newParentId === null) {
      clone.root.children = clone.root.children || [];
      if (insertPosition === null) clone.root.children.push(nodeToMove);
      else
        clone.root.children.splice(
          Math.max(0, Math.min(clone.root.children.length, insertPosition)),
          0,
          nodeToMove,
        );
      return clone;
    }

    function insertInto(parent: any): boolean {
      if (parent.id === newParentId) {
        parent.children = parent.children || [];
        if (insertPosition === null) parent.children.push(nodeToMove);
        else
          parent.children.splice(
            Math.max(0, Math.min(parent.children.length, insertPosition)),
            0,
            nodeToMove,
          );
        return true;
      }
      if (!parent.children) return false;
      for (const c of parent.children) {
        if (insertInto(c)) return true;
      }
      return false;
    }

    if (!insertInto(clone.root)) {
      throw new Error('Ziel-Elternknoten nicht gefunden.');
    }

    return clone;
  }

  return (
    <>
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
        onCreateHierarchyNode={createHierarchyNode}
        onMoveHierarchyNode={handleMoveHierarchyNode}
        isHierarchyBusy={isMutating}
        recentlyMovedNodeId={recentlyMovedNodeId}
        onUpdateHierarchyNode={updateHierarchyNode}
        onDeleteHierarchyNode={deleteHierarchyNode}
        onAction={(action, node) => openModalFor(action, node)}
        onToggleTheme={toggleTheme}
        onOpenSettings={handleOpenSettings}
        onCloseSettings={handleCloseSettings}
        onOpenDocumentation={handleOpenDocumentation}
        onCloseDocumentation={handleCloseDocumentation}
      />

      <HierarchyActionModal
        isOpen={modalOpen}
        kind={modalKind as any}
        node={modalNode}
        loading={isMutating}
        onClose={() => setModalOpen(false)}
        onConfirm={async (value) => {
          if (!modalKind || !modalNode) return setModalOpen(false);
          setIsMutating(true);
          try {
            switch (modalKind) {
              case 'create_chat': {
                const name = value ?? 'Neuer Chat';
                await createHierarchyNode?.({
                  type: 'chat',
                  name,
                  parent_id: modalNode.id ?? null,
                  tool_policy: {},
                  config_overrides: {},
                  metadata: {},
                });
                push('success', `Chat '${name}' erstellt.`);
                break;
              }
              case 'rename': {
                const newName = value ?? modalNode.name;
                await updateHierarchyNode?.(modalNode.id, { name: newName });
                push('success', `'${modalNode.name}' umbenannt in '${newName}'.`);
                break;
              }
              case 'delete': {
                await deleteHierarchyNode?.(modalNode.id);
                push('success', `'${modalNode.name}' wurde gelöscht.`);
                break;
              }
              case 'move': {
                const target = value && value.trim() ? value.trim() : null;
                await moveHierarchyNode?.(modalNode.id, target);
                push('success', `'${modalNode.name}' verschoben.`);
                break;
              }
              case 'edit_prompt': {
                const promptValue = value ?? null;
                // store prompt in metadata.prompt
                const metadata = {
                  ...(modalNode.metadata ?? {}),
                  prompt: promptValue,
                };
                await updateHierarchyNode?.(modalNode.id, { metadata });
                push('success', `Prompt für '${modalNode.name}' gespeichert.`);
                break;
              }
              default:
                break;
            }

            setModalOpen(false);
          } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Fehler bei der Aktion';
            push('error', message);
            setModalOpen(false);
          } finally {
            setIsMutating(false);
          }
        }}
      />

      <SettingsDialog isOpen={isSettingsOpen} onClose={handleCloseSettings} />
      <DocumentationDialog isOpen={isDocumentationOpen} onClose={handleCloseDocumentation} />
    </>
  );
}
