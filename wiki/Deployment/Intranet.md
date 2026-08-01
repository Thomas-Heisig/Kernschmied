# Intranet Deployment

The **Intranet** deployment profile is intended for organizations that operate Kernschmied inside a trusted corporate network while still requiring professional security, centralized administration, and full auditability.

Unlike the Development profile, which prioritizes developer productivity, the Intranet profile assumes real users, production data, and operational responsibilities. At the same time, it does not require all security measures that are necessary for Internet-facing deployments because network access is already restricted by organizational infrastructure.

The Intranet profile provides a balance between usability, performance, and enterprise security while preserving the same application architecture, APIs, schemas, and runtime behavior used in every other deployment profile.

---

## Goals

The Intranet deployment profile is designed to provide:

- Secure internal operation
- Enterprise authentication
- Complete auditability
- Centralized administration
- Stable public contracts
- Efficient internal communication
- Operational reliability
- Future scalability

---

## Design Philosophy

Deployment profiles influence operational policies—not application architecture.

```text
Application Core
        │
        ▼
Deployment Profile
        │
        ▼
Intranet Policies

```

Business logic, runtime configuration, APIs, registries, schemas, and contracts remain identical across all deployment profiles.

---

## High-Level Architecture

```text
Corporate Network

        │

        ▼

Internal Reverse Proxy

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

Only authenticated internal users may access the platform.

---

## Typical Environment

A typical intranet deployment consists of:

- corporate network
- internal DNS
- reverse proxy
- FastAPI backend
- PostgreSQL database
- centralized authentication
- internal AI providers
- enterprise monitoring

The exact infrastructure depends on organizational requirements.

---

## Trusted Network

The Intranet profile assumes that the application is deployed inside an organization's controlled network.

Typical protection mechanisms include:

- corporate firewall
- VPN
- network segmentation
- internal routing
- restricted administrative access

Network trust reduces exposure but does not replace application security.

---

## Secure Communication

Internal communication should use encrypted transport whenever practical.

```text
User

↓

HTTPS

↓

Reverse Proxy

↓

Backend

```

Even within trusted networks, HTTPS is recommended to protect credentials and session data.

---

## Reverse Proxy

A reverse proxy typically provides:

- TLS termination
- request routing
- compression
- header normalization
- request limits
- centralized logging

The backend remains responsible for business logic.

---

## Authentication

Unlike the Development profile, the Intranet profile always requires authenticated users.

Typical authentication mechanisms include:

- Active Directory
- LDAP
- Kerberos
- OpenID Connect
- OAuth
- corporate identity providers

Authentication integrates with existing enterprise infrastructure whenever possible.

---

## Authorization

Authentication does not imply authorization.

Every request follows the same authorization pipeline.

```text
Authenticated User

↓

Authorization

↓

Business Operation

```

Permissions remain fully backend-controlled.

---

## Session Management

Authenticated sessions should be protected through:

- secure cookies
- session expiration
- session renewal
- logout support
- inactivity timeouts

Session policies may be less restrictive than Internet deployments while still providing enterprise security.

---

## Runtime Configuration

Business behavior continues to use Runtime Configuration.

Administrators may update:

- prompt fragments
- model selection
- tool availability
- hierarchy
- feature flags
- UI schemas

Changes become effective without restarting the application.

---

## Environment Variables

Environment variables contain infrastructure settings only.

Typical examples include:

- deployment profile
- database connection
- authentication endpoints
- logging configuration
- secret keys

Business configuration remains stored in the database.

---

## Database

PostgreSQL is the preferred database for production intranet deployments.

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

The architecture remains database-independent.

---

## AI Providers

Organizations may choose different provider strategies.

Examples include:

- local Ollama servers
- internal inference clusters
- dedicated GPU servers
- approved external gateways

The Model Registry abstracts provider differences.

---

## API Security

Every API request is validated before execution.

Validation includes:

- authentication
- authorization
- schema validation
- payload validation
- identifier validation

Business services never receive invalid requests.

---

## Streaming

Streaming follows the same authorization model as REST APIs.

```text
Authenticated Request

