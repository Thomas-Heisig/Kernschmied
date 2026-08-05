// F:\Kernschmied\frontend\src\hooks\useAppSchema.ts

import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError, apiGet } from '../api/client';

import { isHierarchyTree, type HierarchyNode, type HierarchyTree } from '../contracts/hierarchy';

import { isUISchema, parseUISchema, type UISchema } from '../contracts/schema';
import type { AppBootstrap } from '../types/bootstrap';

const BOOTSTRAP_ENDPOINT = '/bootstrap';

export type AppSchemaLoadStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface AppSchemaError {
  code: string;
  message: string;
  details?: unknown;
  requestId?: string;
  status?: number;
}

export interface UseAppSchemaResult {
  /**
   * Geladenes und validiertes UI-Schema.
   */
  schema: UISchema | null;

  /**
   * Wurzelknoten der geladenen Hierarchie.
   *
   * Diese Eigenschaft bleibt mit bestehenden Aufrufern kompatibel.
   */
  hierarchy: HierarchyNode | null;

  /**
   * Vollständiger, versionierter Hierarchievertrag.
   */
  hierarchyTree: HierarchyTree | null;

  /**
   * Strukturierte Fehlerdaten.
   *
   * Bei einem fehlgeschlagenen Reload kann dieser Wert gesetzt sein,
   * obwohl weiterhin gültige Daten verfügbar sind.
   */
  error: AppSchemaError | null;

  /**
   * Einfache Fehlermeldung für bestehende UI-Komponenten.
   */
  errorMessage: string | null;

  status: AppSchemaLoadStatus;

  /**
   * `true` ausschließlich während des initialen Ladens.
   */
  isLoading: boolean;

  /**
   * `true`, wenn vorhandene Daten im Hintergrund neu geladen werden.
   */
  isRefreshing: boolean;

  /**
   * `true`, sobald ein verwendbares UI-Schema und eine Hierarchie
   * verfügbar sind.
   */
  isReady: boolean;
  /** Normalized, camelCase bootstrap object */
  bootstrap: AppBootstrap | null;

  /**
   * Lädt Bootstrap, UI-Schema und Hierarchie erneut (Full reload).
   */
  reload: () => Promise<void>;

  /**
   * Lädt nur die Hierarchie neu – nützlich nach dem Erstellen von Chats oder
   * anderen Änderungen am Baum, ohne das UI-Schema neu zu laden.
   */
  reloadHierarchy: () => Promise<void>;
}

/**
 * Minimaler, von diesem Hook benötigter Teil des Bootstrap-Vertrags.
 *
 * Ein vollständiger Bootstrap-Vertrag sollte langfristig in
 * `contracts/bootstrap.ts` liegen. Der Hook interpretiert bewusst nur
 * die hier benötigten stabilen Felder.
 */
// AppBootstrap type is imported from ../types/bootstrap and used for normalized bootstrap

