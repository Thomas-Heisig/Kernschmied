// F:\Kernschmied\frontend\src\app\AppProviders.tsx

import {
  type ComponentType,
  type PropsWithChildren,
  type ReactElement,
  type ReactNode,
} from 'react';

import { ThemeProvider } from '../theme';
import { AppStoreProvider } from '../store';
import { ToastProvider } from '../components/ui/ToastProvider';

/**
 * Liste aller Application-Provider in der korrekten Reihenfolge.
 *
 * Die Provider werden von **innen nach außen** verschachtelt:
 * - Der letzte Provider in der Liste ist der äußerste.
 * - Die Reihenfolge ist wichtig für die Verfügbarkeit von Context-Hooks.
 *
 * @example
 * // Provider-Kette (von innen nach außen):
 * // children → ToastProvider → AppStoreProvider → ThemeProvider
 */
type ApplicationProvider = ComponentType<any>;

const APPLICATION_PROVIDERS: readonly ApplicationProvider[] = [
  AppStoreProvider,
  ThemeProvider,
  ToastProvider,
];

/**
 * Komponiert eine Kette von React-Providern.
 *
 * Verwendet `reduceRight`, um die Provider von **innen nach außen** zu verschachteln.
 * Der erste Provider in der Liste ist der innerste, der letzte der äußerste.
 *
 * @param providers - Liste der Provider-Komponenten
 * @param children - Die zu umschließenden Kinder-Komponenten
 * @returns Die verschachtelte Provider-Struktur
 */
function composeProviders(
  providers: readonly ApplicationProvider[],
  children: ReactNode,
): ReactNode {
  return providers.reduceRight<ReactNode>(
    (currentChildren, Provider) => <Provider>{currentChildren}</Provider>,
    children,
  );
}

/**
 * AppProviders – Zentrale Provider-Komposition für die gesamte Anwendung.
 *
 * Stellt folgende Provider bereit:
 * - `AppStoreProvider`: Globaler Anwendungszustand (Zustand)
 * - `ThemeProvider`: Dark-/Light-Mode
 * - `ToastProvider`: Toast-Benachrichtigungen
 *
 * @param props.children - Die Kinder-Komponenten der App
 * @returns Die mit allen Providern umschlossene App
 */
export function AppProviders({ children }: PropsWithChildren): ReactElement {
  return <>{composeProviders(APPLICATION_PROVIDERS, children)}</>;
}