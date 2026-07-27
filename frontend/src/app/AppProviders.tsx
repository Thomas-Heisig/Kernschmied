// F:\Kernschmied\frontend\src\app\AppProviders.tsx

import {
  type ComponentType,
  type PropsWithChildren,
  type ReactElement,
  type ReactNode,
} from "react";

import { AppStoreProvider } from "../store";

/**
 * Generischer React-Provider, der ausschließlich `children` benötigt.
 *
 * Provider mit zusätzlichen verpflichtenden Eigenschaften müssen über
 * eine kleine Adapterkomponente eingebunden werden.
 */
type ApplicationProvider =
  ComponentType<PropsWithChildren>;

/**
 * Zentrale Liste aller globalen Anwendungs-Provider.
 *
 * Die Reihenfolge ist relevant:
 *
 * Der erste Provider wird durch `composeProviders` zum äußersten
 * Provider und steht damit allen nachfolgenden Providern zur Verfügung.
 *
 * Beispiel:
 *
 * [
 *   OuterProvider,
 *   InnerProvider,
 * ]
 *
 * ergibt:
 *
 * <OuterProvider>
 *   <InnerProvider>
 *     {children}
 *   </InnerProvider>
 * </OuterProvider>
 */
const APPLICATION_PROVIDERS:
  readonly ApplicationProvider[] = [
    AppStoreProvider,
  ];

function composeProviders(
  providers: readonly ApplicationProvider[],
  children: ReactNode,
): ReactNode {
  return providers.reduceRight<ReactNode>(
    (
      currentChildren,
      Provider,
    ) => (
      <Provider>
        {currentChildren}
      </Provider>
    ),
    children,
  );
}

/**
 * Bündelt alle globalen React-Provider der Anwendung.
 *
 * Fachliche Provider sollten nur dann hier registriert werden, wenn sie
 * tatsächlich für die gesamte Anwendung benötigt werden. Lokale
 * Feature-Provider gehören möglichst nah an das jeweilige Feature.
 */
export function AppProviders({
  children,
}: PropsWithChildren): ReactElement {
  return (
    <>
      {composeProviders(
        APPLICATION_PROVIDERS,
        children,
      )}
    </>
  );
}
