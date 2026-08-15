import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { normalizeBootstrapResponse } from '../../hooks/useBootstrap';
import { AuthProvider } from '../AuthProvider';
import LoginPage from '../LoginPage';
import { loadCurrentUser } from '../auth-api';

vi.mock('../auth-api', () => ({
  loadCurrentUser: vi.fn(),
  loginAsDevelopmentAdmin: vi.fn(),
  loginWithPassword: vi.fn(),
  logoutCurrentSession: vi.fn(),
  registerUser: vi.fn(),
}));

describe('LoginPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(loadCurrentUser).mockResolvedValue({ authenticated: false, user: null });
  });

  it('shows self-registration and development login from the backend bootstrap contract', async () => {
    const bootstrap = normalizeBootstrapResponse({
      security_profile: {
        environment: 'development',
        available_login_methods: ['development_admin', 'registration'],
      },
      features: {
        development_admin_login: true,
        self_registration: true,
      },
      endpoints: {
        auth_me: '/api/v1/auth/me',
        auth_development_login: '/api/v1/auth/development-login',
        auth_register: '/api/v1/auth/register',
      },
    });

    render(
      <AuthProvider bootstrap={bootstrap}>
        <LoginPage />
      </AuthProvider>,
    );

    await waitFor(() => expect(loadCurrentUser).toHaveBeenCalledOnce());

    expect(
      screen.getByRole('button', { name: 'Als Development-Administrator starten' }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Noch kein Benutzerkonto? Registrieren' }),
    ).toBeInTheDocument();
  });
});