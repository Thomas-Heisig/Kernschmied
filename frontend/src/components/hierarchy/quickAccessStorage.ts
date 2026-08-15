export const RECENT_NODE_STORAGE_KEY = 'kernschmied.sidebar.recent';
export const FAVORITE_NODE_STORAGE_KEY = 'kernschmied.sidebar.favorites';
export const MAX_QUICK_ACCESS_ITEMS = 5;

export function readStoredNodeIds(key: string): string[] {
  try {
    const value = JSON.parse(window.localStorage.getItem(key) ?? '[]');
    return Array.isArray(value)
      ? value.filter((id): id is string => typeof id === 'string')
      : [];
  } catch {
    return [];
  }
}
