import { apiGet, apiPost } from '../api/client';
import { apiPatch, apiDelete } from '../api/client';
import type {
  CurrentUser,
  UpdateOwnProfileInput,
  UserPreferences,
  UpdateUserPreferencesInput,
  UserSession,
  ChangePasswordInput,
} from './auth-contracts';

function normalizeUser(raw: unknown): CurrentUser | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;

  const id = r.id ?? r['id'];
  if (id === undefined) return null;

  const username = String(r.username ?? r['username'] ?? r.name ?? id);
  const displayName = String(r.display_name ?? r.displayName ?? username);
  const rawEmail = r.email ?? r['email'];
  const email = rawEmail === undefined || rawEmail === null ? null : String(rawEmail);

  const tenantRaw = r.tenant ?? r['tenant'] ?? null;
  const tenant =
    tenantRaw && typeof tenantRaw === 'object'
      ? {
          id: String((tenantRaw as any).id ?? ''),
          displayName: String(
            (tenantRaw as any).display_name ?? (tenantRaw as any).displayName ?? '',
          ),
        }
      : null;

  const roles = Array.isArray(r.roles) ? (r.roles as unknown[]).map((v) => String(v)) : [];

  return {
    id: String(id),
    username,
    displayName,
    email,
    tenant,
    roles,
    authenticated: Boolean(r.authenticated ?? r['authenticated'] ?? false),
    developmentSession: Boolean(r.development_session ?? r['developmentSession'] ?? false),
    passwordLoginAvailable: Boolean(
      r.password_login_available ?? r['passwordLoginAvailable'] ?? false,
    ),
    createdAt: r.created_at ? String(r.created_at) : null,
    lastLoginAt: r.last_login_at ? String(r.last_login_at) : null,
    schemaVersion: String(r.schema_version ?? r['schemaVersion'] ?? '1.0'),
  };
}

export interface CurrentUserResult {
  authenticated: boolean;
  user: CurrentUser | null;
}

export async function loadCurrentUser(
  meEndpoint: string | undefined,
  signal?: AbortSignal,
): Promise<CurrentUserResult> {
  const ep = meEndpoint ?? '/api/v1/auth/me';
  const resRaw = await apiGet<unknown>(ep, { credentials: 'include', signal });

  // Some backends return a wrapper like { authenticated: true, user: {...} }
  // while others return the user object directly. Normalize both cases.
  if (!resRaw || typeof resRaw !== 'object') {
    return { authenticated: false, user: null };
  }

  const r = resRaw as Record<string, unknown>;

  if ('authenticated' in r) {
    const authenticated = Boolean(r.authenticated);
    if ('user' in r) {
      return { authenticated, user: normalizeUser((r.user as unknown) ?? null) };
    }
    // If authenticated is true but no user object, attempt to normalize the wrapper itself
    const possibleUser = normalizeUser(r);
    return { authenticated, user: possibleUser };
  }

  // Otherwise try to interpret the response as a user object
  const normalized = normalizeUser(resRaw);
  return { authenticated: !!normalized, user: normalized };
}

