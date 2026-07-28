// F:\Kernschmied\frontend\src\App.tsx

import { useEffect } from "react";
import { Sun, Moon } from "lucide-react";

import { useTheme } from "./theme";
import { GenericChatView } from "./components/chat/GenericChatView";
import { GenericTree } from "./components/schema/GenericTree";
import { useAppSchema } from "./hooks/useAppSchema";
import {
  selectExpandedNodeIds,
  selectHierarchyRoot,
  selectSelectedNode,
  selectSelectedNodeId,
  useAppStoreCommands,
  useAppStoreState,
} from "./store";

export default function App() {
  const {
    schema: loadedSchema,
    hierarchyTree: loadedHierarchyTree,
    error: loadError,
    isLoading,
    reload,
  } = useAppSchema();

  const state = useAppStoreState();

  const {
    beginLoading,
    setLoadedData,
    setError,
    selectHierarchyNode,
    replaceExpandedNodeIds,
  } = useAppStoreCommands();

  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    if (!isLoading) return;
    beginLoading();
  }, [beginLoading, isLoading]);

  useEffect(() => {
    if (!loadedSchema || !loadedHierarchyTree) return;
    setLoadedData(loadedSchema, loadedHierarchyTree);
  }, [loadedHierarchyTree, loadedSchema, setLoadedData]);

  useEffect(() => {
    if (!loadError) return;
    setError(loadError);
  }, [loadError, setError]);

  const root = selectHierarchyRoot(state);
  const selectedNode = selectSelectedNode(state);
  const selectedNodeId = selectSelectedNodeId(state);
  const expandedNodeIds = selectExpandedNodeIds(state);

  const handleReload = (): void => {
    void reload();
  };

  if (state.status === "idle" || state.status === "loading") {
    return <AppLoadingScreen />;
  }

  if (state.status === "error") {
    return (
      <AppErrorScreen
        message={state.error?.message ?? "Die Anwendung konnte nicht geladen werden."}
        requestId={state.error?.requestId}
        onRetry={handleReload}
      />
    );
  }

  if (!state.schema || !root) {
    return (
      <AppErrorScreen
        message="Das UI-Schema oder die Hierarchie ist nicht verfügbar."
        onRetry={handleReload}
      />
    );
  }

  return (
    <div className="flex h-full min-h-0 bg-surface-muted dark:bg-slate-900/30 text-text dark:text-white">
      {/* Seitenleiste */}
      <aside className="flex h-full w-72 shrink-0 flex-col border-r border-border bg-white/80 backdrop-blur-md dark:bg-slate-800/80 dark:border-white/10 shadow-glass">
        <header className="shrink-0 border-b border-border px-4 py-4 dark:border-white/10">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold text-text dark:text-white">
              Kernschmied
            </h1>
            <button
              onClick={toggleTheme}
              className="rounded-full p-1.5 hover:bg-surface-hover dark:hover:bg-slate-700/50 transition-colors"
              aria-label="Theme umschalten"
            >
              {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
            </button>
          </div>
          <p className="mt-1 text-xs text-text-muted dark:text-gray-400">
            UI-Schema{" "}
            <code className="font-mono text-primary dark:text-primary">
              {state.schema.schema_version}
            </code>
          </p>
        </header>

        <nav
          className="min-h-0 flex-1 overflow-y-auto p-2"
          aria-label="Anwendungshierarchie"
        >
          <GenericTree
            root={root}
            schema={state.schema}
            selectedNodeId={selectedNodeId}
            expandedNodeIds={expandedNodeIds}
            onSelect={selectHierarchyNode}
            onExpandedNodeIdsChange={replaceExpandedNodeIds}
          />
        </nav>
      </aside>

      {/* Hauptbereich */}
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="shrink-0 border-b border-border bg-white/80 backdrop-blur-md px-6 py-4 dark:bg-slate-800/80 dark:border-white/10">
          <h2 className="text-lg font-semibold text-text dark:text-white">
            {selectedNode?.name ?? "Keine Auswahl"}
          </h2>
          {selectedNode && (
            <p className="mt-1 text-sm text-text-muted dark:text-gray-400">
              Knotentyp:{" "}
              <code className="font-mono text-primary dark:text-primary">
                {selectedNode.type}
              </code>
            </p>
          )}
        </header>

        <section className="min-h-0 flex-1 overflow-y-auto p-6">
          {selectedNode ? (
            selectedNode.type === "chat" ? (
              <GenericChatView
                title={selectedNode.name}
                hierarchyNodeId={selectedNode.id}
              />
            ) : (
              <SelectedNodePlaceholder
                nodeName={selectedNode.name}
                nodeType={selectedNode.type}
              />
            )
          ) : (
            <EmptySelection />
          )}
        </section>
      </main>
    </div>
  );
}

