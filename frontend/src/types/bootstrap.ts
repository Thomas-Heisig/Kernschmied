export interface AppBootstrap {
  security: {
    profile: 'development' | 'intranet' | 'internet';
    authenticationRequired: boolean;
    developmentIdentityActive: boolean;
    availableLoginMethods: string[];
  };
  features: {
    developmentAdminLogin: boolean;
    // derived convenience flags computed by normalizer
    developmentLoginAvailable?: boolean;
    selfRegistration?: boolean;
    registrationRequiresInvitation?: boolean;
  };
  endpoints: {
    authLogin?: string;
    authLogout?: string;
    authMe?: string;
    authDevelopmentLogin?: string;
    authRegister?: string;
    userProfile?: string;
    userPreferences?: string;
    uiSchema?: string;
    hierarchy?: string;
  };
  schemaVersion?: string;
  apiVersion?: string;
  requestId?: string | null;
}
