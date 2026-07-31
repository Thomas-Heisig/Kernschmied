// F:\Kernschmied\frontend\src\api\client.ts

const SOURCE_FILE = "frontend/src/api/client.ts";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;

const DEFAULT_STREAM_CONNECT_TIMEOUT_MS = 30_000;

const DEFAULT_STREAM_CONTENT_TYPE = "text/event-stream";

const DEFAULT_REQUEST_CREDENTIALS: RequestCredentials = "include";

const FALLBACK_BROWSER_ORIGIN = "http://localhost";

const CLIENT_REQUEST_ID_HEADER = "X-Client-Request-ID";

const SERVER_REQUEST_ID_HEADER = "X-Request-ID";

const MAX_REQUEST_ID_LENGTH = 128;

const REQUEST_ID_PATTERN = /^[A-Za-z0-9_.-]+$/;

type QueryPrimitive = string | number | boolean;

type QueryValue = QueryPrimitive | null | undefined | readonly QueryPrimitive[];

export type ApiQueryParams = Record<string, QueryValue>;

export type ApiResponseType = "auto" | "json" | "text" | "blob" | "void";

export type ApiErrorResponse = {
  code?: string;
  message?: string;
  details?: unknown;
  request_id?: string;
};

export type ApiRequestOptions = {
  /**
   * URL-Queryparameter.
   *
   * Arrays werden als mehrfach vorhandene Parameter übertragen:
   *
   * ?status=open&status=closed
   */
  query?: ApiQueryParams;

  /**
   * Zusätzliche HTTP-Header.
   */
  headers?: HeadersInit;

  /**
   * Optionales Abbruchsignal, beispielsweise von AbortController.
   */
  signal?: AbortSignal;

  /**
   * Individuelles Timeout für diesen Request.
   *
   * Mit `null` wird das automatische Timeout deaktiviert.
   */
  timeoutMs?: number | null;

  /**
   * Standardmäßig werden Cookies und Sessiondaten auch für die
   * getrennten Entwicklungsursprünge 5173 und 8000 übertragen.
   */
  credentials?: RequestCredentials;

  /**
   * Überschreibt den erwarteten Antworttyp.
   *
   * Standardmäßig wird der Antworttyp anhand des Content-Type bestimmt.
   */
  responseType?: ApiResponseType;

  /**
   * Optional vorgegebene Client-Request-ID.
   *
   * Wird keine ID angegeben, erzeugt der Client eine UUID.
   */
  clientRequestId?: string;
};

export type ApiRequestWithBodyOptions<TBody> = ApiRequestOptions & {
  body?: TBody;
};

export type ApiStreamRequestOptions<TBody = unknown> = Omit<
  ApiRequestWithBodyOptions<TBody>,
  "responseType"
> & {
  /**
   * Erwarteter MIME-Typ der Streaming-Antwort.
   *
   * Standard: `text/event-stream`.
   */
  expectedContentType?: string;
};

export type ApiStreamHandle = {
  response: Response;
  clientRequestId: string;
  requestId?: string;

  /**
   * Beendet den laufenden Request und damit auch das Lesen des Streams.
   */
  cancel: (reason?: unknown) => void;

  /**
   * Entfernt Timeout und Event-Listener.
   *
   * Nach natürlichem Abschluss des Streams muss `dispose()` aufgerufen
   * werden. Zum vorzeitigen Beenden zuerst `cancel()` verwenden.
   */
  dispose: () => void;
};

type DeveloperLogLevel = "debug" | "info" | "warn" | "error";

type DeveloperLogContext = Record<string, unknown>;

type CombinedAbortSignal = {
  signal: AbortSignal;

  /**
   * Beendet den Request ausdrücklich.
   */
  abort: (reason?: unknown) => void;

  /**
   * Entfernt nur das automatische Timeout.
   *
   * Der externe Abort-Listener bleibt aktiv.
   */
  clearTimeout: () => void;

  /**
   * Entfernt sämtliche Ressourcen.
   */
  cleanup: () => void;
};

type PreparedApiRequest = {
  method: string;
  url: string;
  headers: Headers;
  body: BodyInit | undefined;
  signal: AbortSignal;
  credentials: RequestCredentials;
  clientRequestId: string;
  abort: (reason?: unknown) => void;
  clearTimeout: () => void;
  cleanup: () => void;
};