export function useAppSchema(enabled: boolean = true, initialBootstrap: AppBootstrap | null = null): UseAppSchemaResult {
  const [schema, setSchema] = useState<UISchema | null>(null);

  const [hierarchyTree, setHierarchyTree] = useState<HierarchyTree | null>(null);

  const [error, setError] = useState<AppSchemaError | null>(null);

  const [status, setStatus] = useState<AppSchemaLoadStatus>('idle');

  const [isRefreshing, setIsRefreshing] = useState(false);

  const [bootstrapState, setBootstrapState] = useState<AppBootstrap | null>(null);

  const activeRequestControllerRef = useRef<AbortController | null>(null);

  const hierarchyEndpointRef = useRef<string | null>(null);

  /**
   * Verhindert, dass eine ältere Anfrage den Zustand einer neueren
   * Anfrage überschreibt, selbst wenn ein Transport einen Abbruch
   * nicht vollständig respektiert.
   */
  const requestGenerationRef = useRef(0);

  /**
   * Wird als Ref geführt, damit `load` nicht von den geladenen Daten
   * abhängt und dadurch im Effect keine ungewollte Ladeschleife
   * entsteht.
   */
  const hasUsableDataRef = useRef(false);

  const loadFull = useCallback(async (): Promise<void> => {
    activeRequestControllerRef.current?.abort();

    const requestController = new AbortController();

    activeRequestControllerRef.current = requestController;

    const requestGeneration = requestGenerationRef.current + 1;

    requestGenerationRef.current = requestGeneration;

    const isInitialLoad = !hasUsableDataRef.current;

    if (isInitialLoad) {
      setStatus('loading');
    } else {
      setIsRefreshing(true);
    }

    setError(null);

    try {
      // Ensure we have bootstrapState available. If not, fetch bootstrap-only first.
      if (!bootstrapState) {
        await loadBootstrapOnly();
      }

      const bootstrap = bootstrapState as AppBootstrap;

      const uiSchemaEndpoint = normalizeBootstrapEndpointIfPresent(
        bootstrap.endpoints.uiSchema ?? '',
        'endpoints.uiSchema',
      );

      const hierarchyEndpoint = normalizeBootstrapEndpointIfPresent(
        bootstrap.endpoints.hierarchy ?? '',
        'endpoints.hierarchy',
      );

      // Hierarchie-Endpunkt für spätere Teil-Reloads speichern
      hierarchyEndpointRef.current = hierarchyEndpoint ?? null;

      // If enabled is false, do not fetch uiSchema/hierarchy yet.
      if (!enabled) {
        // Mark that we have bootstrap data but not full schema
        hasUsableDataRef.current = false;
        setStatus('idle');
        setIsRefreshing(false);
        return;
      }

      const [rawSchemaResponse, rawHierarchyResponse] = await Promise.all([
        apiGet<unknown>(uiSchemaEndpoint ?? '', {
          signal: requestController.signal,
        }),

        apiGet<unknown>(hierarchyEndpoint ?? '', {
          signal: requestController.signal,
        }),
      ]);

      if (import.meta.env.DEV) {
        console.debug('UI schema raw response:', rawSchemaResponse);
        console.debug('Hierarchy raw response:', rawHierarchyResponse);
      }

      assertRequestIsCurrent(requestController, requestGeneration, requestGenerationRef);


      const normalizedSchema = normalizeUISchemaResponse(rawSchemaResponse);

      const normalizedHierarchy = normalizeHierarchyResponse(rawHierarchyResponse);

      if (import.meta.env.DEV) {
        console.debug('UI schema normalized:', normalizedSchema);
        console.debug('Hierarchy normalized:', normalizedHierarchy);
      }

      assertRequestIsCurrent(requestController, requestGeneration, requestGenerationRef);

      setSchema(normalizedSchema);
      setHierarchyTree(normalizedHierarchy);

      hasUsableDataRef.current = true;

      setError(null);
      setStatus('ready');
    } catch (caughtError) {
      if (
        requestController.signal.aborted ||
        isAbortError(caughtError) ||
        requestGeneration !== requestGenerationRef.current
      ) {
        return;
      }

      const normalizedError = normalizeAppSchemaError(caughtError);

      logDevelopmentError(
        'Bootstrap, UI-Schema oder Hierarchie konnten nicht geladen werden.',
        caughtError,
      );

      setError(normalizedError);

      /**
       * Ein fehlgeschlagener Reload darf bereits erfolgreich geladene
       * Daten nicht unbrauchbar machen.
       */
      if (hasUsableDataRef.current) {
        setStatus('ready');
      } else {
        setStatus('error');
      }
    } finally {
      if (requestGeneration === requestGenerationRef.current) {
        setIsRefreshing(false);
      }

      if (activeRequestControllerRef.current === requestController) {
        activeRequestControllerRef.current = null;
      }
    }
  }, [enabled]);

  /**
   * Lädt nur den Bootstrap-Teil (ohne UI-Schema und Hierarchie).
   * Wird initial immer ausgeführt, damit die Anwendung schnell
   * die öffentlichen Einstiegspunkte kennt. Vollständige Ladung
   * erfolgt durch `loadFull`.
   */
  const loadBootstrapOnly = useCallback(async (): Promise<void> => {
    activeRequestControllerRef.current?.abort();
    const requestController = new AbortController();
    activeRequestControllerRef.current = requestController;
    const requestGeneration = requestGenerationRef.current + 1;
    requestGenerationRef.current = requestGeneration;

    try {
      const rawBootstrapResponse = await apiGet<unknown>(BOOTSTRAP_ENDPOINT, {
        signal: requestController.signal,
      });

      assertRequestIsCurrent(requestController, requestGeneration, requestGenerationRef);

      const bootstrap = normalizeBootstrapResponse(rawBootstrapResponse);
      setBootstrapState(bootstrap);

      const hierarchyEndpoint = normalizeBootstrapEndpointIfPresent(
        bootstrap.endpoints.hierarchy ?? '',
        'endpoints.hierarchy',
      );

      hierarchyEndpointRef.current = hierarchyEndpoint ?? null;

      // Keep status idle until full load
      setStatus('idle');
    } catch (err) {
      if (
        requestController.signal.aborted ||
        isAbortError(err) ||
        requestGeneration !== requestGenerationRef.current
      ) {
        return;
      }

      const normalizedError = normalizeAppSchemaError(err);
      setError(normalizedError);
      setStatus('error');
    } finally {
      if (activeRequestControllerRef.current === requestController) {
        activeRequestControllerRef.current = null;
      }
    }
  }, []);

  /**
   * Lädt nur die Hierarchie neu (ohne Bootstrap und UI-Schema).
   * Nützlich nach dem Erstellen von Chats oder anderen Baumänderungen.
   */
  const loadHierarchy = useCallback(async (): Promise<void> => {
    // Falls noch kein Endpunkt bekannt ist, Full-Reload durchführen
    if (!hierarchyEndpointRef.current) {
      await loadFull();
      return;
    }

    const hierarchyEndpoint = hierarchyEndpointRef.current;

    // Eigene Abort-Controller für Hierarchie-Reload
    const abortController = new AbortController();

    // Wenn schon ein aktiver Hierarchie-Reload läuft, abbrechen
    // (vereinfacht: wir verwenden den gleichen Controller wie für Full-Reload,
    // aber das würde den Full-Reload abbrechen – besser eigenen Controller)
    // Für Einfachheit: wir nutzen einen separaten Controller, speichern ihn aber nicht global.
    // Stattdessen lassen wir ihn einfach laufen und verhindern State-Updates nach Abort.

    const requestGeneration = requestGenerationRef.current + 1;

    requestGenerationRef.current = requestGeneration;

    // Wir setzen isRefreshing auf true, damit UI Rückmeldung bekommt
    setIsRefreshing(true);

    try {
      const rawHierarchyResponse = await apiGet<unknown>(hierarchyEndpoint, {
        signal: abortController.signal,
      });

      // Prüfen, ob die Anfrage noch aktuell ist
      if (abortController.signal.aborted || requestGeneration !== requestGenerationRef.current) {
        return;
      }

      const normalizedHierarchy = normalizeHierarchyResponse(rawHierarchyResponse);

      // Prüfen, ob die Anfrage noch aktuell ist (nach der Verarbeitung)
      if (abortController.signal.aborted || requestGeneration !== requestGenerationRef.current) {
        return;
      }

      setHierarchyTree(normalizedHierarchy);

      // Fehler zurücksetzen, da erfolgreich geladen
      setError(null);
      // Status bleibt "ready", da wir bereits Daten haben
      setStatus('ready');
    } catch (caughtError) {
      // Abort ignorieren
      if (
        abortController.signal.aborted ||
        isAbortError(caughtError) ||
        requestGeneration !== requestGenerationRef.current
      ) {
        return;
      }

      const normalizedError = normalizeAppSchemaError(caughtError);

      logDevelopmentError('Hierarchie konnte nicht neu geladen werden.', caughtError);

      // Fehler setzen, aber Status bleibt "ready", da wir bereits Daten haben
      setError(normalizedError);
    } finally {
      // isRefreshing zurücksetzen, aber nur wenn keine neuere Anfrage läuft
      if (requestGeneration === requestGenerationRef.current) {
        setIsRefreshing(false);
      }
    }
  }, [loadFull]);

  useEffect(() => {
    // If an initial bootstrap is provided, use it and skip internal bootstrap fetch.
    if (initialBootstrap) {
      const bootstrap = normalizeBootstrapResponse(initialBootstrap as unknown);
      setBootstrapState(bootstrap);
      const hierarchyEndpoint = normalizeBootstrapEndpointIfPresent(
        bootstrap.endpoints.hierarchy ?? '',
        'endpoints.hierarchy',
      );
      hierarchyEndpointRef.current = hierarchyEndpoint ?? null;
      setStatus('idle');
      return;
    }

    // Always fetch bootstrap-only on mount so UI gets endpoints and features when no initial bootstrap
    void loadBootstrapOnly();

    return () => {
      requestGenerationRef.current += 1;

      activeRequestControllerRef.current?.abort();

      activeRequestControllerRef.current = null;
    };
  }, [loadBootstrapOnly, initialBootstrap]);

  const isReady = schema !== null && hierarchyTree !== null;
  useEffect(() => {
    // When enabled flips to true, perform the full load (if not already ready).
    if (enabled && !isReady) {
      void loadFull();
    }
  }, [enabled, isReady, loadFull]);

  return {
    schema,
    hierarchy: hierarchyTree?.root ?? null,
    hierarchyTree,
    error,
    errorMessage: error?.message ?? null,
    status,
    isLoading: status === 'loading' && !isReady,
    isRefreshing,
    isReady,
    bootstrap: bootstrapState,
    reload: async () => {
      if (enabled) {
        await loadFull();
      } else {
        await loadBootstrapOnly();
      }
    },
    reloadHierarchy: loadHierarchy,
  };
}

