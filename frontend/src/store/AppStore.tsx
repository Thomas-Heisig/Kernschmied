// F:\Kernschmied\frontend\src\store\AppStore.tsx

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  type Dispatch,
  type PropsWithChildren,
} from "react";

import type {
  HierarchyNode,
  HierarchyTree,
} from "../contracts/hierarchy";
import type { UISchema } from "../contracts/schema";

export type AppStoreStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";

export interface AppStoreError {
  code: string;
  message: string;
  details?: unknown;
  requestId?: string;
  status?: number;
}

export interface AppStoreState {
  /**
   * Aktuell geladenes UI-Schema.
   */
  schema: UISchema | null;

  /**
   * Vollständiger, versionierter Hierarchiebaum.
   */
  hierarchyTree: HierarchyTree | null;

  /**
   * Aktuell ausgewählter Hierarchieknoten.
   */
  selectedNodeId: string | null;

  /**
   * Aufgeklappte Knoten im generischen Baum.
   */
  expandedNodeIds: ReadonlySet<string>;

  /**
   * Globaler Ladezustand des initialen App-Kontexts.
   */
  status: AppStoreStatus;

  /**
   * Strukturierter Lade- oder Vertragsfehler.
   */
  error: AppStoreError | null;

  /**
   * Gibt an, ob die linke Navigation sichtbar ist.
   */
  isNavigationOpen: boolean;

  /**
   * Gibt an, ob eine optionale rechte Seitenleiste sichtbar ist.
   */
  isDetailsPanelOpen: boolean;
}

export type AppStoreAction =
  | {
      type: "app/load_started";
    }
  | {
      type: "app/load_succeeded";
      payload: {
        schema: UISchema;
        hierarchyTree: HierarchyTree;
      };
    }
  | {
      type: "app/load_failed";
      payload: AppStoreError;
    }
  | {
      type: "app/error_cleared";
    }
  | {
      type: "schema/replaced";
      payload: UISchema;
    }
  | {
      type: "hierarchy/replaced";
      payload: HierarchyTree;
    }
  | {
      type: "hierarchy/node_selected";
      payload: {
        nodeId: string | null;
      };
    }
  | {
      type: "hierarchy/node_expansion_toggled";
      payload: {
        nodeId: string;
      };
    }
  | {
      type: "hierarchy/expanded_nodes_replaced";
      payload: {
        nodeIds: ReadonlySet<string>;
      };
    }
  | {
      type: "hierarchy/all_nodes_collapsed";
    }
  | {
      type: "ui/navigation_visibility_changed";
      payload: {
        open: boolean;
      };
    }
  | {
      type: "ui/details_panel_visibility_changed";
      payload: {
        open: boolean;
      };
    }
  | {
      type: "app/reset";
    };

export interface AppStoreCommands {
  beginLoading: () => void;

  setLoadedData: (
    schema: UISchema,
    hierarchyTree: HierarchyTree,
  ) => void;

  setError: (error: AppStoreError) => void;
  clearError: () => void;

  replaceSchema: (schema: UISchema) => void;
  replaceHierarchy: (hierarchyTree: HierarchyTree) => void;

  selectNode: (nodeId: string | null) => void;
  selectHierarchyNode: (node: HierarchyNode | null) => void;

  toggleNodeExpanded: (nodeId: string) => void;
  replaceExpandedNodeIds: (
    nodeIds: ReadonlySet<string>,
  ) => void;
  collapseAllNodes: () => void;

  setNavigationOpen: (open: boolean) => void;
  setDetailsPanelOpen: (open: boolean) => void;

  reset: () => void;
}

export interface AppStoreValue {
  state: AppStoreState;
  dispatch: Dispatch<AppStoreAction>;
  commands: AppStoreCommands;
}

const INITIAL_STATE: AppStoreState = {
  schema: null,
  hierarchyTree: null,
  selectedNodeId: null,
  expandedNodeIds: new Set<string>(),
  status: "idle",
  error: null,
  isNavigationOpen: true,
  isDetailsPanelOpen: true,
};

const AppStoreContext =
  createContext<AppStoreValue | null>(null);

export interface AppStoreProviderProps {
  initialState?: Partial<AppStoreState>;
}

