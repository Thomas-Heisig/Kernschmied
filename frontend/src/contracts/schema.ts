// F:\Kernschmied\frontend\src\contracts\schema.ts

export const UI_API_SCHEMA_VERSION = "1.0" as const;
export const UI_SCHEMA_VERSION = "1.0" as const;


/**
 * Bekannte Aktionstypen, die das Frontend sicher ausführen darf.
 *
 * Unbekannte Aktionen werden ignoriert und nicht als Button dargestellt.
 */
export const KNOWN_ACTION_KINDS = [
  "create_child",
  "rename",
  "delete",
  "move",
  "open_form",
  "navigate",
  "download",
  "export",
  "edit_prompt",
  "toggle_tools",
  "invoke_operation",
] as const;

export type KnownActionKind = typeof KNOWN_ACTION_KINDS[number];
export type JsonScalar =
  | string
  | number
  | boolean
  | null;

/**
 * Rekursive Typdefinition für JSON-Werte.
 *
 * Die Rekursion erfolgt direkt über das Objektliteral und das Array,
 * ohne einen separaten `JsonObject`-Alias, der auf `JsonValue` verweist.
 * Dadurch wird die zirkuläre Referenz vermieden.
 */
export type JsonValue =
  | JsonScalar
  | { [key: string]: JsonValue }
  | JsonValue[];

/**
 * Alias für ein JSON-Objekt, das ausschließlich `JsonValue`-Werte enthält.
 * Dies ist nicht rekursiv, da es nicht in `JsonValue` verwendet wird.
 */
export type JsonObject = Record<string, JsonValue>;

export interface UIComponentDefinition {
  id: string;
  type: string;

  title?: string | null;
  description?: string | null;

  props?: JsonObject;
  children?: UIComponentDefinition[];

  visible?: boolean;
  enabled?: boolean;
}

export type UIActionMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE";

export interface UIActionDefinition {
  id: string;
  type: string;

  label?: string | null;
  icon?: string | null;

  endpoint?: string | null;
  method?: UIActionMethod | null;

  required_permissions?: string[];
  confirmation_required?: boolean;
  enabled?: boolean;

  payload_schema?: JsonObject | null;
}

export interface UIFormDefinition {
  id: string;

  title?: string | null;
  description?: string | null;

  schema: JsonObject;
  submit_action_id?: string | null;
}

/**
 * Registry-Einträge bleiben bewusst generische JSON-Objekte.
 *
 * Das Backend erlaubt zusätzliche Felder. Das Frontend darf diese
 * transportieren und anzeigen, aber unbekannte Komponenten und
 * Aktionen niemals automatisch ausführen.
 */
export type UISchemaRegistry =
  Record<string, JsonObject>;

export interface UISchemaDocument {
  schema_name: string;
  schema_version: string;

  node_types: JsonObject;
  forms: UISchemaRegistry;
  components: UISchemaRegistry;
  actions: UISchemaRegistry;
  metadata: JsonObject;

  minimum_client_version?: string;
  revision?: number;
  feature_flags?: Record<string, boolean>;
}

/**
 * Kompatibilitätsname für bestehende Frontend-Komponenten.
 *
 * GenericTree und useAppSchema können weiterhin `UISchema`
 * importieren. Der präzisere Vertragsname ist `UISchemaDocument`.
 */
export type UISchema = UISchemaDocument;

export interface UISchemaResponse {
  api_schema_version: string;
  ui_schema_version: string;
  config_revision: number;

  schema: UISchemaDocument;

  request_id?: string | null;
}

export interface SchemaValidationIssue {
  path: string;
  code: string;
  message: string;
  received?: unknown;
}

export interface UISchemaParseSuccess {
  valid: true;
  schema: UISchemaDocument;
  issues: [];
}

export interface UISchemaParseFailure {
  valid: false;
  schema: null;
  issues: SchemaValidationIssue[];
}

export type UISchemaParseResult =
  | UISchemaParseSuccess
  | UISchemaParseFailure;

export interface UISchemaResponseParseSuccess {
  valid: true;
  response: UISchemaResponse;
  schema: UISchemaDocument;
  issues: [];
}

export interface UISchemaResponseParseFailure {
  valid: false;
  response: null;
  schema: null;
  issues: SchemaValidationIssue[];
}

export type UISchemaResponseParseResult =
  | UISchemaResponseParseSuccess
  | UISchemaResponseParseFailure;

export function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}

