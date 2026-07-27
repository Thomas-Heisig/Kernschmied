// F:\Kernschmied\frontend\src\api\client.ts

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_REQUEST_TIMEOUT_MS = 30_000;
const FALLBACK_BROWSER_ORIGIN = "http://localhost";

type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | readonly (string | number | boolean)[];

export type ApiQueryParams = Record<string, QueryValue>;

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
   * Standardmäßig werden Cookies für gleiche Ursprünge übertragen.
   *
   * Für Session-Authentifizierung kann global oder je Request
   * `include` verwendet werden.
   */
  credentials?: RequestCredentials;

  /**
   * Überschreibt den erwarteten Antworttyp.
   *
   * Standardmäßig wird der Antworttyp anhand des Content-Type bestimmt.
   */
  responseType?: "auto" | "json" | "text" | "blob" | "void";
};

export type ApiRequestWithBodyOptions<TBody> =
  ApiRequestOptions & {
    body?: TBody;
  };

export class ApiError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly code: string;
  readonly details: unknown;
  readonly requestId?: string;
  readonly url: string;

  constructor(params: {
    message: string;
    status: number;
    statusText: string;
    code?: string;
    details?: unknown;
    requestId?: string;
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
    this.url = params.url;
  }
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

function normalizeBaseUrl(
  value: string | undefined,
): string {
  const configuredValue =
    value?.trim() || DEFAULT_API_BASE_URL;

  const url = new URL(
    configuredValue,
    getBrowserOrigin(),
  );

  if (
    url.protocol !== "http:" &&
    url.protocol !== "https:"
  ) {
    throw new Error(
      `Nicht unterstütztes API-Protokoll: ${url.protocol}`,
    );
  }

  url.pathname =
    normalizeUrlPathname(url.pathname) || "/";

  url.search = "";
  url.hash = "";

  return url.toString().replace(/\/+$/, "");
}

export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_URL,
);

const PARSED_API_BASE_URL = new URL(API_BASE_URL);
const API_BASE_ORIGIN = PARSED_API_BASE_URL.origin;

const API_BASE_PATHNAME =
  normalizeUrlPathname(
    PARSED_API_BASE_URL.pathname,
  );

function normalizeUrlPathname(
  pathname: string,
): string {
  const normalized =
    pathname.replace(/\/{2,}/g, "/");

  if (normalized === "/") {
    return "";
  }

  return normalized.replace(/\/+$/, "");
}

