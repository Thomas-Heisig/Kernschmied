// F:\Kernschmied\frontend\src\hooks\useSystemConfig.ts

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import {
  ConfigApiError,
  loadSystemConfig,
  loadFullSystemConfig,
  updateSystemConfig,
} from '../api/config';
import type {
  ConfigObject,
  ConfigValue,
  ConfigEntryResponse,
  ConfigGroupResponse,
} from '../contracts/config';

export type UseSystemConfigReturn = ReturnType<typeof useSystemConfig>;

interface SystemConfigError {
  code: string;
  message: string;
  requestId?: string;
}

interface UseSystemConfigResult {
  // Draft values currently edited in the UI
  values: ConfigObject;
  // Persisted snapshot metadata
  groups?: ConfigGroupResponse[] | null;
  entriesByFullKey?: Record<string, ConfigEntryResponse> | null;
  persistedEntriesByFullKey?: Record<string, ConfigEntryResponse> | null;
  draftValues?: ConfigObject;
  revision: number | null;
  isLoading: boolean;
  isSaving: boolean;
  isDirty: boolean;
  error: SystemConfigError | null;

  setValues: (values: ConfigObject) => void;
  setDraftValues?: (values: ConfigObject) => void;

  reload: () => Promise<void>;
  save: () => Promise<boolean>;
  reset: () => void;
}

interface ConfigEntryLike {
  group: string;
  key: string;
  value: ConfigValue;
}

interface ConfigSnapshotLike {
  revision: number;
  values?: unknown;
  items?: unknown;
}

export function useSystemConfig(): UseSystemConfigResult {
  const [persistedValues, setPersistedValues] = useState<ConfigObject>({});
  const [persistedEntriesByFullKey, setPersistedEntriesByFullKey] = useState<Record<
    string,
    ConfigEntryResponse
  > | null>(null);

  const [groups, setGroups] = useState<ConfigGroupResponse[] | null>(null);

  // `values` is the draft currently edited by the UI
  const [values, setValuesState] = useState<ConfigObject>({});

  const [revision, setRevision] = useState<number | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [isSaving, setIsSaving] = useState(false);

  const [error, setError] = useState<SystemConfigError | null>(null);

  const loadAbortController = useRef<AbortController | null>(null);

  const saveAbortController = useRef<AbortController | null>(null);

  const isDirty = useMemo(
    () => !configObjectsEqual(values, persistedValues),
    [values, persistedValues],
  );

  const reload = useCallback(async (): Promise<void> => {
    loadAbortController.current?.abort();

    const controller = new AbortController();

    loadAbortController.current = controller;

    setIsLoading(true);

    setError(null);

    try {
      const loaded = await loadFullSystemConfig(controller.signal);

      setPersistedValues(loaded.values);

      setPersistedEntriesByFullKey(loaded.entriesByFullKey ?? null);

      setValuesState(loaded.values);

      setGroups(loaded.response?.groups ?? null);

      setRevision(normalizeRevision(loaded.revision));
    } catch (caughtError: unknown) {
      if (caughtError instanceof DOMException && caughtError.name === 'AbortError') {
        return;
      }

      setError(normalizeConfigError(caughtError));
    } finally {
      if (loadAbortController.current === controller) {
        setIsLoading(false);

        loadAbortController.current = null;
      }
    }
  }, []);

  const save = useCallback(async (): Promise<boolean> => {
    if (!isDirty || isSaving) {
      return false;
    }

    saveAbortController.current?.abort();

    const controller = new AbortController();

    saveAbortController.current = controller;

    setIsSaving(true);

    setError(null);

    try {
      // Compute delta as changes[] (group/key/value) to send to the server.
      const changes: Array<ConfigEntryLike> = [];

      const persisted = persistedEntriesByFullKey ?? {};

      // Collect keys from persisted entries
      for (const fullKey of Object.keys(persisted)) {
        const entry = persisted[fullKey];
        const group = entry.group;
        const key = entry.key;
        const draftGroup = (values as any)[group] as Record<string, unknown> | undefined;
        const draftValue = draftGroup ? (draftGroup[key] as ConfigValue) : undefined;

        const persistedValue = entry.value as ConfigValue;

        if (!configValuesEqual(draftValue, persistedValue)) {
          changes.push({ group, key, value: draftValue as ConfigValue });
        }
      }

      // Also include new draft keys not present in persistedEntries
      for (const rawGroup of Object.keys(values)) {
        const group = rawGroup;
        const groupValues = (values as any)[group] as Record<string, unknown> | undefined;
        if (!groupValues) continue;

        for (const rawKey of Object.keys(groupValues)) {
          const key = rawKey;
          const fullKey = `${group}.${key}`;
          if (persisted[fullKey]) continue;
          const draftValue = groupValues[key] as ConfigValue;
          changes.push({ group, key, value: draftValue });
        }
      }

      if (changes.length === 0) {
        // Nothing changed (race or normalization); reload to be safe.
        await reload();
        return true;
      }

      const rawSnapshot = await updateSystemConfig(
        {
          changes,
          expected_revision: revision,
        },
        controller.signal,
      );

      // The API returns a LoadedConfig normalized by the client helper.
      const loaded = rawSnapshot as unknown as {
        values: ConfigObject;
        entriesByFullKey?: Record<string, ConfigEntryResponse> | null;
        response?: { groups?: ConfigGroupResponse[] };
        revision?: number | null;
      };

      setPersistedValues(loaded.values);
      setValuesState(loaded.values);
      setPersistedEntriesByFullKey(loaded.entriesByFullKey ?? null);
      setGroups(loaded.response?.groups ?? null);
      setRevision(normalizeRevision(loaded.revision));

      return true;
    } catch (caughtError: unknown) {
      if (caughtError instanceof DOMException && caughtError.name === 'AbortError') {
        return false;
      }

      setError(normalizeConfigError(caughtError));

      return false;
    } finally {
      if (saveAbortController.current === controller) {
        setIsSaving(false);

        saveAbortController.current = null;
      }
    }
  }, [isDirty, isSaving, reload, revision, values]);

  const reset = useCallback((): void => {
    setValuesState(cloneConfigObject(persistedValues));

    setError(null);
  }, [persistedValues]);

  // Autosave: when enabled, automatically save dirty changes after a short debounce.
  const autosaveTimer = useRef<number | null>(null);

  useEffect(() => {
    // Determine autosave preference from config values. Default to true.
    const valuesRec = values as unknown as Record<string, unknown>;
    const ui = (valuesRec.ui as Record<string, unknown> | undefined) ?? undefined;
    const autosavePref =
      ui && typeof ui.autosave_enabled !== 'undefined' ? Boolean(ui.autosave_enabled) : true;

    if (!autosavePref) {
      // If disabled, clear any pending timer and do nothing.
      if (autosaveTimer.current !== null) {
        window.clearTimeout(autosaveTimer.current);
        autosaveTimer.current = null;
      }
      return;
    }

    if (isLoading || isSaving || !isDirty) {
      return;
    }

    // Debounce save by 1s to avoid rapid calls during typing.
    if (autosaveTimer.current !== null) {
      window.clearTimeout(autosaveTimer.current);
    }

    autosaveTimer.current = window.setTimeout(() => {
      void save();
      autosaveTimer.current = null;
    }, 1000);

    return () => {
      if (autosaveTimer.current !== null) {
        window.clearTimeout(autosaveTimer.current);
        autosaveTimer.current = null;
      }
    };
  }, [values, isDirty, isLoading, isSaving, save]);

  const setValues = useCallback((nextValues: ConfigObject): void => {
    setValuesState(nextValues);
  }, []);

  useEffect(() => {
    void reload();

    return () => {
      loadAbortController.current?.abort();
      saveAbortController.current?.abort();
    };
  }, [reload]);

  return {
    values,
    groups,
    entriesByFullKey: persistedEntriesByFullKey,
    persistedEntriesByFullKey,
    draftValues: values,
    revision,
    isLoading,
    isSaving,
    isDirty,
    error,
    setValues,
    setDraftValues: setValues,
    reload,
    save,
    reset,
  };
}

