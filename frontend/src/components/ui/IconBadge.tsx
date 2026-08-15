// F:\Kernschmied\frontend\src\components\ui\IconBadge.tsx

import React from 'react';
import { DynamicIcon, DEFAULT_ICON_NAME } from '../../registry/iconRegistry';
import CommonIconBadge, { type IconBadgeProps as CommonProps } from '../common/IconBadge';

export type IconBadgeVariant = 'sm' | 'md' | 'lg';

export interface IconBadgeProps {
  /** Name des Icons (wird an DynamicIcon übergeben) */
  name?: string | null;
  /** URL zu einem benutzerdefinierten Bild */
  src?: string | null;
  /** Hintergrundfarbe (überschreibt die Variante) */
  color?: string | null;
  /** Größen-Variante (sm/md/lg) → wird auf die `size`-Prop der neuen Komponente abgebildet */
  variant?: IconBadgeVariant;
  /** Titel für Tooltip (wird als `label` oder `title`-Attribut verwendet) */
  title?: string;
  /** Zusätzliche CSS-Klassen */
  className?: string;
}

/**
 * @deprecated Verwende stattdessen die IconBadge-Komponente aus `common/IconBadge`.
 * Diese Komponente ist ein Wrapper, der die alte API (name/src) auf die neue API (icon) abbildet
 * und so die Kompatibilität mit bestehenden Aufrufen gewährleistet.
 *
 * Die visuelle Darstellung entspricht nun der einheitlichen IconBadge aus `common/`.
 */
export default function IconBadge({
  name,
  src,
  color,
  variant = 'md',
  title,
  className,
}: IconBadgeProps) {
  // Abbildung der alten Variant-Namen auf die neuen Size-Namen
  const sizeMap: Record<IconBadgeVariant, CommonProps['size']> = {
    sm: 'sm',
    md: 'md',
    lg: 'lg',
  };

  // Icon als React‑Node vorbereiten
  let icon: React.ReactNode;
  if (src) {
    icon = <img src={String(src)} alt="" className="max-h-full max-w-full object-contain" />;
  } else {
    icon = <DynamicIcon name={name ?? DEFAULT_ICON_NAME} />;
  }

  // Die neue Komponente hat kein eigenes `title`‑Attribut für Tooltips.
  // Wir übergeben `title` als `aria-label`, um die Barrierefreiheit zu verbessern.
  // Zusätzlich setzen wir es als `label` (wenn vorhanden) – das rendert einen Text
  // rechts neben dem Icon, was nicht ganz dasselbe ist, aber die nächste Entsprechung.
  // Für reine Tooltips ohne sichtbaren Text setzen wir `label` nicht.
  // Stattdessen wird `title` als `aria-label` verwendet.
  // Die neue Komponente unterstützt auch `className` und `color`.
  // Für die alte `variant` (sm/md/lg) verwenden wir die `size`‑Prop.

  // Damit die alte border- und rounding-Optik nicht verloren geht, fügen wir
  // bei Bedarf eine `border`-Klasse hinzu – aber die neue Komponente hat
  // standardmäßig kein `border`. Da wir aber Konsistenz anstreben, lassen wir
  // die border weg, da die meisten anderen `IconBadge`‑Verwendungen im Projekt
  // ebenfalls kein border haben (nach den vorherigen Verbesserungen).

  return (
    <CommonIconBadge
      icon={icon}
      size={sizeMap[variant]}
      variant="default" // Die alte Komponente hatte keine Farbvarianten; wir belassen 'default'
      color={color ?? undefined}
      className={className}
      // `label` würde einen Text neben dem Icon anzeigen, was wir nicht wollen.
      // Stattdessen setzen wir die `aria-label` auf `title`, falls vorhanden.
      // Die neue Komponente unterstützt `aria-label` über die `...rest`-Props.
      // Wir nutzen das, indem wir es als reguläres Attribut übergeben.
      aria-label={title || undefined}
    />
  );
}