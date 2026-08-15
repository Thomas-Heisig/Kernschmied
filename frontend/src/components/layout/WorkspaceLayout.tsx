// F:\Kernschmied\frontend\src\components\layout\WorkspaceLayout.tsx

import React, { ReactNode } from 'react';
import clsx from 'clsx';

interface WorkspaceLayoutProps {
  /** Icon (z. B. IconBadge mit DynamicIcon) */
  icon: ReactNode;
  /** Titel des Arbeitsbereichs */
  title: string;
  /** Optionale Aktionen (z. B. Buttons) */
  actions?: ReactNode;
  /** Widget‑Badges (werden absolut in der oberen rechten Ecke positioniert) */
  widgetBadges?: ReactNode;
  children: ReactNode;
  className?: string;
  /** Hintergrundfarbe */
  background?: 'white' | 'slate' | 'transparent';
  /** Padding für den Container (Standard: p-6 sm:p-8) */
  padding?: string;
}

/**
 * Einheitliches Layout für alle Workspace‑Ansichten (Chat, Bereich, Projekt, Einstellungen, etc.)
 *
 * - Kopfzeile mit Icon und Titel
 - Optionale Widget‑Badges (absolut positioniert)
 - Scrollbarer Inhaltsbereich
 */
export function WorkspaceLayout({
  icon,
  title,
  actions,
  widgetBadges,
  children,
  className,
  background = 'white',
  padding = 'p-6 sm:p-8',
}: WorkspaceLayoutProps) {
  const titleId = React.useId(); // oder eine feste ID, aber useId ist eindeutig

  const bgClass =
    background === 'white'
      ? 'bg-white dark:bg-slate-950'
      : background === 'slate'
        ? 'bg-slate-50 dark:bg-slate-950/30'
        : 'bg-transparent';

  return (
    <section
      className={clsx(
        'relative flex h-full min-h-0 w-full flex-col overflow-hidden',
        bgClass,
        padding,
        className,
      )}
      aria-labelledby={titleId}
    >
      {/* Widget-Badges (z. B. für System/Widgets) */}
      {widgetBadges ? <div className="absolute right-4 top-4 z-20">{widgetBadges}</div> : null}

      {/* Kopfzeile mit Icon, Titel und Aktionen */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <div aria-hidden="true">{icon}</div>
          <h1 id={titleId} className="truncate text-xl font-semibold text-text dark:text-white">
            {title}
          </h1>
        </div>

        {actions ? <div className="shrink-0">{actions}</div> : null}
      </div>

      {/* Inhaltsbereich */}
      <div className="mt-4 min-h-0 flex-1 overflow-y-auto">{children}</div>
    </section>
  );
}

export default WorkspaceLayout;