export function isJsonValue(
  value: unknown,
  seen: WeakSet<object> = new WeakSet(),
): value is JsonValue {
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

  if (typeof value !== "object") {
    return false;
  }

  if (seen.has(value)) {
    return false;
  }

  seen.add(value);

  if (Array.isArray(value)) {
    return value.every((entry) =>
      isJsonValue(entry, seen),
    );
  }

  return Object.values(value).every((entry) =>
    isJsonValue(entry, seen),
  );
}

function isNonEmptyString(
  value: unknown,
): value is string {
  return (
    typeof value === "string" &&
    value.trim().length > 0
  );
}

function isNonNegativeInteger(
  value: unknown,
): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 0
  );
}

function addIssue(
  issues: SchemaValidationIssue[],
  issue: SchemaValidationIssue,
): void {
  issues.push(issue);
}

function validateJsonObject(
  value: unknown,
  path: string,
  issues: SchemaValidationIssue[],
): value is JsonObject {
  if (!isRecord(value)) {
    addIssue(issues, {
      path,
      code: "expected_object",
      message: `${path} muss ein Objekt sein.`,
      received: value,
    });

    return false;
  }

  if (!isJsonValue(value)) {
    addIssue(issues, {
      path,
      code: "invalid_json_value",
      message:
        `${path} enthält einen nicht unterstützten JSON-Wert.`,
      received: value,
    });

    return false;
  }

  return true;
}

function validateRegistry(
  value: unknown,
  path: string,
  issues: SchemaValidationIssue[],
): value is UISchemaRegistry {
  if (!isRecord(value)) {
    addIssue(issues, {
      path,
      code: "expected_registry",
      message:
        `${path} muss ein Registry-Objekt sein.`,
      received: value,
    });

    return false;
  }

  let valid = true;

  for (
    const [registryKey, registryValue]
    of Object.entries(value)
  ) {
    if (!registryKey.trim()) {
      valid = false;

      addIssue(issues, {
        path,
        code: "empty_registry_key",
        message:
          `${path} enthält einen leeren Registry-Schlüssel.`,
      });

      continue;
    }

    if (!isRecord(registryValue)) {
      valid = false;

      addIssue(issues, {
        path: `${path}.${registryKey}`,
        code: "expected_registry_entry",
        message:
          `${path}.${registryKey} muss ein Objekt sein.`,
        received: registryValue,
      });

      continue;
    }

    if (!isJsonValue(registryValue)) {
      valid = false;

      addIssue(issues, {
        path: `${path}.${registryKey}`,
        code: "invalid_json_value",
        message:
          `${path}.${registryKey} enthält ungültige JSON-Werte.`,
        received: registryValue,
      });
    }
  }

  return valid;
}

function validateOptionalBooleanRecord(
  value: unknown,
  path: string,
  issues: SchemaValidationIssue[],
): value is Record<string, boolean> | undefined {
  if (value === undefined) {
    return true;
  }

  if (!isRecord(value)) {
    addIssue(issues, {
      path,
      code: "expected_object",
      message: `${path} muss ein Objekt sein.`,
      received: value,
    });

    return false;
  }

  let valid = true;

  for (const [key, entry] of Object.entries(value)) {
    if (typeof entry !== "boolean") {
      valid = false;

      addIssue(issues, {
        path: `${path}.${key}`,
        code: "expected_boolean",
        message:
          `${path}.${key} muss ein boolescher Wert sein.`,
        received: entry,
      });
    }
  }

  return valid;
}

export function validateUISchema(
  value: unknown,
): SchemaValidationIssue[] {
  const issues: SchemaValidationIssue[] = [];

  if (!isRecord(value)) {
    addIssue(issues, {
      path: "$",
      code: "expected_object",
      message:
        "Das UI-Schema muss ein Objekt sein.",
      received: value,
    });

    return issues;
  }

  if (!isNonEmptyString(value.schema_name)) {
    addIssue(issues, {
      path: "$.schema_name",
      code: "invalid_schema_name",
      message:
        "schema_name muss eine nicht leere Zeichenfolge sein.",
      received: value.schema_name,
    });
  }

  if (!isNonEmptyString(value.schema_version)) {
    addIssue(issues, {
      path: "$.schema_version",
      code: "invalid_schema_version",
      message:
        "schema_version muss eine nicht leere Zeichenfolge sein.",
      received: value.schema_version,
    });
  }

  validateJsonObject(
    value.node_types,
    "$.node_types",
    issues,
  );

  validateRegistry(
    value.forms,
    "$.forms",
    issues,
  );

  validateRegistry(
    value.components,
    "$.components",
    issues,
  );

  validateRegistry(
    value.actions,
    "$.actions",
    issues,
  );

  validateJsonObject(
    value.metadata,
    "$.metadata",
    issues,
  );

  if (
    value.minimum_client_version !== undefined &&
    !isNonEmptyString(value.minimum_client_version)
  ) {
    addIssue(issues, {
      path: "$.minimum_client_version",
      code: "invalid_minimum_client_version",
      message:
        "minimum_client_version muss eine nicht leere Zeichenfolge sein.",
      received: value.minimum_client_version,
    });
  }

  if (
    value.revision !== undefined &&
    !isNonNegativeInteger(value.revision)
  ) {
    addIssue(issues, {
      path: "$.revision",
      code: "invalid_revision",
      message:
        "revision muss eine nicht negative Ganzzahl sein.",
      received: value.revision,
    });
  }

  validateOptionalBooleanRecord(
    value.feature_flags,
    "$.feature_flags",
    issues,
  );

  return issues;
}