function normalizeRequestPath(
  path: string,
): string {
  const normalized = path.trim();

  if (!normalized) {
    throw new Error(
      "Der API-Pfad darf nicht leer sein.",
    );
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

function hasExplicitUrlScheme(
  value: string,
): boolean {
  return /^[a-z][a-z\d+.-]*:/i.test(value);
}

/**
 * Löst einen API-Pfad gegen die konfigurierte API-Basis auf.
 *
 * Unterstützte Eingaben:
 *
 * `/bootstrap`
 *   wird relativ zur API-Basis aufgelöst.
 *
 * `/api/v1/bootstrap`
 *   wird als bereits vollständiger lokaler API-Pfad behandelt.
 *
 * `http://localhost:8000/api/v1/bootstrap`
 *   ist nur zulässig, wenn der Ursprung mit der konfigurierten
 *   API-Basis übereinstimmt.
 */
export function resolveApiUrl(
  path: string,
): URL {
  const normalizedPath =
    normalizeRequestPath(path);

  if (hasExplicitUrlScheme(normalizedPath)) {
    const absoluteUrl =
      new URL(normalizedPath);

    if (
      absoluteUrl.protocol !== "http:" &&
      absoluteUrl.protocol !== "https:"
    ) {
      throw new Error(
        `Nicht unterstütztes API-Protokoll: ${absoluteUrl.protocol}`,
      );
    }

    if (
      absoluteUrl.origin !==
      API_BASE_ORIGIN
    ) {
      throw new Error(
        `Externe API-URLs sind nicht erlaubt: ${absoluteUrl.origin}`,
      );
    }

    absoluteUrl.hash = "";

    return absoluteUrl;
  }

  const parsedPath = new URL(
    normalizedPath,
    API_BASE_ORIGIN,
  );

  const requestedPathname =
    normalizeUrlPathname(
      parsedPath.pathname,
    );

  const alreadyContainsApiBasePath =
    API_BASE_PATHNAME.length === 0 ||
    requestedPathname === API_BASE_PATHNAME ||
    requestedPathname.startsWith(
      `${API_BASE_PATHNAME}/`,
    );

  const resolvedPathname =
    alreadyContainsApiBasePath
      ? requestedPathname
      : joinUrlPathnames(
          API_BASE_PATHNAME,
          requestedPathname,
        );

  const resolvedUrl =
    new URL(API_BASE_ORIGIN);

  resolvedUrl.pathname =
    resolvedPathname || "/";

  resolvedUrl.search =
    parsedPath.search;

  resolvedUrl.hash = "";

  return resolvedUrl;
}

function joinUrlPathnames(
  basePathname: string,
  requestPathname: string,
): string {
  const normalizedBase =
    normalizeUrlPathname(basePathname);

  const normalizedRequest =
    normalizeUrlPathname(
      requestPathname,
    );

  if (!normalizedBase) {
    return normalizedRequest || "/";
  }

  if (!normalizedRequest) {
    return normalizedBase;
  }

  return `${normalizedBase}/${normalizedRequest.replace(
    /^\/+/,
    "",
  )}`;
}

function buildApiUrl(
  path: string,
  query?: ApiQueryParams,
): string {
  const url = resolveApiUrl(path);

  if (query) {
    appendQueryParams(
      url,
      query,
    );
  }

  return url.toString();
}

function appendQueryParams(
  url: URL,
  query: ApiQueryParams,
): void {
  for (
    const [key, rawValue] of
    Object.entries(query)
  ) {
    if (
      rawValue === undefined ||
      rawValue === null
    ) {
      continue;
    }

    const values =
      Array.isArray(rawValue)
        ? rawValue
        : [rawValue];

    for (const value of values) {
      url.searchParams.append(
        key,
        String(value),
      );
    }
  }
}

function isJsonContentType(
  contentType: string | null,
): boolean {
  if (!contentType) {
    return false;
  }

  const normalizedContentType =
    contentType.toLowerCase();

  return (
    normalizedContentType.includes(
      "application/json",
    ) ||
    normalizedContentType.includes(
      "+json",
    )
  );
}

function isBodyAllowed(
  method: string,
): boolean {
  return (
    method !== "GET" &&
    method !== "HEAD"
  );
}

function isFormData(
  value: unknown,
): value is FormData {
  return (
    typeof FormData !== "undefined" &&
    value instanceof FormData
  );
}

function isBlob(
  value: unknown,
): value is Blob {
  return (
    typeof Blob !== "undefined" &&
    value instanceof Blob
  );
}

function isUrlSearchParams(
  value: unknown,
): value is URLSearchParams {
  return (
    typeof URLSearchParams !== "undefined" &&
    value instanceof URLSearchParams
  );
}

function isRequestBody(
  value: unknown,
): value is BodyInit {
  return (
    typeof value === "string" ||
    isFormData(value) ||
    isBlob(value) ||
    isUrlSearchParams(value) ||
    value instanceof ArrayBuffer ||
    ArrayBuffer.isView(value)
  );
}

function serializeRequestBody(
  body: unknown,
  headers: Headers,
): BodyInit | undefined {
  if (
    body === undefined ||
    body === null
  ) {
    return undefined;
  }

  if (isRequestBody(body)) {
    return body;
  }

  if (!headers.has("Content-Type")) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  return JSON.stringify(body);
}

function normalizeTimeoutMs(
  timeoutMs: number | null,
): number | null {
  if (timeoutMs === null) {
    return null;
  }

  if (
    !Number.isFinite(timeoutMs) ||
    timeoutMs <= 0
  ) {
    return null;
  }

  return Math.floor(timeoutMs);
}

function createCombinedAbortSignal(params: {
  externalSignal?: AbortSignal;
  timeoutMs: number | null;
}): {
  signal: AbortSignal;
  cleanup: () => void;
} {
  const controller =
    new AbortController();

  let timeoutId:
    | ReturnType<typeof setTimeout>
    | undefined;

  const abortFromExternalSignal =
    (): void => {
      controller.abort(
        params.externalSignal?.reason,
      );
    };

  if (params.externalSignal) {
    if (
      params.externalSignal.aborted
    ) {
      abortFromExternalSignal();
    } else {
      params.externalSignal.addEventListener(
        "abort",
        abortFromExternalSignal,
        {
          once: true,
        },
      );
    }
  }

  const normalizedTimeoutMs =
    normalizeTimeoutMs(
      params.timeoutMs,
    );

  if (
    normalizedTimeoutMs !== null
  ) {
    timeoutId = setTimeout(() => {
      controller.abort(
        new DOMException(
          `API-Anfrage nach ${normalizedTimeoutMs} ms abgebrochen.`,
          "TimeoutError",
        ),
      );
    }, normalizedTimeoutMs);
  }

  return {
    signal: controller.signal,

    cleanup: () => {
      if (
        timeoutId !== undefined
      ) {
        clearTimeout(timeoutId);
      }

      params.externalSignal?.removeEventListener(
        "abort",
        abortFromExternalSignal,
      );
    },
  };
}

async function parseErrorResponse(
  response: Response,
): Promise<ApiErrorResponse> {
  const contentType =
    response.headers.get(
      "content-type",
    );

  if (
    isJsonContentType(contentType)
  ) {
    try {
      const payload =
        (await response.json()) as unknown;

      if (isRecord(payload)) {
        return {
          code:
            typeof payload.code ===
            "string"
              ? payload.code
              : undefined,

          message:
            typeof payload.message ===
            "string"
              ? payload.message
              : undefined,

          details:
            payload.details,

          request_id:
            typeof payload.request_id ===
            "string"
              ? payload.request_id
              : undefined,
        };
      }
    } catch {
      // Bei ungültigem JSON wird weiter unten eine generische
      // Fehlerantwort erzeugt.
    }
  }

  try {
    const text =
      await response.text();

    if (text.trim()) {
      return {
        message: text.trim(),
      };
    }
  } catch {
    // Die generische Fehlermeldung bleibt als Fallback erhalten.
  }

  return {};
}

async function parseSuccessResponse<T>(
  response: Response,
  responseType:
    ApiRequestOptions["responseType"],
): Promise<T> {
  if (
    responseType === "void" ||
    response.status === 204 ||
    response.status === 205
  ) {
    return undefined as T;
  }

  if (responseType === "blob") {
    return (
      await response.blob()
    ) as T;
  }

  if (responseType === "text") {
    return (
      await response.text()
    ) as T;
  }

  if (responseType === "json") {
    return (
      await response.json()
    ) as T;
  }

  const contentType =
    response.headers.get(
      "content-type",
    );

  if (
    isJsonContentType(contentType)
  ) {
    return (
      await response.json()
    ) as T;
  }

  return (
    await response.text()
  ) as T;
}

function getAbortErrorDetails(
  signal: AbortSignal,
): {
  code: string;
  message: string;
  statusText: string;
} {
  const reason = signal.reason;

  if (
    reason instanceof DOMException &&
    reason.name === "TimeoutError"
  ) {
    return {
      code: "request_timeout",
      message:
        reason.message ||
        "Die API-Anfrage hat das Zeitlimit überschritten.",
      statusText: "Request timeout",
    };
  }

  return {
    code: "request_aborted",
    message:
      "Die API-Anfrage wurde abgebrochen.",
    statusText: "Request aborted",
  };
}

export async function apiRequest<
  TResponse,
  TBody = unknown,
>(
  method: string,
  path: string,
  options: ApiRequestWithBodyOptions<TBody> = {},
): Promise<TResponse> {
  const normalizedMethod =
    method.trim().toUpperCase();

  if (!normalizedMethod) {
    throw new ApiError({
      message:
        "Die HTTP-Methode darf nicht leer sein.",
      status: 0,
      statusText:
        "Invalid request",
      code:
        "invalid_http_method",
      details: null,
      url: path,
    });
  }

  let url: string;

  try {
    url = buildApiUrl(
      path,
      options.query,
    );
  } catch (error) {
    throw new ApiError({
      message:
        error instanceof Error
          ? error.message
          : "Der API-Pfad ist ungültig.",
      status: 0,
      statusText:
        "Invalid API URL",
      code:
        "invalid_api_url",
      details: {
        path,
      },
      url: path,
      cause: error,
    });
  }

  const headers =
    new Headers(options.headers);

  if (!headers.has("Accept")) {
    headers.set(
      "Accept",
      "application/json",
    );
  }

  const timeoutMs =
    options.timeoutMs === undefined
      ? DEFAULT_REQUEST_TIMEOUT_MS
      : options.timeoutMs;

  const {
    signal,
    cleanup,
  } = createCombinedAbortSignal({
    externalSignal:
      options.signal,
    timeoutMs,
  });

  try {
    const response =
      await fetch(url, {
        method:
          normalizedMethod,

        headers,

        signal,

        credentials:
          options.credentials ??
          "same-origin",

        body:
          isBodyAllowed(
            normalizedMethod,
          )
            ? serializeRequestBody(
                options.body,
                headers,
              )
            : undefined,
      });

    if (!response.ok) {
      const errorPayload =
        await parseErrorResponse(
          response,
        );

      const requestId =
        errorPayload.request_id ??
        response.headers.get(
          "x-request-id",
        ) ??
        undefined;

      throw new ApiError({
        message:
          errorPayload.message ??
          `API-Anfrage fehlgeschlagen: ${response.status} ${response.statusText}`,

        status:
          response.status,

        statusText:
          response.statusText,

        code:
          errorPayload.code,

        details:
          errorPayload.details,

        requestId,

        url,
      });
    }

    return await parseSuccessResponse<TResponse>(
      response,
      options.responseType ??
        "auto",
    );
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    if (
      signal.aborted ||
      (
        error instanceof DOMException &&
        error.name === "AbortError"
      )
    ) {
      const abortError =
        getAbortErrorDetails(
          signal,
        );

      throw new ApiError({
        message:
          abortError.message,

        status: 0,

        statusText:
          abortError.statusText,

        code:
          abortError.code,

        details: {
          reason:
            signal.reason,
        },

        url,

        cause: error,
      });
    }

    throw new ApiError({
      message:
        error instanceof Error
          ? error.message
          : "Die API ist nicht erreichbar.",

      status: 0,

      statusText:
        "Network error",

      code:
        "network_error",

      details: null,

      url,

      cause: error,
    });
  } finally {
    cleanup();
  }
}

export function apiGet<TResponse>(
  path: string,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>(
    "GET",
    path,
    options,
  );
}

export function apiPost<
  TResponse,
  TBody = unknown,
>(
  path: string,
  body?: TBody,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<
    TResponse,
    TBody
  >(
    "POST",
    path,
    {
      ...options,
      body,
    },
  );
}

export function apiPut<
  TResponse,
  TBody = unknown,
>(
  path: string,
  body?: TBody,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<
    TResponse,
    TBody
  >(
    "PUT",
    path,
    {
      ...options,
      body,
    },
  );
}

export function apiPatch<
  TResponse,
  TBody = unknown,
>(
  path: string,
  body?: TBody,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<
    TResponse,
    TBody
  >(
    "PATCH",
    path,
    {
      ...options,
      body,
    },
  );
}

export function apiDelete<
  TResponse = void,
>(
  path: string,
  options?: ApiRequestOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>(
    "DELETE",
    path,
    options,
  );
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}
