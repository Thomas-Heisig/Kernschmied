# Bootstrap API

The Bootstrap API is the first endpoint every Kernschmied client calls after startup.

It provides the minimum amount of information required for a client to safely initialize itself without embedding deployment-specific knowledge or hardcoded assumptions.

The Bootstrap endpoint acts as the **discovery mechanism** for the platform.

It intentionally returns only lightweight metadata.

Large resources such as hierarchy data, UI schemas, registries, runtime configuration, conversations or documents are retrieved through their dedicated APIs.

---

# Purpose

The Bootstrap endpoint provides:

- application identity
- deployment profile
- security profile
- authenticated user information
- effective tenant information
- platform capabilities
- enabled features
- supported contract versions
- endpoint discovery
- runtime revisions
- registry revisions
- startup metadata
- diagnostic information

The bootstrap response is intentionally:

- deterministic
- lightweight
- cacheable
- versioned
- forward compatible

---

# Endpoint

```http
GET /api/v1/bootstrap
```

---

# Authentication

Authentication depends on the active deployment profile.

| Profile     | Authentication |
| ----------- | -------------- |
| development | Optional       |
| intranet    | Required       |
| internet    | Required       |

The bootstrap endpoint never bypasses authentication rules.

---

# Response Structure

```json
{
  "application": {},
  "environment": {},
  "deployment": {},
  "user": {},
  "tenant": {},
  "security": {},
  "capabilities": {},
  "features": {},
  "versions": {},
  "endpoints": {},
  "revisions": {},
  "diagnostics": {},
  "request_id": "..."
}
```

Each section represents an independent contract.

---

# Application

Application metadata.

```json
{
  "name": "Kernschmied",
  "version": "0.1.0",
  "build": "20260803",
  "edition": "community"
}
```

The frontend may display this information for diagnostics.

---

# Environment

Describes the active runtime profile.

```json
{
  "profile": "development"
}
```

Possible values:

- development
- intranet
- internet

---

# Deployment

Provides deployment metadata.

```json
{
  "instance_id": "local-dev",
  "node": "desktop-01",
  "startup_time": "...",
  "timezone": "Europe/Berlin"
}
```

Clients should treat these values as informational.

---

# User

Contains information about the authenticated identity.

```json
{
  "id": "user-123",
  "display_name": "Thomas Heisig",
  "authenticated": true
}
```

This information is informational only.

Authorization decisions remain server-side.

---

# Tenant

Provides the currently active tenant.

```json
{
  "id": "tenant-default",
  "display_name": "Default Tenant"
}
```

Future multi-tenant deployments may switch tenants dynamically.

---

# Security

Indicates the active security profile.

```json
{
  "profile": "internet",
  "authorization": "required"
}
```

The frontend may adapt its presentation but never enforce permissions.

---

# Capabilities

Capabilities describe what the backend currently supports.

Example:

```json
{
  "hierarchy": true,
  "chat": true,
  "resources": true,
  "widgets": true,
  "actions": true,
  "registries": true,
  "workflows": false
}
```

Capabilities enable forward compatibility.

Clients simply hide unsupported functionality.

---

# Features

Features describe optional behaviour.

Examples:

- schema_driven_ui
- runtime_registry
- dynamic_resources
- widget_layouts
- streaming
- reasoning
- multi_tenant

Features are intentionally coarse-grained.

---

# Versions

Every public contract exposes its own version.

Example:

```json
{
  "api": 1,
  "bootstrap": 1,
  "hierarchy": 1,
  "context": 1,
  "chat": 1,
  "resources": 1,
  "widgets": 1,
  "actions": 1,
  "events": 1,
  "registries": 1,
  "configuration": 1
}
```

Clients compare versions before assuming compatibility.

---

# Endpoints

Bootstrap publishes canonical endpoint locations.

Example:

```json
{
  "bootstrap": "/api/v1/bootstrap",
  "hierarchy": "/api/v1/hierarchy",
  "context": "/api/v1/context",
  "resources": "/api/v1/resources",
  "widgets": "/api/v1/widgets",
  "actions": "/api/v1/actions",
  "registries": "/api/v1/registries"
}
```

Clients should never hardcode API URLs.

---

# Revisions

Revision numbers describe mutable runtime state.

```json
{
  "configuration": 18,
  "hierarchy": 7,
  "registries": {
    "resource_types": 12,
    "widget_types": 5,
    "actions": 9,
    "concepts": 4,
    "models": 8,
    "tools": 11
  }
}
```

Whenever a revision changes, cached information becomes invalid.

---

# Diagnostics

Provides diagnostic metadata.

```json
{
  "server_time": "...",
  "api_status": "online",
  "request_duration_ms": 3
}
```

Useful for debugging and support.

---

# Request ID

Every response contains a request identifier.

```json
{
  "request_id": "5f42cb67"
}
```

The request identifier must appear in logs and error responses.

---

# Startup Sequence

Typical client initialization:

```text
Application Start

        │

        ▼

GET /bootstrap

        │

        ▼

Read Contract Versions

        │

        ▼

Read Capabilities

        │

        ▼

Read Endpoints

        │

        ▼

Load Effective Context

        │

        ▼

Load Runtime Registries

        │

        ▼

Load UI Schema

        │

        ▼

Load Hierarchy

        │

        ▼

Initialize Widgets

        │

        ▼

Ready
```

---

# Why Bootstrap Does Not Return Business Data

Bootstrap intentionally excludes:

- hierarchy data
- conversations
- resources
- widgets
- prompts
- workflows
- runtime configuration
- registry contents
- model definitions
- tool definitions
- search indexes

Reasons:

- smaller payloads
- faster startup
- independent versioning
- independent caching
- reduced bandwidth
- better scalability

---

# Versioning

The Bootstrap endpoint follows the REST API version.

```
/api/v1/bootstrap
```

The payload additionally contains independent contract versions for every public subsystem.

This allows contracts to evolve independently while maintaining backward compatibility.

---

# Error Responses

Errors follow the platform-wide error contract.

```json
{
  "code": "bootstrap_generation_failed",
  "message": "Bootstrap could not be generated.",
  "details": {},
  "request_id": "..."
}
```

---

# Caching

Bootstrap responses may be cached for a short time.

Clients should invalidate cached responses when:

- authentication changes
- deployment changes
- application restarts
- configuration revisions change
- registry revisions change
- contract versions change

---

# Security Considerations

Bootstrap must never expose:

- secrets
- passwords
- API keys
- encryption keys
- internal filesystem paths
- private runtime configuration
- provider credentials

Only information required for client initialization may be returned.

---

# Performance Considerations

Bootstrap should:

- execute within a few milliseconds
- avoid expensive database queries
- avoid loading complete registries
- avoid loading hierarchy data
- avoid loading large configuration objects

The endpoint should remain lightweight regardless of platform size.

---

# Related ADRs

- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0007 — Generic Hierarchy and Context Architecture
- ADR-0009 — Runtime Registry Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0020 — Multi-Tenant Architecture

---

# Summary

The Bootstrap API is the canonical discovery endpoint of the Kernschmied platform.

It provides only the metadata required for client initialization while delegating all business data to dedicated APIs.

By exposing contract versions, capabilities, endpoint discovery, runtime revisions and deployment metadata through a lightweight, stable and versioned contract, the Bootstrap API enables independent evolution of frontend and backend while maintaining long-term compatibility and minimizing startup complexity.

---

Ich würde sogar noch einen Schritt weitergehen und den Bootstrap komplett an den **32-ADR-Standard** anpassen. Dann wäre er praktisch die "Visitenkarte" der gesamten Plattform und müsste später kaum noch verändert werden.
