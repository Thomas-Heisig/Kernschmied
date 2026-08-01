// F:\Kernschmied\frontend\src\components\workspace\SelectedNodeWorkspace.tsx

import { useEffect, useState } from "react";
import { Globe2, Plus } from "lucide-react";

import { GenericChatView } from "../chat";
import { SettingsDialog } from "../settings";
import { WebsiteWorkspace } from "../websites";
import SchemaRenderer from "../schema/SchemaRenderer";

/* ============================================================
 * Typen und Konstanten
 * ============================================================ */

export interface SelectedWorkspaceNode {
  id: string;
  name: string;
  type: string;
}

interface SelectedNodeWorkspaceProps {
  node: SelectedWorkspaceNode | null;
  schema?: any;
}

const SETTINGS_NODE_TYPES = new Set<string>([
  "settings",
  "configuration",
  "system_config",
  "system-configuration",
]);

const CHAT_NODE_TYPES = new Set<string>(["chat", "conversation"]);

const WEBSITE_COLLECTION_NODE_TYPES = new Set<string>([
  "websites",
  "website_collection",
  "website-collection",
  "webseiten",
]);

const WEBSITE_NODE_TYPES = new Set<string>([
  "website",
  "webseite",
  "static_website",
  "static-website",
]);

/* ============================================================
 * Hauptkomponente
 * ============================================================ */

