import type { ReactNode } from 'react';

interface NodeWorkspaceMetric {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
}

interface NodeWorkspaceOverviewProps {
  eyebrow: string;
  title: string;
  description: string;
  icon: ReactNode;
  actions?: ReactNode;
  details?: ReactNode;
  metrics?: NodeWorkspaceMetric[];
  compact?: boolean;
}

export default function NodeWorkspaceOverview({
  eyebrow,
  title,
  description,
  icon,
  actions,
  details,
  metrics = [],
  compact = false,
}: NodeWorkspaceOverviewProps) {
  return (
    <section
      className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50/90 shadow-sm dark:border-white/10 dark:bg-slate-900/55"
      aria-label={`${eyebrow}: ${title}`}
    >
      <div className={compact ? 'p-4' : 'p-5 sm:p-6'}>
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
          <div className="flex min-w-0 items-start gap-3.5">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/70 dark:bg-emerald-950/40 dark:text-emerald-200 [&>svg]:h-5 [&>svg]:w-5">
              {icon}
            </span>
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-800 dark:text-emerald-300">
                {eyebrow}
              </p>
              <h2 className={`${compact ? 'mt-1 text-lg' : 'mt-1.5 text-xl'} font-semibold tracking-tight text-slate-950 dark:text-white`}>
                {title}
              </h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                {description}
              </p>
            </div>
          </div>
          {actions ? <div className="flex shrink-0 flex-wrap gap-2">{actions}</div> : null}
        </div>
        {details ? <div className="mt-5">{details}</div> : null}
      </div>

      {metrics.length > 0 ? (
        <dl className={`grid border-t border-slate-200 bg-white/55 dark:border-white/10 dark:bg-black/10 ${metrics.length >= 4 ? 'grid-cols-2 sm:grid-cols-4' : 'grid-cols-1 sm:grid-cols-3'}`}>
          {metrics.map((metric) => (
            <div key={metric.label} className="flex items-center gap-3 border-r border-slate-200 px-4 py-3 last:border-r-0 dark:border-white/10 sm:px-5">
              {metric.icon ? <span className="shrink-0 text-emerald-700 dark:text-emerald-300">{metric.icon}</span> : null}
              <div className="min-w-0">
                <dt className="text-xs text-slate-500 dark:text-slate-400">{metric.label}</dt>
                <dd className="mt-0.5 truncate text-sm font-semibold text-slate-950 dark:text-white">{metric.value}</dd>
              </div>
            </div>
          ))}
        </dl>
      ) : null}
    </section>
  );
}

export function NodeWorkspaceAction({
  icon,
  children,
  onClick,
  danger = false,
}: {
  icon?: ReactNode;
  children: ReactNode;
  onClick?: () => void;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={danger
        ? 'inline-flex items-center gap-2 rounded-lg border border-red-200 bg-white px-3 py-2 text-sm font-medium text-red-700 transition hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 dark:border-red-900/60 dark:bg-slate-900 dark:text-red-300 dark:hover:bg-red-950/30'
        : 'inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 dark:border-white/15 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-emerald-800 dark:hover:bg-emerald-950/30'}
    >
      {icon}
      {children}
    </button>
  );
}
