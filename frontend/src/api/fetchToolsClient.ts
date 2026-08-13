import { apiGet, apiPatch, apiPut } from './client';

export type ToolEntry = {
  id: string;
  name: string;
  description?: string | null;
  category?: string | null;
  enabled?: boolean;
  available?: boolean;
  selectable?: boolean;
  required_permissions?: string[];
  metadata?: Record<string, unknown>;
};

export async function listRegistry(opts?: { include_disabled?: boolean; include_unavailable?: boolean; category?: string | null }) {
  const q = new URLSearchParams();
  if (opts?.include_disabled) q.set('include_disabled', 'true');
  if (opts?.include_unavailable) q.set('include_unavailable', 'true');
  if (opts?.category) q.set('category', String(opts.category));
  return apiGet<{ items: ToolEntry[] }>(`/tools?${q.toString()}`);
}

export async function getNode(nodeId: string) {
  return apiGet<any>(`/hierarchy/${encodeURIComponent(nodeId)}`);
}

export async function setNodeToolPolicy(nodeId: string, policy: Record<string, boolean>) {
  // legacy: update via hierarchy patch
  return apiPatch(`/hierarchy/${encodeURIComponent(nodeId)}`, { tool_policy: policy });
}

export async function updateNode(nodeId: string, payload: Record<string, unknown>) {
  return apiPatch(`/hierarchy/${encodeURIComponent(nodeId)}`, payload);
}

export async function getNodeToolPolicy(nodeId: string) {
  return apiGet<any>(`/tools/nodes/${encodeURIComponent(nodeId)}`);
}

export async function getNodeEffectiveTools(nodeId: string) {
  return apiGet<any>(`/tools/nodes/${encodeURIComponent(nodeId)}/effective`);
}

export async function putNodeToolPolicy(nodeId: string, payload: { tool_policy: Record<string, boolean>; metadata?: Record<string, unknown> }) {
  return apiPut(`/tools/nodes/${encodeURIComponent(nodeId)}/policy`, payload);
}

export default { listRegistry, getNode, setNodeToolPolicy, updateNode, getNodeToolPolicy, getNodeEffectiveTools, putNodeToolPolicy };