export function AppStoreProvider({
  children,
  initialState,
}: PropsWithChildren<AppStoreProviderProps>) {
  const [state, dispatch] = useReducer(
    appStoreReducer,
    initialState,
    createInitialState,
  );

  const beginLoading = useCallback(() => {
    dispatch({
      type: "app/load_started",
    });
  }, []);

  const setLoadedData = useCallback(
    (
      schema: UISchema,
      hierarchyTree: HierarchyTree,
    ) => {
      dispatch({
        type: "app/load_succeeded",
        payload: {
          schema,
          hierarchyTree,
        },
      });
    },
    [],
  );

  const setError = useCallback(
    (error: AppStoreError) => {
      dispatch({
        type: "app/load_failed",
        payload: error,
      });
    },
    [],
  );

  const clearError = useCallback(() => {
    dispatch({
      type: "app/error_cleared",
    });
  }, []);

  const replaceSchema = useCallback(
    (schema: UISchema) => {
      dispatch({
        type: "schema/replaced",
        payload: schema,
      });
    },
    [],
  );

  const replaceHierarchy = useCallback(
    (hierarchyTree: HierarchyTree) => {
      dispatch({
        type: "hierarchy/replaced",
        payload: hierarchyTree,
      });
    },
    [],
  );

  const selectNode = useCallback(
    (nodeId: string | null) => {
      dispatch({
        type: "hierarchy/node_selected",
        payload: {
          nodeId,
        },
      });
    },
    [],
  );

  const selectHierarchyNode = useCallback(
    (node: HierarchyNode | null) => {
      dispatch({
        type: "hierarchy/node_selected",
        payload: {
          nodeId: node?.id ?? null,
        },
      });
    },
    [],
  );

  const toggleNodeExpanded = useCallback(
    (nodeId: string) => {
      dispatch({
        type: "hierarchy/node_expansion_toggled",
        payload: {
          nodeId,
        },
      });
    },
    [],
  );

  const replaceExpandedNodeIds = useCallback(
    (nodeIds: ReadonlySet<string>) => {
      dispatch({
        type: "hierarchy/expanded_nodes_replaced",
        payload: {
          nodeIds,
        },
      });
    },
    [],
  );

  const collapseAllNodes = useCallback(() => {
    dispatch({
      type: "hierarchy/all_nodes_collapsed",
    });
  }, []);

  const setNavigationOpen = useCallback(
    (open: boolean) => {
      dispatch({
        type: "ui/navigation_visibility_changed",
        payload: {
          open,
        },
      });
    },
    [],
  );

  const setDetailsPanelOpen = useCallback(
    (open: boolean) => {
      dispatch({
        type: "ui/details_panel_visibility_changed",
        payload: {
          open,
        },
      });
    },
    [],
  );

  const reset = useCallback(() => {
    dispatch({
      type: "app/reset",
    });
  }, []);

  const commands = useMemo<AppStoreCommands>(
    () => ({
      beginLoading,
      setLoadedData,
      setError,
      clearError,
      replaceSchema,
      replaceHierarchy,
      selectNode,
      selectHierarchyNode,
      toggleNodeExpanded,
      replaceExpandedNodeIds,
      collapseAllNodes,
      setNavigationOpen,
      setDetailsPanelOpen,
      reset,
    }),
    [
      beginLoading,
      setLoadedData,
      setError,
      clearError,
      replaceSchema,
      replaceHierarchy,
      selectNode,
      selectHierarchyNode,
      toggleNodeExpanded,
      replaceExpandedNodeIds,
      collapseAllNodes,
      setNavigationOpen,
      setDetailsPanelOpen,
      reset,
    ],
  );

  const value = useMemo<AppStoreValue>(
    () => ({
      state,
      dispatch,
      commands,
    }),
    [commands, state],
  );

  return (
    <AppStoreContext.Provider value={value}>
      {children}
    </AppStoreContext.Provider>
  );
}

export function useAppStore(): AppStoreValue {
  const store = useContext(AppStoreContext);

  if (!store) {
    throw new Error(
      "useAppStore muss innerhalb eines AppStoreProvider verwendet werden.",
    );
  }

  return store;
}

export function useAppStoreState(): AppStoreState {
  return useAppStore().state;
}

export function useAppStoreCommands(): AppStoreCommands {
  return useAppStore().commands;
}

