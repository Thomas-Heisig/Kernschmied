// API-Wrapper für Hierarchie-Mutationen
import { apiPost, apiPatch, apiDelete } from "./client";
import type {
  HierarchyNodeCreate,
  HierarchyNodeUpdate,
} from "../contracts/hierarchy";

export async function createHierarchyNode(payload: HierarchyNodeCreate) {
  return apiPost<unknown, HierarchyNodeCreate>("/hierarchy", payload);
}

export async function updateHierarchyNode(
  id: string,
  payload: HierarchyNodeUpdate,
) {
  return apiPatch<unknown, HierarchyNodeUpdate>(
    `/hierarchy/${encodeURIComponent(id)}`,
    payload,
  );
}

export async function moveHierarchyNode(
  id: string,
  newParentId: string | null,
) {
  return apiPost<unknown, { new_parent_id: string | null }>(
    `/hierarchy/${encodeURIComponent(id)}/move`,
    {
      new_parent_id: newParentId,
    },
  );
}

export async function deleteHierarchyNode(id: string) {
  return apiDelete<void>(`/hierarchy/${encodeURIComponent(id)}`);
}
