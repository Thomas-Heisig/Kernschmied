import React from 'react';
import type { UIComponentDefinition } from '../contracts/schema';
import { DynamicIcon } from './iconRegistry';
import IconBadge from '../components/common/IconBadge';
import UnsupportedSchemaComponent from '../components/schema/UnsupportedSchemaComponent';
import WidgetsForNode from '../components/widgets/WidgetsForNode';

/**
 * Map of known schema component types to renderer functions.
 * Each renderer returns a React node for a given component definition.
 */
export type ComponentRenderer = (
  def: UIComponentDefinition,
  children: React.ReactNode,
  props?: { [key: string]: unknown },
) => React.ReactNode;

const registry: Record<string, ComponentRenderer> = {
  heading: (def, children) => <h2 className="text-lg font-semibold">{def.title ?? children}</h2>,

  paragraph: (def, children) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    return (
      <p className="text-sm text-slate-700 dark:text-slate-300">{String(props.text ?? children)}</p>
    );
  },

  text: (def, children) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    return <span>{props.text !== undefined ? String(props.text) : children}</span>;
  },

  alert: (def, children) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    return (
      <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm">
        {props.text !== undefined ? String(props.text) : children}
      </div>
    );
  },

  badge: (def) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    return (
      <span className="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-xs font-medium">
        {String(props.text ?? def.title)}
      </span>
    );
  },

  button: (def, children, props = {}) => {
    const p = props as { onClick?: React.MouseEventHandler<HTMLButtonElement> };
    const componentProps = (def.props ?? {}) as Record<string, unknown>;
    return (
      <button
        type="button"
        onClick={p.onClick}
        className="inline-flex items-center gap-2 rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700"
      >
        {componentProps.icon ? (
          <IconBadge icon={<DynamicIcon name={String(componentProps.icon)} />} size="sm" variant="default" />
        ) : null}
        {def.title ?? children}
      </button>
    );
  },

  stack: (def, children) => <div className="flex flex-col gap-2">{children}</div>,

  grid: (def, children) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const cols = props.columns as string | number | undefined;
    const gridTemplateColumns = typeof cols === 'string' || typeof cols === 'number' ? cols : undefined;
    return (
      <div className="grid gap-3" style={{ gridTemplateColumns }}>
        {children}
      </div>
    );
  },

  section: (def, children) => (
    <section className="rounded-md border border-slate-200 p-4">{children}</section>
  ),

  card: (def, children) => (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">{children}</div>
  ),

  divider: () => <hr className="my-2 border-slate-200" />,

  text_input: (def, children) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const val = props.value;
    return (
      <input
        className="w-full rounded border px-2 py-1"
        placeholder={String(props.placeholder ?? '')}
        defaultValue={typeof val === 'string' || typeof val === 'number' ? (val as string | number) : String(val ?? '')}
        readOnly={Boolean(props.readonly)}
      />
    );
  },

  textarea: (def) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const val = props.value;
    return (
      <textarea
        className="w-full rounded border px-2 py-1"
        placeholder={String(props.placeholder ?? '')}
        defaultValue={typeof val === 'string' ? (val as string) : String(val ?? '')}
        readOnly={Boolean(props.readonly)}
      />
    );
  },

  number_input: (def) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const val = props.value;
    return (
      <input
        type="number"
        className="w-full rounded border px-2 py-1"
        defaultValue={typeof val === 'number' ? val : Number(val ?? 0)}
        readOnly={Boolean(props.readonly)}
      />
    );
  },

  checkbox: (def) => (
    <label className="inline-flex items-center gap-2">
      <input type="checkbox" defaultChecked={Boolean(def.props?.checked)} />
      <span>{def.title}</span>
    </label>
  ),

  select: (def, children) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const value = props.value as unknown;
    const options = Array.isArray(props.options) ? (props.options as unknown[]) : [];
    return (
      <select className="w-full rounded border px-2 py-1" defaultValue={String(value ?? '')}>
        {options.map((opt: unknown, i: number) => {
          if (opt && typeof opt === 'object' && !Array.isArray(opt)) {
            const o = opt as Record<string, unknown>;
            return (
              <option key={i} value={String(o.value ?? '')}>
                {String(o.label ?? String(o.value ?? ''))}
              </option>
            );
          }
          return (
            <option key={i} value={String(opt ?? '')}>
              {String(opt ?? '')}
            </option>
          );
        })}
      </select>
    );
  },

  multi_select: (def) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const options = Array.isArray(props.options) ? (props.options as unknown[]) : [];
    return (
      <select multiple className="w-full rounded border px-2 py-1">
        {options.map((opt: unknown, i: number) => {
          if (opt && typeof opt === 'object' && !Array.isArray(opt)) {
            const o = opt as Record<string, unknown>;
            return (
              <option key={i} value={String(o.value ?? '')}>
                {String(o.label ?? String(o.value ?? ''))}
              </option>
            );
          }
          return (
            <option key={i} value={String(opt ?? '')}>
              {String(opt ?? '')}
            </option>
          );
        })}
      </select>
    );
  },

  tags: (def) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    const items = Array.isArray(props.items) ? (props.items as unknown[]) : [];
    return (
      <div className="flex flex-wrap gap-1">
        {items.map((t: unknown, i: number) => (
          <span key={i} className="rounded bg-slate-100 px-2 py-0.5 text-xs">
            {String(t ?? '')}
          </span>
        ))}
      </div>
    );
  },

  json: (def) => {
    const props = (def.props ?? {}) as Record<string, unknown>;
    return <pre className="rounded bg-slate-50 p-2 text-xs">{JSON.stringify(props.value ?? {}, null, 2)}</pre>;
  },

  // Renders effective widgets for a node using the shared WidgetsForNode component.
  // Expects the SchemaRenderer to pass `context.nodeId` in props.
  effective_widgets: (def, children, props = {}) => {
    const p = props as { context?: Record<string, unknown> };
    const nodeId = p.context && typeof p.context.nodeId === 'string' ? (p.context.nodeId as string) : undefined;
    if (!nodeId) {
      return <UnsupportedSchemaComponent type="effective_widgets" definition={def} />;
    }
    return <WidgetsForNode nodeId={nodeId} />;
  },
};

export function getComponentRenderer(type: string): ComponentRenderer | null {
  if (type in registry) return registry[type];
  return null;
}

export default registry;
