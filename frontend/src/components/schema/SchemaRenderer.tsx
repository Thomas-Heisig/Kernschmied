import React, { useCallback, useMemo } from 'react';
import type { UIComponentDefinition, UIActionDefinition } from '../../contracts/schema';
import UnsupportedSchemaComponent from './UnsupportedSchemaComponent';
import { getComponentRenderer } from '../../registry/componentRegistry';
import { SettingsField } from '../settings/SettingsField';
import type { ConfigEntryResponse, ConfigValue } from '../../contracts/config';
import { getActionDefinition, executeRegisteredAction } from '../../registry/actionRegistry';

export interface SchemaRenderContext {
  path?: string[];
  nodeId?: string;
  [key: string]: unknown;
}

export interface SchemaRendererProps {
  schema: UIComponentDefinition;
  value?: unknown;
  disabled?: boolean;
  readonly?: boolean;
  context?: SchemaRenderContext;
  onChange?: (value: unknown) => void;
  onAction?: (action: UIActionDefinition, context: SchemaRenderContext) => void | Promise<unknown>;
  // Optional explicit action definitions supplied by the caller or context.
  actionDefinitions?: Readonly<Record<string, UIActionDefinition>>;
}

/**
 * Controlled, safe SchemaRenderer implementation.
 * - Uses a fixed component registry
 * - Unknown components rendered via UnsupportedSchemaComponent
 * - Actions executed via actionRegistry or forwarded to onAction
 */