export function SelectedNodeWorkspace({
  node,
  schema,
}: SelectedNodeWorkspaceProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const normalizedType = node ? normalizeNodeType(node.type) : null;

  /*
   * Wird ein Einstellungsknoten ausgewählt, öffnet sich der Dialog
   * automatisch. Beim Wechsel zu einem anderen Knotentyp wird er
   * geschlossen.
   */
  useEffect(() => {
    setIsSettingsOpen(
      normalizedType !== null && SETTINGS_NODE_TYPES.has(normalizedType),
    );
  }, [normalizedType, node?.id]);

  if (!node || !normalizedType) {
    return <EmptyWorkspace />;
  }

  /* ----------------------------------------------------------
   * Systemeinstellungen
   * ---------------------------------------------------------- */

  if (SETTINGS_NODE_TYPES.has(normalizedType)) {
    return (
      <section
        className={[
          "flex min-h-0 min-w-0",
          "w-full flex-1 flex-col",
          "overflow-hidden",
          "bg-slate-50",
          "dark:bg-slate-950/30",
        ].join(" ")}
        aria-label={`Einstellungen: ${node.name}`}
      >
        {isSettingsOpen ? (
          <SettingsDialog
            isOpen={isSettingsOpen}
            onClose={() => {
              setIsSettingsOpen(false);
            }}
          />
        ) : (
          <SettingsClosedView
            onOpen={() => {
              setIsSettingsOpen(true);
            }}
          />
        )}
      </section>
    );
  }

  /* ----------------------------------------------------------
   * Chat
   * ---------------------------------------------------------- */

  if (CHAT_NODE_TYPES.has(normalizedType)) {
    return (
      <section
        className={[
          "flex min-h-0 min-w-0",
          "w-full flex-1",
          "overflow-hidden",
          "bg-white",
          "dark:bg-slate-950",
        ].join(" ")}
        aria-label={`Chat: ${node.name}`}
      >
        <GenericChatView title={node.name} hierarchyNodeId={node.id} />
      </section>
    );
  }

  /* ----------------------------------------------------------
   * Webseiten-Sammlung
   * ---------------------------------------------------------- */

  if (WEBSITE_COLLECTION_NODE_TYPES.has(normalizedType)) {
    return <WebsiteCollectionView node={node} />;
  }

  /* ----------------------------------------------------------
   * Einzelne Webseite
   * ---------------------------------------------------------- */

  if (WEBSITE_NODE_TYPES.has(normalizedType)) {
    return <WebsiteWorkspace websiteId={node.id} title={node.name} />;
  }

  /* ----------------------------------------------------------
   * Noch nicht unterstützter Knotentyp
   * ---------------------------------------------------------- */
  if (WEBSITE_COLLECTION_NODE_TYPES.has(normalizedType)) {
    return <WebsiteCollectionView node={node} />;
  }

  if (WEBSITE_NODE_TYPES.has(normalizedType)) {
    return <WebsiteWorkspace websiteId={node.id} title={node.name} />;
  }

  // If the schema provides a node definition for this type, render the SchemaRenderer
  if (schema && schema.node_types && schema.node_types[normalizedType]) {
    return (
      <section
        className={[
          "flex min-h-0 min-w-0",
          "w-full flex-1",
          "overflow-auto",
          "bg-slate-50 p-6",
          "dark:bg-slate-950/30",
          "sm:p-8",
        ].join(" ")}
        aria-label={`Schema view: ${node.name}`}
      >
        <div className="mx-auto w-full max-w-6xl">
          <SchemaRenderer schema={schema.node_types?.[normalizedType]} context={{ nodeId: node.id }} />
        </div>
      </section>
    );
  }

  return <NodePlaceholder node={node} schema={schema} />;
}
function NodePlaceholder({
  node,
  schema,
}: NodePlaceholderProps & { schema?: any }) {
  const titleId = createElementId("workspace-node-title", node.id);

  return (
    <section
      className={[
        "flex min-h-0 min-w-0",
        "w-full flex-1",
        "items-center justify-center",
        "overflow-auto",
        "bg-slate-50 p-6",
        "dark:bg-slate-950/30",
        "sm:p-8",
      ].join(" ")}
      aria-labelledby={titleId}
    >
      <div
        className={[
          "w-full max-w-xl",
          "rounded-2xl",
          "border border-slate-200",
          "bg-white p-6",
          "shadow-sm",
          "dark:border-white/10",
          "dark:bg-slate-900/50",
        ].join(" ")}
      >
        <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
          {node.type}
        </p>

        <h1
          id={titleId}
          className="mt-2 text-xl font-semibold text-slate-950 dark:text-white"
        >
          {node.name}
        </h1>

        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-400">
          {/** prefer schema-driven description if available */}
          {schema &&
          schema.node_types &&
          schema.node_types[node.type] &&
          schema.node_types[node.type].description
            ? schema.node_types[node.type].description
            : "Für diesen Knotentyp wird künftig die passende schema-gesteuerte Ansicht über den zentralen SchemaRenderer dargestellt."}
        </p>

        <dl className="mt-5 grid gap-3 rounded-xl bg-slate-100 p-4 text-sm dark:bg-white/5">
          <div className="flex min-w-0 gap-3">
            <dt className="w-20 shrink-0 font-medium text-slate-500 dark:text-slate-400">
              ID
            </dt>

            <dd className="min-w-0 flex-1 wrap-break-words font-mono text-slate-800 dark:text-slate-200">
              {node.id}
            </dd>
          </div>

          <div className="flex min-w-0 gap-3">
            <dt className="w-20 shrink-0 font-medium text-slate-500 dark:text-slate-400">
              Typ
            </dt>

            <dd className="min-w-0 flex-1 wrap-break-words font-mono text-slate-800 dark:text-slate-200">
              {node.type}
            </dd>
          </div>
        </dl>
      </div>
    </section>
  );
}

/* ============================================================
 * Leerer Arbeitsbereich
 * ============================================================ */

function EmptyWorkspace() {
  return (
    <section
      className={[
        "flex min-h-0 min-w-0",
        "w-full flex-1",
        "items-center justify-center",
        "overflow-auto",
        "bg-slate-50 p-6",
        "dark:bg-slate-950/30",
        "sm:p-8",
      ].join(" ")}
      aria-labelledby="empty-workspace-title"
    >
      <div className="w-full max-w-md text-center">
        <h1
          id="empty-workspace-title"
          className="text-xl font-semibold text-slate-950 dark:text-white"
        >
          Kein Bereich ausgewählt
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">
          Wähle links einen Arbeitsbereich, ein Projekt, einen Chat, eine
          Webseite oder die Systemeinstellungen aus.
        </p>
      </div>
    </section>
  );
}

/* ============================================================
 * Webseiten-Sammlung
 * ============================================================ */

interface WebsiteCollectionViewProps {
  node: SelectedWorkspaceNode;
}

