// F:\Kernschmied\frontend\src\components\layout\AppHierarchySidebar.tsx

import { useState } from 'react';
import { DynamicIcon } from '../../registry/iconRegistry';

import type { ComponentProps } from 'react';

import { GenericTree } from '../schema/GenericTreeClean';

type GenericTreeProps = ComponentProps<typeof GenericTree>;

interface AppHierarchySidebarProps {
  root: GenericTreeProps['root'];
  schema: GenericTreeProps['schema'];
  selectedNodeId: GenericTreeProps['selectedNodeId'];
  expandedNodeIds: GenericTreeProps['expandedNodeIds'];
  onSelect: GenericTreeProps['onSelect'];
  onExpandedNodeIdsChange: GenericTreeProps['onExpandedNodeIdsChange'];
  onAction?: GenericTreeProps['onAction'];
  onCreateChat?: GenericTreeProps['onCreateChat'];
  onNodeDrop?: GenericTreeProps['onNodeDrop'];
  isBusy?: boolean;
  recentlyMovedNodeId?: string | null;

  defaultOpen?: boolean;
  onCreatePublicWorkspace?: () => void;
  onCreateInternWorkspace?: () => void;
  onCreateUser?: () => void;
}

export function AppHierarchySidebar({
  root,
  schema,
  selectedNodeId,
  expandedNodeIds,
  onSelect,
  onExpandedNodeIdsChange,
  onAction,
  onCreateChat,
  onNodeDrop,
  isBusy = false,
  recentlyMovedNodeId = null,
  defaultOpen = true,
  onCreatePublicWorkspace,
  onCreateInternWorkspace,
  onCreateUser,
}: AppHierarchySidebarProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [filterText, setFilterText] = useState('');
  const [showArchived, setShowArchived] = useState(false);

  function toggleSidebar(): void {
    setOpen((currentOpen) => !currentOpen);
  }

  const toggleLabel = open ? 'Hierarchie einklappen' : 'Hierarchie ausklappen';

  return (
    <aside
      className={[
        'flex h-full min-h-0 shrink-0 flex-col',
        'border-r border-border',
        'bg-white/80 shadow-glass backdrop-blur-md',
        'transition-[width] duration-200 ease-out',
        'dark:border-white/10 dark:bg-slate-800/80',
        open ? 'w-72' : 'w-12',
      ].join(' ')}
      aria-label="Anwendungshierarchie"
      data-state={open ? 'open' : 'collapsed'}
    >
      <header
        className={[
          'flex shrink-0 border-b border-border',
          'dark:border-white/10',
          open
            ? 'min-h-16 items-center justify-between gap-3 px-4 py-3'
            : 'h-12 items-center justify-center px-1',
        ].join(' ')}
      >
        {open ? (
          <div className="flex w-full items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="truncate text-sm font-semibold tracking-wide text-text uppercase dark:text-white">
                Hierarchie
              </h2>

              <p className="mt-1 truncate text-xs text-text-muted dark:text-gray-400">
                Arbeitsbereiche, Projekte und Chats
              </p>

              <div className="mt-3 grid grid-cols-3 gap-2">
                {/* Bento-style icon grid (icons-only, helptext on hover) */}
                <button
                  type="button"
                  onClick={() => onCreateUser?.()}
                  className="flex h-10 w-10 items-center justify-center rounded border border-border bg-transparent hover:bg-surface-hover"
                  title="Neuer Benutzer"
                  aria-label="Neuer Benutzer"
                >
                  <DynamicIcon name="UserCircle" size={16} />
                </button>

                <button
                  type="button"
                  onClick={() => onCreatePublicWorkspace?.()}
                  className="flex h-10 w-10 items-center justify-center rounded border border-border bg-transparent hover:bg-surface-hover"
                  title="Neuer Public-Bereich"
                  aria-label="Neuer Public-Bereich"
                >
                  <DynamicIcon name="Building2" size={16} />
                </button>

                <button
                  type="button"
                  onClick={() => onCreateInternWorkspace?.()}
                  className="flex h-10 w-10 items-center justify-center rounded border border-border bg-transparent hover:bg-surface-hover"
                  title="Neuer interner Bereich"
                  aria-label="Neuer interner Bereich"
                >
                  <DynamicIcon name="FolderKanban" size={16} />
                </button>
              </div>
            </div>

            <div className="flex items-center">
              <button
                type="button"
                onClick={toggleSidebar}
                className={[
                  'inline-flex h-9 w-9 shrink-0',
                  'items-center justify-center rounded-lg',
                  'text-text-muted transition',
                  'hover:bg-surface-hover hover:text-text',
                  'focus-visible:outline-none',
                  'focus-visible:ring-2',
                  'focus-visible:ring-primary',
                  'dark:text-gray-400',
                  'dark:hover:bg-slate-700/70',
                  'dark:hover:text-white',
                ].join(' ')}
                aria-label={toggleLabel}
                aria-expanded={open}
                title={toggleLabel}
              >
                <HierarchyToggleIcon open={open} />
              </button>
            </div>
          </div>
        ) : null}
        {!open ? (
          <button
            type="button"
            onClick={toggleSidebar}
            className={[
              'flex min-h-0 flex-1',
              'items-center justify-center',
              'text-text-subtle transition',
              'hover:bg-surface-hover hover:text-text',
              'focus-visible:outline-none',
              'focus-visible:ring-2',
              'focus-visible:ring-inset',
              'focus-visible:ring-primary',
              'dark:text-gray-500',
              'dark:hover:bg-slate-800',
              'dark:hover:text-gray-300',
            ].join(' ')}
            aria-label="Hierarchie ausklappen"
            title="Hierarchie ausklappen"
          >
            <span
              className={[
                'select-none text-[10px]',
                'font-semibold tracking-[0.18em]',
                'uppercase',
                '[writing-mode:vertical-rl]',
              ].join(' ')}
              aria-hidden="true"
            >
              Hierarchie
            </span>
          </button>
        ) : null}
      </header>

      {open ? (
        <nav
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-2"
          aria-label="Hierarchiebaum"
        >
          <div className="relative">
              <div className="mb-3 px-2 flex items-center gap-2">
                <input
                  type="search"
                  className="flex-1 rounded border px-2 py-1"
                  placeholder="Filter..."
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                  aria-label="Hierarchie filtern"
                />

                <button
                  type="button"
                  onClick={() => setShowArchived((s) => !s)}
                  className={[
                    'inline-flex h-8 w-8 items-center justify-center rounded hover:bg-surface-hover',
                    showArchived ? 'bg-surface/60 ring-2 ring-primary/30' : '',
                  ].join(' ')}
                  title={showArchived ? 'Archiv ausblenden' : 'Archiv anzeigen'}
                  aria-pressed={showArchived}
                  aria-label="Archiv anzeigen"
                >
                  <DynamicIcon name="Archive" size={16} />
                </button>
              </div>
            {isBusy ? (
              <div className="absolute inset-0 z-40 flex items-center justify-center bg-white/60 dark:bg-slate-900/60">
                <svg className="h-8 w-8 animate-spin text-text-muted" viewBox="0 0 24 24">
                  <circle
                    cx="12"
                    cy="12"
                    r="10"
                    strokeWidth="4"
                    stroke="currentColor"
                    strokeDasharray="60"
                    strokeLinecap="round"
                    fill="none"
                  ></circle>
                </svg>
              </div>
            ) : null}
            <GenericTree
              root={root}
              schema={schema}
              selectedNodeId={selectedNodeId}
              expandedNodeIds={expandedNodeIds}
              onSelect={onSelect}
              onExpandedNodeIdsChange={onExpandedNodeIdsChange}
              onAction={onAction}
              onCreateChat={onCreateChat}
              onNodeDrop={onNodeDrop}
              filterText={filterText}
              showArchived={showArchived}
              isBusy={isBusy}
              recentlyMovedNodeId={recentlyMovedNodeId}
            />
          </div>
        </nav>
      ) : (
        <button
          type="button"
          onClick={toggleSidebar}
          className={[
            'flex min-h-0 flex-1',
            'items-center justify-center',
            'text-text-subtle transition',
            'hover:bg-surface-hover hover:text-text',
            'focus-visible:outline-none',
            'focus-visible:ring-2',
            'focus-visible:ring-inset',
            'focus-visible:ring-primary',
            'dark:text-gray-500',
            'dark:hover:bg-slate-800',
            'dark:hover:text-gray-300',
          ].join(' ')}
          aria-label="Hierarchie ausklappen"
          title="Hierarchie ausklappen"
        >
          <span
            className={[
              'select-none text-[10px]',
              'font-semibold tracking-[0.18em]',
              'uppercase',
              '[writing-mode:vertical-rl]',
            ].join(' ')}
            aria-hidden="true"
          >
            Hierarchie
          </span>
        </button>
      )}
    </aside>
  );
}

interface HierarchyToggleIconProps {
  open: boolean;
}

function HierarchyToggleIcon({ open }: HierarchyToggleIconProps) {
  return (
    <svg
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="16" rx="2" strokeWidth="1.8" />

      <path d="M9 4v16" strokeWidth="1.8" />

      {open ? (
        <path d="m14 9-3 3 3 3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
      ) : (
        <path d="m11 9 3 3-3 3" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
      )}
    </svg>
  );
}