export class ApiError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly code: string;
  readonly details: unknown;
  readonly requestId?: string;
  readonly clientRequestId?: string;
  readonly url: string;

  constructor(params: {
    message: string;
    status: number;
    statusText: string;
    code?: string;
    details?: unknown;
    requestId?: string;
    clientRequestId?: string;
    url: string;
    cause?: unknown;
  }) {
    super(params.message, {
      cause: params.cause,
    });

    this.name = "ApiError";
    this.status = params.status;
    this.statusText = params.statusText;

    this.code = params.code ?? "api_error";

    this.details = params.details;

    this.requestId = params.requestId;

    this.clientRequestId = params.clientRequestId;

    this.url = params.url;
  }
}

function logDeveloperStep(
  level: DeveloperLogLevel,
  step: string,
  context: DeveloperLogContext = {},
): void {
  if (!import.meta.env.DEV) {
    return;
  }

  const entry = {
    timestamp: new Date().toISOString(),
    source: SOURCE_FILE,
    area: "api-client",
    step,
    ...context,
  };

  switch (level) {
    case "error":
      console.error("[Kernschmied][ApiClient]", entry);
      break;

    case "warn":
      console.warn("[Kernschmied][ApiClient]", entry);
      break;

    case "info":
      console.info("[Kernschmied][ApiClient]", entry);
      break;

    default:
      console.debug("[Kernschmied][ApiClient]", entry);
  }
}

function createRequestId(): string {
  if (
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
  ) {
    return crypto.randomUUID();
  }

  return [
    "request",
    Date.now().toString(36),
    Math.random().toString(36).slice(2),
  ].join("-");
}

function normalizeRequestId(
  value: string | null | undefined,
): string | undefined {
  if (value === null || value === undefined) {
    return undefined;
  }

  const normalized = value.trim();

  if (!normalized) {
    return undefined;
  }

  if (normalized.length > MAX_REQUEST_ID_LENGTH) {
    return undefined;
  }

  if (!REQUEST_ID_PATTERN.test(normalized)) {
    return undefined;
  }

  return normalized;
}

function resolveClientRequestId(
  options: ApiRequestOptions,
  headers: Headers,
  url: string,
): string {
  const optionValue = options.clientRequestId;

  if (optionValue !== undefined) {
    const normalizedOptionValue = normalizeRequestId(optionValue);

    if (!normalizedOptionValue) {
      throw new ApiError({
        message: "Die angegebene Client-Request-ID ist ungültig.",
        status: 0,
        statusText: "Invalid request ID",
        code: "invalid_client_request_id",
        details: {
          maxLength: MAX_REQUEST_ID_LENGTH,
        },
        url,
      });
    }

    headers.set(CLIENT_REQUEST_ID_HEADER, normalizedOptionValue);

    return normalizedOptionValue;
  }

  const existingHeaderValue = headers.get(CLIENT_REQUEST_ID_HEADER);

  if (existingHeaderValue !== null) {
    const normalizedHeaderValue = normalizeRequestId(existingHeaderValue);

    if (!normalizedHeaderValue) {
      throw new ApiError({
        message: `Der Header ${CLIENT_REQUEST_ID_HEADER} enthält eine ungültige Request-ID.`,
        status: 0,
        statusText: "Invalid request ID",
        code: "invalid_client_request_id",
        details: {
          header: CLIENT_REQUEST_ID_HEADER,
          maxLength: MAX_REQUEST_ID_LENGTH,
        },
        url,
      });
    }

    headers.set(CLIENT_REQUEST_ID_HEADER, normalizedHeaderValue);

    return normalizedHeaderValue;
  }

  const generatedRequestId = createRequestId();

  headers.set(CLIENT_REQUEST_ID_HEADER, generatedRequestId);

  return generatedRequestId;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getBrowserOrigin(): string {
  if (
    typeof globalThis.location !== "undefined" &&
    typeof globalThis.location.origin === "string" &&
    globalThis.location.origin.length > 0
  ) {
    return globalThis.location.origin;
  }

  return FALLBACK_BROWSER_ORIGIN;
}

function normalizeUrlPathname(pathname: string): string {
  const normalized = pathname.replace(/\/{2,}/g, "/");

  if (normalized === "/") {
    return "";
  }

  return normalized.replace(/\/+$/, "");
}

function normalizeBaseUrl(value: string | undefined): string {
  const configuredValue = value?.trim() || DEFAULT_API_BASE_URL;

  const url = new URL(configuredValue, getBrowserOrigin());

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error(`Nicht unterstütztes API-Protokoll: ${url.protocol}`);
  }

  url.pathname = normalizeUrlPathname(url.pathname) || "/";

  url.search = "";
  url.hash = "";

  return url.toString().replace(/\/+$/, "");
}

