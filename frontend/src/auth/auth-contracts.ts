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