// Helper that treats empty endpoints as absent instead of throwing
function normalizeBootstrapEndpointIfPresent(value: string, fieldName: string): string | null {
  const trimmed = (value ?? '').trim();
  if (trimmed.length === 0) return null;
  return normalizeBootstrapEndpoint(trimmed, fieldName);
}


// ============================================================
// Normalisierungs- und Validierungs-Hilfen (unverändert)
// ============================================================

function toCamel(s: string): string {
  return s.replace(/_([a-z0-9])/g, (_, ch) => ch.toUpperCase());
}

function deepCamel<T>(obj: unknown): T {
  if (Array.isArray(obj)) {
    return obj.map((v) => deepCamel(v)) as unknown as T;
  }

  if (obj === null || typeof obj !== 'object') {
    return obj as T;
  }

  const out: Record<string, unknown> = {};

  for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
    const nk = toCamel(k);
    out[nk] = deepCamel(v);
  }

  return out as T;
}

function normalizeBootstrapResponse(value: unknown): AppBootstrap {
  const candidates = getResponseCandidates(value, ['data', 'bootstrap', 'result']);

  for (const candidate of candidates) {
    if (!isRecord(candidate)) continue;

    // Convert keys recursively to camelCase for normalized handling
    const camel = deepCamel<Record<string, unknown>>(candidate);

    // Extract security
    const securityRaw = (camel.security_profile ?? camel.security ?? camel.securityProfile) as
      | Record<string, unknown>
      | undefined;

    const featuresRaw = (camel.features ?? camel.capabilities ?? {}) as Record<string, unknown>;

    const endpointsRaw = (camel.endpoints ?? {}) as Record<string, unknown>;

    const security = {
      profile: String((securityRaw?.profile ?? securityRaw?.environment ?? 'internet')).toLowerCase() as
        | 'development'
        | 'intranet'
        | 'internet',
      authenticationRequired: Boolean(securityRaw?.authentication_required ?? securityRaw?.authenticationRequired ?? false),
      developmentIdentityActive: Boolean(securityRaw?.development_identity_active ?? securityRaw?.developmentIdentityActive ?? false),
      availableLoginMethods: Array.isArray(securityRaw?.available_login_methods ?? securityRaw?.availableLoginMethods)
        ? ((securityRaw?.available_login_methods ?? securityRaw?.availableLoginMethods) as string[])
        : [],
    } as AppBootstrap['security'];

    const features = {
      developmentAdminLogin: Boolean(
        featuresRaw.development_admin_login ?? featuresRaw.developmentAdminLogin ?? featuresRaw.development_login ?? false,
      ),
      selfRegistration: Boolean(
        featuresRaw.self_registration ?? featuresRaw.selfRegistration ?? false,
      ),
      registrationRequiresInvitation: Boolean(
        featuresRaw.registration_requires_invitation ?? featuresRaw.registrationRequiresInvitation ?? false,
      ),
    } as AppBootstrap['features'];

    const endpoints = {
      authLogin: String(endpointsRaw.auth_login ?? endpointsRaw.authLogin ?? endpointsRaw.login ?? ''),
      authLogout: String(endpointsRaw.auth_logout ?? endpointsRaw.authLogout ?? endpointsRaw.logout ?? ''),
      authMe: String(endpointsRaw.me ?? endpointsRaw.auth_me ?? endpointsRaw.authMe ?? ''),
      authDevelopmentLogin: String(
        endpointsRaw.auth_development_login ?? endpointsRaw.authDevelopmentLogin ?? endpointsRaw.development_login_endpoint ?? '',
      ),
      authRegister: String(endpointsRaw.auth_register ?? endpointsRaw.authRegister ?? ''),
      userProfile: String(endpointsRaw.user_profile ?? endpointsRaw.userProfile ?? ''),
      userPreferences: String(endpointsRaw.user_preferences ?? endpointsRaw.userPreferences ?? ''),
      uiSchema: String(endpointsRaw.ui_schema ?? endpointsRaw.uiSchema ?? ''),
      hierarchy: String(endpointsRaw.hierarchy ?? ''),
    } as AppBootstrap['endpoints'];

    // Compute derived availability per spec
    const developmentLoginAvailable =
      security.profile === 'development' &&
      features.developmentAdminLogin === true &&
      security.availableLoginMethods.map((s) => String(s)).includes('development_admin') &&
      Boolean(endpoints.authDevelopmentLogin);

    features.developmentLoginAvailable = developmentLoginAvailable;

    const registrationAvailable =
      features.selfRegistration === true &&
      security.availableLoginMethods.map((s) => String(s)).includes('registration') &&
      Boolean(endpoints.authRegister);

    features.registrationRequiresInvitation = Boolean(features.registrationRequiresInvitation);
    // preserve computed convenience flag
    (features as any).registrationAvailable = registrationAvailable;

    const requestIdVal =
      typeof camel.request_id === 'string'
        ? camel.request_id
        : typeof camel.requestId === 'string'
        ? camel.requestId
        : null;

    const result: AppBootstrap = {
      security,
      features,
      endpoints,
      schemaVersion: String(camel.schema_version ?? camel.schemaVersion ?? camel.schema ?? ''),
      apiVersion: String(camel.api_version ?? camel.apiVersion ?? ''),
      requestId: requestIdVal,
    };

    // Validate minimal shape
    if (!result.endpoints.uiSchema || !result.endpoints.hierarchy) {
      continue;
    }

    return result;
  }

  throw createContractError(
    'invalid_bootstrap_schema',
    'Das Backend hat einen ungültigen Bootstrap-Vertrag geliefert.',
    createContractErrorDetails(value, candidates),
  );
}

