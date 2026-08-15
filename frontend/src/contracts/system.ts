export type SystemServiceState = 'up' | 'down' | 'unknown';

export interface SystemOverviewResponse {
  schema_version: '1.0';
  api_version: 'v1';
  status: 'ok';
  environment: string;
  config_revision: number;
  security_profile: Record<string, unknown>;
  services: Record<string, { status: SystemServiceState }>;
  registries: {
    models: number;
    tools: number;
  };
  request_id?: string;
}