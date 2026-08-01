import type { SettingsCatalogResponse } from '../contracts/settings';

const SETTINGS_CATALOG_ENDPOINT = '/api/v1/settings/catalog';

export async function fetchSettingsCatalog(signal?: AbortSignal): Promise<SettingsCatalogResponse> {
  const response = await fetch(SETTINGS_CATALOG_ENDPOINT, {
    method: 'GET',
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
    signal,
  });

  if (!response.ok) {
    throw new Error(`Settings-Katalog konnte nicht geladen werden (${response.status}).`);
  }

  return (await response.json()) as SettingsCatalogResponse;
}
