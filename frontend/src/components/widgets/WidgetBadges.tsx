import { useEffect, useState } from 'react';
import { DynamicIcon } from '../../registry/iconRegistry';
import fetchWidgetsClient from '../../api/fetchWidgetsClient';
import type { EffectiveWidget } from '../../contracts/widgets';

export default function WidgetBadges({ nodeId }: { nodeId: string }) {
  const [widgets, setWidgets] = useState<EffectiveWidget[]>([]);

  useEffect(() => {
    let mounted = true;
    if (!nodeId) return;

    (async () => {
      try {
        const res = await fetchWidgetsClient.getEffectiveWidgets(nodeId);
        if (mounted) setWidgets((res.items ?? []) as unknown as EffectiveWidget[]);
      } catch (err) {
        // ignore silently — badges are non-critical
      }
    })();

    return () => {
      mounted = false;
    };
  }, [nodeId]);

  if (!widgets || widgets.length === 0) return null;

  return (
    <div className="flex gap-2 items-center" aria-hidden={true}>
      {widgets.map((w, idx) => {
        const name = typeof w?.name === 'string' ? w.name : `widget-${idx}`;
        const icon = typeof w?.icon === 'string' ? w.icon : undefined;
        const title = typeof w?.label === 'string' ? w.label : name;

        return (
          <div
            key={String(w.id ?? idx)}
            title={title}
            className="h-7 w-7 shrink-0 rounded-md border border-border-soft bg-surface-muted flex items-center justify-center text-xs text-text-muted"
          >
            {icon ? <DynamicIcon name={icon} size={14} /> : <span className="text-[10px]">{String(name).slice(0, 2)}</span>}
          </div>
        );
      })}
    </div>
  );
}