↓

Authorization

↓

SSE Stream

↓

Client

```

Streaming endpoints never bypass security policies.

---

## CORS

CORS policies should allow only trusted organizational origins.

Example:

```text
Corporate Web Portal

↓

Allowed Origin

↓

API Access

```

Unknown origins should be rejected.

---

## Logging

Operational logging typically includes:

- startup events
- configuration changes
- authentication events
- authorization failures
- structured errors
- registry initialization

Logs support operational monitoring and troubleshooting.

---

## Audit Logging

Configuration and administrative operations are fully audited.

Typical audit information includes:

- authenticated administrator
- timestamp
- operation
- affected configuration
- revision changes
- previous and new values

Auditability is a core requirement of the Intranet profile.

---

## Configuration Revisions

Configuration updates increment revision numbers.

```text
Configuration Updated

↓

Revision++

↓

Cache Invalidated

↓

Updated Runtime Behavior

```

Multiple backend instances remain synchronized through revision tracking.

---

## Plugin Security

Plugins follow the same validation pipeline as the application core.

Registration requires:

- valid manifest
- compatible schema version
- supported extension points
- successful validation

Plugins cannot bypass authorization or modify core services.

---

## Error Handling

Structured error responses remain enabled.

Example:

```text
code

message

details

request_id

```

Operational diagnostics may be richer than in Internet deployments while still avoiding unnecessary exposure of internal implementation details.

---

## Monitoring

Typical monitoring includes:

- application health
- request latency
- authentication status
- database availability
- registry health
- resource utilization

Monitoring supports operational stability and capacity planning.

---

## Backup Strategy

Organizations should regularly back up:

- runtime configuration
- hierarchy
- audit logs
- application database
- uploaded files

Backup procedures should be tested periodically.

---

## High Availability

Larger organizations may deploy multiple backend instances.

```text
Internal Load Balancer

        │

   ┌────┴────┐

   ▼         ▼

Backend   Backend

        │

        ▼

 PostgreSQL

```

Shared runtime configuration ensures consistent behavior across all instances.

---

## Security Principles

The Intranet profile enforces several mandatory principles.

- authenticated users
- server-side authorization
- schema validation
- structured errors
- runtime configuration validation
- audit logging
- revision tracking
- least privilege

These principles apply regardless of network trust.

---

## Differences from Other Profiles

| Feature        | Development | Intranet      | Internet |
| -------------- | ----------- | ------------- | -------- |
| HTTPS          | Optional    | Recommended   | Required |
| Authentication | Simplified  | Required      | Required |
| Authorization  | Required    | Required      | Required |
| Audit Logging  | Optional    | Required      | Required |
| Rate Limiting  | Optional    | Optional      | Required |
| Debug Features | Enabled     | Disabled      | Disabled |
| Public Access  | No          | Internal Only | Public   |

The application architecture remains identical across all profiles.

---

## Future Extensions

The Intranet deployment profile supports future enhancements including:

- enterprise single sign-on
- centralized policy management
- directory synchronization
- organization-wide configuration templates
- distributed caching
- cluster-aware configuration updates
- internal monitoring dashboards

These capabilities can be added without changing the application's architecture.

---

## Relationship to Other Deployment Profiles

The Intranet profile shares the same application architecture with:

- [[Development]]
- [[Internet]]

Only operational policies and security requirements differ.

---

## Related Documentation

## Deployment

- [[Deployment Overview]]
- [[Development]]
- [[Internet]]

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

The Intranet deployment profile provides a secure and manageable environment for operating Kernschmied inside an organization's trusted network. It combines enterprise authentication, server-side authorization, runtime configuration, audit logging, schema validation, and centralized administration while maintaining the same APIs, contracts, registries, and architecture used in every other deployment profile.

By separating operational security policies from application behavior, the Intranet profile allows organizations to deploy Kernschmied reliably within their internal infrastructure while preserving architectural consistency, scalability, and long-term maintainability.

---

Back to [[Home]].
