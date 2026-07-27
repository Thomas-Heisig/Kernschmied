# ADR-0009: Authentication and Authorization

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed to operate in multiple deployment environments with significantly different security requirements.

Examples include:

- Local development
- Internal company networks
- Public internet deployments

Each environment requires different authentication mechanisms while preserving a consistent authorization model.

The platform therefore separates **authentication** (who is the user?) from **authorization** (what is the user allowed to do?).

---

# Problem

Many applications tightly couple authentication and authorization.

Typical examples include:

- permissions embedded inside login providers
- business logic checking JWT claims directly
- role handling duplicated across services
- deployment-specific authentication code scattered throughout the application

These approaches become increasingly difficult to maintain as authentication providers evolve.

Kernschmied must support multiple authentication mechanisms without changing business logic.

---

# Decision

Authentication and authorization are separated into independent architectural layers.

Authentication determines the identity of the caller.

Authorization determines whether the authenticated caller may execute the requested action.

Business services never authenticate users directly.

---

# Architectural Principle

> Authentication identifies.
>
> Authorization decides.

---

# High-Level Architecture

```text
Client

        │

        ▼

Authentication Middleware

        │

        ▼

Authentication Context

        │

        ▼

Authorization Service

        │

        ▼

Business Service
```

---

# Design Goals

The security architecture should provide:

- deployment independence
- provider independence
- centralized authorization
- explicit permissions
- auditability
- extensibility
- deny-by-default behavior

---

# Authentication

Authentication establishes the caller identity.

Typical identity information includes:

- user id
- username
- display name
- authentication method
- roles
- groups
- authentication state

Authentication itself never grants permissions.

---

# Authorization

Authorization determines whether an authenticated user may perform an operation.

Authorization evaluates:

- user
- roles
- permissions
- hierarchy
- deployment profile
- configuration
- requested action

---

# Security Profiles

Authentication behavior depends on the deployment profile.

Supported profiles include:

| Profile | Purpose |
|----------|---------|
| Development | Local development |
| Intranet | Company network |
| Internet | Public deployment |

Each profile defines minimum security requirements.

---

# Development Profile

The development profile prioritizes developer productivity.

Characteristics:

- optional authentication
- local development user
- simplified setup
- testing support

A local user may be injected automatically.

Example:

```text
local-user
```

Development mode must never be enabled unintentionally in production.

---

# Intranet Profile

The intranet profile assumes a trusted internal network.

Typical authentication providers include:

- Active Directory
- LDAP
- Kerberos
- Reverse Proxy Authentication
- SSO

Authentication is required.

Audit logging is enabled.

---

# Internet Profile

Internet deployments require the highest security level.

Typical requirements include:

- HTTPS
- secure cookies
- CSRF protection where applicable
- session authentication
- rate limiting
- HSTS
- secure headers

Authentication is mandatory.

---

# Authentication Providers

Authentication mechanisms should remain replaceable.

Examples include:

- Local Development Provider
- OAuth2
- OpenID Connect
- LDAP
- Active Directory
- SAML
- Future Enterprise Providers

Business services remain independent of the chosen provider.

---

# Authentication Middleware

Authentication is performed before request processing.

Typical request flow:

```text
HTTP Request

↓

Authentication Middleware

↓

Identity Established

↓

Authorization

↓

Endpoint
```

---

# Authentication Context

The middleware creates an Authentication Context.

Example fields include:

- user id
- display name
- authentication provider
- roles
- permissions
- authentication timestamp

The context remains immutable during request processing.

---

# User Context

Business services receive a strongly typed user context.

Typical fields:

- identifier
- authenticated
- administrator
- roles
- permissions
- hierarchy scope

Business services should never inspect JWTs or authentication tokens directly.

---

# Permission Model

Permissions are explicit.

Examples:

- configuration.read
- configuration.write
- chat.create
- chat.delete
- tool.execute
- model.use
- hierarchy.edit

Permissions are evaluated centrally.

---

# Roles

Roles group permissions.

Example:

```text
Administrator

↓

Configuration

↓

Tool Management

↓

User Management
```

Another example:

```text
User

↓

Chat

↓

Models

↓

Own Configuration
```

Roles remain configurable.

---

# Authorization Flow

```text
Request

↓

Authenticated User

↓

Permission Check

↓

Allowed?

↓

Yes → Execute

↓

No → Forbidden
```