export default function SchemaRenderer({
  schema,
  value,
  disabled,
  readonly,
  context,
  onChange,
  onAction,
  actionDefinitions,
}: SchemaRendererProps) {
  const ctx: SchemaRenderContext = useMemo(
    () => ({ ...(context ?? {}), nodeId: context?.nodeId ?? undefined }),
    [context],
  );

  const handleAction = useCallback(
    async (actionRef: string | UIActionDefinition) => {
      let actionDef: UIActionDefinition | undefined;
      if (typeof actionRef === 'string') {
        // Prefer explicit actionDefinitions passed via props
        actionDef = actionDefinitions?.[actionRef];
      } else {
        actionDef = actionRef;
      }

      if (!actionDef) {
        const known = getActionDefinition(
          typeof actionRef === 'string' ? actionRef : actionRef.type,
        );
        if (known) {
          actionDef = {
            id: known.kind,
            type: known.kind,
            label: known.label,
          } as UIActionDefinition;
        }
      }

      if (!actionDef) return;

      if (onAction) {
        await onAction(actionDef, ctx);
        return;
      }

      try {
        await executeRegisteredAction(actionDef.type, {
          target: ctx,
          payload: undefined,
        });
      } catch (e) {
        // do not crash renderer

        console.warn('Action execution failed', e);
      }
    },
    [onAction, ctx, schema],
  );

  function renderNode(nodeDef?: UIComponentDefinition, idx = 0): React.ReactNode {
    if (!nodeDef || typeof nodeDef.type !== 'string') {
      return <UnsupportedSchemaComponent type={String(nodeDef?.type)} definition={nodeDef} />;
    }

    // Respect explicit visibility flag on node definitions
    if (nodeDef.visible === false) return null;

    const renderer = getComponentRenderer(nodeDef.type);
    const children = (nodeDef.children ?? []).map((c, i) =>
      renderNode(c as UIComponentDefinition, i),
    );

    // Inputs and controls must be controlled using onChange.
    // Support per-field binding via `props.path` (dot-separated or array).
    const getValueFromPath = (root: unknown, path?: string | string[]) => {
      if (!path) return root;
      const parts = typeof path === 'string' ? path.split('.') : path;
      let cur: unknown = root;
      for (const p of parts) {
        if (!cur || typeof cur !== 'object' || Array.isArray(cur)) return undefined;
        cur = (cur as Record<string, unknown>)[p];
      }
      return cur;
    };

    const setValueAtPath = (root: unknown, path?: string | string[], newValue?: unknown) => {
      if (!path) return newValue;
      const parts = typeof path === 'string' ? path.split('.') : path;
      const base: Record<string, unknown> =
        typeof root === 'object' && root !== null && !Array.isArray(root)
          ? { ...(root as Record<string, unknown>) }
          : {};

      let cur = base;
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i];
        if (i === parts.length - 1) {
          cur[p] = newValue;
        } else {
          const next = cur[p];
          if (!next || typeof next !== 'object' || Array.isArray(next)) {
            cur[p] = {};
          } else {
            cur[p] = { ...(next as Record<string, unknown>) };
          }
          cur = cur[p] as Record<string, unknown>;
        }
      }

      return base;
    };

    const primitiveOnChange = (v: unknown, path?: string | string[]) => {
      if (!onChange) return;
      if (path) {
        const next = setValueAtPath(value, path, v);
        onChange(next);
        return;
      }
      onChange(v);
    };

    if (!renderer) {
      return <UnsupportedSchemaComponent type={nodeDef.type} definition={nodeDef} />;
    }

    // Special: button triggers action
    if (nodeDef.type === 'button') {
      const actionRef = nodeDef.props?.action as string | undefined;

      return renderer(nodeDef, children, {
        onClick: (e: React.MouseEvent) => {
          e.preventDefault();
          if (actionRef) void handleAction(actionRef);
        },
      });
    }

    // Controlled inputs
    if (nodeDef.type === 'text_input') {
      const pathProp = nodeDef.props?.path as string | string[] | undefined;
      const current =
        getValueFromPath(value, pathProp) ?? (nodeDef.props?.value as string | undefined) ?? '';

      const effectiveDisabled = Boolean(disabled) || Boolean(nodeDef.props?.disabled);
      const effectiveReadOnly = Boolean(readonly) || Boolean(nodeDef.props?.readonly);

      return (
        <input
          className="w-full rounded border px-2 py-1"
          value={String(current)}
          placeholder={String(nodeDef.props?.placeholder ?? '')}
          disabled={effectiveDisabled}
          readOnly={effectiveReadOnly}
          onChange={(e) => primitiveOnChange(e.target.value, pathProp)}
        />
      );
    }

    if (nodeDef.type === 'textarea') {
      const pathProp = nodeDef.props?.path as string | string[] | undefined;
      const current =
        getValueFromPath(value, pathProp) ?? (nodeDef.props?.value as string | undefined) ?? '';

      const effectiveDisabled = Boolean(disabled) || Boolean(nodeDef.props?.disabled);
      const effectiveReadOnly = Boolean(readonly) || Boolean(nodeDef.props?.readonly);

      return (
        <textarea
          className="w-full rounded border px-2 py-1"
          value={String(current)}
          placeholder={String(nodeDef.props?.placeholder ?? '')}
          disabled={effectiveDisabled}
          readOnly={effectiveReadOnly}
          onChange={(e) => primitiveOnChange(e.target.value, pathProp)}
        />
      );
    }

    if (nodeDef.type === 'number_input') {
      const pathProp = nodeDef.props?.path as string | string[] | undefined;
      const current = getValueFromPath(value, pathProp) ?? Number(nodeDef.props?.value ?? 0);

      const effectiveDisabled = Boolean(disabled) || Boolean(nodeDef.props?.disabled);
      const effectiveReadOnly = Boolean(readonly) || Boolean(nodeDef.props?.readonly);

      return (
        <input
          type="number"
          className="w-full rounded border px-2 py-1"
          value={String(current)}
          disabled={effectiveDisabled}
          readOnly={effectiveReadOnly}
          onChange={(e) => primitiveOnChange(Number(e.target.value), pathProp)}
        />
      );
    }

    if (nodeDef.type === 'checkbox') {
      const pathProp = nodeDef.props?.path as string | string[] | undefined;
      const checked = Boolean(getValueFromPath(value, pathProp) ?? nodeDef.props?.checked);

      const effectiveDisabled = Boolean(disabled) || Boolean(nodeDef.props?.disabled);

      return (
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={checked}
            disabled={effectiveDisabled}
            onChange={(e) => primitiveOnChange(e.target.checked, pathProp)}
          />
          <span>{nodeDef.title}</span>
        </label>
      );
    }

    if (nodeDef.type === 'select') {
      const options = Array.isArray(nodeDef.props?.options)
        ? (nodeDef.props?.options as unknown[])
        : [];
      const pathProp = nodeDef.props?.path as string | string[] | undefined;
      const current = getValueFromPath(value, pathProp) ?? nodeDef.props?.value;

      const effectiveDisabled = Boolean(disabled) || Boolean(nodeDef.props?.disabled);

      return (
        <select
          className="w-full rounded border px-2 py-1"
          value={String(current ?? '')}
          disabled={effectiveDisabled}
          onChange={(e) => primitiveOnChange(e.target.value, pathProp)}
        >
          {options.map((opt, i) => {
            let val: unknown = opt;
            let label: string = String(opt);

            if (opt && typeof opt === 'object' && !Array.isArray(opt)) {
              const asObj = opt as Record<string, unknown>;
              if ('value' in asObj) val = asObj.value;
              if ('label' in asObj && typeof asObj.label === 'string')
                label = asObj.label as string;
            }

            return (
              <option key={i} value={String(val ?? '')}>
                {label}
              </option>
            );
          })}
        </select>
      );
    }

    // Support rendering a config entry using the SettingsField dispatcher.
    // The schema node can either provide a full `entry` object in props or
    // a minimal set of props (group,key,value,ui) from which we construct
    // a compatible `ConfigEntryResponse`.
    if (nodeDef.type === 'config_entry' || nodeDef.type === 'setting_field') {
      const entryProp = nodeDef.props?.entry as ConfigEntryResponse | undefined;

      const makeEntry = (): ConfigEntryResponse => {
        if (entryProp) return entryProp;

        const group = String(nodeDef.props?.group ?? '');
        const key = String(
          nodeDef.props?.key ??
            (nodeDef.props?.path ? String(nodeDef.props.path).replace(/\./g, '_') : ''),
        );
        const full_key = nodeDef.props?.full_key ?? `${group}.${key}`;
        const display_name = nodeDef.title ?? String(nodeDef.props?.title ?? key);
        const description = String(nodeDef.props?.description ?? '');
        const val = (nodeDef.props?.value ?? nodeDef.props?.default ?? undefined) as ConfigValue;

        const ui = {
          component: (nodeDef.props?.component as any) ?? undefined,
          category: nodeDef.props?.category ?? undefined,
          section: nodeDef.props?.section ?? undefined,
          order: nodeDef.props?.order ?? undefined,
          placeholder: nodeDef.props?.placeholder ?? null,
          help_text: nodeDef.props?.help_text ?? null,
          unit: nodeDef.props?.unit ?? null,
          advanced: Boolean(nodeDef.props?.advanced ?? false),
          hidden: Boolean(nodeDef.props?.hidden ?? false),
          readonly: Boolean(nodeDef.props?.readonly ?? false),
          options: Array.isArray(nodeDef.props?.options)
            ? nodeDef.props.options.map((o: any) => ({
                value: o.value ?? o,
                label: o.label ?? String(o),
              }))
            : [],
          dynamic_options: nodeDef.props?.dynamic_options ?? null,
        };

        return {
          group,
          key,
          full_key,
          display_name,
          description,
          value: val as any,
          default_value: nodeDef.props?.default ?? null,
          schema_version: '2.0',
          value_type: undefined,
          value_schema: undefined,
          editable: !(ui.readonly ?? false),
          sensitive: Boolean(nodeDef.props?.sensitive ?? false),
          secret_configured: false,
          requires_restart: false,
          runtime_editable: !(ui.readonly ?? false),
          nullable: true,
          visibility: '',
          allowed_scopes: [],
          current_scope: 'application',
          permissions: { read: 'config:read', write: 'config:write', reveal_secret: null },
          ui,
          deprecated: false,
        } as ConfigEntryResponse;
      };

      const entry = makeEntry();

      return (
        <div>
          <SettingsField
            entry={entry}
            path={
              Array.isArray(nodeDef.props?.path)
                ? (nodeDef.props.path as string[])
                : typeof nodeDef.props?.path === 'string'
                  ? (nodeDef.props.path as string).split('.')
                  : []
            }
            disabled={Boolean(disabled) || Boolean(nodeDef.props?.disabled)}
            onChange={(nextPath: string[], v: ConfigValue) => {
              // propagate change to parent using SchemaRenderer onChange
              if (!onChange) return;
              // reconstruct object with updated path
              const targetPath = nodeDef.props?.path ?? entry.full_key;
              // If the entry is bound via path, we let primitiveOnChange handle it
              primitiveOnChange(v, targetPath as any);
            }}
          />
        </div>
      );
    }

    // Default: use registry renderer for cards, stacks, headings etc.
    return renderer(nodeDef, children, { onChange: primitiveOnChange });
  }

  // Error boundary to ensure a broken renderer doesn't crash the entire UI
  class SchemaErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean }
  > {
    constructor(props: { children: React.ReactNode }) {
      super(props);
      this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
      return { hasError: true };
    }

    componentDidCatch(error: unknown) {
      console.error('SchemaRenderer error:', error);
    }

    render() {
      if (this.state.hasError) {
        return (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">
            Ein Fehler ist im SchemaRenderer aufgetreten.
          </div>
        );
      }

      return this.props.children as React.ReactNode;
    }
  }

  return (
    <SchemaErrorBoundary>
      <div className="space-y-3">{renderNode(schema)}</div>
    </SchemaErrorBoundary>
  );
}
