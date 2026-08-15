// F:\Kernschmied\frontend\src\components\widgets\WidgetBadges.tsx

import { useEffect, useState } from 'react';
import IconBadge from '../common/IconBadge';
import { DynamicIcon } from '../../registry/iconRegistry';
import fetchWidgetsClient from '../../api/fetchWidgetsClient';
import type { EffectiveWidget } from '../../contracts/widgets';

export interface WidgetBadgesProps {
  nodeId: string;
  /** Optional: Nur Widgets anzeigen, deren componentType mit einem dieser Prefixe beginnt */
  allowedComponentTypePrefixes?: string[];
  /** Größen‑Variant: 'sm' (24x24) oder 'md' (32x32) – Standard: 'md' */
  size?: 'sm' | 'md';
  /** Ob die Badges als Buttons gerendert werden sollen (klickbar) */
  interactive?: boolean;
  /** Callback beim Klick auf ein Badge */
  onWidgetClick?: (widget: EffectiveWidget) => void;
}

export default function WidgetBadges({
  nodeId,
  allowedComponentTypePrefixes,
  size = 'md',
  interactive = true,
  onWidgetClick,
}: WidgetBadgesProps) {
  const [widgets, setWidgets] = useState<EffectiveWidget[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    if (!nodeId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    (async () => {
      try {
        const res = await fetchWidgetsClient.getEffectiveWidgets(nodeId);
        if (mounted) {
          setWidgets((res.items ?? []) as unknown as EffectiveWidget[]);
        }
      } catch (err) {
        // Badges sind nicht kritisch – stille Fehlerbehandlung
        if (mounted) setWidgets([]);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [nodeId]);

  // Filterung nach componentType‑Prefix
  const filtered = (widgets || []).filter((w) => {
    if (!allowedComponentTypePrefixes || allowedComponentTypePrefixes.length === 0) return true;
    const declared = (w.componentType ?? (w.metadata && (w.metadata.component_type as string | undefined))) as string | undefined;
    if (!declared) return false;
    return allowedComponentTypePrefixes.some((p) => declared.startsWith(p));
  });

  // Leer‑ oder Lade‑Zustand
  if (loading) return null;
  if (!filtered || filtered.length === 0) return null;

  const badgeSize = size === 'sm' ? 'sm' : 'md';

  return (
    <div className="flex items-center gap-1.5" aria-label="Widgets" role="group">
      {filtered.map((widget, idx) => {
        const name = typeof widget?.name === 'string' ? widget.name : `widget-${idx}`;
        const icon = typeof widget?.icon === 'string' ? widget.icon : undefined;
        const label = typeof widget?.label === 'string' ? widget.label : name;
        const widgetId = String(widget.id ?? idx);

        const badgeContent = icon ? (
          <DynamicIcon name={icon} />
        ) : (
          <span className="text-[10px] font-medium uppercase">{String(name).slice(0, 2)}</span>
        );

        const className = [
          'flex shrink-0 items-center justify-center rounded-lg border border-border-soft bg-white/70 transition-colors',
          'hover:bg-surface-hover hover:text-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          interactive ? 'cursor-pointer' : 'cursor-default',
          'dark:border-white/10 dark:bg-slate-800/70 dark:hover:bg-slate-700 dark:hover:text-white',
          size === 'sm' ? 'h-7 w-7' : 'h-9 w-9',
        ].filter(Boolean).join(' ');

        const commonProps = {
          title: label,
          'aria-label': label,
          className,
        };

        if (interactive) {
          return (
            <button
              key={widgetId}
              type="button"
              {...commonProps}
              onClick={() => onWidgetClick?.(widget)}
            >
              <IconBadge icon={badgeContent} size={badgeSize} variant="default" />
            </button>
          );
        }

        return (
          <div key={widgetId} {...commonProps}>
            <IconBadge icon={badgeContent} size={badgeSize} variant="default" />
          </div>
        );
      })}
    </div>
  );
}