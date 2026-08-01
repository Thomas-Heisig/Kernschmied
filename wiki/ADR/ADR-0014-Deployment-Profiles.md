# ADR-0014: Deployment Profiles

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

## Context

Kernschmied is intended to run in very different operational environments while maintaining a single code base.

Typical deployment scenarios include:

- Local development
- Small office installations
- Company intranets
- Dedicated on-premise servers
- Internet-facing enterprise installations
- Future cloud deployments

Each environment has fundamentally different requirements regarding:

- authentication
- transport security
- logging
- auditing
- performance
- administration
- user management
- monitoring

A deployment architecture based solely on configuration flags often results in inconsistent security and unpredictable runtime behavior.

---

## Problem

Applications frequently allow arbitrary combinations of security settings.

Examples include:

- authentication disabled in production
- HTTPS optional on public deployments
- unrestricted CORS
- missing audit logging
- insecure cookies
- debug endpoints exposed publicly

Such configurations create security vulnerabilities and increase operational complexity.

The platform requires predefined deployment profiles with mandatory security guarantees.

---

## Decision

Kernschmied introduces **Deployment Profiles**.

Each deployment profile defines a minimum security baseline that cannot be weakened through runtime configuration.

Business functionality remains identical across profiles.

Only operational characteristics differ.

---

## Architectural Principle

> Deployment profiles define operational behavior.
>
> They never change business logic.

---

## Supported Profiles

Kernschmied currently defines three deployment profiles.

| Profile     | Purpose                        |
| ----------- | ------------------------------ |
| development | Local development              |
| intranet    | Internal enterprise deployment |
| internet    | Public internet deployment     |

Additional profiles may be introduced in future releases.

---

## High-Level Architecture

```text
Bootstrap

        │

Deployment Profile

        │

        ▼

Security Middleware

        │

        ▼

Authentication

        │

        ▼

Authorization

        │

        ▼

Business Services

```

---

## Profile Selection

The deployment profile is selected during application startup.

Example:

```text
APP_PROFILE=development

```

The profile becomes immutable until the application restarts.

---

## Why Immutable?

Changing deployment profiles at runtime could:

- invalidate security assumptions
- break active sessions
- alter middleware behavior
- create inconsistent authorization

Therefore the profile is part of bootstrap configuration.

---

## Development Profile

The development profile prioritizes productivity.

Typical characteristics include:

- simplified authentication
- local development user
- verbose logging
- debugging support
- automatic reload
- local SQLite database
- relaxed CORS
- optional HTTPS

Development mode should only be used on trusted development systems.

---

## Development Authentication

Typical authentication:

```text
Developer

↓

Development Middleware

↓

local-user

↓

Application

```

This eliminates unnecessary setup during local development.

---

## Development Logging

Logging is intentionally verbose.

Typical log level:

```text
DEBUG

```

Additional diagnostic information may be enabled.

---

## Intranet Profile

The intranet profile targets trusted internal company networks.

Typical characteristics include:

- mandatory authentication
- audit logging
- HTTPS recommended
- enterprise identity providers
- centralized logging
- production database
- restricted administration

The intranet profile assumes organizational network protection but still enforces authentication.

---

## Typical Authentication Providers

Examples include:

- LDAP
- Active Directory
- Kerberos
- OAuth2
- OpenID Connect
- Reverse Proxy Authentication

Authentication providers remain interchangeable.

---

## Internet Profile

The internet profile represents the highest security level.

Characteristics include:

- mandatory HTTPS
- secure cookies
- HSTS
- rate limiting
- session authentication
- strict CORS
- audit logging
- security headers
- production logging

Security requirements cannot be disabled.

---

## Security Comparison

| Feature        | Development | Intranet    | Internet  |
| -------------- | ----------- | ----------- | --------- |
| Authentication | Optional    | Required    | Required  |
| HTTPS          | Optional    | Recommended | Mandatory |
| Audit Logging  | Optional    | Required    | Required  |
| Rate Limiting  | Optional    | Recommended | Required  |
| Secure Cookies | Optional    | Recommended | Required  |
| HSTS           | Disabled    | Optional    | Required  |
| Strict CORS    | Relaxed     | Restricted  | Strict    |

---

## CORS Policy

Each deployment profile defines its own CORS policy.

Development:

```text
localhost

127.0.0.1

```

Intranet:

```text
Corporate Domains

```

Internet:

```text
Explicit Allow List

```

Wildcards should never be used in internet deployments.

---

## HTTPS Requirements

Development:

Optional.

Intranet:

Strongly recommended.

Internet:

Mandatory.

The backend should refuse insecure production deployments whenever possible.

---

## HTTP Security Headers

Internet deployments automatically enable headers including:

