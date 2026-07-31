# ADR-0004: Security Profiles and Deployment Modes

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed to operate in different environments throughout its lifecycle.

The same application may be used:

- by a single developer on a local workstation,
- within a trusted company intranet,
- or as an Internet-facing production system.

Each environment has fundamentally different security requirements.

A development workstation values convenience and rapid iteration.

An internal company deployment requires authentication, authorization, and auditing.

A public Internet deployment requires significantly stronger security controls, stricter defaults, and hardened infrastructure.

Attempting to satisfy every environment using a single static security configuration would either:

- unnecessarily hinder development, or
- expose production systems to unacceptable risks.

The platform therefore requires a deterministic mechanism for selecting security behavior based on the deployment environment.

---

# Problem

Many applications accumulate numerous security-related feature flags.

Typical examples include:

- ENABLE_AUTH
- ENABLE_CORS
- ENABLE_TLS
- ENABLE_RATE_LIMIT
- DISABLE_LOGIN
- DEV_MODE
- ALLOW_DEBUG
- ENABLE_AUDIT

Over time these flags become difficult to understand because they interact in unexpected ways.

This creates several problems.

---

## Inconsistent Deployments

Two production systems may behave differently simply because one forgotten environment variable was configured differently.

---

## Security Drift

Over time production systems may accidentally become less secure.

---

## Weak Defaults

Optional security features are frequently disabled "temporarily" and later forgotten.

---

## Complex Configuration

Administrators must understand dozens of unrelated options instead of selecting a deployment profile.

---

## Difficult Testing

Every combination of feature flags potentially creates another security configuration that must be tested.

---

# Decision

Kernschmied adopts **Security Profiles**.

A deployment profile defines a minimum security baseline.

The platform currently defines three profiles:

- Development
- Intranet
- Internet

Each profile represents a complete security policy rather than a collection of independent feature flags.

---

# Architectural Principle

> **Deployment determines the minimum security baseline.**
>
> Runtime configuration may strengthen security, but it must never weaken the guarantees established by the active deployment profile.

---

# High-Level Architecture

```text
Application Startup

        │

        ▼

Bootstrap Configuration

        │

        ▼

Deployment Profile

        │

        ▼

Security Profile

        │

        ▼

Authentication

Authorization

CORS

Rate Limiting

Headers

Sessions

TLS

Audit

Logging
```

---

# Why Profiles Instead of Feature Flags?

Profiles provide several important advantages.

## Predictability

Every deployment behaves consistently.

---

## Reduced Complexity

Operators choose one deployment mode rather than configuring many unrelated switches.

---

## Easier Documentation

Each deployment profile has clearly defined expectations.

---

## Safer Defaults

Security starts from a hardened baseline instead of an insecure one.

---

## Easier Auditing

Security reviews verify profile compliance instead of individual settings.

---

# Deployment Profiles

---

# Development

The Development profile is intended exclusively for local development.

Its primary goals are:

- fast development
- debugging
- local testing
- experimentation

Typical characteristics include:

- simplified authentication
- local developer identity
- verbose logging
- debugging enabled
- development diagnostics
- local HTTP permitted
- relaxed CORS (configurable)
- reduced caching

Development is **never** intended for public deployment.

---

# Intranet

The Intranet profile targets trusted organizational networks.

Typical environments include:

- company LAN
- VPN
- internal servers
- isolated datacenters

Characteristics include:

- authentication required
- authorization enabled
- audit logging
- session management
- HTTPS recommended
- production logging
- restricted CORS
- configuration auditing

This profile assumes authenticated users inside a controlled environment.

---

# Internet

The Internet profile is intended for publicly accessible deployments.

Security takes precedence over convenience.

Typical characteristics include:

- HTTPS required
- authenticated sessions
- secure cookies
- CSRF protection (where applicable)
- strict CORS policy
- rate limiting
- hardened HTTP headers
- comprehensive audit logging
- request tracing
- production logging
- security monitoring

Public deployments should always use this profile.

---

# Minimum Security Guarantees

Every profile defines a minimum security baseline.

The runtime configuration system may **increase** security but must never reduce it below the profile guarantees.

Example:

```text
Internet Profile

↓

HTTPS Required

↓

Runtime Configuration

↓

Cannot Disable HTTPS
```

---

# Bootstrap Responsibility

The deployment profile belongs to the bootstrap configuration.

It is determined before the application loads runtime configuration because security must already be established before processing business data.

The deployment profile therefore belongs in infrastructure configuration rather than database-managed runtime configuration.

---

# Runtime Configuration

Runtime configuration may adjust security-related behavior where permitted.

Examples include:

- session timeout
- password policy
- MFA requirements
- allowed identity providers
- audit retention
- login banner

However, runtime configuration may never violate the active deployment profile.

---

# Authentication

Authentication behavior depends on the selected profile.

## Development

Authentication may be simplified.

Typical examples:

- fixed developer identity
- local mock authentication
- development-only login

---

## Intranet