function WebsiteCollectionView({ node }: WebsiteCollectionViewProps) {
  const titleId = createElementId("website-collection-title", node.id);

  return (
    <section
      className={[
        "flex min-h-0 min-w-0",
        "w-full flex-1 flex-col",
        "overflow-auto",
        "bg-slate-50",
        "p-6",
        "dark:bg-slate-950/30",
        "sm:p-8",
      ].join(" ")}
      aria-labelledby={titleId}
    >
      <div className="mx-auto w-full max-w-6xl">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div
                className={[
                  "flex h-11 w-11 shrink-0",
                  "items-center justify-center",
                  "rounded-xl",
                  "border border-blue-200",
                  "bg-blue-50",
                  "text-blue-600",
                  "dark:border-blue-400/20",
                  "dark:bg-blue-500/10",
                  "dark:text-blue-400",
                ].join(" ")}
                aria-hidden="true"
              >
                <Globe2 size={22} />
              </div>

              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                  Webseiten
                </p>

                <h1
                  id={titleId}
                  className="truncate text-2xl font-semibold text-slate-950 dark:text-white"
                >
                  {node.name}
                </h1>
              </div>
            </div>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-400">
              Hier werden die in Kernschmied registrierten Webseiten verwaltet.
              Wähle links eine Webseite aus, um ihre Vorschau zu öffnen und sie
              später zu bearbeiten.
            </p>
          </div>

          <button
            type="button"
            disabled
            className={[
              "inline-flex shrink-0",
              "items-center justify-center",
              "gap-2 rounded-xl",
              "bg-blue-600",
              "px-4 py-2.5",
              "text-sm font-semibold",
              "text-white shadow-sm",
              "transition",
              "disabled:cursor-not-allowed",
              "disabled:opacity-50",
            ].join(" ")}
            title="Das Anlegen neuer Webseiten wird später über eine autorisierte Backend-Aktion bereitgestellt."
          >
            <Plus size={17} aria-hidden="true" />
            Webseite hinzufügen
          </button>
        </header>

        <div
          className={[
            "mt-8 rounded-2xl",
            "border border-dashed",
            "border-slate-300",
            "bg-white/70",
            "p-8 text-center",
            "dark:border-white/15",
            "dark:bg-slate-900/40",
          ].join(" ")}
        >
          <Globe2
            size={36}
            className="mx-auto text-slate-400 dark:text-slate-500"
            aria-hidden="true"
          />

          <h2 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">
            Webseite in der Hierarchie auswählen
          </h2>

          <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-600 dark:text-slate-400">
            Die vorhandenen Webseiten erscheinen als untergeordnete Knoten
            dieses Bereichs. Für die Vorschau wird der Knotentyp
            <code className="mx-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs dark:bg-white/10">
              website
            </code>
            verwendet.
          </p>
        </div>
      </div>
    </section>
  );
}

/* ============================================================
 * Platzhalter für unbekannte Knotentypen
 * ============================================================ */

interface NodePlaceholderProps {
  node: SelectedWorkspaceNode;
}

/* ============================================================
 * Geschlossene Einstellungen
 * ============================================================ */

interface SettingsClosedViewProps {
  onOpen: () => void;
}

function SettingsClosedView({ onOpen }: SettingsClosedViewProps) {
  return (
    <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center p-6">
      <div className="text-center">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Die Einstellungen wurden geschlossen.
        </p>

        <button
          type="button"
          className={[
            "mt-3 rounded-lg",
            "bg-blue-600",
            "px-4 py-2",
            "text-sm font-medium",
            "text-white",
            "transition",
            "hover:bg-blue-700",
            "focus-visible:outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-blue-500",
            "focus-visible:ring-offset-2",
            "dark:focus-visible:ring-offset-slate-950",
          ].join(" ")}
          onClick={onOpen}
        >
          Einstellungen öffnen
        </button>
      </div>
    </div>
  );
}

/* ============================================================
 * Hilfsfunktionen
 * ============================================================ */

function normalizeNodeType(nodeType: string): string {
  return nodeType.trim().toLowerCase();
}

function createElementId(prefix: string, value: string): string {
  const normalizedValue = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^[-_]+|[-_]+$/g, "");

  return normalizedValue ? `${prefix}-${normalizedValue}` : prefix;
}