function configValuesEqual(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

function normalizeSnapshotValues(snapshot: ConfigSnapshotLike): ConfigObject {
  /*
   * Bevorzugte Frontend-Struktur:
   *
   * {
   *   identity: {
   *     name: "Kernschmied"
   *   }
   * }
   */
  if (isConfigObject(snapshot.values)) {
    return cloneConfigObject(snapshot.values);
  }

  /*
   * Backend-Transportstruktur:
   *
   * {
   *   items: [
   *     {
   *       group: "identity",
   *       key: "name",
   *       value: "Kernschmied"
   *     }
   *   ]
   * }
   */
  if (Array.isArray(snapshot.items)) {
    return buildConfigObject(snapshot.items);
  }

  /*
   * Kompatibilität für API-Clients, die items versehentlich
   * unter values zurückgeben.
   */
  if (Array.isArray(snapshot.values)) {
    return buildConfigObject(snapshot.values);
  }

  return {};
}

function buildConfigObject(rawEntries: unknown[]): ConfigObject {
  const result: ConfigObject = {};

  for (const rawEntry of rawEntries) {
    if (!isConfigEntryLike(rawEntry)) {
      continue;
    }

    const group = rawEntry.group.trim().toLowerCase();

    const key = rawEntry.key.trim().toLowerCase();

    if (!group || !key) {
      continue;
    }

    const existingGroup = result[group];

    const groupValues: ConfigObject = isConfigObject(existingGroup) ? existingGroup : {};

    result[group] = {
      ...groupValues,
      [key]: rawEntry.value,
    };
  }

  return result;
}

function isConfigEntryLike(value: unknown): value is ConfigEntryLike {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.group === 'string' &&
    typeof record.key === 'string' &&
    isConfigValue(record.value)
  );
}

function isConfigObject(value: unknown): value is ConfigObject {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false;
  }

  return Object.values(value).every(isConfigValue);
}

function isConfigValue(value: unknown): value is ConfigValue {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') {
    return true;
  }

  if (typeof value === 'number') {
    return Number.isFinite(value);
  }

  if (Array.isArray(value)) {
    return value.every(isConfigValue);
  }

  if (typeof value === 'object' && value !== null) {
    return Object.values(value).every(isConfigValue);
  }

  return false;
}

function cloneConfigObject(values: ConfigObject): ConfigObject {
  return structuredClone(values);
}

function configObjectsEqual(left: ConfigObject, right: ConfigObject): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function normalizeRevision(value: unknown): number | null {
  if (typeof value === 'number' && Number.isInteger(value) && value >= 0) {
    return value;
  }

  return null;
}

function normalizeConfigError(error: unknown): SystemConfigError {
  if (error instanceof ConfigApiError) {
    return {
      code: error.code,
      message: error.message,
      requestId: error.requestId,
    };
  }

  if (error instanceof Error) {
    return {
      code: 'unexpected_config_error',
      message: error.message,
    };
  }

  return {
    code: 'unexpected_config_error',
    message: 'Beim Verarbeiten der Konfiguration ' + 'ist ein unbekannter Fehler aufgetreten.',
  };
}
