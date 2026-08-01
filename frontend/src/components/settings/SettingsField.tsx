// New, slim SettingsField dispatcher that supports the new `entry`-based API
// but remains backward-compatible with the legacy prop-based usage.
import React from "react";
import type { ConfigEntryResponse, ConfigValue } from "../../contracts/config";

import BooleanSetting from "./fields/BooleanSetting";
import NumberSetting from "./fields/NumberSetting";
import TextSetting from "./fields/TextSetting";
import SelectSetting from "./fields/SelectSetting";
import JsonSetting from "./fields/JsonSetting";
import TagsSetting from "./fields/TagsSetting";
import UnsupportedSetting from "./UnsupportedSetting";

type LegacyProps = {
  fieldKey?: string;
  label?: string;
  value?: ConfigValue;
  path?: string[];
  disabled?: boolean;
  description?: string;
  sensitive?: boolean;
  readOnly?: boolean;
  required?: boolean;
  placeholder?: string;
  minimum?: number;
  maximum?: number;
  step?: number;
  options?: { value: string | number | boolean; label: string }[];
  dynamicOptions?: unknown | null;
  valuesByFullKey?: Record<string, ConfigValue> | null;
  onChange?: (path: string[], value: ConfigValue) => void;
};

export function SettingsField(props: { entry?: ConfigEntryResponse } & Partial<LegacyProps>) {
  const { entry: maybeEntry, path = [], valuesByFullKey = null, disabled = false, onChange } = props as any;

  const entry: ConfigEntryResponse = maybeEntry
    ? maybeEntry
    : ({
        group: "",
        key: props.fieldKey ?? String(path.slice(-1)[0] ?? ""),
        full_key: (path ?? []).concat(props.fieldKey ?? []).join("."),
        display_name: props.label ?? String(props.fieldKey ?? ""),
        description: props.description ?? "",
        value: props.value as ConfigValue,
        default_value: props.value as ConfigValue,
        schema_version: "",
        editable: !props.readOnly,
        sensitive: Boolean(props.sensitive),
        requires_restart: false,
        runtime_editable: true,
        nullable: !Boolean(props.required),
        visibility: "",
        allowed_scopes: [],
        current_scope: "",
        ui: {
          component: undefined,
          placeholder: props.placeholder ?? null,
          help_text: null,
          options: props.options as any,
          dynamic_options: (props.dynamicOptions as any) ?? null,
        },
      } as ConfigEntryResponse);

  const readOnly = entry.ui.readonly ?? !entry.editable;
  const required = !entry.nullable;

  const component = entry.ui.component ?? inferComponentFromValue(entry.value);

  switch (component) {
    case "checkbox":
      return (
        <BooleanSetting entry={entry} path={path} value={entry.value} disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />
      );

    case "number":
      return (
        <NumberSetting entry={entry} path={path} value={entry.value} disabled={disabled} readOnly={readOnly} required={required} minimum={undefined} maximum={undefined} onChange={onChange} />
      );

    case "textarea":
      return <TextSetting entry={entry} path={path} value={entry.value} kind="multiline" disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />;

    case "password":
      return <TextSetting entry={entry} path={path} value={entry.value} kind="password" disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />;

    case "email":
      return <TextSetting entry={entry} path={path} value={entry.value} kind="email" disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />;

    case "url":
      return <TextSetting entry={entry} path={path} value={entry.value} kind="url" disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />;

    case "text":
      return <TextSetting entry={entry} path={path} value={entry.value} kind="text" disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />;

    case "select":
    case "provider_select":
    case "model_select":
    case "tool_select":
    case "node_select":
      return <SelectSetting entry={entry} path={path} value={entry.value} disabled={disabled} readOnly={readOnly} required={required} valuesByFullKey={valuesByFullKey} onChange={onChange} />;

    case "multi_select":
    case "tags":
      return <TagsSetting entry={entry} path={path} value={entry.value} disabled={disabled} readOnly={readOnly} required={required} onChange={onChange} />;

    case "json":
      return <JsonSetting entry={entry} path={path} value={entry.value} disabled={disabled} readOnly={readOnly} onChange={onChange} />;

    case "hidden":
      return null;

    default:
      return <UnsupportedSetting entry={entry} path={path} />;
  }
}

function inferComponentFromValue(value: ConfigValue): string {
  if (typeof value === "boolean") return "checkbox";
  if (typeof value === "number") return "number";
  if (typeof value === "object" && value !== null) return "json";
  return "text";
}

