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