function normalizeUISchemaResponse(value: unknown): UISchema {
  const candidates = getResponseCandidates(value, ['data', 'schema', 'ui_schema', 'result']);

  const validationAttempts: Array<{
    candidateIndex: number;
    candidateType: string;
    issues: unknown;
  }> = [];

  for (let index = 0; index < candidates.length; index += 1) {
    const candidate = candidates[index];

    const validation = parseUISchema(candidate);

    if (validation.valid && validation.schema) {
      return validation.schema;
    }

    validationAttempts.push({
      candidateIndex: index,
      candidateType: describeValueType(candidate),
      issues: validation.issues,
    });

    /*
     * Übergangs-Fallback:
     *
     * Ein strukturell gültiges Schema wird während der Migration
     * weiterhin akzeptiert, selbst wenn die strengere semantische
     * Prüfung noch Abweichungen meldet.
     */
    if (isUISchema(candidate)) {
      if (import.meta.env.DEV) {
        console.warn(
          'Das UI-Schema ist strukturell gültig, erfüllt aber noch nicht alle semantischen Prüfungen.',
          {
            candidate,
            issues: validation.issues,
          },
        );
      }

      return candidate;
    }
  }

  if (import.meta.env.DEV) {
    console.error('UI-Schema vollständig abgelehnt.', {
      rawResponse: value,
      candidates,
      validationAttempts,
    });
  }

  throw createContractError(
    'invalid_ui_schema',
    'Das Backend hat ein ungültiges oder nicht unterstütztes UI-Schema geliefert.',
    {
      received_type: describeValueType(value),
      validation_attempts: validationAttempts,
    },
  );
}

