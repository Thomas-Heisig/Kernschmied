# Internet Deployment

The **Internet** deployment profile is designed for securely operating Kernschmied in public or untrusted network environments. Unlike the Development profile, which prioritizes developer productivity, or the Intranet profile, which assumes a trusted organizational network, the Internet profile enforces the platform's highest security standards.

The Internet profile protects both users and infrastructure through strong authentication, encrypted communication, strict authorization, secure session handling, rate limiting, audit logging, and comprehensive validation.

Although operational policies become significantly stricter, the application's architecture, APIs, schemas, registries, and contracts remain identical to every other deployment profile.

---

## Goals

The Internet deployment profile is designed to provide:

- Secure public operation
- Strong authentication
- Strict authorization
- Encrypted communication
- Attack resistance
- Complete auditability
- Stable public contracts
- Enterprise-grade security

---

## Design Philosophy

The deployment profile influences operational behavior—not application architecture.

```text
Application Core
        │
        ▼
Deployment Profile
        │
        ▼
Internet Policies

```

Business logic, APIs, schemas, and runtime behavior remain identical across deployment profiles.

---

## High-Level Architecture

```text
Internet

        │

        ▼

HTTPS Reverse Proxy

        │

        ▼

FastAPI Backend

        │

        ▼

Runtime Configuration

        │

        ▼

Database

        │

        ▼

Model Providers

```

Every incoming request passes through multiple security layers before reaching application services.

---

## Typical Environment

A typical Internet deployment consists of:

- HTTPS reverse proxy
- FastAPI backend
- PostgreSQL database
- dedicated storage
- secure AI providers
- centralized logging
- monitoring infrastructure

Individual components may be distributed across multiple servers while preserving the same architecture.

---

## Secure Communication

All external communication must use encrypted transport.

```text
Client

↓

HTTPS

↓

Reverse Proxy

↓

Backend

```

Unencrypted HTTP traffic should either be rejected or permanently redirected to HTTPS.

---

## TLS

Transport Layer Security protects:

- authentication credentials
- session cookies
- API requests
- streamed responses
- uploaded files
- configuration traffic

TLS termination typically occurs at the reverse proxy.

---

## Reverse Proxy

A reverse proxy provides the first security boundary.

Typical responsibilities include:

- TLS termination
- request routing
- compression
- header normalization
- rate limiting
- request size limits

The backend remains focused on business logic.

---

## Authentication

Internet deployments require authenticated users.

Typical authentication methods include:

- username/password
- enterprise identity providers
- OAuth
- OpenID Connect
- SAML

Authentication must never be optional.

---

## Session Management

Authenticated sessions must be protected.

Typical requirements include:

- secure cookies
- HTTP-only cookies
- SameSite protection
- session expiration
- session renewal
- logout handling

Session management is enforced independently of business services.

---

## Authorization

Every request undergoes server-side authorization.

```text
Authenticated User

↓

Authorization

↓

Business Operation

```

Authorization is never delegated to the frontend.

---

## Runtime Configuration

Business configuration continues to use the Runtime Configuration system.

Administrators may update:

- prompts
- models
- tools
- UI schemas
- hierarchy
- feature flags

Configuration changes remain fully validated and audited.

---

## Environment Variables

Only infrastructure settings belong in environment variables.

Typical examples include:

- deployment profile
- database connection
- TLS settings
- secret keys
- external service endpoints

Business configuration remains database-driven.

---

## Database

Production Internet deployments typically use PostgreSQL.

```text
Backend

↓

PostgreSQL

↓

Configuration

Hierarchy

Audit

Application Data

```

The architecture remains compatible with SQLite for development environments.

---

## AI Providers

The Model Registry abstracts AI providers.

Supported deployment strategies include:

- local inference
- private inference servers
- secure API gateways
- self-hosted model clusters

Provider implementations remain interchangeable.

---

## API Security

Every API request is validated before processing.

Validation includes:

- authentication
- authorization
- schema validation
- request validation
- rate limiting
- input sanitization

Malformed requests never reach business logic.

---

## Streaming Security

Streaming endpoints follow the same security policies as REST endpoints.

```text
Authenticated Request

↓

Authorization

↓

SSE Stream

↓

Client

```

Streaming never bypasses authentication or authorization.

---

## CORS

Cross-Origin Resource Sharing is configured explicitly.

Only trusted origins should be permitted.

Example:

```text
Allowed Origin

↓

CORS Validation

↓

Request Accepted

```

