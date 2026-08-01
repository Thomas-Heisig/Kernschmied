export type SettingsAvailability = "available" | "prepared" | "planned";
export type SettingsSource =
  "config" | "resource" | "runtime" | "local_preference";
export type SettingsControl =
  | "text"
  | "textarea"
  | "number"
  | "boolean"
  | "select"
  | "multiselect"
  | "readonly"
  | "link";

export interface SettingsOption {
  value: string;
  label: string;
}

export interface SettingsFieldDescriptor {
  id: string;
  title: string;
  description?: string | null;
  source: SettingsSource;
  availability: SettingsAvailability;
  control: SettingsControl;
  config_group?: string | null;
  config_key?: string | null;
  endpoint?: string | null;
  editable: boolean;
  sensitive: boolean;
  requires_confirmation: boolean;
  restart_required: boolean;
  options: SettingsOption[];
  minimum?: number | null;
  maximum?: number | null;
  order: number;
  tags: string[];
}

export interface SettingsSectionDescriptor {
  id: string;
  title: string;
  description?: string | null;
  order: number;
  availability: SettingsAvailability;
  fields: SettingsFieldDescriptor[];
}

export interface SettingsGroupDescriptor {
  id: string;
  title: string;
  description: string;
  icon: string;
  order: number;
  availability: SettingsAvailability;
  sections: SettingsSectionDescriptor[];
}

export interface SettingsCatalogResponse {
  schema_version: "1.0";
  groups: SettingsGroupDescriptor[];
  request_id?: string | null;
}