---

# Hierarchical Authorization

Permissions may depend on hierarchy.

Examples:

- Workspace
- Project
- Folder
- Chat

A user may have permission within one project but not another.

---

# Configuration Authorization

Administrative configuration requires dedicated permissions.

Typical examples:

- changing runtime configuration
- modifying providers
- enabling tools
- changing deployment settings

Configuration endpoints should never rely solely on client-side checks.

---

# Tool Authorization

Every tool execution is authorized individually.

Authorization may consider:

- user
- deployment profile
- tool category
- workspace
- runtime configuration

Tool permissions remain independent from model permissions.

---

# Model Authorization

Model usage may also require permissions.

Examples:

- local models
- cloud models
- premium providers
- experimental models

The Model Registry exposes only models available to the current user.

---

# API Authorization

Authorization is enforced inside backend services.

Clients may hide unavailable actions for usability, but backend validation remains authoritative.

Client-side authorization is never considered a security mechanism.

---

# Deny by Default

Unknown users, unknown roles, or unknown permissions are denied.

Example:

```text
Permission Missing

↓

Access Denied
```

Explicit permission grants are always required.

---

# Audit Logging

Security-sensitive operations are logged.

Examples include:

- login
- logout
- configuration changes
- permission failures
- administrative actions
- tool execution

Audit records should contain:

- timestamp
- user
- action
- outcome
- request id

---

# Session Management

Authenticated sessions should provide:

- expiration
- renewal
- revocation
- secure storage

Session management depends on the authentication provider but exposes a consistent abstraction to the application.

---

# Security Considerations

The security architecture enforces:

- centralized authorization
- immutable user context
- explicit permissions
- deny-by-default
- provider independence
- backend enforcement

Authentication tokens should never be trusted without validation.

---

# Performance Considerations

Authentication should occur once per request.

Authorization decisions may use cached role and permission information where appropriate.

Permission evaluation should remain deterministic and inexpensive.

---

# Operational Impact

The architecture enables:

- multiple authentication providers
- centralized security configuration
- deployment-specific policies
- enterprise integration
- future federation

Operations teams can adapt authentication mechanisms without modifying business services.

---

# Consequences

## Positive

- Clear separation of concerns
- Provider independence
- Centralized authorization
- Consistent security model
- Easier testing
- Enterprise readiness

## Negative

- Additional abstraction
- Authorization infrastructure
- Permission administration
- More configuration

---

# Alternatives Considered

## Authentication Inside Business Services

Rejected because security logic becomes duplicated throughout the application.

---

## Provider-Specific Authorization

Rejected because business logic would become coupled to authentication providers.

---

## Client-Side Authorization

Rejected because clients cannot enforce security.

Only the backend is authoritative.

---

## Hard-Coded Roles

Rejected because enterprise deployments require configurable permission models.

---

# Risks

Potential risks include:

- incorrect permission assignments
- misconfigured authentication providers
- overly permissive roles
- stale authorization caches

Mitigation strategies include:

- automated testing
- audit logging
- deny-by-default
- centralized permission evaluation
- security reviews

---

# Implementation Notes

The implementation should provide:

- AuthenticationContextMiddleware
- Authentication Context
- User Context
- Authorization Service
- Permission Registry
- Role Management
- Security Profile integration
- Audit Logging

Authentication providers should be replaceable without affecting business services.

---

# Related Decisions

- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0014-Deployment-Profiles]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Security-Architecture]]
- [[Deployment]]

---

## Backend

- [[Authentication]]
- [[Authorization]]
- [[Security]]
- [[Configuration]]

---

## Concepts

- [[Security-Profiles]]
- [[User-Context]]
- [[Permissions]]
- [[Audit-Log]]

---

# Decision Summary

Kernschmied adopts a security architecture that **strictly separates authentication from authorization**.

Authentication establishes the identity of the caller using deployment-specific authentication providers, while authorization centrally evaluates roles, permissions, hierarchy, runtime configuration, and security profiles before allowing access to protected functionality.

All authorization decisions are enforced exclusively by the backend. Business services depend only on a strongly typed user context rather than authentication tokens or provider-specific implementations.

This architecture enables consistent security across development, intranet, and internet deployments while remaining extensible, testable, and suitable for future enterprise authentication providers.

---

Back to [[Home]].