Unknown origins are rejected.

---

## Rate Limiting

Rate limiting protects the platform against abuse.

Typical strategies include:

- requests per minute
- concurrent sessions
- streaming limits
- authentication limits
- upload limits

Rate limiting policies depend on deployment requirements.

---

## Request Validation

Every request is validated before execution.

Validation includes:

- JSON schema
- required fields
- value types
- parameter ranges
- identifier formats

Invalid requests generate structured error responses.

---

## Audit Logging

Administrative operations are fully audited.

Typical audit information includes:

- authenticated user
- timestamp
- operation
- affected resource
- configuration changes
- revision updates

Audit records support compliance and incident investigation.

---

## Logging

Operational logging should include:

- startup information
- security events
- authentication failures
- authorization failures
- structured errors
- application warnings

Sensitive information must never be written to logs.

---

## Secrets

Secrets must never be stored in runtime configuration.

Examples include:

- signing keys
- API credentials
- encryption keys
- database passwords

Secrets belong to protected infrastructure configuration.

---

## Plugin Security

Plugins operate under the same security rules as the core platform.

Requirements include:

- manifest validation
- compatibility verification
- schema validation
- registry validation
- authorization enforcement

Plugins cannot bypass platform security.

---

## Error Handling

Internet deployments always return structured error responses.

Example:

```text
code

message

details

request_id

```

Internal implementation details are never exposed to external users.

---

## Monitoring

Operational monitoring typically includes:

- application health
- request latency
- resource utilization
- authentication failures
- error rates
- registry status
- database availability

Monitoring improves reliability without changing application behavior.

---

## Backup Strategy

Internet deployments should include regular backups for:

- runtime configuration
- hierarchy
- audit logs
- application data
- uploaded assets

Backup procedures should be tested periodically.

---

## High Availability

The Internet profile supports multi-instance deployments.

```text
Load Balancer

      │

 ┌────┴────┐

 ▼         ▼

Backend   Backend

      │

      ▼

 PostgreSQL

```

Shared runtime configuration and revision tracking keep all instances synchronized.

---

## Security Principles

The Internet profile enforces several mandatory principles.

- HTTPS only
- Strong authentication
- Server-side authorization
- Input validation
- Structured errors
- Audit logging
- Revision tracking
- Least privilege
- Defense in depth

These principles are not optional.

---

## Differences from Other Profiles

| Feature          | Development | Intranet    | Internet |
| ---------------- | ----------- | ----------- | -------- |
| HTTPS            | Optional    | Recommended | Required |
| Authentication   | Simplified  | Required    | Required |
| Session Security | Basic       | Strong      | Strict   |
| Rate Limiting    | Optional    | Recommended | Required |
| Audit Logging    | Optional    | Required    | Required |
| Public Access    | No          | Limited     | Yes      |
| Debug Features   | Enabled     | Limited     | Disabled |

The underlying application architecture remains identical.

---

## Future Extensions

The Internet deployment profile supports future enhancements including:

- Web Application Firewall integration
- distributed rate limiting
- multi-factor authentication
- hardware security modules
- zero-trust networking
- distributed session management
- security analytics
- automated threat detection

These enhancements strengthen operational security without changing application contracts.

---

## Relationship to Other Deployment Profiles

The Internet profile shares the same core architecture with:

- [[Development]]
- [[Intranet]]

Only deployment policies and operational security differ.

---

## Related Documentation

## Deployment

- [[Deployment Overview]]
- [[Development]]
- [[Intranet]]

---

## Architecture

- [[Security-Architecture]]
- [[Configuration-Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Request-Lifecycle]]

---

## Backend

- [[Security]]
- [[Bootstrap]]
- [[Configuration]]
- [[Model-Registry]]
- [[Tool-Registry]]

---

## Concepts

- [[Runtime Configuration]]
- [[Plugin-System]]
- [[Dynamic-UI]]
- [[Schema Versioning]]

---

## Summary

The Internet deployment profile enables Kernschmied to operate securely in public network environments by enforcing strong authentication, encrypted communication, strict authorization, comprehensive validation, audit logging, and robust operational security practices. While security policies are significantly stricter than in other deployment profiles, the platform preserves identical APIs, schemas, registries, runtime configuration, and application architecture.

By separating operational security from business logic and maintaining stable contracts across all environments, the Internet profile delivers a secure, scalable, and enterprise-ready foundation for exposing Kernschmied services to external users and systems.

---

Back to [[Home]].