function normalizeHierarchyResponse(value: unknown): HierarchyTree {
  const candidates = getResponseCandidates(value, [
    'data',
    'hierarchy',
    'hierarchy_tree',
    'tree',
    'result',
  ]);

  for (const candidate of candidates) {
    if (isHierarchyTree(candidate)) {
      return candidate;
    }
  }

  throw createContractError(
    'invalid_hierarchy_schema',
    'Das Backend hat eine ungültige Hierarchie geliefert.',
    createContractErrorDetails(value, candidates),
  );
}

/**
 * Bootstrap-Endpunkte müssen lokale absolute Pfade sein.
 *
 * Das Backend darf über den Bootstrap-Vertrag keine beliebigen externen
 * Ziele oder protokollrelativen URLs in den API-Client einschleusen.
 */
function normalizeBootstrapEndpoint(value: string, fieldName: string): string {
  const normalizedValue = value.trim();

  if (normalizedValue.length === 0) {
    throw createContractError(
      'invalid_bootstrap_endpoint',
      `Der Bootstrap-Einstiegspunkt "${fieldName}" ist leer.`,
      {
        field: fieldName,
        value,
      },
    );
  }

  if (
    !normalizedValue.startsWith('/') ||
    normalizedValue.startsWith('//') ||
    normalizedValue.includes('\\') ||
    hasUrlScheme(normalizedValue)
  ) {
    throw createContractError(
      'unsafe_bootstrap_endpoint',
      `Der Bootstrap-Einstiegspunkt "${fieldName}" ist nicht zulässig.`,
      {
        field: fieldName,
        value,
      },
    );
  }

  return normalizedValue;
}

