# Deployment Architecture

The **Deployment Architecture** defines how Kernschmied is deployed across different operating environments while preserving identical application behavior, stable public contracts, and consistent security guarantees.

Unlike many applications that contain environment-specific code paths, Kernschmied separates **business logic** from **deployment concerns**. The same application can therefore operate as a local desktop assistant, an internal company application, or a secure Internet service without architectural changes.

The deployment profile influences infrastructure, authentication, transport security, and operational behavior, but **never changes the application's business functionality**.

---

## Goals

The deployment architecture is designed to provide:

- Identical business behavior across all deployments
- Environment-independent application logic
- Stable public contracts
- Predictable security
- Simple local development
- Enterprise-ready deployment
- Future cloud compatibility
- Minimal operational complexity

---

## Architectural Principles

## One Application

Kernschmied is a single application.

There are not separate versions for:

- Local Edition
- Enterprise Edition
- Cloud Edition

Instead, deployment behavior is controlled through deployment profiles.

---

## Stable Contracts

Regardless of deployment profile:

- REST APIs remain identical.
- SSE contracts remain identical.
- UI Schemas remain identical.
- Configuration contracts remain identical.

Clients never need different implementations for different deployment targets.

---

## Deployment is Infrastructure

Deployment influences:

- networking
- authentication
- HTTPS
- logging
- monitoring
- scaling

Deployment does **not** influence:

- hierarchy
- prompts
- schemas
- registries
- chat behavior

---

## Deployment Profiles

Kernschmied currently defines three official deployment profiles.

```text
Development

↓

Intranet

↓

Internet

```

Each profile provides progressively stronger security guarantees.

---

## Development Profile

Purpose:

Local development on a single workstation.

Typical environment:

```text
Developer PC

↓

Frontend

↓

FastAPI

↓

SQLite

↓

Local Ollama

```

Characteristics:

- local execution
- simplified authentication
- verbose logging
- debugging enabled
- localhost networking
- relaxed CORS
- rapid development

---

## Intranet Profile

Purpose:

Deployment inside a trusted company network.

Typical architecture:

```text
Employees

↓

HTTPS

↓

FastAPI

↓

Database

↓

Local AI Models

```

Characteristics:

- authenticated users
- audit logging
- HTTPS
- central database
- controlled access
- internal DNS
- company authentication

---

## Internet Profile

Purpose:

Public Internet deployment.

Typical architecture:

```text
Internet Users

↓

Reverse Proxy

↓

HTTPS

↓

FastAPI

↓

Database

↓

AI Providers

```

Characteristics:

- mandatory HTTPS
- session authentication
- rate limiting
- strict CORS
- hardened headers
- security monitoring
- production logging

---

## Deployment Comparison

| Feature        | Development | Intranet    | Internet |
| -------------- | ----------- | ----------- | -------- |
| HTTPS          | Optional    | Recommended | Required |
| Authentication | Simplified  | Required    | Required |
| Authorization  | Required    | Required    | Required |
| Audit Log      | Optional    | Enabled     | Enabled  |
| Rate Limiting  | Optional    | Optional    | Required |
| Debug Logging  | Enabled     | Limited     | Disabled |
| CORS           | Relaxed     | Restricted  | Strict   |

---

## Deployment Overview

```text
               Deployment

                    │

      ┌─────────────┼─────────────┐

      │             │             │

Development     Intranet      Internet

```

Each profile shares the same application code.

---

## Runtime Components

Every deployment consists of the same logical components.

```text
Browser

↓

React Frontend

↓

FastAPI Backend

↓

Configuration

↓

Registries

↓

Repositories

↓

Database

```

Additional infrastructure may surround these components.

---

## Development Deployment

Typical local setup:

```text
+-------------------------+

Developer Workstation

-------------------------

React (Vite)

↓

FastAPI

↓

SQLite

↓

Ollama

+-------------------------+

```

Everything executes on one machine.

---

## Intranet Deployment

Example:

```text
Employees

↓

HTTPS

↓

Reverse Proxy

↓

FastAPI

↓

PostgreSQL

↓

Internal Ollama Server

```

Multiple users share the same application.

---

## Internet Deployment

Typical production architecture:

```text
Internet

↓

Firewall

↓

Load Balancer

↓

Reverse Proxy

↓

FastAPI

↓

Database

↓

Provider Layer

```