export function isUISchema(
  value: unknown,
): value is UISchema {
  return validateUISchema(value).length === 0;
}

export function parseUISchema(
  value: unknown,
): UISchemaParseResult {
  const issues = validateUISchema(value);

  if (issues.length > 0) {
    return {
      valid: false,
      schema: null,
      issues,
    };
  }

  return {
    valid: true,
    schema: value as UISchemaDocument,
    issues: [],
  };
}

export function validateUISchemaResponse(
  value: unknown,
): SchemaValidationIssue[] {
  const issues: SchemaValidationIssue[] = [];

  if (!isRecord(value)) {
    addIssue(issues, {
      path: "$",
      code: "expected_response_object",
      message:
        "Die UI-Schema-Antwort muss ein Objekt sein.",
      received: value,
    });

    return issues;
  }

  if (!isNonEmptyString(value.api_schema_version)) {
    addIssue(issues, {
      path: "$.api_schema_version",
      code: "invalid_api_schema_version",
      message:
        "api_schema_version muss eine nicht leere Zeichenfolge sein.",
      received: value.api_schema_version,
    });
  }

  if (!isNonEmptyString(value.ui_schema_version)) {
    addIssue(issues, {
      path: "$.ui_schema_version",
      code: "invalid_ui_schema_version",
      message:
        "ui_schema_version muss eine nicht leere Zeichenfolge sein.",
      received: value.ui_schema_version,
    });
  }

  if (!isNonNegativeInteger(value.config_revision)) {
    addIssue(issues, {
      path: "$.config_revision",
      code: "invalid_config_revision",
      message:
        "config_revision muss eine nicht negative Ganzzahl sein.",
      received: value.config_revision,
    });
  }

  if (
    value.request_id !== undefined &&
    value.request_id !== null &&
    !isNonEmptyString(value.request_id)
  ) {
    addIssue(issues, {
      path: "$.request_id",
      code: "invalid_request_id",
      message:
        "request_id muss null oder eine nicht leere Zeichenfolge sein.",
      received: value.request_id,
    });
  }

  const schemaIssues =
    validateUISchema(value.schema);

  for (const issue of schemaIssues) {
    addIssue(issues, {
      ...issue,
      path:
        issue.path === "$"
          ? "$.schema"
          : `$.schema${issue.path.slice(1)}`,
    });
  }

  if (
    isNonEmptyString(value.ui_schema_version) &&
    isRecord(value.schema) &&
    isNonEmptyString(value.schema.schema_version) &&
    value.ui_schema_version !==
      value.schema.schema_version
  ) {
    addIssue(issues, {
      path: "$.ui_schema_version",
      code: "schema_version_mismatch",
      message:
        "ui_schema_version stimmt nicht mit schema.schema_version überein.",
      received: {
        ui_schema_version:
          value.ui_schema_version,
        schema_version:
          value.schema.schema_version,
      },
    });
  }

  return issues;
}

export function isUISchemaResponse(
  value: unknown,
): value is UISchemaResponse {
  return (
    validateUISchemaResponse(value).length === 0
  );
}

export function parseUISchemaResponse(
  value: unknown,
): UISchemaResponseParseResult {
  const issues =
    validateUISchemaResponse(value);

  if (issues.length > 0) {
    return {
      valid: false,
      response: null,
      schema: null,
      issues,
    };
  }

  const response =
    value as UISchemaResponse;

  return {
    valid: true,
    response,
    schema: response.schema,
    issues: [],
  };
}