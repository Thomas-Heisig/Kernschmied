import { API_BASE_URL } from './client';
import { EffectiveWidget, EffectiveWidgetsResponse } from '../contracts/widgets';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  if (res.status === 204) return undefined as unknown as T;

  return (await res.json()) as T;
}

function normalizeItem(raw: any): EffectiveWidget {
  return {
    id: String(raw.id),
    name: raw.name ?? raw.id ?? '',
    label: raw.label ?? raw.title ?? raw.name ?? null,
    description: raw.description ?? null,
    status: raw.status ?? null,
    version: raw.version ?? null,
    interactionMode: raw.interaction_mode ?? raw.interactionMode ?? null,
    // prefer explicit component_type, then type, then nested metadata
    componentType:
      raw.component_type ??
      raw.type ??
      raw.metadata?.component_type ??
      raw.metadata?.widget_metadata?.component_type ??
      null,
    icon: raw.icon ?? raw.icon_name ?? null,
    requiredPermissions: Array.isArray(raw.required_permissions)
      ? raw.required_permissions.map(String)
      : (raw.requiredPermissions || []).map(String),
    // configuration may be provided at top-level or inside metadata/widget_metadata
    configuration: raw.configuration ?? raw.metadata?.configuration ?? raw.metadata?.widget_metadata?.configuration ?? null,
    position: raw.position ?? null,
    metadata: raw.metadata ?? {},
  };
}

export async function loadEffectiveWidgets(nodeId: string, signal?: AbortSignal): Promise<EffectiveWidget[]> {
  const path = `/widgets/nodes/${encodeURIComponent(nodeId)}/effective`;
  const res = await request<EffectiveWidgetsResponse>(path, { signal });
  const items = res.items ?? [];
  return items.map(normalizeItem);
}

export default { loadEffectiveWidgets };
