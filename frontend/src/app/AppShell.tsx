// F:\Kernschmied\frontend\src\app\AppShell.tsx

import { useCallback, useState, useEffect, useMemo, useRef } from 'react';
import { LoaderCircle } from 'lucide-react';
import IconBadge from '../components/common/IconBadge';

import { AppErrorScreen } from '../components/errors';
import { AppLoadingScreen } from '../components/status';
import { ToastProvider, useToast } from '../components/ui/ToastProvider';
import Modal from '../components/ui/Modal';
import HierarchyActionModal from '../components/ui/HierarchyActionModal';
import NodeEditorDialog from '../components/hierarchy/NodeEditorDialog';
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
import { USERS_ROOT_NODE_ID, WORKSPACES_ROOT_NODE_ID } from '../contracts/hierarchy';
import { useTheme } from '../theme';
import { AppWorkspace } from './AppWorkspace';
import { useAppBootstrap } from './useAppBootstrap';
import { useAppStoreCommands, useAppStoreState } from '../store';
import { useAppSchema } from '../hooks/useAppSchema';
import { useBootstrap } from '../hooks/useBootstrap';

export function AppShell() {
  const bootstrapHook = useBootstrap();

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
  const isHierarchyAdmin = Boolean(
    auth.user?.developmentSession
    || auth.user?.roles.some((role) => role.toLowerCase() === 'admin'),
  );
  const { bootstrap, status: bootstrapStatus, error: bootstrapError } = bootstrapHook;

  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDocumentationOpen, setIsDocumentationOpen] = useState(false);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  const schemaHook = useAppSchema(
    auth.status === 'authenticated',
    bootstrap ?? null,
    auth.user?.id ?? null,
  );
  const {
    schema: loadedSchema,
    hierarchy: loadedHierarchy,
    hierarchyTree: loadedHierarchyTree,
    status: schemaStatus,
    error: schemaError,
    isLoading,
    isReady,
    reload,
    reloadHierarchy,
  } = schemaHook;

  const state = useAppStoreState();
  const { beginLoading, setLoadedData, setError } = useAppStoreCommands();

  const appBootstrap = useAppBootstrap({
    bootstrap: bootstrap ?? null,
    reload: reload,
    reloadHierarchy: reloadHierarchy,
  });

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
    if (isLoading) beginLoading();
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

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalKind, setModalKind] = useState<HierarchyActionKind | null>(null);
  const [modalNode, setModalNode] = useState<HierarchyNode | null>(null);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editorNode, setEditorNode] = useState<HierarchyNode | null>(null);
  const [editorInitialTab, setEditorInitialTab] = useState<
    'general' | 'structure' | 'widgets' | 'prompts' | 'tools' | null
  >('general');

  const [isMutating, setIsMutating] = useState(false);
  const [recentlyMovedNodeId, setRecentlyMovedNodeId] = useState<string | null>(null);

  // ============================================================
  // Handler
  // ============================================================

  const handleOpenSettings = useCallback((): void => setIsSettingsOpen(true), []);
  const handleCloseSettings = useCallback((): void => setIsSettingsOpen(false), []);
  const handleOpenDocumentation = useCallback((): void => setIsDocumentationOpen(true), []);
  const handleCloseDocumentation = useCallback((): void => setIsDocumentationOpen(false), []);
  const handleOpenCalendar = useCallback((): void => setIsCalendarOpen(true), []);

  // ============================================================
  // Debug (nur im Development)
  // ============================================================

  if (import.meta.env.DEV) {
    console.debug('[Kernschmied startup state]', {
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
  }

  // ============================================================
  // Auth‑ & Bootstrap‑State Machine
  // ============================================================

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
      <RegisterPage onSuccess={() => void auth.reload()} onBack={() => setAuthView('login')} />
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

  // ============================================================
  // Hierarchie‑Aktionen
  // ============================================================

  function openModalFor(action: HierarchyActionKind, node: HierarchyNode) {
    if (action === 'edit_node' || action === 'edit_config') {
      setEditorNode(node);
      setEditorInitialTab('general');
      setEditorOpen(true);
      return;
    }
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

    try {
      const optimistic = moveNodeInTree(prev as HierarchyTree, id, newParentId, position ?? null);
      replaceHierarchy(optimistic);
    } catch (err: unknown) {
      push('error', err instanceof Error ? err.message : 'Fehler beim Anwenden der lokalen Änderung');
      setIsMutating(false);
      return;
    }

    try {
      await moveHierarchyNode?.(id, newParentId, position ?? null);
      push('success', 'Verschoben.');
      setRecentlyMovedNodeId(id);
      window.setTimeout(() => setRecentlyMovedNodeId(null), 900);
    } catch (err: unknown) {
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
        parent_id: WORKSPACES_ROOT_NODE_ID,
        metadata: { visibility: 'public', owner_user_id: auth.user?.id },
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
        parent_id: WORKSPACES_ROOT_NODE_ID,
        metadata: { visibility: 'internal', owner_user_id: auth.user?.id },
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
        parent_id: USERS_ROOT_NODE_ID,
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
    const mapping: Record<string, { type: string; defaultName: string }> = {
      benutzer: { type: 'workspace', defaultName: 'Neuer Bereich' },
      user: { type: 'workspace', defaultName: 'Neuer Bereich' },
      bereich: { type: 'project', defaultName: 'Neues Projekt' },
      workspace: { type: 'project', defaultName: 'Neues Projekt' },
      area: { type: 'project', defaultName: 'Neues Projekt' },
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

    if (newParentId === null) {
      clone.root.children = clone.root.children || [];
      if (insertPosition === null) clone.root.children.push(nodeToMove);
      else {
        clone.root.children.splice(
          Math.max(0, Math.min(clone.root.children.length, insertPosition)),
          0,
          nodeToMove,
        );
      }
      return clone;
    }

    function insertInto(parent: HierarchyNode): boolean {
      if (parent.id === newParentId) {
        parent.children = parent.children || [];
        if (insertPosition === null) parent.children.push(nodeToMove as HierarchyNode);
        else {
          parent.children.splice(
            Math.max(0, Math.min(parent.children.length, insertPosition)),
            0,
            nodeToMove as HierarchyNode,
          );
        }
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

  // ============================================================
  // Render
  // ============================================================

  return (
    <>
      <AppWorkspace
        schema={schema}
        root={root}
        bootstrap={bootstrap}
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
        onCreatePublicWorkspace={isHierarchyAdmin ? handleCreatePublicWorkspace : undefined}
        onCreateInternWorkspace={isHierarchyAdmin ? handleCreateInternWorkspace : undefined}
        onCreateUser={isHierarchyAdmin ? handleCreateUser : undefined}
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

      {/* Hierarchie‑Aktions‑Modal */}
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
              case 'create_chat': {
                const chosen = chooseChildTypeForParent((modalNode as any)?.type);
                const childType = modalKind === 'create_chat' ? 'chat' : chosen.type;
                const defaultName = modalKind === 'create_chat' ? 'Neuer Chat' : chosen.defaultName;
                const name = value ?? defaultName;

                await createHierarchyNode?.({
                  type: childType,
                  name,
                  parent_id: modalNode.id ?? null,
                  system_prompt:
                    (modalNode as any)?.system_prompt ??
                    (modalNode as any)?.metadata?.prompt ??
                    undefined,
                  tool_policy: {},
                  config_overrides: {},
                  metadata: {},
                } as any);
                push(
                  'success',
                  `${childType === 'chat' ? 'Chat' : 'Unterelement'} '${name}' erstellt.`,
                );
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
                const payload: any = {
                  system_prompt: promptValue,
                  prompt_enabled: !!promptValue,
                };
                if ((modalNode as any)?.prompt_mode !== undefined) {
                  payload.prompt_mode = (modalNode as any).prompt_mode;
                }
                if ((modalNode as any)?.prompt_priority !== undefined) {
                  payload.prompt_priority = (modalNode as any).prompt_priority;
                }
                await updateHierarchyNode?.(modalNode.id, payload);
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

      {/* Node‑Editor‑Dialog */}
      <NodeEditorDialog
        isOpen={editorOpen}
        node={editorNode}
        nodeTypes={state.schema?.node_types ?? {}}
        onClose={() => setEditorOpen(false)}
        initialTab={editorInitialTab ?? undefined}
        onSaved={async () => {
          setEditorOpen(false);
          await reloadHierarchy?.();
        }}
      />

      {/* Einstellungen */}
      <SettingsDialog isOpen={isSettingsOpen} onClose={handleCloseSettings} />

      {/* Dokumentation */}
      <DocumentationDialog isOpen={isDocumentationOpen} onClose={handleCloseDocumentation} />

      {/* Kalender – jetzt mit einheitlichem Modal */}
      {isCalendarOpen && (
        <Modal
          isOpen={isCalendarOpen}
          title="Kalenderverwaltung"
          onClose={() => setIsCalendarOpen(false)}
          confirmLabel="Schließen"
          onConfirm={() => setIsCalendarOpen(false)}
        >
          <React.Suspense
            fallback={
              <div className="flex items-center justify-center py-12">
                <IconBadge icon={<LoaderCircle className="animate-spin" />} size="lg" variant="default" />
                <span className="ml-3 text-text-muted dark:text-gray-400">Kalender wird geladen …</span>
              </div>
            }
          >
            <CalendarPanel onClose={() => setIsCalendarOpen(false)} />
          </React.Suspense>
        </Modal>
      )}
    </>
  );
}