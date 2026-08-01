// src/app/AppProviders.tsx
import {
  type ComponentType,
  type PropsWithChildren,
  type ReactElement,
  type ReactNode,
} from "react";

import { ThemeProvider } from "../theme";
import { AppStoreProvider } from "../store";

type ApplicationProvider = ComponentType<any>;

const APPLICATION_PROVIDERS: readonly ApplicationProvider[] = [
  AppStoreProvider,
  ThemeProvider,
];

function composeProviders(
  providers: readonly ApplicationProvider[],
  children: ReactNode,
): ReactNode {
  return providers.reduceRight<ReactNode>(
    (currentChildren, Provider) => <Provider>{currentChildren}</Provider>,
    children,
  );
}

export function AppProviders({ children }: PropsWithChildren): ReactElement {
  return <>{composeProviders(APPLICATION_PROVIDERS, children)}</>;
}
