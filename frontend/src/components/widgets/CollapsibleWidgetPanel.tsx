import { useId, useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface CollapsibleWidgetPanelProps {
  title: string;
  icon: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  actions?: ReactNode;
}

export default function CollapsibleWidgetPanel({
  title,
  icon,
  children,
  defaultOpen = true,
  actions,
}: CollapsibleWidgetPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const contentId = useId();

  return (
    <section className="overflow-hidden rounded-lg border border-border-soft bg-white shadow-sm dark:border-white/10 dark:bg-slate-900/50">
      <header className="flex min-h-12 items-center gap-2 px-3 sm:px-4">
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-3 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-expanded={isOpen}
          aria-controls={contentId}
          onClick={() => setIsOpen((current) => !current)}
        >
          <span className="text-text-muted dark:text-slate-300" aria-hidden="true">{icon}</span>
          <span className="truncate text-sm font-semibold text-text dark:text-white">{title}</span>
          <span className="ml-auto text-text-muted dark:text-slate-400" aria-hidden="true">
            {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </span>
        </button>
        {actions ? <div className="shrink-0" onClick={(event) => event.stopPropagation()}>{actions}</div> : null}
      </header>
      {isOpen ? (
        <div id={contentId} className="border-t border-border-soft p-4 dark:border-white/10 sm:p-5">
          {children}
        </div>
      ) : null}
    </section>
  );
}