// F:\Kernschmied\frontend\src\theme\ThemeProvider.tsx

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

export type Theme = 'light' | 'dark';

interface ThemeContextValue {
  /** Aktuelles Theme ('light' | 'dark') */
  theme: Theme;
  /** Theme explizit setzen */
  setTheme: (theme: Theme) => void;
  /** Theme umschalten (light ↔ dark) */
  toggleTheme: () => void;
}

interface ThemeProviderProps {
  children: ReactNode;
}

/** Schlüssel für localStorage */
const THEME_STORAGE_KEY = 'kernschmied.theme' as const;

/** Name des Meta‑Tags für die Theme‑Color */
const THEME_COLOR_META_NAME = 'theme-color';

/** Farben für light/dark Mode (für mobile Browser) */
const THEME_COLORS: Record<Theme, string> = {
  light: '#ffffff',
  dark: '#0f172a', // slate-950
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

/**
 * ThemeProvider – verwaltet das globale Theme (light/dark).
 *
 * - Speichert das Theme im localStorage
 * - Wendet die `dark`‑Klasse am `<html>`‑Element an
 * - Aktualisiert das `theme-color`‑Meta‑Tag für mobile Browser
 * - Synchronisiert Theme‑Änderungen über mehrere Tabs (storage‑Event)
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(readInitialTheme);

  const setTheme = useCallback((nextTheme: Theme): void => {
    setThemeState(nextTheme);
  }, []);

  const toggleTheme = useCallback((): void => {
    setThemeState((currentTheme) => (currentTheme === 'light' ? 'dark' : 'light'));
  }, []);

  // Theme anwenden, wenn es sich ändert
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  // Cross‑Tab‑Synchronisation: Wenn sich das Theme in einem anderen Tab ändert,
  // wird dieses Event empfangen und das Theme aktualisiert.
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === THEME_STORAGE_KEY) {
        const newTheme = event.newValue as Theme | null;
        if (newTheme === 'light' || newTheme === 'dark') {
          setThemeState(newTheme);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const contextValue = useMemo<ThemeContextValue>(
    () => ({
      theme,
      setTheme,
      toggleTheme,
    }),
    [theme, setTheme, toggleTheme],
  );

  return <ThemeContext.Provider value={contextValue}>{children}</ThemeContext.Provider>;
}

/**
 * useTheme – Hook für den Zugriff auf das Theme‑Context.
 *
 * @throws {Error} Wenn außerhalb eines ThemeProvider verwendet
 * @returns {ThemeContextValue} Theme, setTheme, toggleTheme
 */
export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme muss innerhalb eines ThemeProvider verwendet werden.');
  }

  return context;
}

// ============================================================
// Private Hilfsfunktionen
// ============================================================

/**
 * Liest das initiale Theme aus localStorage oder System‑Preferenz.
 *
 * Priorität:
 * 1. localStorage (gespeicherte Benutzer‑Präferenz)
 * 2. System‑Preferenz (`prefers-color-scheme: dark`)
 * 3. Fallback: 'light'
 */
function readInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'light';
  }

  try {
    const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);

    if (storedTheme === 'light' || storedTheme === 'dark') {
      return storedTheme;
    }
  } catch {
    // localStorage nicht verfügbar → System‑Preferenz verwenden
  }

  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

/**
 * Wendet das Theme auf die gesamte App an.
 *
 * - Fügt/entfernt die `dark`‑Klasse am `<html>`‑Element
 * - Setzt `data-theme` und `color-scheme` Attribute
 * - Aktualisiert das `theme-color`‑Meta‑Tag
 * - Speichert die Präferenz im localStorage
 */
function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  const isDark = theme === 'dark';

  // Tailwind‑Dark‑Mode aktivieren/deaktivieren
  root.classList.toggle('dark', isDark);

  // CSS‑Attribute für zusätzliche Styling‑Möglichkeiten
  root.dataset.theme = theme;
  root.style.colorScheme = theme;

  // Meta‑Tag für mobile Browser (Chrome, Safari) aktualisieren
  updateThemeColorMeta(theme);

  // Präferenz im localStorage speichern
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // localStorage nicht verfügbar – ignorieren
  }

  // Development‑Logging
  if (import.meta.env.DEV) {
    console.debug(`[Theme] Applied theme: ${theme}`);
  }
}

/**
 * Aktualisiert das `theme-color`‑Meta‑Tag für mobile Browser.
 *
 * Das Meta‑Tag wird entweder aktualisiert oder neu erstellt,
 * falls es noch nicht existiert.
 */
function updateThemeColorMeta(theme: Theme): void {
  const color = THEME_COLORS[theme];

  let metaTag = document.querySelector<HTMLMetaElement>(
    `meta[name="${THEME_COLOR_META_NAME}"]`,
  );

  if (!metaTag) {
    metaTag = document.createElement('meta');
    metaTag.name = THEME_COLOR_META_NAME;
    document.head.appendChild(metaTag);
  }

  metaTag.content = color;
}