export const API_BASE_URL = normalizeBaseUrl(import.meta.env.VITE_API_URL);

const PARSED_API_BASE_URL = new URL(API_BASE_URL);

const API_BASE_ORIGIN = PARSED_API_BASE_URL.origin;

const API_BASE_PATHNAME = normalizeUrlPathname(PARSED_API_BASE_URL.pathname);

logDeveloperStep("info", "api-client-initialized", {
  apiBaseOrigin: API_BASE_ORIGIN,
  apiBasePathname: API_BASE_PATHNAME,
  defaultCredentials: DEFAULT_REQUEST_CREDENTIALS,
});

function normalizeRequestPath(path: string): string {
  const normalized = path.trim();

  if (!normalized) {
    throw new Error("Der API-Pfad darf nicht leer sein.");
  }

  if (normalized.startsWith("//")) {
    throw new Error(
      `Protokollrelative API-URLs sind nicht erlaubt: ${normalized}`,
    );
  }

  if (normalized.includes("\\")) {
    throw new Error(
      `API-Pfade dürfen keine Backslashes enthalten: ${normalized}`,
    );
  }

  return normalized;
}

function hasExplicitUrlScheme(value: string): boolean {
  return /^[a-z][a-z\d+.-]*:/i.test(value);
}

function joinUrlPathnames(
  basePathname: string,
  requestPathname: string,
): string {
  const normalizedBase = normalizeUrlPathname(basePathname);

  const normalizedRequest = normalizeUrlPathname(requestPathname);

  if (!normalizedBase) {
    return normalizedRequest || "/";
  }

  if (!normalizedRequest) {
    return normalizedBase;
  }

  return `${normalizedBase}/${normalizedRequest.replace(/^\/+/, "")}`;
}

/**
 * Löst einen API-Pfad gegen die konfigurierte API-Basis auf.
 *
 * Absolute URLs sind ausschließlich auf demselben Ursprung erlaubt.
 */
export function resolveApiUrl(path: string): URL {
  const normalizedPath = normalizeRequestPath(path);

  if (hasExplicitUrlScheme(normalizedPath)) {
    const absoluteUrl = new URL(normalizedPath);

    if (absoluteUrl.protocol !== "http:" && absoluteUrl.protocol !== "https:") {
      throw new Error(
        `Nicht unterstütztes API-Protokoll: ${absoluteUrl.protocol}`,
      );
    }

    if (absoluteUrl.origin !== API_BASE_ORIGIN) {
      throw new Error(
        `Externe API-URLs sind nicht erlaubt: ${absoluteUrl.origin}`,
      );
    }

    absoluteUrl.hash = "";

    return absoluteUrl;
  }

  const parsedPath = new URL(normalizedPath, API_BASE_ORIGIN);

  const requestedPathname = normalizeUrlPathname(parsedPath.pathname);

  const alreadyContainsApiBasePath =
    API_BASE_PATHNAME.length === 0 ||
    requestedPathname === API_BASE_PATHNAME ||
    requestedPathname.startsWith(`${API_BASE_PATHNAME}/`);

  const resolvedPathname = alreadyContainsApiBasePath
    ? requestedPathname
    : joinUrlPathnames(API_BASE_PATHNAME, requestedPathname);

  const resolvedUrl = new URL(API_BASE_ORIGIN);

  resolvedUrl.pathname = resolvedPathname || "/";

  resolvedUrl.search = parsedPath.search;

  resolvedUrl.hash = "";

  return resolvedUrl;
}

function appendQueryParams(url: URL, query: ApiQueryParams): void {
  for (const [key, rawValue] of Object.entries(query)) {
    if (rawValue === undefined || rawValue === null) {
      continue;
    }

    const values = Array.isArray(rawValue) ? rawValue : [rawValue];

    for (const value of values) {
      url.searchParams.append(key, String(value));
    }
  }
}

function buildApiUrl(path: string, query?: ApiQueryParams): string {
  const url = resolveApiUrl(path);

  if (query) {
    appendQueryParams(url, query);
  }

  return url.toString();
}

function getSafeLogUrl(value: string): string {
  try {
    const url = new URL(value);

    return `${url.origin}${url.pathname}`;
  } catch {
    return value;
  }
}

