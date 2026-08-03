# ADR-0034: Authentifizierung, Sitzungen und Benutzerverwaltung

Status: Accepted

Datum: 2026-08-03

## Kontext

- Das Projekt verfügt derzeit über einen Development-Fallback-Administrator (`bootstrap-admin`) in der Hierarchie, aber keine persistente, versionierte Benutzerverwaltung.
- Es fehlen Login/Logout-Endpunkte, persistente Sessions und Session-Management.
- Benutzer sind eng mit Hierarchie-Knoten verknüpft; diese Beziehung muss erhalten bleiben, ohne Identität und Navigationsdaten zu vermischen.
- Es existieren drei Betriebsprofile mit unterschiedlichen Sicherheitsanforderungen: `development`, `intranet`, `internet`.

## Entscheidung

Wir führen ein erstes, sicheres und erweiterbares Benutzer- und Sessionmodell ein, das folgende Komponenten umfasst:

- HTTP Request
  → Authentication Middleware
  → Session/Identity Resolver
  → UserContext
  → HierarchyActor (Adapter)
  → serverseitige Autorisierung (Dependencies)
  → Service Layer
  → Repository / Datenbank

Authentifizierung und Autorisierung bleiben strikt getrennte Verantwortlichkeiten. Das Frontend trifft keine Autorisierungsentscheidungen — das Backend validiert jede Aktion.

## Authentifizierungsverfahren (MVP)

- Serverseitige Session-Authentifizierung über ein HttpOnly-Cookie (`kernschmied_session`).
- SameSite-Policy gesetzt; `Secure` abhängig vom Betriebsprofil (production/internet: true).
- Keine JWT im LocalStorage; Session-Token nur im Cookie und serverseitig gehasht gespeichert.
- CSRF-Token an Session gebunden; Frontend sendet `X-CSRF-Token` für schreibende Requests.

## Passwortverfahren

- Verwendung einer etablierten Passwort-Hashing-Bibliothek (Argon2id empfohlen).
- Salt- und Parametrisierung durch die Bibliothek; keine eigene Kryptographie.
- Passwort-Hashes werden niemals an das Frontend geliefert oder in Logs aufgenommen.

## Betriebsprofile

- development: automatischer neutraler Bootstrap-Administrator zulässig; Development-Fallback nur wenn ausdrücklich konfiguriert; deutliche Startwarnung.
- intranet: Session-Login erforderlich; Auditierung aktiviert; kein Development-Fallback.
- internet: HTTPS erforderlich; `Secure` Cookies; Session-Rotation; Login-Rate-Limiting; CSRF-Schutz und strengere Untergrenzen.

## Datenmodell (Kurzüberblick)

- `users` (id, username, display_name, email, password_hash, is_active, is_system_admin, must_change_password, failed_login_attempts, locked_until, last_login_at, created_at, updated_at, created_by, updated_by, schema_version)
- `auth_sessions` (id, user_id, session_token_hash, created_at, expires_at, last_seen_at, revoked_at, ip_address, user_agent, csrf_token_hash, schema_version)
- `user_preferences` (id, user_id, locale, timezone, theme, accent_color, compact_mode, default_model_id, default_workspace_id, preferences_json, revision, created_at, updated_at, schema_version)
- Rollen- und Berechtigungs-Modelle (`roles`, `permissions`, `user_roles`, `role_permissions`) mit klarer Normalisierung; keine Wildcard-`*`-Rollen.

## Audit

- Audit-Ereignisse für Auth- und User-Operationen (login.succeeded, login.failed, logout, password.changed, session.revoked, user.created, user.updated, user.disabled, user.roles.changed, user.preferences.updated).
- Audit-Daten enthalten actor_user_id, target_user_id, request_id, ip_address, timestamp, changed_fields; keine Secrets.

## Alternativen (abgelehnt für MVP)

- JWT im LocalStorage: abgelehnt wegen XSS-Risiko und fehlender Server-side Revocation.
- Öffentliche Registrierung: nicht Teil des MVP.
- OAuth/OIDC: wird als mögliche Erweiterung dokumentiert.

## Konsequenzen

- Neue Tabellen und Migrationen erforderlich (SQLite- und PostgreSQL-kompatibel).
- Session-Cleanup-Job und Audit-Log werden benötigt.
- Bestehender Development-Hierarchie-Knoten `bootstrap-admin` wird idempotent mit persistiertem Admin-Benutzer verknüpft.
- Frontend erhält neue Auth-Provider, Loginseite und Benutzermenü im Header.

## Risiken

- Development-Fallback muss klar und explizit sein; unbeabsichtigte Aktivierung in produktiven Profilen muss verhindert werden.
- Migrationen müssen SQLite-kompatibel bleiben und vorhandene Chats/Hierarchiedaten intakt lassen.

## Nachfolgende Aufgaben

- Migrationen erstellen (Users, AuthSessions, UserPreferences, Roles/Permissions).
- Backend-Services: PasswordService, AuthenticationService, SessionService, UserService.
- API-Endpunkte unter `/api/v1/auth` und `/api/v1/users` implementieren.
- Frontend: AuthProvider, LoginPage, UserMenu und UserManagement-Views.
