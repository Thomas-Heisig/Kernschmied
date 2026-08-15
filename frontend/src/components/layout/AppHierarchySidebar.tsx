// F:\Kernschmied\frontend\src\components\layout\AppHierarchySidebar.tsx

import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, ChevronsUp, Clock3, Focus, LoaderCircle, Search, Star } from 'lucide-react';
import { DynamicIcon } from '../../registry/iconRegistry';
import IconBadge from '../common/IconBadge';
import { getNodeTypeConfig } from '../../config/nodeTypeConfig';
import {
  FAVORITE_NODE_STORAGE_KEY,
  MAX_QUICK_ACCESS_ITEMS,
  readStoredNodeIds,
  RECENT_NODE_STORAGE_KEY,
} from '../hierarchy/quickAccessStorage';

import type { ComponentProps, ReactNode } from 'react';
import type { HierarchyNode } from '../../contracts/hierarchy';

import { GenericTree } from '../schema/GenericTreeClean';

type GenericTreeProps = ComponentProps<typeof GenericTree>;
type NodeTypeFilter = 'all' | 'chat' | 'project' | 'workspace';

const TYPE_FILTERS: Array<{ value: NodeTypeFilter; label: string; types: string[] }> = [
  { value: 'all', label: 'Alle', types: [] },
  { value: 'chat', label: 'Chats', types: ['chat', 'conversation'] },
  { value: 'project', label: 'Projekte', types: ['project', 'projekt'] },
  { value: 'workspace', label: 'Bereiche', types: ['workspace', 'bereich'] },
];