export async function loginWithPassword(
  loginEndpoint: string | undefined,
  username: string,
  password: string,
): Promise<void> {
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

export interface ManagedUser {
  id: string;
  username: string;
  displayName: string;
  email: string | null;
  isActive: boolean;
  isSystem: boolean;
  accessLevel: AccessLevel;
  workspaceQuota: QuotaSetting;
  projectQuota: QuotaSetting;
  chatQuota: QuotaSetting;
}

export type AccessLevel = 'guest' | 'internal' | 'admin';
export type QuotaSetting = number | 'unlimited' | null;

export interface ManagedUserInput {
  username: string;
  displayName: string;
  email?: string | null;
  password?: string | null;
  generatePassword?: boolean;
  requirePasswordChange?: boolean;
  accessLevel?: AccessLevel;
  workspaceQuota?: QuotaSetting;
  projectQuota?: QuotaSetting;
  chatQuota?: QuotaSetting;
}

function normalizeQuotaSetting(value: unknown): QuotaSetting {
  if (value === 'unlimited') return 'unlimited';
  if (typeof value === 'number' && Number.isInteger(value) && value >= 0) return value;
  return null;
}

function normalizeManagedUser(raw: unknown): ManagedUser {
  const value = raw as Record<string, unknown>;
  return {
    id: String(value.id),
    username: String(value.username),
    displayName: String(value.display_name ?? value.displayName ?? value.username),
    email: value.email ? String(value.email) : null,
    isActive: Boolean(value.is_active ?? value.isActive),
    isSystem: Boolean(value.is_system ?? value.isSystem),
    accessLevel:
      value.access_level === 'admin' || value.access_level === 'internal'
        ? value.access_level
        : 'guest',
      workspaceQuota: normalizeQuotaSetting(value.workspace_quota ?? value.workspaceQuota),
      projectQuota: normalizeQuotaSetting(value.project_quota ?? value.projectQuota),
      chatQuota: normalizeQuotaSetting(value.chat_quota ?? value.chatQuota),
  };
}

export async function listManagedUsers(): Promise<ManagedUser[]> {
  const response = await apiGet<unknown[]>('/api/v1/users/', { credentials: 'include' });
  return Array.isArray(response) ? response.map(normalizeManagedUser) : [];
}

export async function createManagedUser(input: ManagedUserInput): Promise<{
  user: ManagedUser;
  temporaryPassword: string | null;
}> {
  const response = await apiPost<Record<string, unknown>>(
    '/api/v1/users/',
    {
      username: input.username,
      display_name: input.displayName,
      email: input.email ?? null,
      password: input.password || null,
      generate_password: Boolean(input.generatePassword),
      require_password_change: input.requirePasswordChange ?? true,
      roles: null,
      access_level: input.accessLevel ?? 'guest',
      workspace_quota: input.workspaceQuota ?? null,
      project_quota: input.projectQuota ?? null,
      chat_quota: input.chatQuota ?? null,
      is_active: true,
      preferences: null,
      create_default_workspace: true,
      default_workspace_name: `${input.displayName} – Arbeitsbereich`,
    },
    { credentials: 'include' },
  );
  const credentials = response.generated_credentials as Record<string, unknown> | null;
  return {
    user: normalizeManagedUser(response.user),
    temporaryPassword: credentials?.temporary_password
      ? String(credentials.temporary_password)
      : null,
  };
}

export async function updateManagedUser(
  userId: string,
  input: {
    displayName: string;
    email?: string | null;
    isActive: boolean;
    accessLevel: AccessLevel;
    workspaceQuota: QuotaSetting;
    projectQuota: QuotaSetting;
    chatQuota: QuotaSetting;
  },
): Promise<ManagedUser> {
  const response = await apiPatch<unknown, Record<string, unknown>>(
    `/api/v1/users/${encodeURIComponent(userId)}`,
    {
      display_name: input.displayName,
      email: input.email ?? null,
      is_active: input.isActive,
      access_level: input.accessLevel,
      workspace_quota: input.workspaceQuota,
      project_quota: input.projectQuota,
      chat_quota: input.chatQuota,
    },
    { credentials: 'include' },
  );
  return normalizeManagedUser(response);
}

export async function resetManagedUserPassword(
  userId: string,
  password: string | null,
): Promise<string | null> {
  const response = await apiPost<{ temporary_password?: string | null }>(
    `/api/v1/users/${encodeURIComponent(userId)}/password-reset`,
    {
      generate_password: !password,
      password: password || null,
      require_password_change: true,
      revoke_sessions: true,
    },
    { credentials: 'include' },
  );
  return response.temporary_password ?? null;
}

export async function deleteManagedUser(userId: string): Promise<void> {
  await apiDelete(`/api/v1/users/${encodeURIComponent(userId)}`, {
    credentials: 'include',
  });
}

export async function registerUser(
  registerEndpoint: string | undefined,
  payload: RegisterInput,
): Promise<any> {
  const ep = registerEndpoint ?? '/api/v1/auth/register';
  return await apiPost(
    ep,
    {
      username: payload.username,
      display_name: payload.displayName,
      email: payload.email ?? null,
      password: payload.password,
      password_confirmation: payload.passwordConfirmation,
      invitation_token: payload.invitationToken ?? null,
    },
    { credentials: 'include' },
  );
}

// ---------- Profile / Preferences / Sessions wrappers ----------

export async function loadOwnProfile(endpoint?: string): Promise<CurrentUser | null> {
  const ep = endpoint ?? '/api/v1/users/me';
  const resRaw = await apiGet<unknown>(ep, { credentials: 'include' });
  return normalizeUser(resRaw);
}

export async function updateOwnProfile(
  endpoint: string | undefined,
  input: UpdateOwnProfileInput,
): Promise<CurrentUser> {
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

function normalizePreferences(raw: unknown): UserPreferences | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  const density = (r.density ?? r['density'] ?? r['compactMode'] ?? null) as string | null;
  const compactMode =
    density === 'compact' || Boolean(r.compact_mode ?? r['compact_mode'] ?? false);
  return {
    language: String(r.language ?? r['language'] ?? 'de') === 'en' ? 'en' : 'de',
    timezone: String(r.timezone ?? r['timezone'] ?? 'Europe/Berlin'),
    theme: (r.theme as any) ?? (r['theme'] as any) ?? 'system',
    compactMode: Boolean(compactMode),
    defaultView:
      (r.default_view ?? r['defaultView'] ?? null) == null
        ? null
        : String(r.default_view ?? r['defaultView']),
    notificationsEnabled: Boolean(r.notifications_enabled ?? r['notificationsEnabled'] ?? true),
    deliveryReceiptsEnabled: Boolean(
      r.delivery_receipts_enabled ?? r['deliveryReceiptsEnabled'] ?? true,
    ),
    notificationSoundEnabled: Boolean(
      r.notification_sound_enabled ?? r['notificationSoundEnabled'] ?? false,
    ),
    aiResponseOnMentions: Boolean(
      r.ai_response_on_mentions ?? r['aiResponseOnMentions'] ?? false,
    ),
    revision: Number(r.revision ?? 0) as number,
    updatedAt: r.updated_at ? String(r.updated_at) : null,
    schemaVersion: String(r.schema_version ?? r['schemaVersion'] ?? '1.0'),
  };
}

export async function loadUserPreferences(
  endpoint?: string,
): Promise<import('./auth-contracts').UserPreferences | null> {
  const ep = endpoint ?? '/api/v1/users/me/preferences';
  const resRaw = await apiGet<unknown>(ep, { credentials: 'include' });
  return normalizePreferences(resRaw);
}

export async function updateUserPreferences(
  endpoint: string | undefined,
  input: import('./auth-contracts').UpdateUserPreferencesInput,
): Promise<import('./auth-contracts').UserPreferences> {
  const ep = endpoint ?? '/api/v1/users/me/preferences';
  const body: Record<string, unknown> = {};
  if (input.language !== undefined) body.language = input.language;
  if (input.timezone !== undefined) body.timezone = input.timezone;
  if (input.theme !== undefined) body.theme = input.theme;
  if ((input as UpdateUserPreferencesInput).compactMode !== undefined)
    body.density = (input as UpdateUserPreferencesInput).compactMode ? 'compact' : 'comfortable';
  if (input.defaultView !== undefined) body.default_view = input.defaultView;
  if (input.notificationsEnabled !== undefined)
    body.notifications_enabled = input.notificationsEnabled;
  if (input.deliveryReceiptsEnabled !== undefined)
    body.delivery_receipts_enabled = input.deliveryReceiptsEnabled;
  if (input.notificationSoundEnabled !== undefined)
    body.notification_sound_enabled = input.notificationSoundEnabled;
  if (input.aiResponseOnMentions !== undefined)
    body.ai_response_on_mentions = input.aiResponseOnMentions;

  const resRaw = await apiPatch<unknown, typeof body>(ep, body, { credentials: 'include' });
  const normalized = normalizePreferences(resRaw);
  if (!normalized) throw new Error('Invalid preferences response');
  return normalized;
}

function normalizeSession(raw: unknown): UserSession | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  return {
    id: String(r.id),
    current: Boolean(r.current ?? false),
    authenticationMethod: String(r.authentication_method ?? r['authenticationMethod'] ?? ''),
    ipAddress: r.ip_address === undefined ? null : String(r.ip_address ?? r['ipAddress']),
    userAgent: r.user_agent === undefined ? null : String(r.user_agent ?? r['userAgent']),
    createdAt: String(r.created_at ?? r['createdAt'] ?? ''),
    lastSeenAt: r.last_seen_at ? String(r.last_seen_at) : null,
    expiresAt: String(r.expires_at ?? r['expiresAt'] ?? ''),
    revokedAt: r.revoked_at ? String(r.revoked_at) : null,
  };
}