function hasUrlScheme(value: string): boolean {
  return /^[a-z][a-z\d+.-]*:/i.test(value);
}

/**
 * Liefert die direkte Antwort sowie Inhalte aus fest bekannten
 * Wrapper-Feldern.
 *
 * Es wird nicht rekursiv durch beliebige Antwortstrukturen gesucht.
 */
function getResponseCandidates(value: unknown, wrapperKeys: readonly string[]): unknown[] {
  const candidates: unknown[] = [value];

  if (!isRecord(value)) {
    return candidates;
  }

  for (const key of wrapperKeys) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      candidates.push(value[key]);
    }
  }

  return candidates;
}

function isAppBootstrap(value: unknown): value is AppBootstrap {
  if (!isRecord(value)) {
    return false;
  }

  if (!isRecord(value.endpoints)) {
    return false;
  }

  return (
    isNonEmptyString(value.schema_version) &&
    isNonEmptyString(value.endpoints.ui_schema) &&
    isNonEmptyString(value.endpoints.hierarchy) &&
    (value.request_id === undefined || isNonEmptyString(value.request_id))
  );
}

function assertRequestIsCurrent(
  controller: AbortController,
  requestGeneration: number,
  requestGenerationRef: {
    readonly current: number;
  },
): void {
  if (controller.signal.aborted || requestGeneration !== requestGenerationRef.current) {
    throw createAbortError();
  }
}

function createAbortError(): Error {
  if (typeof DOMException !== 'undefined') {
    return new DOMException('Die Anfrage wurde abgebrochen.', 'AbortError');
  }

  const error = new Error('Die Anfrage wurde abgebrochen.');

  error.name = 'AbortError';

  return error;
}

