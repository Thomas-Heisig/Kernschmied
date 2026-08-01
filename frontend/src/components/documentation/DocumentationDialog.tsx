import { useEffect, useMemo, useRef, useState } from 'react';
import { BookOpen, LoaderCircle, Search, X, ChevronDown, ChevronRight } from 'lucide-react';

import { loadDocumentationIndex, loadDocumentationPage } from '../../api/documentation';
import type {
  DocumentationIndexResponse,
  DocumentationPageResponse,
} from '../../contracts/documentation';
import { MarkdownDocument } from './MarkdownDocument';

interface DocumentationDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentationDialog({ isOpen, onClose }: DocumentationDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const [index, setIndex] = useState<DocumentationIndexResponse | null>(null);
  const [page, setPage] = useState<DocumentationPageResponse | null>(null);
  const [activePageId, setActivePageId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const navRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingIndex, setIsLoadingIndex] = useState(false);
  const [isLoadingPage, setIsLoadingPage] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen || index !== null) return;

    const controller = new AbortController();
    setIsLoadingIndex(true);
    setError(null);

    void loadDocumentationIndex(controller.signal)
      .then((result) => {
        setIndex(result);
        setActivePageId(result.default_page_id);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : 'Die Dokumentation konnte nicht geladen werden.',
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingIndex(false);
      });

    return () => controller.abort();
  }, [index, isOpen]);

  useEffect(() => {
    if (!isOpen || activePageId === null) return;

    const controller = new AbortController();
    setIsLoadingPage(true);
    setError(null);

    void loadDocumentationPage(activePageId, controller.signal)
      .then(setPage)
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            reason instanceof Error
              ? reason.message
              : 'Die Dokumentationsseite konnte nicht geladen werden.',
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingPage(false);
      });

    return () => controller.abort();
  }, [activePageId, isOpen]);

  const filteredSections = useMemo(() => {
    if (!index) return [];
    const query = search.trim().toLocaleLowerCase('de');
    if (!query) return index.sections;

    return index.sections
      .map((section) => ({
        ...section,
        pages: section.pages.filter((candidate) =>
          `${candidate.title} ${candidate.description}`.toLocaleLowerCase('de').includes(query),
        ),
      }))
      .filter((section) => section.pages.length > 0);
  }, [index, search]);

  useEffect(() => {
    // initialize all sections as collapsed by default
    if (!index) return;
    const map: Record<string, boolean> = {};
    for (const s of index.sections) map[s.id] = s.id === 'user-manual';

    // load persisted state
    try {
      const raw = localStorage.getItem('docs:expandedSections');
      if (raw) {
        const persisted = JSON.parse(raw) as Record<string, boolean>;
        setExpandedSections((prev) => ({ ...map, ...persisted, ...prev }));
        return;
      }
    } catch {
      /* ignore */
    }

    setExpandedSections((prev) => ({ ...map, ...prev }));
  }, [index]);

  useEffect(() => {
    try {
      localStorage.setItem('docs:expandedSections', JSON.stringify(expandedSections));
    } catch {
      /* ignore */
    }
  }, [expandedSections]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-3 backdrop-blur-sm sm:p-5 lg:p-8"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="flex h-[min(92vh,960px)] min-h-0 w-full max-w-7xl flex-col overflow-hidden rounded-2xl border border-border-soft bg-white shadow-2xl dark:border-white/10 dark:bg-slate-950"
        role="dialog"
        aria-modal="true"
        aria-labelledby="documentation-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border bg-white px-4 dark:border-white/10 dark:bg-slate-950 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary dark:bg-primary/20">
              <BookOpen size={21} aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <h1
                id="documentation-dialog-title"
                className="truncate text-base font-semibold text-text dark:text-white"
              >
                Dokumentation & Benutzerhandbuch
              </h1>
              <p className="truncate text-xs text-text-muted dark:text-slate-400">
                Lokale, versionierte Kernschmied-Dokumentation
              </p>
            </div>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-text-soft transition-colors hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            aria-label="Dokumentation schließen"
            title="Schließen"
            onClick={onClose}
          >
            <X size={19} aria-hidden="true" />
          </button>
        </header>

        <div className="flex min-h-0 flex-1 overflow-hidden">
          <aside className="hidden w-80 shrink-0 flex-col border-r border-border bg-surface-muted/60 dark:border-white/10 dark:bg-slate-900/40 md:flex">
            <div className="border-b border-border p-4 dark:border-white/10">
              <label className="relative block">
                <Search
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted"
                  size={17}
                  aria-hidden="true"
                />
                <span className="sr-only">Dokumentation durchsuchen</span>
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Dokumentation durchsuchen …"
                  className="h-10 w-full rounded-lg border border-border bg-white pl-10 pr-3 text-sm text-text outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-950 dark:text-white"
                />
              </label>
            </div>

            <nav
              className="min-h-0 flex-1 overflow-y-auto p-3"
              aria-label="Dokumentationsnavigation"
            >
              {isLoadingIndex ? (
                <div className="flex items-center gap-2 px-3 py-4 text-sm text-text-muted">
                  <LoaderCircle className="animate-spin" size={17} />
                  Übersicht wird geladen …
                </div>
              ) : null}

              {filteredSections.map((section) => {
                const isExpanded = !!expandedSections[section.id];
                return (
                  <section key={section.id} className="mb-5">
                    <button
                      type="button"
                      aria-expanded={isExpanded}
                      data-doc-button
                      onClick={() =>
                        setExpandedSections((prev) => ({
                          ...prev,
                          [section.id]: !prev[section.id],
                        }))
                      }
                      className="flex w-full items-center justify-between px-3 pb-2"
                    >
                      <h2 className="text-[11px] font-semibold uppercase tracking-wider text-text-muted dark:text-slate-500">
                        {section.title}
                      </h2>
                      <span className="text-xs text-text-muted">
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </span>
                    </button>

                    <div
                      ref={navRef}
                      className={isExpanded ? 'space-y-1' : 'hidden'}
                      onKeyDown={(e) => {
                        // keyboard navigation within expanded section
                        const el = navRef.current;
                        if (!el) return;
                        const buttons = Array.from(
                          el.querySelectorAll<HTMLButtonElement>('button[data-doc-button]'),
                        );
                        if (!buttons.length) return;

                        const active = document.activeElement as HTMLElement | null;
                        const idx = buttons.findIndex((b) => b === active);

                        if (e.key === 'ArrowDown') {
                          e.preventDefault();
                          const next = buttons[Math.min(Math.max(0, idx + 1), buttons.length - 1)];
                          next?.focus();
                        } else if (e.key === 'ArrowUp') {
                          e.preventDefault();
                          const prev = buttons[Math.min(Math.max(0, idx - 1), buttons.length - 1)];
                          prev?.focus();
                        } else if (e.key === 'Home') {
                          e.preventDefault();
                          buttons[0]?.focus();
                        } else if (e.key === 'End') {
                          e.preventDefault();
                          buttons[buttons.length - 1]?.focus();
                        }
                      }}
                    >
                      {section.pages.map((candidate) => {
                        const isActive = candidate.id === activePageId;
                        return (
                          <button
                            key={candidate.id}
                            type="button"
                            data-doc-button
                            onClick={() => setActivePageId(candidate.id)}
                            className={[
                              'w-full rounded-lg px-3 py-2.5 text-left transition-colors',
                              isActive
                                ? 'bg-primary text-white shadow-sm'
                                : 'text-text-soft hover:bg-white hover:text-text dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white',
                            ].join(' ')}
                          >
                            <span className="block text-sm font-medium">{candidate.title}</span>
                            {candidate.description ? (
                              <span
                                className={[
                                  'mt-0.5 block line-clamp-2 text-xs',
                                  isActive
                                    ? 'text-white/75'
                                    : 'text-text-muted dark:text-slate-500',
                                ].join(' ')}
                              >
                                {candidate.description}
                              </span>
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  </section>
                );
              })}
            </nav>
          </aside>

          <main className="min-w-0 flex-1 overflow-y-auto bg-white dark:bg-slate-950">
            {error ? (
              <div className="m-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200">
                {error}
              </div>
            ) : null}

            {isLoadingPage ? (
              <div className="flex h-full min-h-80 items-center justify-center gap-3 text-text-muted dark:text-slate-400">
                <LoaderCircle className="animate-spin" size={22} />
                Dokumentationsseite wird geladen …
              </div>
            ) : page ? (
              <>
                <div className="border-b border-border bg-surface-muted/40 px-5 py-3 text-xs text-text-muted dark:border-white/10 dark:bg-slate-900/30 dark:text-slate-400 sm:px-8 lg:px-12">
                  {page.section_title} / {page.title}
                </div>
                <MarkdownDocument content={page.content} />
              </>
            ) : !error && index ? (
              // Wiki-like start page: show sections and pages for navigation
              <div className="prose max-w-none p-6 sm:p-8 lg:p-12">
                <h2>Willkommen zur Dokumentation</h2>
                <p>
                  Hier findest du eine Übersicht über alle zentralen Dokumentationen. Klicke auf
                  einen Eintrag, um die Seite zu öffnen.
                </p>
                {index.sections.map((section) => (
                  <div key={section.id} className="mb-6">
                    <h3 className="mb-2 text-sm font-semibold">{section.title}</h3>
                    <ul className="ml-4 list-disc">
                      {section.pages.map((p) => (
                        <li key={p.id} className="mb-1">
                          <button
                            type="button"
                            onClick={() => setActivePageId(p.id)}
                            className="text-left text-sm text-primary hover:underline"
                          >
                            {p.title}
                          </button>
                          {p.description ? (
                            <div className="text-xs text-text-muted">{p.description}</div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : !error ? (
              <div className="flex h-full min-h-80 items-center justify-center text-sm text-text-muted">
                Wähle eine Dokumentationsseite aus.
              </div>
            ) : null}
          </main>
        </div>
      </section>
    </div>
  );
}
