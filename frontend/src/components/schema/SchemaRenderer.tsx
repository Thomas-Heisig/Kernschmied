import React, { useCallback, useMemo } from "react";
import type {
  UIComponentDefinition,
  UIActionDefinition,
} from "../../contracts/schema";
import UnsupportedSchemaComponent from "./UnsupportedSchemaComponent";
import { getComponentRenderer } from "../../registry/componentRegistry";
import {
  getActionDefinition,
  executeRegisteredAction,
} from "../../registry/actionRegistry";

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
  onAction?: (
    action: UIActionDefinition,
    context: SchemaRenderContext,
  ) => void | Promise<unknown>;
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
}: SchemaRendererProps) {
  const ctx: SchemaRenderContext = useMemo(
    () => ({ ...(context ?? {}), nodeId: context?.nodeId ?? undefined }),
    [context],
  );

  const handleAction = useCallback(
    async (actionRef: string | UIActionDefinition) => {
      let actionDef: UIActionDefinition | undefined;

      if (typeof actionRef === "string") {
        // try to resolve via registry name
        actionDef = (schema as any)?.schema?.actions?.[actionRef] as
          UIActionDefinition | undefined;
      } else {
        actionDef = actionRef;
      }

      if (!actionDef) {
        const known = getActionDefinition(
          typeof actionRef === "string" ? actionRef : actionRef.type,
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
        // eslint-disable-next-line no-console
        console.warn("Action execution failed", e);
      }
    },
    [onAction, ctx, schema],
  );

  function renderNode(
    nodeDef?: UIComponentDefinition,
    idx = 0,
  ): React.ReactNode {
    if (!nodeDef || typeof nodeDef.type !== "string") {
      return (
        <UnsupportedSchemaComponent
          type={String(nodeDef?.type)}
          definition={nodeDef}
        />
      );
    }

    const renderer = getComponentRenderer(nodeDef.type);
    const children = (nodeDef.children ?? []).map((c, i) =>
      renderNode(c as UIComponentDefinition, i),
    );

    // Inputs and controls must be controlled using onChange
    const primitiveOnChange = (v: unknown) => onChange?.(v);

    if (!renderer) {
      return (
        <UnsupportedSchemaComponent type={nodeDef.type} definition={nodeDef} />
      );
    }

    // Special: button triggers action
    if (nodeDef.type === "button") {
      const actionRef = nodeDef.props?.action as string | undefined;

      return renderer(nodeDef, children, {
        onClick: (e: React.MouseEvent) => {
          e.preventDefault();
          if (actionRef) void handleAction(actionRef);
        },
      });
    }

    // Controlled inputs
    if (nodeDef.type === "text_input") {
      const current =
        typeof value === "string"
          ? value
          : ((nodeDef.props?.value as string | undefined) ?? "");

      return (
        <input
          className="w-full rounded border px-2 py-1"
          value={String(current)}
          placeholder={String(nodeDef.props?.placeholder ?? "")}
          disabled={Boolean(disabled) || Boolean(nodeDef.props?.disabled)}
          readOnly={Boolean(readonly) || Boolean(nodeDef.props?.readonly)}
          onChange={(e) => primitiveOnChange(e.target.value)}
        />
      );
    }

    if (nodeDef.type === "textarea") {
      const current =
        typeof value === "string"
          ? value
          : ((nodeDef.props?.value as string | undefined) ?? "");

      return (
        <textarea
          className="w-full rounded border px-2 py-1"
          value={String(current)}
          placeholder={String(nodeDef.props?.placeholder ?? "")}
          disabled={Boolean(disabled) || Boolean(nodeDef.props?.disabled)}
          readOnly={Boolean(readonly) || Boolean(nodeDef.props?.readonly)}
          onChange={(e) => primitiveOnChange(e.target.value)}
        />
      );
    }

    if (nodeDef.type === "number_input") {
      const current =
        typeof value === "number" ? value : Number(nodeDef.props?.value ?? 0);

      return (
        <input
          type="number"
          className="w-full rounded border px-2 py-1"
          value={String(current)}
          disabled={Boolean(disabled) || Boolean(nodeDef.props?.disabled)}
          readOnly={Boolean(readonly) || Boolean(nodeDef.props?.readonly)}
          onChange={(e) => primitiveOnChange(Number(e.target.value))}
        />
      );
    }

    if (nodeDef.type === "checkbox") {
      const checked = Boolean(value ?? nodeDef.props?.checked);

      return (
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={checked}
            disabled={Boolean(disabled) || Boolean(nodeDef.props?.disabled)}
            onChange={(e) => primitiveOnChange(e.target.checked)}
          />
          <span>{nodeDef.title}</span>
        </label>
      );
    }

    if (nodeDef.type === "select") {
      const options = Array.isArray(nodeDef.props?.options)
        ? nodeDef.props?.options
        : [];
      const current = value ?? nodeDef.props?.value;

      return (
        <select
          className="w-full rounded border px-2 py-1"
          value={String(current ?? "")}
          disabled={Boolean(disabled) || Boolean(nodeDef.props?.disabled)}
          onChange={(e) => primitiveOnChange(e.target.value)}
        >
          {options.map((opt: any, i: number) => (
            <option key={i} value={opt.value ?? opt}>
              {opt.label ?? String(opt)}
            </option>
          ))}
        </select>
      );
    }

    // Default: use registry renderer for cards, stacks, headings etc.
    return renderer(nodeDef, children, { onChange: primitiveOnChange });
  }

  return <div className="space-y-3">{renderNode(schema)}</div>;
}
