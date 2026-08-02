// API-Wrapper für Hierarchie-Mutationen
import { apiPost, apiPatch, apiDelete } from './client';
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

export async function reorderHierarchy(
  items: Array<{ id: string; new_parent_id: string | null; new_position: number }>,
) {
  return apiPost<
    void,
    { items: Array<{ id: string; new_parent_id: string | null; new_position: number }> }
  >(`/hierarchy/reorder`, { items });
}
