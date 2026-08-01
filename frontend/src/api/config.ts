import { API_BASE_URL } from './client';
import type {
  ConfigObject,
  StructuredApiError,
  SystemConfigSnapshot,
  UpdateSystemConfigRequest,
  ConfigListResponse,
  ConfigGroupResponse,
  ConfigEntryResponse,
} from '../contracts/config';

export interface LoadedConfig {
  response: ConfigListResponse;
  values: ConfigObject;
  entriesByFullKey: Record<string, ConfigEntryResponse>;
  revision: number | null;
}

export class ConfigApiError extends Error {
  readonly code: string;
  readonly details?: Record<string, unknown>;
  readonly requestId?: string;
  readonly status: number;

  constructor({
    code,
    message,
    details,
    requestId,
    status,
  }: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    requestId?: string;
    status: number;
  }) {
    super(message);

    this.name = 'ConfigApiError';
    this.code = code;
    this.details = details;
    this.requestId = requestId;
    this.status = status;
  }
}

export async function loadSystemConfig(signal?: AbortSignal): Promise<SystemConfigSnapshot> {
  const response = await fetch(`${API_BASE_URL}/config`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'same-origin',
    signal,
  });

  if (!response.ok) {
    throw await createConfigApiError(response);
  }

  const payload = await readJsonResponse(response);
  const loaded = normalizeConfigSnapshot(payload);

  return {
    values: loaded.values,
    revision: loaded.revision,
  } as SystemConfigSnapshot;
}

export async function loadFullSystemConfig(signal?: AbortSignal): Promise<LoadedConfig> {
  const response = await fetch(`${API_BASE_URL}/config`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    credentials: 'same-origin',
    signal,
  });

  if (!response.ok) {
    throw await createConfigApiError(response);
  }

  const payload = await readJsonResponse(response);

  const loaded = normalizeConfigSnapshot(payload);

  return loaded;
}

export interface BulkUpdateChange {
  group: string;
  key: string;
  value: unknown;
}

export interface BulkUpdateRequest {
  values?: ConfigObject;
  changes?: BulkUpdateChange[];
  expected_revision?: number | null;
}

export async function updateSystemConfig(
  request: BulkUpdateRequest,
  signal?: AbortSignal,
): Promise<LoadedConfig> {
  const body: Record<string, unknown> = {};

  if (Array.isArray(request.changes) && request.changes.length > 0) {
    body.changes = request.changes;
  } else if (request.values) {
    body.values = request.values;
  } else {
    body.values = {};
  }

  body.expected_revision = request.expected_revision ?? null;

  const response = await fetch(`${API_BASE_URL}/config`, {
    method: 'PUT',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
    credentials: 'same-origin',
    signal,
  });

  if (!response.ok) {
    throw await createConfigApiError(response);
  }

  const payload = await readJsonResponse(response);

  return normalizeConfigSnapshot(payload);
}

async function readJsonResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? '';

  if (!contentType.includes('application/json')) {
    return null;
  }

  return response.json() as Promise<unknown>;
}