function isJsonContentType(contentType: string | null): boolean {
  if (!contentType) {
    return false;
  }

  const normalizedContentType = contentType.toLowerCase();

  return (
    normalizedContentType.includes("application/json") ||
    normalizedContentType.includes("+json")
  );
}

function isBodyAllowed(method: string): boolean {
  return method !== "GET" && method !== "HEAD";
}

function isFormData(value: unknown): value is FormData {
  return typeof FormData !== "undefined" && value instanceof FormData;
}

function isBlob(value: unknown): value is Blob {
  return typeof Blob !== "undefined" && value instanceof Blob;
}

function isUrlSearchParams(value: unknown): value is URLSearchParams {
  return (
    typeof URLSearchParams !== "undefined" && value instanceof URLSearchParams
  );
}

function isReadableStream(value: unknown): value is ReadableStream {
  return (
    typeof ReadableStream !== "undefined" && value instanceof ReadableStream
  );
}

function isArrayBuffer(value: unknown): value is ArrayBuffer {
  return typeof ArrayBuffer !== "undefined" && value instanceof ArrayBuffer;
}

function isArrayBufferView(value: unknown): value is ArrayBufferView {
  return typeof ArrayBuffer !== "undefined" && ArrayBuffer.isView(value);
}

function isRequestBody(value: unknown): value is BodyInit {
  return (
    typeof value === "string" ||
    isFormData(value) ||
    isBlob(value) ||
    isUrlSearchParams(value) ||
    isReadableStream(value) ||
    isArrayBuffer(value) ||
    isArrayBufferView(value)
  );
}

function serializeRequestBody(
  body: unknown,
  headers: Headers,
): BodyInit | undefined {
  if (body === undefined || body === null) {
    return undefined;
  }

  if (isRequestBody(body)) {
    return body;
  }

  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  try {
    return JSON.stringify(body);
  } catch (error) {
    throw new ApiError({
      message: "Der Request-Body konnte nicht als JSON serialisiert werden.",
      status: 0,
      statusText: "Invalid request body",
      code: "request_body_serialization_failed",
      details: null,
      url: "",
      cause: error,
    });
  }
}

function normalizeTimeoutMs(timeoutMs: number | null): number | null {
  if (timeoutMs === null) {
    return null;
  }

  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    return null;
  }

  return Math.floor(timeoutMs);
}

function createCombinedAbortSignal(params: {
  externalSignal?: AbortSignal;
  timeoutMs: number | null;
}): CombinedAbortSignal {
  const controller = new AbortController();

  let cleanedUp = false;

  let timeoutId: ReturnType<typeof setTimeout> | undefined;

  const abort = (reason?: unknown): void => {
    if (controller.signal.aborted) {
      return;
    }

    controller.abort(reason);
  };

  const abortFromExternalSignal = (): void => {
    abort(params.externalSignal?.reason);
  };

  if (params.externalSignal) {
    if (params.externalSignal.aborted) {
      abortFromExternalSignal();
    } else {
      params.externalSignal.addEventListener("abort", abortFromExternalSignal, {
        once: true,
      });
    }
  }

  const clearTimeoutResource = (): void => {
    if (timeoutId === undefined) {
      return;
    }

    clearTimeout(timeoutId);

    timeoutId = undefined;
  };

  const normalizedTimeoutMs = normalizeTimeoutMs(params.timeoutMs);

  if (normalizedTimeoutMs !== null) {
    timeoutId = setTimeout(() => {
      abort(
        new DOMException(
          `API-Anfrage nach ${normalizedTimeoutMs} ms abgebrochen.`,
          "TimeoutError",
        ),
      );
    }, normalizedTimeoutMs);
  }

  return {
    signal: controller.signal,

    abort,

    clearTimeout: clearTimeoutResource,

    cleanup: () => {
      if (cleanedUp) {
        return;
      }

      cleanedUp = true;

      clearTimeoutResource();

      params.externalSignal?.removeEventListener(
        "abort",
        abortFromExternalSignal,
      );
    },
  };
}

function normalizeHttpMethod(method: string): string {
  const normalized = method.trim().toUpperCase();

  if (!normalized) {
    throw new ApiError({
      message: "Die HTTP-Methode darf nicht leer sein.",
      status: 0,
      statusText: "Invalid request",
      code: "invalid_http_method",
      details: null,
      url: "",
    });
  }

  if (!/^[A-Z]+$/.test(normalized)) {
    throw new ApiError({
      message: `Die HTTP-Methode "${method}" ist ungültig.`,
      status: 0,
      statusText: "Invalid request",
      code: "invalid_http_method",
      details: {
        method,
      },
      url: "",
    });
  }

  return normalized;
}

