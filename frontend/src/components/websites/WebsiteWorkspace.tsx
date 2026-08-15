// F:\Kernschmied\frontend\src\components\websites\WebsiteWorkspace.tsx

import { ExternalLink, Globe2, RefreshCw } from 'lucide-react';
import IconBadge from '../common/IconBadge';
import { useState } from 'react';

interface WebsiteWorkspaceProps {
  websiteId: string;
  title: string;
  embedded?: boolean;
}

const WEBSITE_PREVIEW_URLS: Readonly<Record<string, string>> = {
  'heisig-naturstein-modern': '/selfhtml/heisig-naturstein-modern/index.html',
};

export function WebsiteWorkspace({ websiteId, title, embedded = false }: WebsiteWorkspaceProps) {
  const [reloadRevision, setReloadRevision] = useState(0);

  const normalizedWebsiteId = websiteId.trim().toLowerCase();
  const previewUrl = WEBSITE_PREVIEW_URLS[normalizedWebsiteId];

  if (!previewUrl) {
    return <WebsiteNotConfiguredView websiteId={websiteId} title={title} />;
  }

  const iframeUrl = `${previewUrl}?preview_revision=${reloadRevision}`;

  // Embedded‑Modus (für WorkspaceLayout)
  if (embedded) {
    return (
      <div className="min-h-0 min-w-0 flex-1 overflow-hidden bg-white dark:bg-slate-950">
        <iframe
          key={iframeUrl}
          src={iframeUrl}
          title={`Vorschau: ${title}`}
          className="block h-full min-h-0 w-full border-0 bg-white dark:bg-slate-950"
        />
      </div>
    );
  }

  // Vollständige Ansicht mit Header
  return (
    <section
      className="flex h-full w-full flex-1 flex-col min-h-0 min-w-0 overflow-hidden bg-slate-100 dark:bg-slate-950"
      aria-label={`Webseitenvorschau: ${title}`}
    >
      {/* Header – einheitlich wie AppHeader */}
      <header
        className={[
          'flex shrink-0 items-center justify-between gap-4',
          'border-b border-border bg-white/90 px-4 py-3 shadow-sm backdrop-blur-sm',
          'dark:border-white/10 dark:bg-slate-950/90',
          'sm:px-6',
        ].join(' ')}
      >
        <div className="flex min-w-0 items-center gap-3">
          <div aria-hidden="true">
            <IconBadge icon={<Globe2 />} size="lg" variant="primary" />
          </div>

          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-text dark:text-white">{title}</h1>
            <p
              className="truncate text-xs text-text-muted dark:text-gray-400"
              title={previewUrl}
            >
              {previewUrl}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {/* Refresh‑Button */}
          <button
            type="button"
            className={[
              'inline-flex h-9 items-center justify-center gap-2',
              'rounded-lg border border-border-soft px-3',
              'bg-white text-text-soft',
              'transition hover:bg-surface-hover hover:text-text',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
              'dark:border-white/10 dark:bg-slate-800 dark:text-gray-300 dark:hover:bg-slate-700 dark:hover:text-white',
            ].join(' ')}
            onClick={() => setReloadRevision((prev) => prev + 1)}
            aria-label="Vorschau neu laden"
            title="Vorschau neu laden"
          >
            <IconBadge icon={<RefreshCw />} size="sm" variant="default" />
            <span className="hidden sm:inline">Neu laden</span>
          </button>

          {/* "Neues Fenster"‑Link */}
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={[
              'inline-flex h-9 items-center justify-center gap-2',
              'rounded-lg px-3',
              'bg-primary text-white shadow-glow',
              'transition hover:bg-primary-hover hover:shadow-primary-glow',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
              'dark:bg-primary/80 dark:hover:bg-primary',
            ].join(' ')}
            aria-label="Vorschau in neuem Fenster öffnen"
            title="Vorschau in neuem Fenster öffnen"
          >
            <IconBadge icon={<ExternalLink />} size="sm" variant="default" />
            <span className="hidden sm:inline">Neues Fenster</span>
          </a>
        </div>
      </header>

      {/* Iframe – Inhalt */}
      <div className="min-h-0 min-w-0 flex-1 overflow-hidden bg-white dark:bg-slate-950">
        <iframe
          key={iframeUrl}
          src={iframeUrl}
          title={`Vorschau: ${title}`}
          className="block h-full min-h-0 w-full border-0 bg-white dark:bg-slate-950"
        />
      </div>
    </section>
  );
}

// ============================================================
// Fallback: Keine Vorschau konfiguriert
// ============================================================

interface WebsiteNotConfiguredViewProps {
  websiteId: string;
  title: string;
}

function WebsiteNotConfiguredView({ websiteId, title }: WebsiteNotConfiguredViewProps) {
  return (
    <section
      className={[
        'flex h-full w-full flex-1 min-h-0 min-w-0',
        'items-center justify-center',
        'overflow-auto',
        'bg-slate-50 p-6',
        'dark:bg-slate-950/30',
      ].join(' ')}
    >
      <div
        className={[
          'w-full max-w-xl rounded-2xl',
          'border border-border-soft',
          'bg-white/80 p-6 text-center shadow-sm backdrop-blur-sm',
          'dark:border-white/10 dark:bg-slate-900/50',
        ].join(' ')}
      >
        <div className="mx-auto text-slate-400">
          <IconBadge icon={<Globe2 />} size="lg" variant="primary" />
        </div>

        <h1 className="mt-4 text-xl font-semibold text-text dark:text-white">
          Keine Vorschau konfiguriert
        </h1>

        <p className="mt-2 text-sm text-text-soft dark:text-gray-300">
          Für „{title}“ wurde keine Vorschau-Adresse gefunden.
        </p>

        <p className="mt-4 wrap-break-word rounded-lg bg-surface-muted p-3 font-mono text-xs text-text-soft dark:bg-white/5 dark:text-gray-300">
          Website-ID: {websiteId}
        </p>
      </div>
    </section>
  );
}