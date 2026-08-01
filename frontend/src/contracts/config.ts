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

export interface ConfigDynamicOptions {
  source: ConfigValueSource;

  endpoint: string | null;

  value_field: string;
  label_field: string;
  description_field: string | null;

  filters: Record<string, ConfigValue>;

  depends_on: string | null;
  dependency_parameter: string | null;
}
