import React from "react";
import type { UIComponentDefinition } from "../contracts/schema";
import { DynamicIcon } from "./iconRegistry";
import UnsupportedSchemaComponent from "../components/schema/UnsupportedSchemaComponent";

/**
 * Map of known schema component types to renderer functions.
 * Each renderer returns a React node for a given component definition.
 */
export type ComponentRenderer = (
  def: UIComponentDefinition,
  children: any,
  props?: { [key: string]: unknown },
) => React.ReactNode;

const registry: Record<string, ComponentRenderer> = {
  heading: (def, children) => (
    <h2 className="text-lg font-semibold">{def.title ?? children}</h2>
  ),

  paragraph: (def, children) => (
    <p className="text-sm text-slate-700 dark:text-slate-300">
      {String((def.props as any)?.text ?? children)}
    </p>
  ),

  text: (def, children) => <span>{def.props?.text ?? children}</span>,

  alert: (def, children) => (
    <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm">
      {def.props?.text ?? children}
    </div>
  ),

  badge: (def) => (
    <span className="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-xs font-medium">
      {String((def.props as any)?.text ?? def.title)}
    </span>
  ),

  button: (def, children, { onClick } = {}) => (
    <button
      type="button"
      onClick={onClick as any}
      className="inline-flex items-center gap-2 rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700"
    >
      {(def.props as any)?.icon ? (
        <DynamicIcon name={String((def.props as any).icon)} size={16} />
      ) : null}
      {def.title ?? children}
    </button>
  ),

  stack: (def, children) => (
    <div className="flex flex-col gap-2">{children}</div>
  ),

  grid: (def, children) => {
    const cols = (def.props as any)?.columns;
    const gridTemplateColumns =
      typeof cols === "string" || typeof cols === "number" ? cols : undefined;
    return (
      <div className="grid gap-3" style={{ gridTemplateColumns }}>
        {children}
      </div>
    );
  },

  section: (def, children) => (
    <section className="rounded-md border border-slate-200 p-4">
      {children}
    </section>
  ),

  card: (def, children) => (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      {children}
    </div>
  ),

  divider: () => <hr className="my-2 border-slate-200" />,

  text_input: (def, children) => (
    <input
      className="w-full rounded border px-2 py-1"
      placeholder={def.props?.placeholder as string}
      defaultValue={def.props?.value as any}
      readOnly={Boolean(def.props?.readonly)}
    />
  ),

  textarea: (def) => (
    <textarea
      className="w-full rounded border px-2 py-1"
      placeholder={def.props?.placeholder as string}
      defaultValue={def.props?.value as any}
      readOnly={Boolean(def.props?.readonly)}
    />
  ),

  number_input: (def) => (
    <input
      type="number"
      className="w-full rounded border px-2 py-1"
      defaultValue={def.props?.value as any}
      readOnly={Boolean(def.props?.readonly)}
    />
  ),

  checkbox: (def) => (
    <label className="inline-flex items-center gap-2">
      <input type="checkbox" defaultChecked={Boolean(def.props?.checked)} />
      <span>{def.title}</span>
    </label>
  ),

  select: (def, children) => {
    const value = (def.props as any)?.value as any;
    const options = Array.isArray((def.props as any)?.options)
      ? ((def.props as any).options as any[])
      : [];
    return (
      <select className="w-full rounded border px-2 py-1" defaultValue={value}>
        {options.map((opt: any, i: number) => (
          <option key={i} value={opt.value ?? opt}>
            {String(opt.label ?? opt)}
          </option>
        ))}
      </select>
    );
  },

  multi_select: (def) => {
    const options = Array.isArray((def.props as any)?.options)
      ? ((def.props as any).options as any[])
      : [];
    return (
      <select multiple className="w-full rounded border px-2 py-1">
        {options.map((opt: any, i: number) => (
          <option key={i} value={opt.value ?? opt}>
            {String(opt.label ?? opt)}
          </option>
        ))}
      </select>
    );
  },

  tags: (def) => {
    const items = Array.isArray((def.props as any)?.items)
      ? ((def.props as any).items as any[])
      : [];
    return (
      <div className="flex flex-wrap gap-1">
        {items.map((t: any, i: number) => (
          <span key={i} className="rounded bg-slate-100 px-2 py-0.5 text-xs">
            {String(t)}
          </span>
        ))}
      </div>
    );
  },

  json: (def) => (
    <pre className="rounded bg-slate-50 p-2 text-xs">
      {JSON.stringify((def.props as any)?.value ?? {}, null, 2)}
    </pre>
  ),
};

export function getComponentRenderer(type: string): ComponentRenderer | null {
  if (type in registry) return registry[type];
  return null;
}

export default registry;
