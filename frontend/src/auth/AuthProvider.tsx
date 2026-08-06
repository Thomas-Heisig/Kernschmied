import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import {
  loadCurrentUser,
  loginWithPassword,
  loginAsDevelopmentAdmin,
  logoutCurrentSession,
  registerUser,
} from './auth-api';
import type { CurrentUser } from './auth-contracts';
import type { AppBootstrap } from '../types/bootstrap';

type User = CurrentUser | null;

type AuthStatus = 'checking' | 'authenticated' | 'unauthenticated' | 'error';

type AuthContextValue = {
  status: AuthStatus;
  user: User;
  error: string | null;
  isSubmitting: boolean;
  developmentLoginAvailable: boolean;
  registrationAvailable: boolean;
  registrationRequiresInvitation: boolean;
  login: (username: string, password: string) => Promise<void>;
  developmentLogin: () => Promise<void>;
  developmentAdminLogin: () => Promise<void>;
  register: (input: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshCurrentUser: () => Promise<void>;
  reload: () => Promise<void>;
  markUnauthenticated: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({
  children,
  bootstrap,
}: {
  children: React.ReactNode;
  bootstrap?: AppBootstrap | null;
}) {
  const [user, setUser] = useState<User>(null);
  const [status, setStatus] = useState<AuthStatus>('checking');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeRequestControllerRef = useRef<AbortController | null>(null);
  const requestGenerationRef = useRef(0);

  function getEndpoint(key: keyof AppBootstrap['endpoints']): string | undefined {
    return (bootstrap && bootstrap.endpoints && (bootstrap.endpoints[key] as string)) ?? undefined;
  }

  // Memoize endpoint-derived flags so effects can depend on stable values
  const meEndpoint =
    (bootstrap && bootstrap.endpoints && (bootstrap.endpoints.authMe as string)) ??
    '/api/v1/auth/me';

  const developmentLoginAvailable = Boolean(
    (bootstrap &&
      (bootstrap.features?.developmentAdminLogin ||
        bootstrap.features?.developmentLoginAvailable)) ||
    false,
  );
  const registrationAvailable = Boolean(
    (bootstrap &&
      (bootstrap.features?.selfRegistration ||
        (bootstrap as any).features?.registrationAvailable)) ||
    false,
  );
  const registrationRequiresInvitation = Boolean(
    (bootstrap && bootstrap.features?.registrationRequiresInvitation) || false,
  );

  async function fetchUser(signal?: AbortSignal): Promise<void> {
    // manage request generation to avoid races
    requestGenerationRef.current += 1;
    const generation = requestGenerationRef.current;

    activeRequestControllerRef.current?.abort();
    const controller = new AbortController();
    activeRequestControllerRef.current = controller;

    try {
      const meEndpoint = getEndpoint('authMe') ?? '/api/v1/auth/me';
      const res = await loadCurrentUser(meEndpoint, controller.signal);

      // If this request is stale, ignore
      if (generation !== requestGenerationRef.current) return;
      if (res.authenticated) {
        setUser(res.user);
        setStatus('authenticated');
        setError(null);
      } else {
        setUser(null);
        setStatus('unauthenticated');
        setError(null);
      }
    } catch (err: any) {
      if (controller.signal.aborted) return;
      // Interpret 401/unauthenticated as unauthenticated
      if (controller.signal.aborted) return;
      if (err && (err.status === 401 || err.status === '401')) {
        setUser(null);
        setStatus('unauthenticated');
        setError(null);
        return;
      }
      setUser(null);
      setStatus('error');
      setError(err?.message ?? String(err));
    } finally {
      if (activeRequestControllerRef.current === controller) {
        activeRequestControllerRef.current = null;
      }
    }
  }

  async function login(username: string, password: string) {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const ep = getEndpoint('authLogin') ?? '/api/v1/auth/login';
      await loginWithPassword(ep, username, password);
      await fetchUser();
    } catch (err: any) {
      setError(err?.message ?? String(err));
      setStatus('error');
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }

  async function developmentAdminLogin() {
    if (isSubmitting) return;
    if (!developmentLoginAvailable) throw new Error('Development login not available');
    setIsSubmitting(true);
    setError(null);
    try {
      const ep = getEndpoint('authDevelopmentLogin') ?? '/api/v1/auth/development-login';
      await loginAsDevelopmentAdmin(ep);
      await fetchUser();
    } catch (err: any) {
      setError(err?.message ?? String(err));
      setStatus('error');
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }

  // Alias to match requested API
  async function developmentLogin() {
    return developmentAdminLogin();
  }

  async function logout() {
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const ep = getEndpoint('authLogout') ?? '/api/v1/auth/logout';
      await logoutCurrentSession(ep);
      // only finalize after server confirmed
      setUser(null);
      setStatus('unauthenticated');
      setError(null);
    } catch (err: any) {
      setError(err?.message ?? String(err));
      setStatus('error');
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }

  // Fetch current user when bootstrap becomes available or the meEndpoint changes.
  const bootstrapReady = Boolean(bootstrap);

  function isUnauthorizedError(e: unknown): boolean {
    try {
      const err = e as any;
      return err && (err.status === 401 || err.status === '401');
    } catch {
      return false;
    }
  }

  function getAuthErrorMessage(e: unknown): string {
    try {
      const err = e as any;
      return err?.message ?? String(e ?? 'Unknown error');
    } catch {
      return String(e);
    }
  }

  useEffect(() => {
    if (!bootstrapReady) return;

    const controller = new AbortController();
    let active = true;

    if (import.meta.env.DEV) {
      console.debug('[AuthProvider] current-user request started', {
        bootstrapReady,
        meEndpoint,
      });
    }

    setStatus('checking');
    setError(null);

    void loadCurrentUser(meEndpoint, controller.signal)
      .then((result) => {
        if (!active) return;

        if (import.meta.env.DEV) {
          console.debug('[AuthProvider] current-user resolved', {
            active,
            aborted: controller.signal.aborted,
            authenticated: result.authenticated,
            hasUser: result.user !== null,
          });
        }

        if (result.authenticated && result.user) {
          if (import.meta.env.DEV) {
            console.debug('[AuthProvider] status transition', {
              from: 'checking',
              to: 'authenticated',
            });
          }
          setUser(result.user);
          setStatus('authenticated');
          setError(null);
          return;
        }

        if (import.meta.env.DEV) {
          console.debug('[AuthProvider] status transition', {
            from: 'checking',
            to: 'unauthenticated',
          });
        }

        setUser(null);
        setStatus('unauthenticated');
        setError(null);
      })
      .catch((error: unknown) => {
        if (!active || controller.signal.aborted) return;

        if (isUnauthorizedError(error)) {
          setUser(null);
          setStatus('unauthenticated');
          setError(null);
          return;
        }

        setUser(null);
        setStatus('error');
        setError(getAuthErrorMessage(error));
      });

    return () => {
      active = false;
      requestGenerationRef.current += 1;
      controller.abort();
      if (activeRequestControllerRef.current) {
        activeRequestControllerRef.current.abort();
        activeRequestControllerRef.current = null;
      }
    };
  }, [bootstrapReady, meEndpoint]);

  const value: AuthContextValue = {
    status,
    user,
    error,
    isSubmitting,
    developmentLoginAvailable,
    registrationAvailable,
    registrationRequiresInvitation,
    login,
    developmentLogin,
    developmentAdminLogin,
    register: async (input) => {
      const ep = getEndpoint('authRegister') ?? '/api/v1/auth/register';
      await registerUser(ep, input as any);
      // After successful registration, refetch user state
      await fetchUser();
    },
    logout,
    refreshCurrentUser: async () => await fetchUser(),
    reload: async () => await fetchUser(),
    markUnauthenticated: () => {
      setUser(null);
      setStatus('unauthenticated');
      setError(null);
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthProvider;
