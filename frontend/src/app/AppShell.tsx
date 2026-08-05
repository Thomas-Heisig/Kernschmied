import { useCallback, useState, useEffect } from 'react';
import { useRef } from 'react';

import { AppErrorScreen } from '../components/errors';
import { Toaster } from 'sonner';
import { AppLoadingScreen } from '../components/status';
import { ToastProvider, useToast } from '../components/ui/ToastProvider';
import HierarchyActionModal from '../components/ui/HierarchyActionModal';
import { SettingsDialog } from '../components/settings';
import { DocumentationDialog } from '../components/documentation';
import React from 'react';
const CalendarPanel = React.lazy(() => import('../components/calendar/CalendarPanel'));
import AuthProvider, { useAuth } from '../auth/AuthProvider';
import UserAccountPanelsProvider from '../auth/UserAccountPanels';
import LoginPage from '../auth/LoginPage';
import RegisterPage from '../auth/RegisterPage';
import {
  selectExpandedNodeIds,
  selectHierarchyRoot,
  selectSelectedNode,
  selectSelectedNodeId,
} from '../store';
import type { HierarchyNode, HierarchyTree, HierarchyActionKind } from '../contracts/hierarchy';
import { SYSTEM_ROOT_NODE_ID } from '../contracts/hierarchy';
import { useTheme } from '../theme';
import { AppWorkspace } from './AppWorkspace';
import { useAppBootstrap } from './useAppBootstrap';
import { useAppStoreCommands, useAppStoreState } from '../store';
import { useAppSchema } from '../hooks/useAppSchema';
import { useBootstrap } from '../hooks/useBootstrap';
import { useMemo } from 'react';

export function AppShell() {
  const bootstrapHook = useBootstrap();

  // Memoize the specific bootstrap parts passed to AuthProvider so it doesn't
  // receive a new object on every render and cause effects to re-run.
  const authBootstrap = useMemo(() => {
    const b = bootstrapHook.bootstrap;
    if (!b) return null;
    return {
      endpoints: b.endpoints ?? {},
      security: b.security ?? {},
      features: b.features ?? {},
    } as any;
  }, [bootstrapHook.bootstrap]);

  return (
    <ToastProvider>
      <Toaster position="bottom-right" />
      <AuthProvider bootstrap={authBootstrap}>
        <UserAccountPanelsProvider>
          <AppShellContent bootstrapHook={bootstrapHook} />
        </UserAccountPanelsProvider>
      </AuthProvider>
    </ToastProvider>
  );
}