function createContractErrorDetails(
  rawValue: unknown,
  candidates: readonly unknown[],
): Record<string, unknown> {
  return {
    received_type: describeValueType(rawValue),
    candidate_count: candidates.length,

    /**
     * Die vollständige API-Antwort wird absichtlich nicht in den
     * Fehlerdetails abgelegt. Sie könnte vertrauliche oder sehr große
     * Inhalte enthalten.
     */
    candidate_types: candidates.map(describeValueType),
  };
}

function createContractError(code: string, message: string, details?: unknown): AppSchemaError {
  return {
    code,
    message,
    details,
  };
}

function normalizeAppSchemaError(error: unknown): AppSchemaError {
  if (isAppSchemaError(error)) {
    return error;
  }

  if (error instanceof ApiError) {
    return {
      code: error.code,
      message: error.message,
      details: error.details,
      requestId: error.requestId,
      status: error.status,
    };
  }

  if (typeof DOMException !== 'undefined' && error instanceof DOMException) {
    if (error.name === 'AbortError') {
      return {
        code: 'request_aborted',
        message: 'Die Anfrage wurde abgebrochen.',
      };
    }

    return {
      code: 'browser_request_failed',
      message: error.message,
      details: {
        name: error.name,
      },
    };
  }

  if (error instanceof Error) {
    return {
      code: 'app_schema_load_failed',
      message: error.message,
      details: {
        name: error.name,
      },
    };
  }

  return {
    code: 'app_schema_load_failed',
    message: 'Bootstrap, Schema und Hierarchie konnten nicht geladen werden.',
    details: {
      received_type: describeValueType(error),
    },
  };
}

function isAppSchemaError(value: unknown): value is AppSchemaError {
  if (!isRecord(value)) {
    return false;
  }

  return (
    isNonEmptyString(value.code) &&
    isNonEmptyString(value.message) &&
    (value.requestId === undefined || isNonEmptyString(value.requestId)) &&
    (value.status === undefined ||
      (typeof value.status === 'number' &&
        Number.isFinite(value.status) &&
        Number.isInteger(value.status) &&
        value.status >= 100 &&
        value.status <= 599))
  );
}

function isAbortError(error: unknown): boolean {
  if (
    typeof DOMException !== 'undefined' &&
    error instanceof DOMException &&
    error.name === 'AbortError'
  ) {
    return true;
  }

  if (error instanceof Error && error.name === 'AbortError') {
    return true;
  }

  return error instanceof ApiError && error.code === 'request_aborted';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function describeValueType(value: unknown): string {
  if (value === null) {
    return 'null';
  }

  if (Array.isArray(value)) {
    return 'array';
  }

  return typeof value;
}

function logDevelopmentError(message: string, error: unknown): void {
  if (!import.meta.env.DEV) {
    return;
  }

  // Always log the top-level context
  console.error(message, error);

  // If this is an Error instance, show detailed diagnostics
  if (error instanceof Error) {
    console.error('Fehlername:', error.name);
    console.error('Fehlermeldung:', error.message);
    console.error('Stack:', error.stack);
    return;
  }

  // If it's the normalized AppSchemaError-like shape, try to log useful fields
  try {
    const asAny = error as any;

    if (asAny && typeof asAny === 'object') {
      const maybeCode = asAny.code ?? asAny.error_code ?? null;
      const maybeMessage = asAny.message ?? asAny.error_message ?? null;
      const maybeStatus = asAny.status ?? null;
      const maybeRequestId = asAny.requestId ?? asAny.request_id ?? null;

      if (maybeCode || maybeMessage || maybeStatus || maybeRequestId) {
        console.error('Structured Error:', {
          code: maybeCode,
          message: maybeMessage,
          status: maybeStatus,
          requestId: maybeRequestId,
          details: asAny.details ?? null,
        });
        return;
      }
    }
  } catch (e) {
    // fall through to generic stringify
  }

  // Fallback: attempt to stringify the value for inspection
  try {
    console.error('Unbekannter Fehlerwert:', JSON.stringify(error, null, 2));
  } catch (e) {
    console.error('Unbekannter Fehlerwert (nicht serialisierbar):', error);
  }
}
