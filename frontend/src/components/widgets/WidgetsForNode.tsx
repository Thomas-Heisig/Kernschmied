import React, { useEffect } from 'react';
import { DynamicIcon } from '../../registry/iconRegistry';
import WidgetBadges from './WidgetBadges';
import IconBadge from '../common/IconBadge';
import useEffectiveWidgets from '../../hooks/useEffectiveWidgets';
import { getWidgetRenderer } from '../../registry/widgetRegistry';
import UnsupportedSchemaComponent from '../schema/UnsupportedSchemaComponent';

type Variant = 'sidebar' | 'workspace';

export default function WidgetsForNode({ nodeId, variant = 'workspace', showEmptyState = true, allowedComponentTypePrefixes }: { nodeId: string; variant?: Variant; showEmptyState?: boolean; allowedComponentTypePrefixes?: string[] }) {
  const { widgets, isLoading, error, reload } = useEffectiveWidgets(nodeId);

  // Use Vite env helpers instead of `process` for runtime/dev detection
  const isDev = (import.meta as any)?.env?.MODE === 'development' || Boolean((import.meta as any)?.env?.DEV);

  useEffect(() => {
    if (isDev && variant === 'workspace') {
      try {
        const componentTypes = (widgets || []).map((w) => (w.componentType ?? (w.metadata && (w.metadata.component_type as string | undefined))));
        console.debug('[Kernschmied][CentralWidgets]', { nodeId, widgetCount: (widgets || []).length, componentTypes });
      } catch {}
    }
  }, [nodeId, widgets, variant, isDev]);

  if (!nodeId) return <div className="text-xs text-text-muted">Kein Knoten ausgewählt.</div>;

  if (isLoading) {
    if (variant === 'workspace') {
      return (
        <div className="space-y-3">
          <div className="rounded border border-border-soft px-3 py-6 bg-white/60 dark:bg-slate-900/40">Lade Widgets…</div>
        </div>
      );
    }

    return <div className="text-xs text-text-muted">Lade Widgets…</div>;
  }

  if (error) return (
    <div className="text-xs text-red-500">Fehler beim Laden der Widgets: {String(error.message)} <button onClick={() => void reload()} className="ml-2 underline">Erneut</button></div>
  );

  const filtered = (widgets || []).filter((w) => {
    if (!allowedComponentTypePrefixes || allowedComponentTypePrefixes.length === 0) return true;
    const declared = (w.componentType ?? (w.metadata && (w.metadata.component_type as string | undefined))) as string | undefined;
    if (!declared) return false;
    return allowedComponentTypePrefixes.some((p) => declared.startsWith(p));
  });

  if (!filtered || filtered.length === 0) {
    if (!showEmptyState) return null;
    return <div className="text-xs text-text-muted">Keine Widgets für diesen Knoten.</div>;
  }

  // workspace variant: render large stacked widgets
  if (variant === 'workspace') {
    return (
      <div className="space-y-4">
        <div>
          <WidgetBadges nodeId={nodeId} allowedComponentTypePrefixes={allowedComponentTypePrefixes} />
        </div>

        <div className="flex flex-col gap-4">
          {filtered.map((w) => {
            const declared = (w.componentType ?? (w.metadata && (w.metadata.component_type as string | undefined))) as string | undefined;
            const renderer = getWidgetRenderer(declared);
            if (renderer) {
              return <div key={w.id}>{renderer(w, { nodeId })}</div>;
            }
            if (declared) {
              return (
                <div key={w.id} className="rounded border border-border-soft px-3 py-2 bg-white/60 dark:bg-slate-900/40">
                  <UnsupportedSchemaComponent type={declared} definition={w} />
                </div>
              );
            }

            return (
              <div key={w.id} className="rounded border border-border-soft px-3 py-2 bg-white/60 dark:bg-slate-900/40">
                <div className="flex items-start gap-3">
                  <div>
                    <IconBadge icon={w.icon ? <DynamicIcon name={String(w.icon)} /> : <div className="text-sm font-medium">{String((w.name ?? w.id).slice(0,2)).toUpperCase()}</div>} size="lg" variant="default" />
                  </div>

                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-text">{w.label ?? w.name ?? w.id}</div>
                    {w.description ? <div className="text-xs text-text-muted mt-1">{String(w.description)}</div> : null}

                    <div className="mt-2 flex items-center gap-2">
                      {w.interactionMode ? (
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] bg-gray-100 text-gray-800">{String(w.interactionMode)}</span>
                      ) : null}

                      {w.status ? (
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] bg-gray-100 text-gray-800">{String(w.status)}</span>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // sidebar / compact variant
  return (
    <div className="space-y-3">
      <div>
        <WidgetBadges nodeId={nodeId} allowedComponentTypePrefixes={allowedComponentTypePrefixes} />
      </div>

      <div className="flex flex-col gap-2">
          {filtered.map((w) => {
            const declared = (w.componentType ?? (w.metadata && (w.metadata.component_type as string | undefined))) as string | undefined;
            const renderer = getWidgetRenderer(declared);
            if (renderer) {
              return <div key={w.id}>{renderer(w, { nodeId })}</div>;
            }
          if (declared) {
            return (
              <div key={w.id} className="rounded border border-border-soft px-3 py-2 bg-white/60 dark:bg-slate-900/40">
                <UnsupportedSchemaComponent type={declared} definition={w} />
              </div>
            );
          }

          return (
            <div key={w.id} className="rounded border border-border-soft px-3 py-2 bg-white/60 dark:bg-slate-900/40">
              <div className="flex items-start gap-3">
                <div>
                  <IconBadge icon={w.icon ? <DynamicIcon name={String(w.icon)} /> : <div className="text-sm font-medium">{String((w.name ?? w.id).slice(0,2)).toUpperCase()}</div>} size="lg" variant="default" />
                </div>

                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-text">{w.label ?? w.name ?? w.id}</div>
                  {w.description ? <div className="text-xs text-text-muted mt-1">{String(w.description)}</div> : null}

                  <div className="mt-2 flex items-center gap-2">
                    {w.interactionMode ? (
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] bg-gray-100 text-gray-800">{String(w.interactionMode)}</span>
                    ) : null}

                    {w.status ? (
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[11px] bg-gray-100 text-gray-800">{String(w.status)}</span>
                    ) : null}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