function AppShellContent({ bootstrapHook }: { bootstrapHook: ReturnType<typeof useBootstrap> }) {
  const auth = useAuth();
  // Use the single bootstrap hook passed from parent
  const { bootstrap, status: bootstrapStatus, error: bootstrapError } = bootstrapHook;

  // Hooks must be called unconditionally and in the same order on every render.
  // Declare all hooks up-front before any early returns.
  const [authView, setAuthView] = useState<'login' | 'register'>('login');

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDocumentationOpen, setIsDocumentationOpen] = useState(false);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  // Request schema/hierarchy only when authenticated. Hook handles single-load semantics.
  const schemaHook = useAppSchema(auth.status === 'authenticated', bootstrap ?? null);

  const { schema: loadedSchema, hierarchy: loadedHierarchy, hierarchyTree: loadedHierarchyTree, status: schemaStatus, error: schemaError, isLoading, isReady, reload, reloadHierarchy } = schemaHook;

  const state = useAppStoreState();
  const { beginLoading, setLoadedData, setError } = useAppStoreCommands();

  const appBootstrap = useAppBootstrap({ bootstrap: bootstrap ?? null, reload: reload, reloadHierarchy: reloadHierarchy });

  const {
    reloadApplication,
    selectHierarchyNode,
    replaceExpandedNodeIds,
    createHierarchyNode,
    updateHierarchyNode,
    moveHierarchyNode,
    deleteHierarchyNode,
  } = appBootstrap;

  useEffect(() => {
    if (isLoading) {
      beginLoading();
    }
  }, [isLoading, beginLoading]);

  useEffect(() => {
    if (loadedSchema && loadedHierarchyTree) {
      setLoadedData(loadedSchema, loadedHierarchyTree as any);
    }
  }, [loadedSchema, loadedHierarchyTree, setLoadedData]);

  useEffect(() => {
    if (schemaStatus === 'error' && schemaError) {
      setError(schemaError);
    }
  }, [schemaStatus, schemaError, setError]);

  const { theme, toggleTheme } = useTheme();

  const { push } = useToast();
  const { replaceHierarchy } = useAppStoreCommands();

  // Modal state for hierarchy actions (declare hooks early to preserve Hooks order)
  const [modalOpen, setModalOpen] = useState(false);
  const [modalKind, setModalKind] = useState<HierarchyActionKind | null>(null);
  const [modalNode, setModalNode] = useState<HierarchyNode | null>(null);
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

  const handleOpenCalendar = useCallback((): void => {
    setIsCalendarOpen(true);
  }, []);

  const handleCloseDocumentation = useCallback((): void => {
    setIsDocumentationOpen(false);
  }, []);

  // Single debug output for startup state
  console.debug("[Kernschmied startup state]", {
    bootstrapStatus,
    authStatus: auth.status,
    schemaStatus,
    bootstrapReady: !!bootstrap,
    authReady: auth.status === 'authenticated' && !!auth.user,
    schemaReady: isReady,
    bootstrapError: bootstrapError?.message ?? null,
    authError: auth.error ?? null,
    schemaError: schemaError?.message ?? null,
  });

  // Auth state machine handling (render short-circuit cases after hooks)
  // Bootstrap load state must be honored first
  if (bootstrapStatus === 'loading' || (!bootstrap && bootstrapStatus !== 'error')) {
    return <AppLoadingScreen />;
  }

  if (bootstrapStatus === 'error') {
    return (
      <AppErrorScreen
        message={bootstrapError?.message ?? 'Bootstrap konnte nicht geladen werden.'}
        onRetry={() => void bootstrapHook.reloadBootstrap?.()}
      />
    );
  }
  if (auth.status === 'checking') {
    return <AppLoadingScreen />;
  }

  if (auth.status === 'unauthenticated') {
    return authView === 'login' ? (
      <LoginPage onSuccess={() => void auth.reload()} onRegister={() => setAuthView('register')} />
    ) : (
      <RegisterPage onSuccess={() => void auth.reload()} />
    );
  }

  if (auth.status === 'error') {
    return (
      <AppErrorScreen
        message={auth.error ?? 'Verbindung zum Kernschmied-Backend fehlgeschlagen.'}
        onRetry={() => void auth.reload()}
      />
    );
  }

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

  function openModalFor(action: HierarchyActionKind, node: HierarchyNode) {
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
      const optimistic = moveNodeInTree(prev as HierarchyTree, id, newParentId, position ?? null);
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

  const handleCreatePublicWorkspace = async () => {
    setIsMutating(true);
    try {
      const name = 'Public';
      await createHierarchyNode?.({
        type: 'workspace',
        name,
        parent_id: root.id ?? null,
        metadata: { access: 'public', owner: 'Thomas Heisig' },
      } as any);
      push('success', `Public-Bereich '${name}' erstellt.`);
    } catch (err: unknown) {
      push('error', err instanceof Error ? err.message : 'Fehler beim Erstellen des Public-Bereichs');
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateInternWorkspace = async () => {
    setIsMutating(true);
    try {
      const name = 'Intern';
      await createHierarchyNode?.({
        type: 'workspace',
        name,
        parent_id: root.id ?? null,
        metadata: { access: 'intern', owner: 'Thomas Heisig' },
      } as any);
      push('success', `Interner Bereich '${name}' erstellt.`);
    } catch (err: unknown) {
      push('error', err instanceof Error ? err.message : 'Fehler beim Erstellen des internen Bereichs');
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateUser = async () => {
    setIsMutating(true);
    try {
      const name = 'Neuer Benutzer';
      await createHierarchyNode?.({
        type: 'user',
        name: name.trim() || 'Neuer Benutzer',
        // Always create users under the stable system root. Backend enforces admin check.
        parent_id: SYSTEM_ROOT_NODE_ID,
        metadata: {},
      } as any);
      push('success', `Benutzer '${name}' erstellt.`);
    } catch (err: unknown) {
      push('error', err instanceof Error ? err.message : 'Fehler beim Erstellen des Benutzers');
    } finally {
      setIsMutating(false);
    }
  };

  function chooseChildTypeForParent(parentType: string | undefined) {
    const t = parentType ? String(parentType).trim().toLowerCase() : '';

    // Map common parent types to preferred child types
    const mapping: Record<string, { type: string; defaultName: string }> = {
      // Benutzer / user -> Bereich / workspace
      benutzer: { type: 'workspace', defaultName: 'Neuer Bereich' },
      user: { type: 'workspace', defaultName: 'Neuer Bereich' },

      // Bereich / workspace / area -> Projekt
      bereich: { type: 'project', defaultName: 'Neues Projekt' },
      workspace: { type: 'project', defaultName: 'Neues Projekt' },
      area: { type: 'project', defaultName: 'Neues Projekt' },

      // Projekt / project -> chat
      projekt: { type: 'chat', defaultName: 'Neuer Chat' },
      project: { type: 'chat', defaultName: 'Neuer Chat' },
    };

    return mapping[t] ?? { type: 'chat', defaultName: 'Neues Unterelement' };
  }

  function moveNodeInTree(
    hierarchy: HierarchyTree,
    nodeId: string,
    newParentId: string | null,
    insertPosition: number | null = null,
  ) {
    const clone = JSON.parse(JSON.stringify(hierarchy)) as HierarchyTree;

    // Find and remove node
    let nodeToMove: HierarchyNode | null = null;

    function removeNode(parent: HierarchyNode) {
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

    function insertInto(parent: HierarchyNode): boolean {
      if (parent.id === newParentId) {
        parent.children = parent.children || [];
        if (insertPosition === null) parent.children.push(nodeToMove as HierarchyNode);
        else
          parent.children.splice(
            Math.max(0, Math.min(parent.children.length, insertPosition)),
            0,
            nodeToMove as HierarchyNode,
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
          selectedHierarchyNode={selectedHierarchyNode}
          selectedNode={selectedNode}
        selectedNodeId={selectSelectedNodeId(state)}
        expandedNodeIds={selectExpandedNodeIds(state)}
        theme={theme}
        isSettingsOpen={isSettingsOpen}
        isDocumentationOpen={isDocumentationOpen}
        onSelectNode={selectHierarchyNode}
        onExpandedNodeIdsChange={replaceExpandedNodeIds}
        onCreateHierarchyNode={createHierarchyNode}
        onCreatePublicWorkspace={handleCreatePublicWorkspace}
        onCreateInternWorkspace={handleCreateInternWorkspace}
        onCreateUser={handleCreateUser}
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
        onOpenCalendar={handleOpenCalendar}
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
              case 'create_child':
              case 'create_child':
                case 'create_chat': {
                // Determine the child type and default name based on parent type
                const chosen = chooseChildTypeForParent((modalNode as any)?.type);
                const childType = modalKind === 'create_chat' ? 'chat' : chosen.type;
                const defaultName = modalKind === 'create_chat' ? 'Neuer Chat' : chosen.defaultName;
                const name = value ?? defaultName;

                // inherit access/owner from parent when creating children
                const inheritedMetadata = {
                  ...(modalNode.metadata ?? {}),
                } as Record<string, unknown>;

                await createHierarchyNode?.({
                  type: childType,
                  name,
                  parent_id: modalNode.id ?? null,
                  system_prompt:
                    (modalNode as any)?.system_prompt ?? (modalNode as any)?.metadata?.prompt ??
                    undefined,
                  tool_policy: {},
                  config_overrides: {},
                  metadata: inheritedMetadata,
                } as any);
                push('success', `${childType === 'chat' ? 'Chat' : 'Unterelement'} '${name}' erstellt.`);
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
      {isCalendarOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setIsCalendarOpen(false)} />
          <div className="relative z-50 w-[90%] max-w-4xl rounded bg-white p-4 dark:bg-slate-900">
            {/* Lazy load panel to keep bundle small */}
            <React.Suspense fallback={<div>Loading...</div>}>
              <CalendarPanel onClose={() => setIsCalendarOpen(false)} />
            </React.Suspense>
          </div>
        </div>
      )}
    </>
  );
}
