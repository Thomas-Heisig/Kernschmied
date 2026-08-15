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
  const raw = String(type).trim().toLowerCase();

  // Generate candidate keys by normalizing common variants and dup suffixes
  const candidates: string[] = [];

  const pushUnique = (s?: string) => {
    if (!s) return;
    const v = String(s).trim().toLowerCase();
    if (!v) return;
    if (!candidates.includes(v)) candidates.push(v);
  };

  pushUnique(raw);
  pushUnique(raw.replace(/-/g, '_'));

  // Remove duplication markers like '__dup__...'
  const withoutDup = raw.replace(/__dup__.*$/i, '').replace(/[-\s]+/g, '_');
  pushUnique(withoutDup);

  // If there's an alphanumeric prefix before non-word chars, try that
  const prefix = raw.split(/[^a-z0-9_]+/i)[0];
  pushUnique(prefix);

  // Try with and without the common '_widget' suffix
  const tryVariants = [...candidates];
  tryVariants.forEach((c) => {
    if (c.endsWith('_widget')) {
      pushUnique(c.replace(/_widget$/i, ''));
    } else {
      pushUnique(`${c}_widget`);
    }
  });

  // Finally try simple replacement of trailing hyphen groups (e.g. 'w-system')
  candidates.forEach((c) => {
    pushUnique(c.replace(/__?w[_-].*$/i, ''));
    pushUnique(c.replace(/__?w.*$/i, ''));
  });

  for (const k of candidates) {
    if (registry[k]) return registry[k];
  }

  return null;
}

export function listWidgetRendererTypes(): string[] {
  return Object.keys(registry).sort();
}

export default { registerWidgetRenderer, getWidgetRenderer, listWidgetRendererTypes };
