import { apiGet, apiPost } from '../api/client';
import type { CurrentUser } from './auth-contracts';

function normalizeTenant(raw: unknown): CurrentUser['tenant'] {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  const id = r.id ?? r['id'];
  const displayName = r.display_name ?? r.displayName ?? r.name ?? '';
  if (id === undefined) return null;
  return { id: String(id), displayName: String(displayName) };
}

function normalizeUser(raw: unknown): CurrentUser | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;

  const id = r.id ?? r['id'];
  if (id === undefined) return null;

  const username = String(r.username ?? r['username'] ?? r.name ?? id);
  const displayName = String(r.display_name ?? r.displayName ?? r.display_name ?? username);
  const email = r.email === undefined ? null : String(r.email ?? r['email'] ?? null);
  const authenticated = Boolean(r.authenticated ?? r['authenticated'] ?? true);
  const developmentSession = Boolean(r.development_session ?? r.developmentSession ?? false);
  const passwordLoginAvailable = Boolean(
    r.password_login_available ?? r.passwordLoginAvailable ?? r['password_login_available'] ?? false,
  );

  const tenant = normalizeTenant(r.tenant ?? r['tenant']);

  return {
    id: String(id),
    username,
    displayName,
    email,
    authenticated,
    developmentSession,
    passwordLoginAvailable,
    tenant,
  };
}

export async function loadCurrentUser(meEndpoint: string | undefined): Promise<CurrentUser | null> {
  const ep = meEndpoint ?? '/api/v1/auth/me';
  const resRaw = await apiGet<unknown>(ep, { credentials: 'include' });
  const normalized = normalizeUser(resRaw);
  return normalized;
}

export async function loginWithPassword(loginEndpoint: string | undefined, username: string, password: string): Promise<void> {
  const ep = loginEndpoint ?? '/api/v1/auth/login';
  await apiPost(ep, { username, password }, { credentials: 'include' });
}

export async function loginAsDevelopmentAdmin(devEndpoint: string | undefined): Promise<void> {
  const ep = devEndpoint ?? '/api/v1/auth/development-login';
  await apiPost(ep, undefined, { credentials: 'include' });
}

export async function logoutCurrentSession(logoutEndpoint?: string): Promise<void> {
  const ep = logoutEndpoint ?? '/api/v1/auth/logout';
  await apiPost(ep, undefined, { credentials: 'include' });
}

export interface RegisterInput {
  username: string;
  displayName: string;
  email?: string | null;
  password: string;
  passwordConfirmation: string;
  invitationToken?: string | null;
}

export async function registerUser(registerEndpoint: string | undefined, payload: RegisterInput): Promise<any> {
  const ep = registerEndpoint ?? '/api/v1/auth/register';
  return await apiPost(ep, {
    username: payload.username,
    display_name: payload.displayName,
    email: payload.email ?? null,
    password: payload.password,
    password_confirmation: payload.passwordConfirmation,
    invitation_token: payload.invitationToken ?? null,
  }, { credentials: 'include' });
}
