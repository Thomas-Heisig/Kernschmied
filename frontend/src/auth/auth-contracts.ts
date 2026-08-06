export interface CurrentUser {
  id: string;
  username: string;
  displayName: string;
  email: string | null;
  tenant:
    | {
        id: string;
        displayName: string;
      }
    | null;
  roles: string[];
  authenticated: boolean;
  developmentSession: boolean;
  passwordLoginAvailable: boolean;
  createdAt: string | null;
  lastLoginAt: string | null;
  schemaVersion: string;
}

export interface OwnProfile {
  id: string;
  username: string;
  displayName: string;
  email: string | null;
  tenant:
    | {
        id: string;
        displayName: string;
      }
    | null;
  roles: string[];
  createdAt: string | null;
  lastLoginAt: string | null;
  schemaVersion: string;
}

export interface UpdateOwnProfileInput {
  displayName?: string;
  email?: string | null;
}

export interface UserPreferences {
  language: "de" | "en";
  timezone: string;
  theme: "system" | "light" | "dark";
  compactMode: boolean;
  defaultView: string | null;
  notificationsEnabled: boolean;
  revision: number;
  updatedAt: string | null;
  schemaVersion: string;
}

export interface UpdateUserPreferencesInput {
  language?: "de" | "en";
  timezone?: string;
  theme?: "system" | "light" | "dark";
  compactMode?: boolean;
  defaultView?: string | null;
  notificationsEnabled?: boolean;
  revision?: number;
}

export interface UserSession {
  id: string;
  current: boolean;
  authenticationMethod: string;
  ipAddress: string | null;
  userAgent: string | null;
  createdAt: string;
  lastSeenAt: string | null;
  expiresAt: string;
  revokedAt: string | null;
}

export interface ChangePasswordInput {
  currentPassword: string;
  newPassword: string;
  revokeOtherSessions: boolean;
}
