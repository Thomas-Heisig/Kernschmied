export interface TenantInfo {
  id: string;
  displayName: string;
}

export interface CurrentUser {
  id: string;
  username: string;
  displayName: string;
  email: string | null;
  authenticated: boolean;
  developmentSession: boolean;
  passwordLoginAvailable: boolean;
  tenant: TenantInfo | null;
}

export interface OwnProfile extends CurrentUser {}

export interface UpdateOwnProfileInput {
  displayName?: string;
  email?: string | null;
}

export interface UserPreferences {
  schemaVersion: "1.0";
  language: string;
  timezone: string;
  theme: "system" | "light" | "dark";
  density: "comfortable" | "compact";
  defaultView: string | null;
  notificationsEnabled: boolean;
  updatedAt: string | null;
}

export interface UpdateUserPreferencesInput {
  language?: string;
  timezone?: string;
  theme?: "system" | "light" | "dark";
  density?: "comfortable" | "compact";
  defaultView?: string | null;
  notificationsEnabled?: boolean;
}

export interface UserSession {
  schemaVersion: "1.0";
  id: string;
  authenticationMethod: string;
  createdAt: string;
  expiresAt: string;
  lastSeenAt: string | null;
  revokedAt: string | null;
  current: boolean;
  active: boolean;
  ipAddress: string | null;
  userAgent: string | null;
}
