export interface BootstrapApplication {
  name: string;
  version: string;
  environment?: string;
  api_prefix?: string;
}

export interface BootstrapVersions {
  bootstrap_schema?: string;
  ui_schema?: string;
  api?: string;
}

export interface BootstrapRevisions {
  configuration?: number;
  model_registry?: number;
  tool_registry?: number;
}

export interface BootstrapEndpoints {
  bootstrap?: string;
  ui_schema?: string;
  models?: string;
  tools?: string;
  health_live?: string;
  health_ready?: string;
}

export interface BootstrapResponse {
  schema_version: string;
  api_version: string;
  application: BootstrapApplication;
  environment: string;
  versions: BootstrapVersions;
  endpoints?: BootstrapEndpoints;
  revisions?: BootstrapRevisions;
  config_revision?: number;
}
