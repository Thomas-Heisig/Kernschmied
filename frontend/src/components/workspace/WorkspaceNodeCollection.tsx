import { ArrowRight } from 'lucide-react';

interface WorkspaceCollectionNode {
  id: string;
  name: string;
}

export interface WorkspaceNodeCollectionItem {
  node: WorkspaceCollectionNode;
  eyebrow: string;
  icon: React.ReactNode;
}

interface WorkspaceNodeCollectionProps {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  items: WorkspaceNodeCollectionItem[];
  emptyText: string;
  onNavigateToNode?: (nodeId: string) => void;
  columns?: 2 | 3 | 4;
}

const COLUMN_CLASSES = {
  2: 'md:grid-cols-2',
  3: 'md:grid-cols-2 xl:grid-cols-3',
  4: 'md:grid-cols-2 xl:grid-cols-4',
} as const;

export default function WorkspaceNodeCollection({
  id,
  icon,
  title,
  description,
  items,
  emptyText,
  onNavigateToNode,
  columns = 3,
}: WorkspaceNodeCollectionProps) {
  return (
    <section aria-labelledby={id}>
      <WorkspaceSectionHeading id={id} icon={icon} title={title} description={description} />
      {items.length > 0 ? (
        <div className={`mt-3 grid gap-3 ${COLUMN_CLASSES[columns]}`}>
          {items.map(({ node, eyebrow, icon: nodeIcon }) => (
            <button
              key={node.id}
              type="button"
              onClick={() => onNavigateToNode?.(node.id)}
              className="group flex min-w-0 items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-white/10 dark:bg-slate-900/50 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/20"
              aria-label={`${node.name} öffnen`}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">
                {nodeIcon}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold text-slate-950 dark:text-white">{node.name}</span>
                <span className="mt-1 block truncate text-xs text-slate-600 dark:text-gray-400">{eyebrow}</span>
              </span>
              <ArrowRight size={17} className="shrink-0 text-slate-400 transition group-hover:translate-x-0.5 group-hover:text-emerald-700 dark:group-hover:text-emerald-300" />
            </button>
          ))}
        </div>
      ) : (
        <div className="mt-3 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-sm text-slate-600 dark:border-white/15 dark:bg-slate-900/30 dark:text-gray-400">
          {emptyText}
        </div>
      )}
    </section>
  );
}

export function WorkspaceSectionHeading({
  id,
  icon,
  title,
  description,
}: {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-w-0 items-start gap-3">
      <span className="mt-0.5 text-emerald-700 dark:text-emerald-300">{icon}</span>
      <span className="min-w-0">
        <h2 id={id} className="text-base font-semibold text-slate-950 dark:text-white">{title}</h2>
        <p className="mt-0.5 text-sm text-slate-600 dark:text-gray-400">{description}</p>
      </span>
    </div>
  );
}
