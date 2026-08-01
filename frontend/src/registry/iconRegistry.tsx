// F:\Kernschmied\frontend\src\registry\iconRegistry.tsx

import type { CSSProperties, ComponentType } from 'react';
import {
  Building2,
  Circle,
  Download,
  FileOutput,
  FilePenLine,
  FolderKanban,
  MessageSquare,
  Move,
  PanelTopOpen,
  Pencil,
  Play,
  Plus,
  Trash2,
  UserCircle,
  Wrench,
  ArrowRight,
} from 'lucide-react';

export const DEFAULT_ICON_NAME = 'Circle';

export const ICON_REGISTRY = {
  ArrowRight,
  Building2,
  Circle,
  Download,
  FileOutput,
  FilePenLine,
  FolderKanban,
  MessageSquare,
  Move,
  PanelTopOpen,
  Pencil,
  Play,
  Plus,
  Trash2,
  UserCircle,
  Wrench,
} as const;

export type KnownIconName = keyof typeof ICON_REGISTRY;

export interface DynamicIconProps {
  /**
   * Iconname aus der festen Registry.
   */
  name?: string | null;

  /**
   * Optionale Farbe.
   */
  color?: string;

  /**
   * Standardgröße 18 Pixel.
   */
  size?: number;

  /**
   * Zusätzliche CSS-Klasse.
   */
  className?: string;

  /**
   * Optionaler Titel.
   */
  title?: string;
}

function isSafeColor(value: string | undefined): boolean {
  if (!value) {
    return false;
  }

  // Hex
  if (/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(value)) {
    return true;
  }

  // rgb(...)
  if (/^rgb(a?)\(/i.test(value)) {
    return true;
  }

  // CSS-Variable
  if (/^var\(--/.test(value)) {
    return true;
  }

  // Tailwind-/Designfarben wie slate, blue usw.
  if (/^[a-z][a-z0-9-]*$/i.test(value)) {
    return true;
  }

  return false;
}

export function isKnownIconName(value: unknown): value is KnownIconName {
  return typeof value === 'string' && value in ICON_REGISTRY;
}

export function getIconComponent(name: string | null | undefined): ComponentType<{
  size?: number;
  className?: string;
  style?: CSSProperties;
  title?: string;
}> {
  if (name && isKnownIconName(name)) {
    return ICON_REGISTRY[name];
  }

  return ICON_REGISTRY[DEFAULT_ICON_NAME];
}

export function listKnownIcons(): readonly KnownIconName[] {
  return Object.keys(ICON_REGISTRY) as KnownIconName[];
}

export function DynamicIcon({ name, color, size = 18, className, title }: DynamicIconProps) {
  const Icon = getIconComponent(name);

  return (
    <Icon
      size={size}
      className={className}
      title={title}
      aria-hidden={title ? undefined : true}
      style={isSafeColor(color) ? { color } : undefined}
    />
  );
}
