/* Lightweight client for widget registry endpoints */

const BASE = (window as any).__API_BASE__ || '/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  if (res.status === 204) {
    return undefined as unknown as T;
  }

  return (await res.json()) as T;
}

export async function listRegistry() {
  return request(`/widgets/`);
}

export async function createRegistry(payload: Record<string, unknown>) {
  return request(`/widgets/`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function getEffectiveWidgets(nodeId: string) {
  return request<{ items: Array<Record<string, unknown>> }>(`/widgets/nodes/${nodeId}/effective`);
}

export async function setNodeAssignments(nodeId: string, payload: { assignments: Array<Record<string, unknown>> }) {
  return request(`/widgets/nodes/${nodeId}/assignments`, { method: 'POST', body: JSON.stringify(payload) });
}

export default { listRegistry, createRegistry, getEffectiveWidgets, setNodeAssignments };
