// F:\Kernschmied\frontend\src\components\websites\WebsiteWorkspace.tsx

import { ExternalLink, Globe2, RefreshCw } from "lucide-react";
import { useState } from "react";

interface WebsiteWorkspaceProps {
  websiteId: string;
  title: string;
}

const WEBSITE_PREVIEW_URLS: Readonly<Record<string, string>> = {
  "heisig-naturstein-modern": "/selfhtml/heisig-naturstein-modern/index.html",
};

export function WebsiteWorkspace({ websiteId, title }: WebsiteWorkspaceProps) {
  const [reloadRevision, setReloadRevision] = useState(0);

  const normalizedWebsiteId = websiteId.trim().toLowerCase();

  const previewUrl = WEBSITE_PREVIEW_URLS[normalizedWebsiteId];

  if (!previewUrl) {
    return <WebsiteNotConfiguredView websiteId={websiteId} title={title} />;
  }

  const iframeUrl = `${previewUrl}?preview_revision=${reloadRevision}`;

  return (
    <section
      className={[
        "flex min-h-0 min-w-0",
        "h-full w-full flex-1 flex-col",
        "overflow-hidden",
        "bg-slate-100",
        "dark:bg-slate-950",
      ].join(" ")}
      aria-label={`Webseitenvorschau: ${title}`}
    >
      <header
        className={[
          "flex shrink-0",
          "items-center justify-between",
          "gap-4",
          "border-b border-slate-200",
          "bg-white px-4 py-3",
          "dark:border-white/10",
          "dark:bg-slate-900",
          "sm:px-6",
        ].join(" ")}
      >
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={[
              "flex h-10 w-10 shrink-0",
              "items-center justify-center",
              "rounded-xl",
              "border border-blue-200",
              "bg-blue-50 text-blue-600",
              "dark:border-blue-400/20",
              "dark:bg-blue-500/10",
              "dark:text-blue-400",
            ].join(" ")}
            aria-hidden="true"
          >
            <Globe2 size={20} />
          </div>

          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-slate-950 dark:text-white">
              {title}
            </h1>

            <p
              className="truncate text-xs text-slate-500 dark:text-slate-400"
              title={previewUrl}
            >
              {previewUrl}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            className={[
              "inline-flex h-9 items-center",
              "justify-center gap-2 rounded-lg",
              "border border-slate-200",
              "bg-white px-3",
              "text-sm font-medium",
              "text-slate-700",
              "transition hover:bg-slate-100",
              "dark:border-white/10",
              "dark:bg-slate-800",
              "dark:text-slate-200",
              "dark:hover:bg-slate-700",
            ].join(" ")}
            onClick={() => {
              setReloadRevision((currentRevision) => currentRevision + 1);
            }}
          >
            <RefreshCw size={16} aria-hidden="true" />

            <span className="hidden sm:inline">Neu laden</span>
          </button>

          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={[
              "inline-flex h-9 items-center",
              "justify-center gap-2 rounded-lg",
              "bg-blue-600 px-3",
              "text-sm font-medium",
              "text-white transition",
              "hover:bg-blue-700",
            ].join(" ")}
          >
            <ExternalLink size={16} aria-hidden="true" />

            <span className="hidden sm:inline">Neues Fenster</span>
          </a>
        </div>
      </header>

      <div className="min-h-0 min-w-0 flex-1 overflow-hidden bg-white">
        <iframe
          key={iframeUrl}
          src={iframeUrl}
          title={`Vorschau: ${title}`}
          className="block h-full min-h-0 w-full border-0 bg-white"
        />
      </div>
    </section>
  );
}

interface WebsiteNotConfiguredViewProps {
  websiteId: string;
  title: string;
}

function WebsiteNotConfiguredView({
  websiteId,
  title,
}: WebsiteNotConfiguredViewProps) {
  return (
    <section
      className={[
        "flex min-h-0 min-w-0",
        "h-full w-full flex-1",
        "items-center justify-center",
        "overflow-auto",
        "bg-slate-50 p-6",
        "dark:bg-slate-950/30",
      ].join(" ")}
    >
      <div
        className={[
          "w-full max-w-xl rounded-2xl",
          "border border-slate-200",
          "bg-white p-6 text-center",
          "shadow-sm",
          "dark:border-white/10",
          "dark:bg-slate-900/50",
        ].join(" ")}
      >
        <Globe2
          size={36}
          className="mx-auto text-slate-400"
          aria-hidden="true"
        />

        <h1 className="mt-4 text-xl font-semibold text-slate-950 dark:text-white">
          Keine Vorschau konfiguriert
        </h1>

        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Für „{title}“ wurde keine Vorschau-Adresse gefunden.
        </p>

        <p className="mt-4 wrap-break-word rounded-lg bg-slate-100 p-3 font-mono text-xs text-slate-700 dark:bg-white/5 dark:text-slate-300">
          Website-ID: {websiteId}
        </p>
      </div>
    </section>
  );
}