function formatValidationErrorEntries(value: unknown): string | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }

  const entries = value.map((entry) => {
    if (!isRecord(entry)) {
      return String(entry);
    }

    const location = Array.isArray(entry.loc) ? entry.loc.join(".") : "request";

    const message =
      typeof entry.msg === "string" ? entry.msg : "Ungültiger Wert";

    return `${location}: ${message}`;
  });

  return entries.length > 0 ? entries.join("; ") : undefined;
}

function formatStructuredDetails(details: unknown): string | undefined {
  if (!isRecord(details)) {
    return undefined;
  }

  return formatValidationErrorEntries(details.errors);
}

function normalizeErrorPayload(
  payload: Record<string, unknown>,
): ApiErrorResponse {
  const structuredMessage =
    typeof payload.message === "string" ? payload.message : undefined;

  const detailMessage =
    typeof payload.detail === "string"
      ? payload.detail
      : formatValidationErrorEntries(payload.detail);

  const details =
    payload.details !== undefined
      ? payload.details
      : payload.detail !== undefined && typeof payload.detail !== "string"
        ? payload.detail
        : undefined;

  const detailsMessage = formatStructuredDetails(details);

  return {
    code: typeof payload.code === "string" ? payload.code : undefined,

    message: structuredMessage ?? detailMessage ?? detailsMessage,

    details,

    request_id:
      typeof payload.request_id === "string" ? payload.request_id : undefined,
  };
}

