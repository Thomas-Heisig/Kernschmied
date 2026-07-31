import { useCallback, useEffect, useRef, useState } from "react";

import {
  ConfigApiError,
  loadSystemConfig,
  updateSystemConfig,
} from "../api/config";
import type { ConfigObject } from "../contracts/config";

export type UseSystemConfigReturn = ReturnType<typeof useSystemConfig>;

interface SystemConfigError {
  code: string;
  message: string;
  requestId?: string;
}

interface UseSystemConfigResult {
  values: ConfigObject;
  revision: number | null;
  isLoading: boolean;
  isSaving: boolean;
  isDirty: boolean;
  error: SystemConfigError | null;

  setValues: (values: ConfigObject) => void;

  reload: () => Promise<void>;
  save: () => Promise<boolean>;
  reset: () => void;
}

export function useSystemConfig(): UseSystemConfigResult {
  const [persistedValues, setPersistedValues] = useState<ConfigObject>({});

  const [values, setValuesState] = useState<ConfigObject>({});

  const [revision, setRevision] = useState<number | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [isSaving, setIsSaving] = useState(false);

  const [error, setError] = useState<SystemConfigError | null>(null);

  const loadAbortController = useRef<AbortController | null>(null);

  const saveAbortController = useRef<AbortController | null>(null);

  const isDirty = JSON.stringify(values) !== JSON.stringify(persistedValues);

  const reload = useCallback(async (): Promise<void> => {
    loadAbortController.current?.abort();

    const controller = new AbortController();

    loadAbortController.current = controller;

    setIsLoading(true);
    setError(null);

    try {
      const snapshot = await loadSystemConfig(controller.signal);

      setPersistedValues(snapshot.values);
      setValuesState(snapshot.values);
      setRevision(snapshot.revision);
    } catch (caughtError) {
      if (
        caughtError instanceof DOMException &&
        caughtError.name === "AbortError"
      ) {
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
      const snapshot = await updateSystemConfig(
        {
          values,
          expected_revision: revision,
        },
        controller.signal,
      );

      setPersistedValues(snapshot.values);
      setValuesState(snapshot.values);
      setRevision(snapshot.revision);

      return true;
    } catch (caughtError) {
      if (
        caughtError instanceof DOMException &&
        caughtError.name === "AbortError"
      ) {
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
  }, [isDirty, isSaving, revision, values]);

  const reset = useCallback((): void => {
    setValuesState(persistedValues);
    setError(null);
  }, [persistedValues]);

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
    revision,
    isLoading,
    isSaving,
    isDirty,
    error,
    setValues,
    reload,
    save,
    reset,
  };
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
      code: "unexpected_config_error",
      message: error.message,
    };
  }

  return {
    code: "unexpected_config_error",
    message:
      "Beim Verarbeiten der Konfiguration ist ein unbekannter Fehler aufgetreten.",
  };
}
