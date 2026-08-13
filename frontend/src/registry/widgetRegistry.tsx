import React from 'react';
import type { EffectiveWidget } from '../contracts/widgets';

export type WidgetRenderer = (widget: EffectiveWidget, context?: { nodeId?: string }) => React.ReactNode;

const registry: Record<string, WidgetRenderer> = {};

export function registerWidgetRenderer(type: string, renderer: WidgetRenderer) {
  const key = String(type).trim().toLowerCase();
  if (!key) throw new Error('Widget type must be a non-empty string');
  if (registry[key]) throw new Error(`Widget renderer for '${key}' already registered`);
  registry[key] = renderer;
}

export function getWidgetRenderer(type: string | undefined | null): WidgetRenderer | null {
  if (!type) return null;
  const key = String(type).trim().toLowerCase();
  return registry[key] ?? null;
}

export function listWidgetRendererTypes(): string[] {
  return Object.keys(registry).sort();
}

export default { registerWidgetRenderer, getWidgetRenderer, listWidgetRendererTypes };
