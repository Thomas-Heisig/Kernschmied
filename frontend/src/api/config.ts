import { API_BASE_URL } from "./client";
import type {
  ConfigObject,
  StructuredApiError,
  SystemConfigSnapshot,
  UpdateSystemConfigRequest,
} from "../contracts/config";

interface ConfigApiResponse {
  values?: unknown;
  config?: unknown;
  revision?: unknown;
  config_revision?: unknown;
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

    this.name = "ConfigApiError";
    this.code = code;
    this.details = details;
    this.requestId = requestId;
    this.status = status;
  }
}

export async function loadSystemConfig(
  signal?: AbortSignal,
): Promise<SystemConfigSnapshot> {
  const response = await fetch(`${API_BASE_URL}/config`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  if (!response.ok) {
    throw await createConfigApiError(response);
  }

  const payload = await readJsonResponse(response);

  return normalizeConfigSnapshot(payload);
}

export async function updateSystemConfig(
  request: UpdateSystemConfigRequest,
  signal?: AbortSignal,
): Promise<SystemConfigSnapshot> {
  const response = await fetch(`${API_BASE_URL}/config`, {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      values: request.values,
      expected_revision: request.expected_revision ?? null,
    }),
    signal,
  });

  if (!response.ok) {
    throw await createConfigApiError(response);
  }

  const payload = await readJsonResponse(response);

  return normalizeConfigSnapshot(payload);
}

async function readJsonResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (!contentType.includes("application/json")) {
    return null;
  }

  return response.json() as Promise<unknown>;
}

function normalizeConfigSnapshot(payload: unknown): SystemConfigSnapshot {
  if (!isRecord(payload)) {
    throw new ConfigApiError({
      code: "invalid_config_response",
      message: "Die Konfigurationsantwort des Servers ist ungültig.",
      status: 500,
    });
  }

  const response = payload as ConfigApiResponse;

  const rawValues = response.values ?? response.config ?? payload;

  const rawRevision = response.revision ?? response.config_revision ?? null;

  if (!isConfigObject(rawValues)) {
    throw new ConfigApiError({
      code: "invalid_config_values",
      message: "Die Serverantwort enthält keine gültige Konfiguration.",
      status: 500,
    });
  }

  return {
    values: rawValues,
    revision:
      typeof rawRevision === "number" && Number.isInteger(rawRevision)
        ? rawRevision
        : null,
  };
}

async function createConfigApiError(
  response: Response,
): Promise<ConfigApiError> {
  const fallbackMessage =
    `Die Konfiguration konnte nicht verarbeitet werden. ` +
    `HTTP-Status: ${response.status}.`;

  const payload = await readJsonResponse(response);

  if (!isRecord(payload)) {
    return new ConfigApiError({
      code: "config_request_failed",
      message: fallbackMessage,
      status: response.status,
    });
  }

  const structuredError = payload as Partial<StructuredApiError>;

  return new ConfigApiError({
    code:
      typeof structuredError.code === "string"
        ? structuredError.code
        : "config_request_failed",
    message:
      typeof structuredError.message === "string"
        ? structuredError.message
        : fallbackMessage,
    details: isRecord(structuredError.details)
      ? structuredError.details
      : undefined,
    requestId:
      typeof structuredError.request_id === "string"
        ? structuredError.request_id
        : undefined,
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
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "boolean"
  ) {
    return true;
  }

  if (typeof value === "number") {
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
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