- HSTS
- X-Content-Type-Options
- X-Frame-Options
- Referrer-Policy
- Content-Security-Policy (where applicable)

These headers are considered part of the deployment profile rather than runtime configuration.

---

## Rate Limiting

Rate limiting depends on the deployment profile.

Development:

Usually disabled.

Intranet:

Configurable.

Internet:

Mandatory.

The implementation may evolve without changing the deployment architecture.

---

## Session Management

Session handling varies between profiles.

Development:

Simplified sessions.

Intranet:

Enterprise session handling.

Internet:

Secure authenticated sessions.

Business services remain unaware of session implementation details.

---

## Audit Logging

Administrative operations are audited in:

- intranet
- internet

Typical audit events include:

- login
- logout
- configuration changes
- permission failures
- administrative actions
- tool execution

Development deployments may reduce audit verbosity.

---

## Bootstrap Visibility

The frontend receives deployment information through the bootstrap endpoint.

Example:

```json
{
  "environment": {
    "profile": "internet"
  }
}
```

The frontend may adapt presentation accordingly.

The frontend never decides security.

---

## Frontend Behavior

The deployment profile may influence:

- available diagnostics
- development tools
- debug indicators
- feature visibility
- informational banners

Authorization decisions always remain backend responsibilities.

---

## Configuration Restrictions

Certain configuration values cannot override deployment guarantees.

Examples:

Internet profile cannot disable:

- authentication
- HTTPS
- secure cookies
- HSTS
- audit logging

Security baselines are enforced by the platform.

---

## Monitoring

Production deployments should integrate with monitoring solutions.

Typical metrics include:

- request rate
- error rate
- authentication failures
- provider failures
- latency
- resource usage

Monitoring configuration depends on deployment profile.

---

## Logging

Recommended logging levels:

Development:

```text
DEBUG

```

Intranet:

```text
INFO

```

Internet:

```text
INFO

WARNING

ERROR

```

Sensitive production environments should avoid excessive debug logging.

---

## Operational Impact

Deployment profiles simplify operations by providing predefined security baselines.

Administrators no longer need to manually configure dozens of security options for every installation.

---

## Security Considerations

Deployment profiles enforce:

- minimum security guarantees
- immutable startup configuration
- centralized middleware selection
- consistent authentication
- consistent transport security

Security should never depend upon frontend behavior.

---

## Performance Considerations

Profile-specific optimizations include:

- development diagnostics
- production caching
- optimized logging
- rate limiting
- middleware configuration

Performance tuning never weakens security requirements.

---

## Consequences

## Positive

- Consistent deployments
- Predictable security
- Simplified administration
- Easier documentation
- Reduced configuration errors
- Enterprise readiness

## Negative

- Less runtime flexibility
- Additional startup validation
- More operational documentation

---

## Alternatives Considered

## Individual Security Flags

Rejected because unsafe combinations become possible.

---

## Environment Variables Only

Rejected because relationships between settings become difficult to maintain.

---

## Runtime Profile Switching

Rejected because middleware behavior cannot safely change while requests are active.

---

## Separate Code Bases

Rejected because duplicated functionality significantly increases maintenance effort.

---

## Risks

Potential risks include:

- incorrect profile selection
- insecure development deployments exposed publicly
- incomplete production hardening

Mitigation includes:

- startup validation
- immutable deployment profile
- documentation
- automated deployment checks
- security reviews

---

## Implementation Notes

The implementation should provide:

- Deployment Profile enumeration
- startup validation
- profile-aware middleware
- CORS configuration
- HTTPS enforcement
- security headers
- bootstrap exposure
- audit logging integration

Business services should remain completely independent from deployment-specific implementation details.

---

## Related Decisions

- [[ADR-0002-Bootstrap]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0009-Authentication-and-Authorization]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0013-Error-Handling-and-Logging]]

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Security-Architecture]]
- [[Deployment]]

---

## Backend

- [[Bootstrap]]
- [[Configuration]]
- [[Authentication]]
- [[Authorization]]

---

## Frontend

- [[Frontend-Overview]]
- [[API-Client]]

---

## Concepts

- [[Deployment-Profiles]]
- [[Security-Profiles]]
- [[Runtime-Configuration]]
- [[Bootstrap]]

---

## Decision Summary

Kernschmied adopts a **deployment profile architecture** that defines immutable operational environments with predefined security guarantees.

The three initial profiles—**development**, **intranet**, and **internet**—share the same business functionality while differing in authentication, transport security, logging, auditing, monitoring, and operational behavior.

By enforcing minimum security baselines at startup rather than relying on mutable runtime configuration, the platform provides predictable deployments, simplifies administration, and ensures that production environments cannot accidentally operate with development-level security.

---

Back to [[Home]].