function flattenTree(root: HierarchyNode): HierarchyNode[] {
  return [root, ...root.children.flatMap(flattenTree)];
}

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
  const [filterText, setFilterText] = useState('');
  const [showArchived, setShowArchived] = useState(false);
  const [open, setOpen] = useState<boolean>(Boolean(defaultOpen));
  const [typeFilter, setTypeFilter] = useState<NodeTypeFilter>('all');
  const [recentNodeIds, setRecentNodeIds] = useState<string[]>(() => readStoredNodeIds(RECENT_NODE_STORAGE_KEY));
  const [favoriteNodeIds, setFavoriteNodeIds] = useState<Set<string>>(
    () => new Set(readStoredNodeIds(FAVORITE_NODE_STORAGE_KEY)),
  );
  const [focusMode, setFocusMode] = useState(false);

  const allNodes = useMemo(() => flattenTree(root), [root]);
  const nodesById = useMemo(() => new Map(allNodes.map((node) => [node.id, node])), [allNodes]);
  const recentNodes = recentNodeIds
    .map((id) => nodesById.get(id))
    .filter((node): node is HierarchyNode => Boolean(node));
  const favoriteNodes = allNodes
    .filter((node) => favoriteNodeIds.has(node.id))
    .slice(0, MAX_QUICK_ACCESS_ITEMS);
  const activeTypeFilter = TYPE_FILTERS.find((filter) => filter.value === typeFilter);
  const visibleNodeTypes = useMemo(
    () => new Set(activeTypeFilter?.types ?? []),
    [activeTypeFilter],
  );

  useEffect(() => {
    window.localStorage.setItem(RECENT_NODE_STORAGE_KEY, JSON.stringify(recentNodeIds));
  }, [recentNodeIds]);

  useEffect(() => {
    window.localStorage.setItem(FAVORITE_NODE_STORAGE_KEY, JSON.stringify([...favoriteNodeIds]));
  }, [favoriteNodeIds]);

  function handleSelect(node: HierarchyNode): void {
    setRecentNodeIds((current) => [node.id, ...current.filter((id) => id !== node.id)].slice(0, MAX_QUICK_ACCESS_ITEMS));
    if (focusMode) {
      const ancestorIds = new Set<string>();
      let parentId = node.parent_id;
      while (parentId) {
        ancestorIds.add(parentId);
        parentId = nodesById.get(parentId)?.parent_id;
      }
      onExpandedNodeIdsChange?.(ancestorIds);
    }
    onSelect(node);
  }

  function toggleFavorite(node: HierarchyNode): void {
    setFavoriteNodeIds((current) => {
      const next = new Set(current);
      if (next.has(node.id)) next.delete(node.id);
      else next.add(node.id);
      return next;
    });
  }

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
        open ? 'w-80' : 'w-12',
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
            </div>
          </div>
        ) : null}

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
          <IconBadge
            icon={open ? <ChevronLeft /> : <ChevronRight />}
            size="sm"
            variant="default"
          />
        </button>
      </header>

      {open ? (
        <>
          <nav
            className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-2"
            aria-label="Hierarchiebaum"
          >
            <div className="relative">
              <div className="mb-2 flex items-center gap-2 px-2">
                <label className="relative min-w-0 flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-subtle" size={15} />
                  <input
                    type="search"
                    className="w-full rounded-lg border border-border-soft bg-white/70 py-2 pl-10 pr-3 text-sm text-text outline-none transition placeholder:text-text-subtle focus:border-primary focus:ring-2 focus:ring-primary/20 dark:border-white/10 dark:bg-slate-800/50 dark:text-white dark:placeholder:text-gray-500 dark:focus:ring-primary/20"
                    placeholder="Suchen…"
                    value={filterText}
                    onChange={(e) => setFilterText(e.target.value)}
                    aria-label="Hierarchie durchsuchen"
                  />
                </label>

                <button
                  type="button"
                  onClick={() => setShowArchived((s) => !s)}
                  className={[
                    'inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition',
                    'hover:bg-surface-hover',
                    showArchived ? 'bg-primary-soft text-primary dark:bg-primary/20 dark:text-primary' : 'text-text-muted',
                  ].join(' ')}
                  title={showArchived ? 'Archiv ausblenden' : 'Archiv anzeigen'}
                  aria-pressed={showArchived}
                  aria-label="Archiv anzeigen"
                >
                  <IconBadge icon={<DynamicIcon name="Archive" />} size="sm" variant={showArchived ? 'primary' : 'default'} />
                </button>
              </div>

              <div className="mb-3 grid grid-cols-4 gap-1 px-2" aria-label="Knotentyp filtern">
                {TYPE_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    type="button"
                    onClick={() => setTypeFilter(filter.value)}
                    className={[
                      'min-w-0 rounded-md px-1.5 py-1.5 text-[11px] font-medium transition',
                      typeFilter === filter.value
                        ? 'bg-primary text-white'
                        : 'bg-surface-hover text-text-muted hover:text-text dark:bg-slate-700/60 dark:text-gray-300',
                    ].join(' ')}
                    aria-pressed={typeFilter === filter.value}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>

              {(favoriteNodes.length > 0 || recentNodes.length > 0) && !filterText ? (
                <div className="mb-3 space-y-3 border-y border-border-soft px-2 py-3 dark:border-white/10">
                  {favoriteNodes.length > 0 ? (
                    <QuickAccessSection title="Favoriten" icon={<Star size={13} />} nodes={favoriteNodes} onSelect={handleSelect} />
                  ) : null}
                  {recentNodes.length > 0 ? (
                    <QuickAccessSection title="Zuletzt verwendet" icon={<Clock3 size={13} />} nodes={recentNodes} onSelect={handleSelect} />
                  ) : null}
                </div>
              ) : null}

              {isBusy ? (
                <div className="absolute inset-0 z-40 flex items-center justify-center bg-white/60 dark:bg-slate-900/60">
                  <IconBadge icon={<LoaderCircle className="animate-spin" />} size="lg" variant="default" />
                </div>
              ) : null}

              <GenericTree
                root={root}
                schema={schema}
                selectedNodeId={selectedNodeId}
                expandedNodeIds={expandedNodeIds}
                onSelect={handleSelect}
                onExpandedNodeIdsChange={onExpandedNodeIdsChange}
                onAction={onAction}
                onCreateChat={onCreateChat}
                onNodeDrop={onNodeDrop}
                filterText={filterText}
                showArchived={showArchived}
                isBusy={isBusy}
                recentlyMovedNodeId={recentlyMovedNodeId}
                visibleNodeTypes={visibleNodeTypes}
                favoriteNodeIds={favoriteNodeIds}
                onToggleFavorite={toggleFavorite}
              />
            </div>
          </nav>
        </>
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

      <footer
        className={[
          'flex shrink-0 border-t border-border dark:border-white/10',
          'dark:bg-slate-800/80 bg-white/80',
          open ? 'p-3' : 'p-2',
        ].join(' ')}
      >
        {open ? (
          <div className="flex w-full items-center justify-start gap-2">
            <div className="flex items-center gap-2">
              {onCreateUser ? (
                <button
                  type="button"
                  onClick={onCreateUser}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-soft bg-transparent hover:bg-surface-hover dark:border-white/10 dark:hover:bg-slate-800"
                  title="Neuer Benutzer"
                  aria-label="Neuer Benutzer"
                >
                  <IconBadge icon={<DynamicIcon name="UserCircle" />} size="sm" variant="secondary" />
                </button>
              ) : null}

              {onCreatePublicWorkspace ? (
                <button
                  type="button"
                  onClick={onCreatePublicWorkspace}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-soft bg-transparent hover:bg-surface-hover dark:border-white/10 dark:hover:bg-slate-800"
                  title="Neuer Public-Bereich"
                  aria-label="Neuer Public-Bereich"
                >
                  <IconBadge icon={<DynamicIcon name="Building2" />} size="sm" variant="primary" />
                </button>
              ) : null}

              {onCreateInternWorkspace ? (
                <button
                  type="button"
                  onClick={onCreateInternWorkspace}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-soft bg-transparent hover:bg-surface-hover dark:border-white/10 dark:hover:bg-slate-800"
                  title="Neuer interner Bereich"
                  aria-label="Neuer interner Bereich"
                >
                  <IconBadge icon={<DynamicIcon name="FolderKanban" />} size="sm" variant="primary" />
                </button>
              ) : null}

              <button
                type="button"
                onClick={() => setFocusMode((current) => !current)}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-soft bg-transparent hover:bg-surface-hover dark:border-white/10 dark:hover:bg-slate-800"
                title={focusMode ? 'Fokusmodus ausschalten' : 'Fokusmodus: nur aktiven Pfad offen halten'}
                aria-label="Fokusmodus"
                aria-pressed={focusMode}
              >
                <IconBadge icon={<Focus />} size="sm" variant={focusMode ? 'primary' : 'default'} />
              </button>

              <button
                type="button"
                onClick={() => onExpandedNodeIdsChange?.(new Set())}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-soft bg-transparent hover:bg-surface-hover dark:border-white/10 dark:hover:bg-slate-800"
                title="Alle Knoten einklappen"
                aria-label="Alle Knoten einklappen"
              >
                <IconBadge icon={<ChevronsUp />} size="sm" variant="default" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex w-full flex-col items-center gap-2">
            {onCreateUser ? (
              <div className="group relative">
                <button
                  type="button"
                  onClick={onCreateUser}
                  className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-surface-hover dark:hover:bg-slate-800"
                  title="Neuer Benutzer"
                  aria-label="Neuer Benutzer"
                >
                  <IconBadge icon={<DynamicIcon name="UserCircle" />} size="sm" variant="secondary" />
                </button>
                <span className="pointer-events-none absolute left-full ml-2 top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-1 text-xs text-white group-hover:block">
                  Neuer Benutzer
                </span>
              </div>
            ) : null}

            {onCreatePublicWorkspace ? (
              <div className="group relative">
                <button
                  type="button"
                  onClick={onCreatePublicWorkspace}
                  className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-surface-hover dark:hover:bg-slate-800"
                  title="Neuer Public-Bereich"
                  aria-label="Neuer Public-Bereich"
                >
                  <IconBadge icon={<DynamicIcon name="Building2" />} size="sm" variant="primary" />
                </button>
                <span className="pointer-events-none absolute left-full ml-2 top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-1 text-xs text-white group-hover:block">
                  Neuer Public-Bereich
                </span>
              </div>
            ) : null}

            {onCreateInternWorkspace ? (
              <div className="group relative">
                <button
                  type="button"
                  onClick={onCreateInternWorkspace}
                  className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-surface-hover dark:hover:bg-slate-800"
                  title="Neuer interner Bereich"
                  aria-label="Neuer interner Bereich"
                >
                  <IconBadge icon={<DynamicIcon name="FolderKanban" />} size="sm" variant="primary" />
                </button>
                <span className="pointer-events-none absolute left-full ml-2 top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-1 text-xs text-white group-hover:block">
                  Neuer interner Bereich
                </span>
              </div>
            ) : null}

            <div className="group relative">
              <button
                type="button"
                onClick={() => {}}
                className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-surface-hover dark:hover:bg-slate-800"
                title="Platzhalter"
                aria-label="Platzhalter"
              >
                <IconBadge icon={<DynamicIcon name="Plus" />} size="sm" variant="default" />
              </button>
              <span className="pointer-events-none absolute left-full ml-2 top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-1 text-xs text-white group-hover:block">
                Platzhalter
              </span>
            </div>

            <div className="group relative">
              <button
                type="button"
                onClick={() => {}}
                className="flex h-9 w-9 items-center justify-center rounded-lg hover:bg-surface-hover dark:hover:bg-slate-800"
                title="Platzhalter 2"
                aria-label="Platzhalter 2"
              >
                <IconBadge icon={<DynamicIcon name="Wrench" />} size="sm" variant="default" />
              </button>
              <span className="pointer-events-none absolute left-full ml-2 top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded bg-black/80 px-2 py-1 text-xs text-white group-hover:block">
                Platzhalter 2
              </span>
            </div>
          </div>
        )}
      </footer>
    </aside>
  );
}

function QuickAccessSection({
  title,
  icon,
  nodes,
  onSelect,
}: {
  title: string;
  icon: ReactNode;
  nodes: HierarchyNode[];
  onSelect: (node: HierarchyNode) => void;
}) {
  return (
    <section aria-label={title}>
      <h3 className="mb-1.5 flex items-center gap-1.5 px-1 text-[10px] font-semibold uppercase text-text-subtle">
        {icon}
        {title}
      </h3>
      <div className="space-y-0.5">
        {nodes.map((node) => {
          const config = getNodeTypeConfig(node.type);
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => onSelect(node)}
              className="flex w-full min-w-0 items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs text-text-muted hover:bg-surface-hover hover:text-text dark:text-gray-300 dark:hover:bg-slate-700"
            >
              <DynamicIcon name={config.icon} size={14} />
              <span className="truncate">{node.name}</span>
              <span className="ml-auto shrink-0 text-[10px] text-text-subtle">{config.label ?? node.type}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}