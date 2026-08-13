// F:\Kernschmied\frontend\src\main.tsx

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import { AppProviders } from './app/AppProviders';

import './index.css';
import './registry/registerWidgets';

const ROOT_ELEMENT_ID = 'root';

function getRootElement(): HTMLElement {
  const rootElement = document.getElementById(ROOT_ELEMENT_ID);

  if (!rootElement) {
    throw new Error(`Das Root-Element mit der ID "${ROOT_ELEMENT_ID}" wurde nicht gefunden.`);
  }

  return rootElement;
}

createRoot(getRootElement()).render(
  <StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </StrictMode>,
);
