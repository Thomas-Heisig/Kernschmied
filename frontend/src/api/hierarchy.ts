// API-Wrapper für Hierarchie-Mutationen
import { apiDelete, apiGet, apiPatch, apiPost } from './client';
import type { HierarchyNode, HierarchyNodeCreate, HierarchyNodeUpdate } from '../contracts/hierarchy';

export async function createHierarchyNode(payload: HierarchyNodeCreate) {
  return apiPost<HierarchyNode, HierarchyNodeCreate>('/hierarchy', payload);
}

export async function updateHierarchyNode(id: string, payload: HierarchyNodeUpdate) {
  return apiPatch<HierarchyNode, HierarchyNodeUpdate>(`/hierarchy/${encodeURIComponent(id)}`, payload);
}

export async function moveHierarchyNode(id: string, newParentId: string | null) {
  return apiPost<HierarchyNode, { new_parent_id: string | null }>(
    `/hierarchy/${encodeURIComponent(id)}/move`,
    {
      new_parent_id: newParentId,
    },
  );
}

export async function deleteHierarchyNode(id: string) {
  return apiDelete<void>(`/hierarchy/${encodeURIComponent(id)}`);
}

export interface HierarchyQuotaStatus {
  accessLevel: 'guest' | 'internal' | 'admin';
  limits: Record<'workspace' | 'project' | 'chat', number> | null;
  usage: Record<'workspace' | 'project' | 'chat', number> | null;
  remaining: Record<'workspace' | 'project' | 'chat', number> | null;
}

export async function loadOwnHierarchyQuotas(): Promise<HierarchyQuotaStatus> {
  const raw = await apiGet<{
    access_level: HierarchyQuotaStatus['accessLevel'];
    limits: HierarchyQuotaStatus['limits'];
    usage: HierarchyQuotaStatus['usage'];
    remaining: HierarchyQuotaStatus['remaining'];
  }>('/hierarchy/quotas/me');
  return {
    accessLevel: raw.access_level,
    limits: raw.limits,
    usage: raw.usage,
    remaining: raw.remaining,
  };
}

export async function reorderHierarchy(
  items: Array<{ id: string; new_parent_id: string | null; new_position: number }>,
) {
  return apiPost<
    void,
    { items: Array<{ id: string; new_parent_id: string | null; new_position: number }> }
  >(`/hierarchy/reorder`, { items });
}