Authentication is mandatory.

Supported mechanisms may include:

- local accounts
- LDAP
- Active Directory
- OpenID Connect

---

## Internet

Authentication must be production-grade.

Future integrations may include:

- OpenID Connect
- OAuth2
- SAML
- Enterprise Identity Providers
- Multi-Factor Authentication

---

# Authorization

Authorization is independent of deployment.

Every request requiring protected resources must be authorized by the backend.

The frontend never makes authorization decisions.

---

# Transport Security

Development:

- local HTTP permitted

Intranet:

- HTTPS strongly recommended

Internet:

- HTTPS mandatory

Public deployments must never expose unsecured HTTP endpoints except for explicit redirection.

---

# CORS

CORS behavior depends on the deployment profile.

Development may permit configurable local origins.

Intranet allows only approved organizational origins.

Internet restricts origins to explicitly configured production domains.

Wildcard origins are not appropriate for Internet deployments.

---

# Session Management

Session behavior depends on the deployment profile.

Examples include:

- cookie security
- idle timeout
- absolute timeout
- secure cookie attributes
- SameSite policy

Internet deployments should always use secure session cookies.

---

# HTTP Security Headers

The Internet profile should enable modern security headers including:

- Content Security Policy
- X-Content-Type-Options
- Referrer Policy
- Permissions Policy
- X-Frame-Options (or CSP equivalent)

These headers reduce common browser-based attack vectors.

---

# Rate Limiting

Rate limiting is optional in Development.

Recommended in Intranet.

Mandatory in Internet deployments.

Rate limiting helps mitigate:

- brute-force attacks
- resource exhaustion
- abusive API usage

---

# Audit Logging

Development logging focuses on diagnostics.

Intranet introduces audit trails for administrative actions.

Internet deployments require comprehensive auditing for security-relevant events.

Typical audit events include:

- authentication
- authorization failures
- configuration changes
- administrative actions
- security events

---

# Secrets

Secrets are always part of bootstrap configuration.

Examples include:

- encryption keys
- session secrets
- signing keys
- TLS certificates
- database credentials

Secrets must never be stored in runtime business configuration.

---

# Failure Handling

Security initialization failures are fatal.

Examples include:

- missing signing key
- invalid TLS configuration
- unsupported deployment profile
- invalid authentication configuration

The application should fail during startup rather than operate with weakened security.

---

# Consequences

## Positive

### Predictable Security

Each deployment behaves consistently.

---

### Reduced Configuration Complexity

Administrators configure a deployment profile instead of many unrelated flags.

---

### Better Security Reviews

Auditors evaluate a small number of well-defined profiles.

---

### Safer Defaults

Security features cannot be accidentally disabled below the deployment baseline.

---

### Easier Maintenance

Future security improvements can be incorporated into profile definitions.

---

## Negative

### Less Flexibility

Operators cannot arbitrarily disable security mechanisms.

This restriction is intentional.

---

### Additional Documentation

Each deployment profile must be clearly documented and tested.

---

# Alternatives Considered

## Independent Feature Flags

Advantages:

- flexible
- familiar

Disadvantages:

- inconsistent deployments
- security drift
- configuration complexity

Rejected.

---

## Runtime-Only Security Configuration

Advantages:

- centralized administration

Disadvantages:

- bootstrap paradox
- insecure initialization
- difficult enforcement

Rejected.

---

## Separate Applications

Maintaining independent builds for development and production.

Advantages:

- specialized deployments

Disadvantages:

- duplicated code
- inconsistent behavior
- increased maintenance

Rejected.

---

# Risks

Potential risks include:

- selecting the wrong deployment profile
- incomplete profile definitions
- insufficient documentation
- outdated security defaults

Mitigation strategies include:

- typed bootstrap configuration
- startup validation
- automated integration tests
- deployment documentation
- security reviews

---

# Implementation Notes

The implementation should provide:

- strongly typed security profiles
- immutable deployment mode after startup
- centralized security middleware
- profile-aware dependency injection
- startup diagnostics
- integration tests for every deployment profile

Runtime configuration must always be validated against the active profile before activation.

---

# Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0005-Deny-by-Default-Security]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Security-Architecture]]
- [[Deployment-Architecture]]
- [[Bootstrap-Lifecycle]]

---

## Backend

- [[Security]]
- [[Authentication]]
- [[Authorization]]
- [[Configuration]]

---

## Concepts

- [[Deployment-Profiles]]
- [[Runtime-Configuration]]
- [[Audit-Logging]]
- [[Dependency-Injection]]

---

# Decision Summary

Kernschmied adopts **Security Profiles** to provide deterministic and environment-specific security behavior.

The deployment profile selected during bootstrap establishes a non-negotiable minimum security baseline for the application.

Runtime configuration may strengthen security but can never reduce the guarantees defined by the active profile.

This approach provides predictable deployments, simpler operations, stronger defaults, and a secure foundation for running Kernschmied in development, intranet, and Internet environments.

---

Back to [[Home]].
