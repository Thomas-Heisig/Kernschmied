// F:\Kernschmied\frontend\src\App.tsx

import { useEffect } from "react";

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

  useEffect(() => {
    if (!isLoading) {
      return;
    }

    beginLoading();
  }, [
    beginLoading,
    isLoading,
  ]);

  useEffect(() => {
    if (!loadedSchema || !loadedHierarchyTree) {
      return;
    }

    setLoadedData(
      loadedSchema,
      loadedHierarchyTree,
    );
  }, [
    loadedHierarchyTree,
    loadedSchema,
    setLoadedData,
  ]);

  useEffect(() => {
    if (!loadError) {
      return;
    }

    setError(
      loadError,
    );
  }, [
    loadError,
    setError,
  ]);

  const root = selectHierarchyRoot(
    state,
  );

  const selectedNode = selectSelectedNode(
    state,
  );

  const selectedNodeId = selectSelectedNodeId(
    state,
  );

  const expandedNodeIds = selectExpandedNodeIds(
    state,
  );

  const handleReload = (): void => {
    void reload();
  };

  if (
    state.status === "idle" ||
    state.status === "loading"
  ) {
    return <AppLoadingScreen />;
  }

  if (state.status === "error") {
    return (
      <AppErrorScreen
        message={
          state.error?.message ??
          "Die Anwendung konnte nicht geladen werden."
        }
        requestId={state.error?.requestId}
        onRetry={handleReload}
      />
    );
  }

  if (!state.schema || !root) {
    return (
      <AppErrorScreen
        message={
          "Das UI-Schema oder die Hierarchie ist nicht verfügbar."
        }
        onRetry={handleReload}
      />
    );
  }

  return (
    <div className="flex h-full min-h-0 bg-slate-100 text-slate-950">
      <aside className="flex h-full w-72 shrink-0 flex-col border-r border-slate-200 bg-white">
        <header className="shrink-0 border-b border-slate-200 px-4 py-4">
          <h1 className="text-lg font-semibold">
            Kernschmied
          </h1>

          <p className="mt-1 text-xs text-slate-500">
            UI-Schema{" "}
            <code className="font-mono">
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
            onExpandedNodeIdsChange={
              replaceExpandedNodeIds
            }
          />
        </nav>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="shrink-0 border-b border-slate-200 bg-white px-6 py-4">
          <h2 className="text-lg font-semibold">
            {selectedNode?.name ??
              "Keine Auswahl"}
          </h2>

          {selectedNode && (
            <p className="mt-1 text-sm text-slate-500">
              Knotentyp:{" "}
              <code className="font-mono">
                {selectedNode.type}
              </code>
            </p>
          )}
        </header>

        <section className="min-h-0 flex-1 overflow-y-auto p-6">
          {selectedNode ? (
            <SelectedNodePlaceholder
              nodeName={selectedNode.name}
              nodeType={selectedNode.type}
            />
          ) : (
            <EmptySelection />
          )}
        </section>
      </main>
    </div>
  );
}

interface AppErrorScreenProps {
  message: string;
  requestId?: string;
  onRetry: () => void;
}

function AppErrorScreen({
  message,
  requestId,
  onRetry,
}: AppErrorScreenProps) {
  return (
    <main className="flex h-full min-h-0 items-center justify-center overflow-y-auto bg-slate-100 p-6">
      <section
        className="w-full max-w-lg rounded-lg border border-red-200 bg-white p-6 shadow-sm"
        role="alert"
        aria-live="assertive"
      >
        <h1 className="text-lg font-semibold text-red-800">
          Anwendung konnte nicht geladen werden
        </h1>

        <p className="mt-3 text-sm text-slate-700">
          {message}
        </p>

        {requestId && (
          <p className="mt-3 text-xs text-slate-500">
            Anfrage-ID:{" "}
            <code className="font-mono">
              {requestId}
            </code>
          </p>
        )}

        <button
          type="button"
          className="mt-5 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-500 focus-visible:ring-offset-2"
          onClick={onRetry}
        >
          Erneut versuchen
        </button>
      </section>
    </main>
  );
}

function AppLoadingScreen() {
  return (
    <main
      className="flex h-full min-h-0 items-center justify-center bg-slate-100 p-6"
      aria-busy="true"
      aria-live="polite"
    >
      <div className="rounded-lg border border-slate-200 bg-white px-6 py-5 shadow-sm">
        <p className="text-sm font-medium text-slate-700">
          Kernschmied wird geladen …
        </p>
      </div>
    </main>
  );
}

interface SelectedNodePlaceholderProps {
  nodeName: string;
  nodeType: string;
}

function SelectedNodePlaceholder({
  nodeName,
  nodeType,
}: SelectedNodePlaceholderProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="font-semibold">
        {nodeName}
      </h3>

      <p className="mt-2 text-sm text-slate-600">
        Für den Knotentyp{" "}
        <code className="font-mono">
          {nodeType}
        </code>{" "}
        wird hier künftig die passende schema-gesteuerte
        Ansicht über den zentralen SchemaRenderer dargestellt.
      </p>
    </div>
  );
}

function EmptySelection() {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
      Wähle einen Eintrag aus der Hierarchie aus.
    </div>
  );
}