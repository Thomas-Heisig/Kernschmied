// F:\Kernschmied\frontend\src\components\layout\AppContextSidebar.tsx

import { useState } from "react";

interface ContextNode {
  id: string;
  name: string;
  type: string;
}

interface AppContextSidebarProps {
  node: ContextNode | null;
  schemaVersion?: string;
  defaultOpen?: boolean;
}

export function AppContextSidebar({
  node,
  schemaVersion,
  defaultOpen = false,
}: AppContextSidebarProps) {
  const [open, setOpen] = useState(defaultOpen);

  function toggleSidebar(): void {
    setOpen((currentOpen) => !currentOpen);
  }

  const toggleLabel = open
    ? "Kontextleiste einklappen"
    : "Kontextleiste ausklappen";

  return (
    <aside
      className={[
        "flex h-full min-h-0 shrink-0 flex-col",
        "border-l border-border",
        "bg-white/80 shadow-glass backdrop-blur-md",
        "transition-[width] duration-200 ease-out",
        "dark:border-white/10 dark:bg-slate-800/80",
        open ? "w-80" : "w-12",
      ].join(" ")}
      aria-label="Kontextinformationen"
      data-state={open ? "open" : "collapsed"}
    >
      <header
        className={[
          "flex shrink-0 border-b border-border",
          "dark:border-white/10",
          open
            ? "min-h-16 items-center justify-between gap-3 px-4 py-3"
            : "h-12 items-center justify-center px-1",
        ].join(" ")}
      >
        {open ? (
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold tracking-wide text-text uppercase dark:text-white">
              Kontext
            </h2>

            <p className="mt-1 truncate text-xs text-text-muted dark:text-gray-400">
              Informationen zum ausgewählten Bereich
            </p>
          </div>
        ) : null}

        <button
          type="button"
          onClick={toggleSidebar}
          className={[
            "inline-flex h-9 w-9 shrink-0",
            "items-center justify-center rounded-lg",
            "text-text-muted transition",
            "hover:bg-surface-hover hover:text-text",
            "focus-visible:outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-primary",
            "dark:text-gray-400",
            "dark:hover:bg-slate-700/70",
            "dark:hover:text-white",
          ].join(" ")}
          aria-label={toggleLabel}
          aria-expanded={open}
          title={toggleLabel}
        >
          <ContextToggleIcon open={open} />
        </button>
      </header>

      {open ? (
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
          {node ? (
            <ContextContent node={node} schemaVersion={schemaVersion} />
          ) : (
            <EmptyContext />
          )}
        </div>
      ) : (
        <button
          type="button"
          onClick={toggleSidebar}
          className={[
            "flex min-h-0 flex-1",
            "items-center justify-center",
            "text-text-subtle transition",
            "hover:bg-surface-hover hover:text-text",
            "focus-visible:outline-none",
            "focus-visible:ring-2",
            "focus-visible:ring-inset",
            "focus-visible:ring-primary",
            "dark:text-gray-500",
            "dark:hover:bg-slate-800",
            "dark:hover:text-gray-300",
          ].join(" ")}
          aria-label="Kontextleiste ausklappen"
          title="Kontextleiste ausklappen"
        >
          <span
            className={[
              "select-none text-[10px]",
              "font-semibold tracking-[0.18em]",
              "uppercase",
              "[writing-mode:vertical-rl]",
            ].join(" ")}
            aria-hidden="true"
          >
            Kontext
          </span>
        </button>
      )}
    </aside>
  );
}

interface ContextContentProps {
  node: ContextNode;
  schemaVersion?: string;
}

function ContextContent({ node, schemaVersion }: ContextContentProps) {
  return (
    <div className="space-y-5 p-4">
      <ContextSection title="Ausgewählter Knoten">
        <ContextValue label="Name" value={node.name} />

        <ContextValue label="Typ" value={node.type} mono />

        <ContextValue label="ID" value={node.id} mono />
      </ContextSection>

      <ContextSection title="Schema">
        <ContextValue
          label="UI-Schema"
          value={schemaVersion ?? "Nicht verfügbar"}
          mono
        />
      </ContextSection>

      {node.type === "chat" ? (
        <ContextSection title="Chat">
          <ContextValue label="Status" value="Bereit" />

          <ContextValue label="Hierarchieknoten" value={node.id} mono />
        </ContextSection>
      ) : null}
    </div>
  );
}

interface ContextSectionProps {
  title: string;
  children: React.ReactNode;
}

function ContextSection({ title, children }: ContextSectionProps) {
  return (
    <section>
      <h3 className="mb-2 text-xs font-semibold tracking-wide text-text-muted uppercase dark:text-gray-500">
        {title}
      </h3>

      <dl className="overflow-hidden rounded-xl border border-border-soft bg-white/70 dark:border-white/10 dark:bg-slate-900/40">
        {children}
      </dl>
    </section>
  );
}

interface ContextValueProps {
  label: string;
  value: string;
  mono?: boolean;
}

function ContextValue({ label, value, mono = false }: ContextValueProps) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border-soft px-3 py-2.5 last:border-b-0 dark:border-white/10">
      <dt className="shrink-0 text-xs text-text-muted dark:text-gray-500">
        {label}
      </dt>

      <dd
        className={[
          "min-w-0 break-all text-right text-xs",
          "text-text-soft dark:text-gray-300",
          mono ? "font-mono" : "font-medium",
        ].join(" ")}
      >
        {value}
      </dd>
    </div>
  );
}

function EmptyContext() {
  return (
    <div className="p-4">
      <div className="rounded-xl border border-dashed border-border-soft bg-white/50 p-4 text-sm text-text-muted dark:border-white/10 dark:bg-slate-900/30 dark:text-gray-400">
        Wähle einen Eintrag aus der Hierarchie aus, um weitere Informationen
        anzuzeigen.
      </div>
    </div>
  );
}

interface ContextToggleIconProps {
  open: boolean;
}

function ContextToggleIcon({ open }: ContextToggleIconProps) {
  return (
    <svg
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="16" rx="2" strokeWidth="1.8" />

      <path d="M15 4v16" strokeWidth="1.8" />

      {open ? (
        <path
          d="m10 9 3 3-3 3"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.8"
        />
      ) : (
        <path
          d="m13 9-3 3 3 3"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1.8"
        />
      )}
    </svg>
  );
}
