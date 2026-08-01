export type ConfigPrimitive = boolean | number | string | null;

export type ConfigValue = ConfigPrimitive | ConfigValue[] | ConfigObject;

export interface ConfigObject {
  [key: string]: ConfigValue;
}

export interface SystemConfigSnapshot {
  values: ConfigObject;
  revision: number | null;
}

export interface UpdateSystemConfigRequest {
  values: ConfigObject;
  expected_revision?: number | null;
}

export interface StructuredApiErrorDetails {
  [key: string]: unknown;
}

export interface StructuredApiError {
  code: string;
  message: string;
  details?: StructuredApiErrorDetails;
  request_id?: string;
}

export type ConfigUIComponent =
  | "text"
  | "textarea"
  | "password"
  | "number"
  | "checkbox"
  | "select"
  | "multi_select"
  | "tags"
  | "json"
  | "url"
  | "provider_select"
  | "model_select"
  | "tool_select"
  | "node_select"
  | "hidden";

export type ConfigValueSource =
  | "static"
  | "providers"
  | "models"
  | "tools"
  | "hierarchy_nodes"
  | "users"
  | "api";

export interface ConfigDynamicOptionsResponse {
  source: string;

  endpoint?: string | null;

  value_field: string;
  label_field: string;
  description_field?: string | null;

  filters?: Record<string, unknown>;

  depends_on?: string | null;
  dependency_parameter?: string | null;
}

export interface ConfigOptionResponse {
  value: string | number | boolean;
  label: string;
  description?: string | null;
  disabled?: boolean;
}

export interface ConfigUIResponse {
  component?: ConfigUIComponent | null;

  category?: string | null;
  section?: string | null;
  order?: number;

  placeholder?: string | null;
  help_text?: string | null;
  unit?: string | null;

  advanced?: boolean;
  hidden?: boolean;
  readonly?: boolean;

  options?: ConfigOptionResponse[];

  dynamic_options?: ConfigDynamicOptionsResponse | null;
}

export interface ConfigEntryResponse {
  group: string;
  key: string;
  full_key: string;

  display_name: string;
  description: string;

  value: ConfigValue;
  default_value: ConfigValue;

  schema_version: string;
  value_type?: string | null;

  value_schema?: Record<string, unknown>;

  editable: boolean;
  sensitive: boolean;
  secret_configured?: boolean;

  requires_restart: boolean;
  runtime_editable: boolean;
  nullable: boolean;

  visibility: string;

  allowed_scopes: string[];

  current_scope: string;

  permissions?: {
    read: string;
    write: string;
    reveal_secret?: string | null;
  } | null;

  ui: ConfigUIResponse;

  deprecated?: boolean;
  deprecation_message?: string | null;
  replaced_by?: string | null;
}

export interface ConfigGroupResponse {
  id: string;
  label: string;
  description?: string | null;
  order?: number;

  entries: ConfigEntryResponse[];
}

export interface ConfigListResponse {
  schema_version: "2.0";
  revision: number;

  groups: ConfigGroupResponse[];

  request_id?: string | null;
}