async function parseErrorResponse(
  response: Response,
): Promise<ApiErrorResponse> {
  const contentType = response.headers.get("content-type");

  if (isJsonContentType(contentType)) {
    const jsonResponse = response.clone();

    try {
      const payload = (await jsonResponse.json()) as unknown;

      if (isRecord(payload)) {
        return normalizeErrorPayload(payload);
      }
    } catch (error) {
      logDeveloperStep("warn", "error-response-json-parse-failed", {
        status: response.status,
        contentType,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  try {
    const text = await response.text();

    if (text.trim()) {
      return {
        message: text.trim(),
      };
    }
  } catch (error) {
    logDeveloperStep("warn", "error-response-text-read-failed", {
      status: response.status,
      error: error instanceof Error ? error.message : String(error),
    });
  }

  return {};
}

async function parseSuccessResponse<T>(
  response: Response,
  responseType: ApiResponseType,
): Promise<T> {
  if (
    responseType === "void" ||
    response.status === 204 ||
    response.status === 205
  ) {
    return undefined as T;
  }

  if (responseType === "blob") {
    return (await response.blob()) as T;
  }

  if (responseType === "text") {
    return (await response.text()) as T;
  }

  if (responseType === "json") {
    try {
      return (await response.json()) as T;
    } catch (error) {
      throw new ApiError({
        message: "Die API-Antwort enthält kein gültiges JSON.",
        status: response.status,
        statusText: response.statusText,
        code: "invalid_json_response",
        details: null,
        requestId: normalizeRequestId(
          response.headers.get(SERVER_REQUEST_ID_HEADER),
        ),
        url: response.url,
        cause: error,
      });
    }
  }

  const contentType = response.headers.get("content-type");

  if (isJsonContentType(contentType)) {
    try {
      return (await response.json()) as T;
    } catch (error) {
      throw new ApiError({
        message:
          "Die API-Antwort wurde als JSON angekündigt, enthält jedoch kein gültiges JSON.",
        status: response.status,
        statusText: response.statusText,
        code: "invalid_json_response",
        details: {
          contentType,
        },
        requestId: normalizeRequestId(
          response.headers.get(SERVER_REQUEST_ID_HEADER),
        ),
        url: response.url,
        cause: error,
      });
    }
  }

  return (await response.text()) as T;
}

function getAbortErrorDetails(signal: AbortSignal): {
  code: string;
  message: string;
  statusText: string;
  reason: unknown;
} {
  const reason = signal.reason;

  if (reason instanceof DOMException && reason.name === "TimeoutError") {
    return {
      code: "request_timeout",
      message:
        reason.message || "Die API-Anfrage hat das Zeitlimit überschritten.",
      statusText: "Request timeout",
      reason,
    };
  }

  if (reason instanceof Error && reason.name === "TimeoutError") {
    return {
      code: "request_timeout",
      message:
        reason.message || "Die API-Anfrage hat das Zeitlimit überschritten.",
      statusText: "Request timeout",
      reason,
    };
  }

  return {
    code: "request_aborted",
    message: "Die API-Anfrage wurde abgebrochen.",
    statusText: "Request aborted",
    reason,
  };
}

function isAbortLikeError(error: unknown, signal: AbortSignal): boolean {
  if (signal.aborted) {
    return true;
  }

  return error instanceof DOMException && error.name === "AbortError";
}

function prepareApiRequest<TBody>(
  method: string,
  path: string,
  options: ApiRequestWithBodyOptions<TBody>,
  defaultTimeoutMs: number | null,
): PreparedApiRequest {
  const normalizedMethod = normalizeHttpMethod(method);

  let url: string;

  try {
    url = buildApiUrl(path, options.query);
  } catch (error) {
    throw new ApiError({
      message:
        error instanceof Error ? error.message : "Der API-Pfad ist ungültig.",
      status: 0,
      statusText: "Invalid API URL",
      code: "invalid_api_url",
      details: {
        path,
      },
      url: path,
      cause: error,
    });
  }

  if (
    !isBodyAllowed(normalizedMethod) &&
    options.body !== undefined &&
    options.body !== null
  ) {
    throw new ApiError({
      message: `Die HTTP-Methode ${normalizedMethod} darf in diesem Client keinen Request-Body enthalten.`,
      status: 0,
      statusText: "Invalid request body",
      code: "body_not_allowed",
      details: {
        method: normalizedMethod,
      },
      url,
    });
  }

  const headers = new Headers(options.headers);

  const clientRequestId = resolveClientRequestId(options, headers, url);

  const timeoutMs =
    options.timeoutMs === undefined ? defaultTimeoutMs : options.timeoutMs;

  const abortResources = createCombinedAbortSignal({
    externalSignal: options.signal,
    timeoutMs,
  });

  let body: BodyInit | undefined;

  try {
    body = isBodyAllowed(normalizedMethod)
      ? serializeRequestBody(options.body, headers)
      : undefined;
  } catch (error) {
    abortResources.cleanup();

    if (error instanceof ApiError) {
      throw new ApiError({
        message: error.message,
        status: error.status,
        statusText: error.statusText,
        code: error.code,
        details: error.details,
        requestId: error.requestId,
        clientRequestId,
        url,
        cause: error,
      });
    }

    throw error;
  }

  return {
    method: normalizedMethod,
    url,
    headers,
    body,
    signal: abortResources.signal,
    credentials: options.credentials ?? DEFAULT_REQUEST_CREDENTIALS,
    clientRequestId,
    abort: abortResources.abort,
    clearTimeout: abortResources.clearTimeout,
    cleanup: abortResources.cleanup,
  };
}

async function createHttpError(
  response: Response,
  params: {
    url: string;
    clientRequestId: string;
  },
): Promise<ApiError> {
  const errorPayload = await parseErrorResponse(response);

  const requestId =
    normalizeRequestId(errorPayload.request_id) ??
    normalizeRequestId(response.headers.get(SERVER_REQUEST_ID_HEADER));

  return new ApiError({
    message:
      errorPayload.message ??
      `API-Anfrage fehlgeschlagen: ${response.status} ${response.statusText}`,
    status: response.status,
    statusText: response.statusText,
    code: errorPayload.code,
    details: errorPayload.details,
    requestId,
    clientRequestId: params.clientRequestId,
    url: params.url,
  });
}

function normalizeCaughtRequestError(
  error: unknown,
  params: {
    signal: AbortSignal;
    url: string;
    clientRequestId: string;
  },
): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (isAbortLikeError(error, params.signal)) {
    const abortError = getAbortErrorDetails(params.signal);

    return new ApiError({
      message: abortError.message,
      status: 0,
      statusText: abortError.statusText,
      code: abortError.code,
      details: {
        reason: abortError.reason,
      },
      clientRequestId: params.clientRequestId,
      url: params.url,
      cause: error,
    });
  }

  return new ApiError({
    message:
      error instanceof Error ? error.message : "Die API ist nicht erreichbar.",
    status: 0,
    statusText: "Network error",
    code: "network_error",
    details: null,
    clientRequestId: params.clientRequestId,
    url: params.url,
    cause: error,
  });
}

export async function apiRequest<TResponse, TBody = unknown>(
  method: string,
  path: string,
  options: ApiRequestWithBodyOptions<TBody> = {},
): Promise<TResponse> {
  const prepared = prepareApiRequest(
    method,
    path,
    options,
    DEFAULT_REQUEST_TIMEOUT_MS,
  );

  const startedAt = performance.now();

  logDeveloperStep("info", "request-started", {
    method: prepared.method,
    url: getSafeLogUrl(prepared.url),
    clientRequestId: prepared.clientRequestId,
    timeoutMs:
      options.timeoutMs === undefined
        ? DEFAULT_REQUEST_TIMEOUT_MS
        : options.timeoutMs,
    hasBody: prepared.body !== undefined,
    credentials: prepared.credentials,
  });

  try {
    const response = await fetch(prepared.url, {
      method: prepared.method,
      headers: prepared.headers,
      signal: prepared.signal,
      credentials: prepared.credentials,
      body: prepared.body,
    });

    const requestId = normalizeRequestId(
      response.headers.get(SERVER_REQUEST_ID_HEADER),
    );

    logDeveloperStep(
      response.ok ? "info" : "warn",
      "response-headers-received",
      {
        method: prepared.method,
        url: getSafeLogUrl(prepared.url),
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        contentType: response.headers.get("content-type"),
        requestId,
        clientRequestId: prepared.clientRequestId,
        durationMs: Math.round(performance.now() - startedAt),
      },
    );

    if (!response.ok) {
      throw await createHttpError(response, {
        url: prepared.url,
        clientRequestId: prepared.clientRequestId,
      });
    }

    const result = await parseSuccessResponse<TResponse>(
      response,
      options.responseType ?? "auto",
    );

    logDeveloperStep("info", "response-parsed", {
      method: prepared.method,
      url: getSafeLogUrl(prepared.url),
      status: response.status,
      responseType: options.responseType ?? "auto",
      requestId,
      clientRequestId: prepared.clientRequestId,
      durationMs: Math.round(performance.now() - startedAt),
    });

    return result;
  } catch (error) {
    const normalizedError = normalizeCaughtRequestError(error, {
      signal: prepared.signal,
      url: prepared.url,
      clientRequestId: prepared.clientRequestId,
    });

    logDeveloperStep(
      normalizedError.code === "request_aborted" ? "info" : "error",
      "request-failed",
      {
        method: prepared.method,
        url: getSafeLogUrl(prepared.url),
        status: normalizedError.status,
        statusText: normalizedError.statusText,
        code: normalizedError.code,
        message: normalizedError.message,
        requestId: normalizedError.requestId,
        clientRequestId: normalizedError.clientRequestId,
        durationMs: Math.round(performance.now() - startedAt),
      },
    );

    throw normalizedError;
  } finally {
    prepared.cleanup();

    logDeveloperStep("debug", "request-cleanup-completed", {
      method: prepared.method,
      url: getSafeLogUrl(prepared.url),
      clientRequestId: prepared.clientRequestId,
    });
  }
}

/**
 * Öffnet eine Streaming-Antwort.
 *
 * Das automatische Timeout gilt ausschließlich bis zum Empfang der
 * Response-Header. Danach bleibt nur das optionale externe AbortSignal
 * aktiv.
 */
export async function apiStreamRequest<TBody = unknown>(
  method: string,
  path: string,
  options: ApiStreamRequestOptions<TBody> = {},
): Promise<ApiStreamHandle> {
  const prepared = prepareApiRequest(
    method,
    path,
    options,
    DEFAULT_STREAM_CONNECT_TIMEOUT_MS,
  );

  const expectedContentType = (
    options.expectedContentType ?? DEFAULT_STREAM_CONTENT_TYPE
  )
    .trim()
    .toLowerCase();

  if (!prepared.headers.has("Accept")) {
    prepared.headers.set("Accept", expectedContentType);
  }

  const startedAt = performance.now();

  logDeveloperStep("info", "stream-request-started", {
    method: prepared.method,
    url: getSafeLogUrl(prepared.url),
    clientRequestId: prepared.clientRequestId,
    expectedContentType,
    connectTimeoutMs:
      options.timeoutMs === undefined
        ? DEFAULT_STREAM_CONNECT_TIMEOUT_MS
        : options.timeoutMs,
    credentials: prepared.credentials,
  });

  try {
    const response = await fetch(prepared.url, {
      method: prepared.method,
      headers: prepared.headers,
      signal: prepared.signal,
      credentials: prepared.credentials,
      body: prepared.body,
      cache: "no-store",
    });

    /*
     * Der Verbindungsaufbau ist abgeschlossen.
     *
     * Ab jetzt darf das Connect-Timeout den laufenden SSE-Stream
     * nicht mehr beenden.
     */
    prepared.clearTimeout();

    const requestId = normalizeRequestId(
      response.headers.get(SERVER_REQUEST_ID_HEADER),
    );

    const contentType = response.headers.get("content-type");

    logDeveloperStep(
      response.ok ? "info" : "warn",
      "stream-response-headers-received",
      {
        method: prepared.method,
        url: getSafeLogUrl(prepared.url),
        status: response.status,
        statusText: response.statusText,
        contentType,
        requestId,
        clientRequestId: prepared.clientRequestId,
        durationMs: Math.round(performance.now() - startedAt),
      },
    );

    if (!response.ok) {
      throw await createHttpError(response, {
        url: prepared.url,
        clientRequestId: prepared.clientRequestId,
      });
    }

    if (
      !contentType ||
      !contentType.toLowerCase().includes(expectedContentType)
    ) {
      const error = new ApiError({
        message: `Die API hat einen unerwarteten Antworttyp geliefert. Erwartet: ${expectedContentType}, erhalten: ${contentType ?? "unbekannt"}.`,
        status: response.status,
        statusText: response.statusText,
        code: "unexpected_content_type",
        details: {
          expectedContentType,
          actualContentType: contentType,
        },
        requestId,
        clientRequestId: prepared.clientRequestId,
        url: prepared.url,
      });

      try {
        await response.body?.cancel();
      } catch {
        // Der Stream kann bereits geschlossen sein.
      }

      throw error;
    }

    if (!response.body) {
      throw new ApiError({
        message: "Die API hat keinen lesbaren Antwortstream geliefert.",
        status: response.status,
        statusText: response.statusText,
        code: "missing_response_stream",
        details: null,
        requestId,
        clientRequestId: prepared.clientRequestId,
        url: prepared.url,
      });
    }

    let disposed = false;

    const cancel = (
      reason: unknown = new DOMException(
        "Der API-Stream wurde vom Client beendet.",
        "AbortError",
      ),
    ): void => {
      if (prepared.signal.aborted) {
        return;
      }

      logDeveloperStep("info", "stream-request-cancelled", {
        method: prepared.method,
        url: getSafeLogUrl(prepared.url),
        requestId,
        clientRequestId: prepared.clientRequestId,
      });

      prepared.abort(reason);
    };

    const dispose = (): void => {
      if (disposed) {
        return;
      }

      disposed = true;

      prepared.cleanup();

      logDeveloperStep("debug", "stream-request-disposed", {
        method: prepared.method,
        url: getSafeLogUrl(prepared.url),
        requestId,
        clientRequestId: prepared.clientRequestId,
      });
    };

    return {
      response,
      clientRequestId: prepared.clientRequestId,
      requestId,
      cancel,
      dispose,
    };
  } catch (error) {
    prepared.cleanup();

    const normalizedError = normalizeCaughtRequestError(error, {
      signal: prepared.signal,
      url: prepared.url,
      clientRequestId: prepared.clientRequestId,
    });

    logDeveloperStep(
      normalizedError.code === "request_aborted" ? "info" : "error",
      "stream-request-failed",
      {
        method: prepared.method,
        url: getSafeLogUrl(prepared.url),
        status: normalizedError.status,
        statusText: normalizedError.statusText,
        code: normalizedError.code,
        message: normalizedError.message,
        requestId: normalizedError.requestId,
        clientRequestId: normalizedError.clientRequestId,
        durationMs: Math.round(performance.now() - startedAt),
      },
    );

    throw normalizedError;
  }
}

export function apiGet<TResponse>(
  path: string,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>("GET", path, options);
}

export function apiPost<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse, TBody>("POST", path, {
    ...options,
    body,
  });
}

export function apiPut<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse, TBody>("PUT", path, {
    ...options,
    body,
  });
}

export function apiPatch<TResponse, TBody = unknown>(
  path: string,
  body?: TBody,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse, TBody>("PATCH", path, {
    ...options,
    body,
  });
}

export function apiDelete<TResponse = void>(
  path: string,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>("DELETE", path, options);
}

export function apiPostStream<TBody = unknown>(
  path: string,
  body?: TBody,
  options?: Omit<ApiStreamRequestOptions<TBody>, "body">,
): Promise<ApiStreamHandle> {
  return apiStreamRequest("POST", path, {
    ...options,
    body,
  });
}