// ─── Fehlerbildschirm ───────────────────────────────────────────

interface AppErrorScreenProps {
  message: string;
  requestId?: string;
  onRetry: () => void;
}

function AppErrorScreen({ message, requestId, onRetry }: AppErrorScreenProps) {
  return (
    <main className="flex h-full min-h-0 items-center justify-center overflow-y-auto bg-surface-muted p-6 dark:bg-slate-900/30">
      <section
        className="w-full max-w-lg animate-fade-in rounded-2xl border border-danger/30 bg-white/80 backdrop-blur-md p-6 shadow-glass dark:bg-slate-800/80 dark:border-danger/20"
        role="alert"
        aria-live="assertive"
      >
        <h1 className="text-lg font-semibold text-danger dark:text-danger">
          Anwendung konnte nicht geladen werden
        </h1>
        <p className="mt-3 text-sm text-text-soft dark:text-gray-300">{message}</p>
        {requestId && (
          <p className="mt-3 text-xs text-text-muted dark:text-gray-500">
            Anfrage-ID: <code className="font-mono">{requestId}</code>
          </p>
        )}
        <button
          type="button"
          className="mt-5 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow transition hover:bg-primary-hover hover:shadow-primary-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:bg-primary/80 dark:hover:bg-primary"
          onClick={onRetry}
        >
          Erneut versuchen
        </button>
      </section>
    </main>
  );
}

// ─── Ladebildschirm ─────────────────────────────────────────────

function AppLoadingScreen() {
  return (
    <main
      className="flex h-full min-h-0 items-center justify-center bg-surface-muted p-6 dark:bg-slate-900/30"
      aria-busy="true"
      aria-live="polite"
    >
      <div className="animate-fade-in rounded-2xl border border-border-soft bg-white/80 backdrop-blur-md px-6 py-5 shadow-glass dark:bg-slate-800/80 dark:border-white/10">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 animate-pulse rounded-full bg-primary/60 dark:bg-primary/40"></div>
          <p className="text-sm font-medium text-text-soft dark:text-gray-300">
            Kernschmied wird geladen …
          </p>
        </div>
      </div>
    </main>
  );
}

// ─── Platzhalter für nicht unterstützte Knoten ─────────────────

interface SelectedNodePlaceholderProps {
  nodeName: string;
  nodeType: string;
}

function SelectedNodePlaceholder({ nodeName, nodeType }: SelectedNodePlaceholderProps) {
  return (
    <div className="animate-fade-in rounded-2xl border border-border-soft bg-white/80 backdrop-blur-md p-6 shadow-glass dark:bg-slate-800/80 dark:border-white/10">
      <h3 className="font-semibold text-text dark:text-white">{nodeName}</h3>
      <p className="mt-2 text-sm text-text-soft dark:text-gray-300">
        Für den Knotentyp{" "}
        <code className="font-mono text-primary dark:text-primary">{nodeType}</code>{" "}
        ist noch keine Ansicht registriert.
      </p>
    </div>
  );
}

// ─── Leerer Zustand (kein Knoten ausgewählt) ──────────────────

function EmptySelection() {
  return (
    <div className="animate-fade-in rounded-2xl border border-dashed border-border-soft bg-white/60 backdrop-blur-sm p-6 text-sm text-text-muted dark:bg-slate-800/40 dark:border-white/10 dark:text-gray-400">
      Wähle einen Eintrag aus der Hierarchie aus.
    </div>
  );
}