The architecture supports horizontal scaling.

---

## Reverse Proxy

A reverse proxy is recommended for production deployments.

Responsibilities include:

- HTTPS termination
- compression
- caching
- request limits
- security headers
- logging

Common implementations:

- Nginx
- Traefik
- Caddy
- Apache

---

## Database Deployment

Supported databases:

Development:

```text
SQLite

```

Production:

```text
PostgreSQL

```

The repository layer hides database differences from application services.

---

## AI Model Deployment

The provider architecture supports multiple deployment options.

Examples:

Local:

```text
FastAPI

↓

Ollama

```

Remote:

```text
FastAPI

↓

OpenAI

```

Hybrid:

```text
FastAPI

↓

Provider Registry

↓

Multiple Providers

```

Deployment is transparent to the frontend.

---

## Configuration

Bootstrap configuration is provided before startup.

Typical values include:

- database URL
- deployment profile
- HTTPS
- logging
- secrets

Business configuration remains in the database.

---

## Security

Security is determined by deployment profile.

The profile defines:

- authentication
- transport security
- CORS
- cookie policy
- session handling
- request limits

Business services remain unchanged.

---

## HTTPS

Recommended usage:

Development

```text
Optional

```

Intranet

```text
Recommended

```

Internet

```text
Mandatory

```

The backend should never expose unsecured production endpoints.

---

## Authentication

Possible authentication providers include:

- Local Development Identity
- Session Authentication
- LDAP
- Active Directory
- OAuth2
- OpenID Connect

The authentication mechanism is independent of business logic.

---

## Authorization

Authorization is always performed server-side.

Clients never determine:

- permissions
- roles
- resource access

This behavior is identical across all deployments.

---

## Scaling

The architecture supports horizontal scaling.

```text
Load Balancer

↓

FastAPI Instance 1

FastAPI Instance 2

FastAPI Instance 3

↓

Shared Database

```

Application services remain stateless whenever possible.

---

## High Availability

Future deployments may introduce:

- replicated databases
- multiple API servers
- clustered AI providers
- redundant reverse proxies

The architecture already supports these additions.

---

## Monitoring

Typical monitoring includes:

- health endpoints
- request latency
- provider latency
- database performance
- error rates
- configuration revisions

Monitoring remains external to business logic.

---

## Logging

Logging varies by deployment profile.

Development:

- verbose
- stack traces

Production:

- structured logging
- request identifiers
- audit events
- security events

Sensitive information must never be logged.

---

## Backup Strategy

Persistent data should include:

- configuration
- hierarchy
- chat history
- audit log
- revisions

Bootstrap configuration should be stored separately.

---

## Disaster Recovery

Recovery typically consists of:

```text
Infrastructure

↓

Restore Database

↓

Restore Configuration

↓

Start Application

```

Because bootstrap configuration is minimal, recovery remains straightforward.

---

## Deployment Independence

Business functionality is identical regardless of deployment.

Examples:

- hierarchy
- prompts
- schemas
- tools
- models
- registries

Only operational characteristics change.

---

## Future Deployment Options

The architecture can later support:

- Docker
- Kubernetes
- Azure
- AWS
- Google Cloud
- On-Premise Clusters

No architectural redesign is required.

---

## Relationship to Bootstrap

Bootstrap informs clients about:

- deployment profile
- security profile
- available capabilities
- versions

Clients adapt presentation but never security behavior.

---

## Relationship to Security

Deployment determines operational security.

Security Architecture defines:

- authorization
- identity
- policies
- trust boundaries

Together they provide consistent platform security.

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[System-Context]]
- [[C4-Container]]
- [[Security-Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Configuration-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Configuration]]

---

## ADRs

- [[ADR-0004-Security-Profiles]]
- [[ADR-0014-Deployment-Profiles]]
- [[ADR-0002-Bootstrap]]

---

## Summary

The Deployment Architecture enables Kernschmied to operate consistently across development, intranet, and Internet environments without changing application behavior or public contracts.

By separating deployment concerns from business logic, defining standardized deployment profiles, and keeping infrastructure-specific behavior outside the core application, the platform achieves flexibility, maintainability, operational security, and long-term scalability while preserving a single coherent architecture.

---

Back to [[Home]].
