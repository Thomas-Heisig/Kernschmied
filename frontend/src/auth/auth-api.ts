import { apiGet, apiPost } from '../api/client';
import { apiPatch, apiDelete } from '../api/client';
import type { CurrentUser, UpdateOwnProfileInput } from './auth-contracts';

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

// ---------- Profile / Preferences / Sessions wrappers ----------

export async function loadOwnProfile(endpoint?: string): Promise<CurrentUser | null> {
  const ep = endpoint ?? '/api/v1/users/me';
  const resRaw = await apiGet<unknown>(ep, { credentials: 'include' });
  return normalizeUser(resRaw);
}

export async function updateOwnProfile(endpoint: string | undefined, input: UpdateOwnProfileInput): Promise<CurrentUser> {
  const ep = endpoint ?? '/api/v1/users/me';
  const body = {
    display_name: input.displayName,
    email: input.email ?? null,
  };
  const resRaw = await apiPatch<unknown, typeof body>(ep, body, { credentials: 'include' });
  const normalized = normalizeUser(resRaw);
  if (!normalized) throw new Error('Invalid profile response');
  return normalized;
}

function normalizePreferences(raw: unknown): import('./auth-contracts').UserPreferences | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  return {
    schemaVersion: String(r.schema_version ?? '1.0'),
    language: String(r.language ?? 'de'),
    timezone: String(r.timezone ?? 'Europe/Berlin'),
    theme: (r.theme as any) ?? 'system',
    density: (r.density as any) ?? 'comfortable',
    defaultView: r.default_view === undefined ? null : (r.default_view as string | null),
    notificationsEnabled: Boolean(r.notifications_enabled ?? true),
    updatedAt: r.updated_at ? String(r.updated_at) : null,
  } as import('./auth-contracts').UserPreferences;
}

export async function loadUserPreferences(endpoint?: string): Promise<import('./auth-contracts').UserPreferences | null> {
  const ep = endpoint ?? '/api/v1/users/me/preferences';
  const resRaw = await apiGet<unknown>(ep, { credentials: 'include' });
  return normalizePreferences(resRaw);
}

export async function updateUserPreferences(endpoint: string | undefined, input: import('./auth-contracts').UpdateUserPreferencesInput): Promise<import('./auth-contracts').UserPreferences> {
  const ep = endpoint ?? '/api/v1/users/me/preferences';
  const body: Record<string, unknown> = {};
  if (input.language !== undefined) body.language = input.language;
  if (input.timezone !== undefined) body.timezone = input.timezone;
  if (input.theme !== undefined) body.theme = input.theme;
  if (input.density !== undefined) body.density = input.density;
  if (input.defaultView !== undefined) body.default_view = input.defaultView;
  if (input.notificationsEnabled !== undefined) body.notifications_enabled = input.notificationsEnabled;

  const resRaw = await apiPatch<unknown, typeof body>(ep, body, { credentials: 'include' });
  const normalized = normalizePreferences(resRaw);
  if (!normalized) throw new Error('Invalid preferences response');
  return normalized;
}

function normalizeSession(raw: unknown): import('./auth-contracts').UserSession | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  return {
    schemaVersion: String(r.schema_version ?? '1.0'),
    id: String(r.id),
    authenticationMethod: String(r.authentication_method ?? ''),
    createdAt: String(r.created_at ?? ''),
    expiresAt: String(r.expires_at ?? ''),
    lastSeenAt: r.last_seen_at ? String(r.last_seen_at) : null,
    revokedAt: r.revoked_at ? String(r.revoked_at) : null,
    current: Boolean(r.current ?? false),
    active: Boolean(r.active ?? false),
    ipAddress: r.ip_address === undefined ? null : String(r.ip_address),
    userAgent: r.user_agent === undefined ? null : String(r.user_agent),
  } as import('./auth-contracts').UserSession;
}

export async function loadSessions(endpoint?: string): Promise<import('./auth-contracts').UserSession[]> {
  const ep = endpoint ?? '/api/v1/auth/sessions';
  const res = await apiGet<unknown[]>(ep, { credentials: 'include' });
  if (!Array.isArray(res)) return [];
  return res.map(normalizeSession).filter((s): s is import('./auth-contracts').UserSession => s !== null);
}

export async function revokeSession(endpoint: string | undefined, sessionId: string): Promise<void> {
  const ep = endpoint ?? `/api/v1/auth/sessions/${sessionId}`;
  await apiDelete<void>(ep, { credentials: 'include' });
}

export async function logoutAllSessions(endpoint?: string): Promise<{ revoked: number }> {
  const ep = endpoint ?? '/api/v1/auth/logout-all';
  return await apiPost<{ revoked: number }>(ep, undefined, { credentials: 'include' });
}

export async function changePassword(endpoint: string | undefined, payload: { currentPassword: string; newPassword: string }) {
  const ep = endpoint ?? '/api/v1/users/me/password';
  return await apiPost(ep, { current_password: payload.currentPassword, new_password: payload.newPassword }, { credentials: 'include' });
}
