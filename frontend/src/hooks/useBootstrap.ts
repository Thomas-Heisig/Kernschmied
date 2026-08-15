import { useCallback, useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import type { AppBootstrap } from '../types/bootstrap';

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
}

function normalizeProfile(value: unknown): AppBootstrap['security']['profile'] {
  const normalized = String(value ?? '').toLowerCase();
  if (normalized.endsWith('development')) return 'development';
  if (normalized.endsWith('intranet')) return 'intranet';
  return 'internet';
}

export function normalizeBootstrapResponse(raw: unknown): AppBootstrap {
  const root = asRecord(raw);
  const security = asRecord(root.security_profile ?? root.securityProfile ?? root.security);
  const features = asRecord(root.features);
  const endpoints = asRecord(root.endpoints);
  const availableLoginMethods = security.available_login_methods ?? security.availableLoginMethods;

  return {
    security: {
      profile: normalizeProfile(security.environment ?? security.profile),
      authenticationRequired: Boolean(
        security.authentication_required ?? security.authenticationRequired ?? false,
      ),
      developmentIdentityActive: Boolean(
        security.development_identity_active ?? security.developmentIdentityActive ?? false,
      ),
      availableLoginMethods: Array.isArray(availableLoginMethods)
        ? availableLoginMethods.map(String)
        : [],
    },
    features: {
      developmentAdminLogin: Boolean(
        features.development_admin_login ?? features.developmentAdminLogin ?? false,
      ),
      selfRegistration: Boolean(
        features.self_registration ?? features.selfRegistration ?? false,
      ),
      registrationRequiresInvitation: Boolean(
        features.registration_requires_invitation ??
          features.registrationRequiresInvitation ??
          false,
      ),
    },
    endpoints: {
      authLogin: String(endpoints.auth_login ?? endpoints.authLogin ?? ''),
      authLogout: String(endpoints.auth_logout ?? endpoints.authLogout ?? ''),
      authMe: String(endpoints.auth_me ?? endpoints.authMe ?? ''),
      authDevelopmentLogin: String(
        endpoints.auth_development_login ?? endpoints.authDevelopmentLogin ?? '',
      ),
      authRegister: String(endpoints.auth_register ?? endpoints.authRegister ?? ''),
      userProfile: String(endpoints.user_profile ?? endpoints.userProfile ?? ''),
      userPreferences: String(endpoints.user_preferences ?? endpoints.userPreferences ?? ''),
      uiSchema: String(endpoints.ui_schema ?? endpoints.uiSchema ?? ''),
      hierarchy: String(endpoints.hierarchy ?? ''),
    },
    schemaVersion: String(root.schema_version ?? root.schemaVersion ?? ''),
    apiVersion: String(root.api_version ?? root.apiVersion ?? ''),
    requestId:
      typeof (root.request_id ?? root.requestId) === 'string'
        ? String(root.request_id ?? root.requestId)
        : null,
  };
}

export function useBootstrap() {
  const [bootstrap, setBootstrap] = useState<AppBootstrap | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [error, setError] = useState<Error | null>(null);
  // Initial load using local active flag + AbortController to be StrictMode-safe
  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    setStatus('loading');
    setError(null);

    void apiGet('/bootstrap', { signal: controller.signal })
      .then((raw) => {
        if (!active) return;
        setBootstrap(normalizeBootstrapResponse(raw));
        setStatus('ready');
      })
      .catch((err: any) => {
        if (!active || controller.signal.aborted) return;
        setError(err instanceof Error ? err : new Error(String(err)));
        setStatus('error');
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  const reloadBootstrap = useCallback(async (): Promise<void> => {
    let active = true;
    const controller = new AbortController();

    setStatus('loading');
    setError(null);

    try {
      const raw = await apiGet('/bootstrap', { signal: controller.signal });
      if (!active) return;
      setBootstrap(normalizeBootstrapResponse(raw));
      setStatus('ready');
    } catch (err: any) {
      if (!active || controller.signal.aborted) return;
      setError(err instanceof Error ? err : new Error(String(err)));
      setStatus('error');
    } finally {
      active = false;
    }
  }, []);

  return {
    bootstrap,
    status,
    error,
    reloadBootstrap,
  };
}
