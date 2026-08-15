import { ArrowRight, Building2, Clock3, FolderKanban, MessageSquare, UserRound } from 'lucide-react';

import {
  readStoredNodeIds,
  RECENT_NODE_STORAGE_KEY,
} from '../hierarchy/quickAccessStorage';

export interface RecentWorkspaceNode {
  id: string;
  name: string;
  type: string;
  children?: RecentWorkspaceNode[];
}

interface RecentNodeSectionProps {
  nodes: RecentWorkspaceNode[];
  acceptedTypes: string[];
  title: string;
  description: string;
  onNavigateToNode?: (nodeId: string) => void;
  includeDescendants?: boolean;
  maxItems?: number;
}

function flattenNodes(nodes: RecentWorkspaceNode[]): RecentWorkspaceNode[] {
  return nodes.flatMap((node) => [node, ...flattenNodes(node.children ?? [])]);
}

export function resolveRecentNodes(
  nodes: RecentWorkspaceNode[],
  acceptedTypes: string[],
  includeDescendants = false,
  maxItems = 4,
): RecentWorkspaceNode[] {
  const candidates = includeDescendants ? flattenNodes(nodes) : nodes;
  const accepted = new Set(acceptedTypes.map((type) => type.trim().toLowerCase()));
  const byId = new Map(candidates.map((node) => [node.id, node]));

  return readStoredNodeIds(RECENT_NODE_STORAGE_KEY)
    .map((id) => byId.get(id))
    .filter(
      (node): node is RecentWorkspaceNode =>
        Boolean(node && accepted.has(node.type.trim().toLowerCase())),
    )
    .slice(0, maxItems);
}

export default function RecentNodeSection({
  nodes,
  acceptedTypes,
  title,
  description,
  onNavigateToNode,
  includeDescendants = false,
  maxItems = 4,
}: RecentNodeSectionProps) {
  const recentNodes = resolveRecentNodes(
    nodes,
    acceptedTypes,
    includeDescendants,
    maxItems,
  );
  if (recentNodes.length === 0) return null;

  return (
    <section aria-labelledby={`recent-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex min-w-0 items-start gap-3">
        <Clock3 className="mt-0.5 h-[18px] w-[18px] shrink-0 text-emerald-700 dark:text-emerald-300" />
        <span className="min-w-0">
          <h2
            id={`recent-${title.toLowerCase().replace(/\s+/g, '-')}`}
            className="text-base font-semibold text-slate-950 dark:text-white"
          >
            {title}
          </h2>
          <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">{description}</p>
        </span>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {recentNodes.map((node) => (
          <button
            key={node.id}
            type="button"
            onClick={() => onNavigateToNode?.(node.id)}
            className="group flex min-w-0 items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-emerald-300 hover:bg-emerald-50/40 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-white/10 dark:bg-slate-900/50 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/20"
            aria-label={`${node.name} öffnen`}
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">
              {iconForNodeType(node.type)}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-slate-950 dark:text-white">
                {node.name}
              </span>
              <span className="mt-1 block truncate text-xs text-slate-600 dark:text-slate-400">
                {labelForNodeType(node.type)}
              </span>
            </span>
            <ArrowRight className="h-[17px] w-[17px] shrink-0 text-slate-400 transition group-hover:text-emerald-700 dark:group-hover:text-emerald-300" />
          </button>
        ))}
      </div>
    </section>
  );
}

function iconForNodeType(type: string) {
  switch (type.trim().toLowerCase()) {
    case 'user':
      return <UserRound size={19} />;
    case 'workspace':
    case 'bereich':
      return <Building2 size={19} />;
    case 'project':
    case 'projekt':
      return <FolderKanban size={19} />;
    default:
      return <MessageSquare size={19} />;
  }
}

function labelForNodeType(type: string): string {
  switch (type.trim().toLowerCase()) {
    case 'user':
      return 'Benutzer';
    case 'workspace':
    case 'bereich':
      return 'Bereich';
    case 'project':
    case 'projekt':
      return 'Projekt';
    default:
      return 'Chat';
  }
}