import React, { forwardRef, HTMLAttributes } from 'react';

export type IconBadgeSize = 'sm' | 'md' | 'lg';
export type IconBadgeVariant = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger';

export interface IconBadgeProps extends HTMLAttributes<HTMLDivElement> {
  /** Icon as a React node (SVG, image, component) */
  icon: React.ReactNode;
  /** Optional label displayed to the right of the icon */
  label?: string;
  /** Size variant: controls icon pixel size and container */
  size?: IconBadgeSize;
  /** Visual variant for color theming */
  variant?: IconBadgeVariant;
  /** Optional explicit background color (overrides variant) */
  color?: string;
  /** Additional classes for the root container */
  className?: string;
}

/** Map size to container dimensions and icon pixel size */
const SIZE_MAP: Record<IconBadgeSize, { container: string; iconPx: number }> = {
  sm: { container: 'h-6 w-6', iconPx: 16 }, // 24px container
  md: { container: 'h-8 w-8', iconPx: 20 }, // 32px container
  lg: { container: 'h-10 w-10', iconPx: 24 }, // 40px container
};

/** Variant → Tailwind classes for the icon container */
const VARIANT_MAP: Record<IconBadgeVariant, string> = {
  default: 'bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-300',
  primary: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  secondary: 'bg-slate-200 text-slate-700 dark:bg-slate-700/60 dark:text-slate-300',
  success: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  warning: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  danger: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
};

/**
 * IconBadge – einheitliches Icon+Label‑Element für die gesamte App.
 *
 * Verwendet in Sidebars, Tree, Workspace‑Headern, Widgets und Modals, um
 * Konsistenz für System, Bereich, Projekt, Benutzer etc. zu gewährleisten.
 */
const IconBadge = forwardRef<HTMLDivElement, IconBadgeProps>(
  (
    {
      icon,
      label,
      size = 'md',
      variant = 'default',
      color,
      className,
      ...rest
    },
    ref,
  ) => {
    const info = SIZE_MAP[size] ?? SIZE_MAP.md;
    const variantCls = VARIANT_MAP[variant] ?? VARIANT_MAP.default;

    const containerStyle = color ? { backgroundColor: color } : undefined;

    return (
      <div
        ref={ref}
        className={['inline-flex items-center gap-2 select-none', className].filter(Boolean).join(' ')}
        {...rest}
      >
        <div
          className={[
            'flex shrink-0 items-center justify-center rounded-lg',
            info.container,
            variantCls,
          ]
            .filter(Boolean)
            .join(' ')}
          style={containerStyle}
          aria-hidden={!label}
        >
          <span
            style={{
              width: info.iconPx,
              height: info.iconPx,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </span>
        </div>

        {label && <span className="truncate text-sm text-text-soft dark:text-gray-300">{label}</span>}
      </div>
    );
  },
);

IconBadge.displayName = 'IconBadge';

export default IconBadge;