export async function loadSessions(
  endpoint?: string,
): Promise<import('./auth-contracts').UserSession[]> {
  const ep = endpoint ?? '/api/v1/auth/sessions';
  const res = await apiGet<unknown[]>(ep, { credentials: 'include' });
  if (!Array.isArray(res)) return [];
  return res
    .map(normalizeSession)
    .filter((s): s is import('./auth-contracts').UserSession => s !== null);
}

export async function revokeSession(
  endpoint: string | undefined,
  sessionId: string,
): Promise<void> {
  const ep = endpoint ?? `/api/v1/auth/sessions/${sessionId}`;
  await apiDelete<void>(ep, { credentials: 'include' });
}

export async function logoutAllSessions(endpoint?: string): Promise<{ revoked: number }> {
  const ep = endpoint ?? '/api/v1/auth/logout-all';
  return await apiPost<{ revoked: number }>(ep, undefined, { credentials: 'include' });
}

export async function changePassword(endpoint: string | undefined, payload: ChangePasswordInput) {
  const ep = endpoint ?? '/api/v1/users/me/password';
  return await apiPost(
    ep,
    {
      current_password: payload.currentPassword,
      new_password: payload.newPassword,
      revoke_other_sessions: payload.revokeOtherSessions,
    },
    { credentials: 'include' },
  );
}
