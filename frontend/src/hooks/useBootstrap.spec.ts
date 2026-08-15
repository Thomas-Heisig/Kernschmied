import { describe, expect, it } from 'vitest';

import { normalizeBootstrapResponse } from './useBootstrap';

describe('normalizeBootstrapResponse', () => {
  it('normalizes authentication features from the backend snake_case contract', () => {
    const bootstrap = normalizeBootstrapResponse({
      schema_version: '1.1',
      api_version: 'v1',
      security_profile: {
        profile: 'appenvironment.development',
        environment: 'development',
        authentication_required: false,
        development_identity_active: true,
        available_login_methods: ['development_admin', 'registration'],
      },
      features: {
        development_admin_login: true,
        self_registration: true,
        registration_requires_invitation: false,
      },
      endpoints: {
        auth_development_login: '/api/v1/auth/development-login',
        auth_register: '/api/v1/auth/register',
        auth_logout: '/api/v1/auth/logout',
        auth_me: '/api/v1/auth/me',
      },
    });

    expect(bootstrap.security.profile).toBe('development');
    expect(bootstrap.security.availableLoginMethods).toEqual([
      'development_admin',
      'registration',
    ]);
    expect(bootstrap.features.developmentAdminLogin).toBe(true);
    expect(bootstrap.features.selfRegistration).toBe(true);
    expect(bootstrap.endpoints.authRegister).toBe('/api/v1/auth/register');
  });
});