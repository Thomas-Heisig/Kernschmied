export interface EffectiveWidget {
  id: string;
  name: string;
  label?: string | null;
  description?: string | null;

  status?: string | null;
  version?: string | null;

  interactionMode?: string | null;
  icon?: string | null;
  componentType?: string | null;
  requiredPermissions: string[];

  configuration?: Record<string, unknown> | null;
  position?: number | null;

  metadata: Record<string, unknown>;
}

export interface EffectiveWidgetsResponse {
  schemaVersion: string;
  items: EffectiveWidget[];
  requestId?: string | null;
}