export function appStoreReducer(
  state: AppStoreState,
  action: AppStoreAction,
): AppStoreState {
  switch (action.type) {
    case "app/load_started":
      return {
        ...state,
        status: "loading",
        error: null,
      };

    case "app/load_succeeded": {
      const { schema, hierarchyTree } = action.payload;
      const rootNodeId = hierarchyTree.root.id;

      return {
        ...state,
        schema,
        hierarchyTree,
        selectedNodeId: resolveSelectedNodeId(
          hierarchyTree,
          state.selectedNodeId,
        ),
        expandedNodeIds:
          state.expandedNodeIds.size > 0
            ? removeUnknownExpandedNodeIds(
                hierarchyTree,
                state.expandedNodeIds,
              )
            : new Set([rootNodeId]),
        status: "ready",
        error: null,
      };
    }

    case "app/load_failed":
      return {
        ...state,
        status: "error",
        error: action.payload,
      };

    case "app/error_cleared":
      return {
        ...state,
        error: null,
        status:
          state.schema && state.hierarchyTree
            ? "ready"
            : "idle",
      };

    case "schema/replaced":
      return {
        ...state,
        schema: action.payload,
      };

    case "hierarchy/replaced":
      return {
        ...state,
        hierarchyTree: action.payload,
        selectedNodeId: resolveSelectedNodeId(
          action.payload,
          state.selectedNodeId,
        ),
        expandedNodeIds: removeUnknownExpandedNodeIds(
          action.payload,
          state.expandedNodeIds,
        ),
      };

    case "hierarchy/node_selected":
      return {
        ...state,
        selectedNodeId: action.payload.nodeId,
      };

    case "hierarchy/node_expansion_toggled": {
      const nextExpandedNodeIds = new Set(
        state.expandedNodeIds,
      );

      if (nextExpandedNodeIds.has(action.payload.nodeId)) {
        nextExpandedNodeIds.delete(action.payload.nodeId);
      } else {
        nextExpandedNodeIds.add(action.payload.nodeId);
      }

      return {
        ...state,
        expandedNodeIds: nextExpandedNodeIds,
      };
    }

    case "hierarchy/expanded_nodes_replaced":
      return {
        ...state,
        expandedNodeIds: new Set(action.payload.nodeIds),
      };

    case "hierarchy/all_nodes_collapsed":
      return {
        ...state,
        expandedNodeIds: new Set<string>(),
      };

    case "ui/navigation_visibility_changed":
      return {
        ...state,
        isNavigationOpen: action.payload.open,
      };

    case "ui/details_panel_visibility_changed":
      return {
        ...state,
        isDetailsPanelOpen: action.payload.open,
      };

    case "app/reset":
      return createInitialState();

    default:
      return assertNever(action);
  }
}

function createInitialState(
  initialState?: Partial<AppStoreState>,
): AppStoreState {
  return {
    ...INITIAL_STATE,
    ...initialState,
    expandedNodeIds: new Set(
      initialState?.expandedNodeIds ??
        INITIAL_STATE.expandedNodeIds,
    ),
  };
}

function resolveSelectedNodeId(
  hierarchyTree: HierarchyTree,
  selectedNodeId: string | null,
): string | null {
  if (
    selectedNodeId &&
    containsNodeId(hierarchyTree.root, selectedNodeId)
  ) {
    return selectedNodeId;
  }

  return hierarchyTree.root.id;
}

function removeUnknownExpandedNodeIds(
  hierarchyTree: HierarchyTree,
  expandedNodeIds: ReadonlySet<string>,
): ReadonlySet<string> {
  const existingNodeIds = collectNodeIds(
    hierarchyTree.root,
  );

  return new Set(
    [...expandedNodeIds].filter((nodeId) =>
      existingNodeIds.has(nodeId),
    ),
  );
}

function collectNodeIds(
  root: HierarchyNode,
): Set<string> {
  const nodeIds = new Set<string>();
  const stack: HierarchyNode[] = [root];

  while (stack.length > 0) {
    const node = stack.pop();

    if (!node || nodeIds.has(node.id)) {
      continue;
    }

    nodeIds.add(node.id);

    for (const child of node.children) {
      stack.push(child);
    }
  }

  return nodeIds;
}

function containsNodeId(
  root: HierarchyNode,
  nodeId: string,
): boolean {
  const stack: HierarchyNode[] = [root];
  const visitedNodeIds = new Set<string>();

  while (stack.length > 0) {
    const node = stack.pop();

    if (!node || visitedNodeIds.has(node.id)) {
      continue;
    }

    if (node.id === nodeId) {
      return true;
    }

    visitedNodeIds.add(node.id);

    for (const child of node.children) {
      stack.push(child);
    }
  }

  return false;
}

function assertNever(value: never): never {
  throw new Error(
    `Unbekannte Store-Aktion: ${JSON.stringify(value)}`,
  );
}