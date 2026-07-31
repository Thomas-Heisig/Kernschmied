import { useEffect, useMemo, useRef, useState } from "react";
import { BookOpen, LoaderCircle, Search, X } from "lucide-react";

import {
  loadDocumentationIndex,
  loadDocumentationPage,
} from "../../api/documentation";
import type {
  DocumentationIndexResponse,
  DocumentationPageResponse,
} from "../../contracts/documentation";
import { MarkdownDocument } from "./MarkdownDocument";

interface DocumentationDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function DocumentationDialog({
  isOpen,
  onClose,
}: DocumentationDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const [index, setIndex] = useState<DocumentationIndexResponse | null>(null);
  const [page, setPage] = useState<DocumentationPageResponse | null>(null);
  const [activePageId, setActivePageId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoadingIndex, setIsLoadingIndex] = useState(false);
  const [isLoadingPage, setIsLoadingPage] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
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
          setError(reason instanceof Error ? reason.message : "Die Dokumentation konnte nicht geladen werden.");
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
          setError(reason instanceof Error ? reason.message : "Die Dokumentationsseite konnte nicht geladen werden.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoadingPage(false);
      });

    return () => controller.abort();
  }, [activePageId, isOpen]);

  const filteredSections = useMemo(() => {
    if (!index) return [];
    const query = search.trim().toLocaleLowerCase("de");
    if (!query) return index.sections;

    return index.sections
      .map((section) => ({
        ...section,
        pages: section.pages.filter((candidate) =>
          `${candidate.title} ${candidate.description}`
            .toLocaleLowerCase("de")
            .includes(query),
        ),
      }))
      .filter((section) => section.pages.length > 0);
  }, [index, search]);

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
              <h1 id="documentation-dialog-title" className="truncate text-base font-semibold text-text dark:text-white">
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
                <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={17} aria-hidden="true" />
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

            <nav className="min-h-0 flex-1 overflow-y-auto p-3" aria-label="Dokumentationsnavigation">
              {isLoadingIndex ? (
                <div className="flex items-center gap-2 px-3 py-4 text-sm text-text-muted">
                  <LoaderCircle className="animate-spin" size={17} />
                  Übersicht wird geladen …
                </div>
              ) : null}

              {filteredSections.map((section) => (
                <section key={section.id} className="mb-5">
                  <h2 className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-text-muted dark:text-slate-500">
                    {section.title}
                  </h2>
                  <div className="space-y-1">
                    {section.pages.map((candidate) => {
                      const isActive = candidate.id === activePageId;
                      return (
                        <button
                          key={candidate.id}
                          type="button"
                          onClick={() => setActivePageId(candidate.id)}
                          className={[
                            "w-full rounded-lg px-3 py-2.5 text-left transition-colors",
                            isActive
                              ? "bg-primary text-white shadow-sm"
                              : "text-text-soft hover:bg-white hover:text-text dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white",
                          ].join(" ")}
                        >
                          <span className="block text-sm font-medium">{candidate.title}</span>
                          {candidate.description ? (
                            <span className={[
                              "mt-0.5 block line-clamp-2 text-xs",
                              isActive ? "text-white/75" : "text-text-muted dark:text-slate-500",
                            ].join(" ")}>
                              {candidate.description}
                            </span>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                </section>
              ))}
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