function normalizeConfigSnapshot(payload: unknown): LoadedConfig {
  if (!isRecord(payload)) {
    throw new ConfigApiError({
      code: 'invalid_config_response',
      message: 'Die Konfigurationsantwort des Servers ist ungültig.',
      status: 500,
    });
  }

  const payloadRecord = payload as Record<string, unknown>;

  // If the payload already follows ConfigListResponse (groups present), use it.
  if (Array.isArray(payloadRecord.groups)) {
    const response = payload as unknown as ConfigListResponse;

    const values: ConfigObject = {};
    const entriesByFullKey: Record<string, ConfigEntryResponse> = {};

    for (const group of response.groups as ConfigGroupResponse[]) {
      const groupId = (group.id || '').toString().trim().toLowerCase();
      if (!groupId) continue;
      values[groupId] = values[groupId] ?? {};

      for (const entry of group.entries as ConfigEntryResponse[]) {
        const key = (entry.key || '').toString().trim();
        if (!key) continue;
        (values[groupId] as Record<string, unknown>)[key] = entry.value;
        entriesByFullKey[`${groupId}.${key}`] = entry;
      }
    }

    const rawRevision = response.revision ?? null;

    return {
      response: response as ConfigListResponse,
      values,
      entriesByFullKey,
      revision:
        typeof rawRevision === 'number' && Number.isInteger(rawRevision) ? rawRevision : null,
    };
  }

  // Fallback: payload may be a minimal snapshot { values, revision }
  const valuesObj = (payloadRecord.values ?? payloadRecord.items) as
    Record<string, unknown> | undefined;

  const values: ConfigObject = {};
  const entriesByFullKey: Record<string, ConfigEntryResponse> = {};

  if (valuesObj && typeof valuesObj === 'object') {
    // If values is grouped { group: { key: value } }
    for (const [rawGroup, rawGroupValue] of Object.entries(valuesObj)) {
      const groupId = rawGroup.trim().toLowerCase();
      if (!groupId) continue;
      values[groupId] = values[groupId] ?? {};
      if (typeof rawGroupValue === 'object' && rawGroupValue !== null) {
        for (const [rawKey, rawVal] of Object.entries(rawGroupValue as Record<string, unknown>)) {
          const key = rawKey.trim();
          (values[groupId] as Record<string, unknown>)[key] = rawVal as unknown;
          entriesByFullKey[`${groupId}.${key}`] = {
            group: groupId,
            key,
            full_key: `${groupId}.${key}`,
            display_name: key,
            description: '',
            value: rawVal as unknown,
            default_value: null,
            schema_version: '2.0',
            value_type: undefined,
            value_schema: undefined,
            editable: true,
            sensitive: false,
            secret_configured: false,
            requires_restart: false,
            runtime_editable: true,
            nullable: true,
            visibility: '',
            allowed_scopes: [],
            current_scope: '',
            ui: {
              component: undefined,
              category: undefined,
              section: undefined,
              order: undefined,
              placeholder: null,
              help_text: null,
              unit: null,
              advanced: false,
              hidden: false,
              readonly: false,
              options: [],
              dynamic_options: null,
            },
            permissions: {
              read: 'config:read',
              write: 'config:write',
              reveal_secret: null,
            },
          } as ConfigEntryResponse;
        }
      }
    }
  }

  const rawRevision = payloadRecord.revision ?? null;

  const response: ConfigListResponse = {
    schema_version: '2.0',
    revision: typeof rawRevision === 'number' && Number.isInteger(rawRevision) ? rawRevision : 0,
    groups: [],
  };

  return {
    response,
    values,
    entriesByFullKey,
    revision: typeof rawRevision === 'number' && Number.isInteger(rawRevision) ? rawRevision : null,
  };
}

async function createConfigApiError(response: Response): Promise<ConfigApiError> {
  const fallbackMessage =
    `Die Konfiguration konnte nicht verarbeitet werden. ` + `HTTP-Status: ${response.status}.`;

  const payload = await readJsonResponse(response);

  if (!isRecord(payload)) {
    return new ConfigApiError({
      code: 'config_request_failed',
      message: fallbackMessage,
      status: response.status,
    });
  }

  const structuredError = payload as Partial<StructuredApiError>;

  return new ConfigApiError({
    code: typeof structuredError.code === 'string' ? structuredError.code : 'config_request_failed',
    message:
      typeof structuredError.message === 'string' ? structuredError.message : fallbackMessage,
    details: isRecord(structuredError.details) ? structuredError.details : undefined,
    requestId:
      typeof structuredError.request_id === 'string' ? structuredError.request_id : undefined,
    status: response.status,
  });
}

function isConfigObject(value: unknown): value is ConfigObject {
  if (!isRecord(value)) {
    return false;
  }

  return Object.values(value).every(isConfigValue);
}

function isConfigValue(value: unknown): boolean {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') {
    return true;
  }

  if (typeof value === 'number') {
    return Number.isFinite(value);
  }

  if (Array.isArray(value)) {
    return value.every(isConfigValue);
  }

  if (isRecord(value)) {
    return Object.values(value).every(isConfigValue);
  }

  return false;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
