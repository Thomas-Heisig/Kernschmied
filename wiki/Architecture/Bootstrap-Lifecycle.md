# Bootstrap Lifecycle

The **Bootstrap Lifecycle** describes the complete startup process of a Kernschmied client and the initialization sequence of the backend application.

Bootstrap is the first interaction between a client and the platform. It establishes a common understanding of the application's capabilities, versions, deployment profile, available endpoints, and runtime state before any business functionality is accessed.

Unlike many traditional applications, Kernschmied does **not** embed deployment assumptions or feature knowledge into the frontend. Instead, this information is discovered dynamically through the Bootstrap API.

---

## Goals

The Bootstrap Lifecycle is designed to provide:

- Deterministic application startup
- Dynamic capability discovery
- Stable initialization contracts
- Version compatibility checks
- Runtime configuration awareness
- Cache invalidation support
- Deployment profile discovery
- Forward compatibility

---

## Architectural Principles

The bootstrap process follows several core principles.

## Backend Defines Runtime State

The backend is the authoritative source for:

- application metadata
- deployment profile
- supported capabilities
- available endpoints
- contract versions
- configuration revisions

The frontend never hardcodes this information.

---

## Lightweight Initialization

Bootstrap intentionally returns only metadata.

Large resources such as:

- hierarchy
- UI schemas
- model registry
- tool registry

are retrieved through dedicated APIs after bootstrap has completed.

---

## Stable Contracts

The Bootstrap API is one of the most stable contracts within the platform.

Changes are:

- versioned
- backward compatible whenever possible
- independently tracked

---

## High-Level Startup Sequence

```text
Application Start

        │

        ▼

Backend Startup

        │

        ▼

Registry Initialization

        │

        ▼

Configuration Loading

        │

        ▼

HTTP Server Ready

────────────────────────────────────

Frontend Start

        │

        ▼

GET /api/v1/bootstrap

        │

        ▼

Application Initialization

        │

        ▼

Load Additional Resources

        │

        ▼

Ready

```

---

## Backend Bootstrap

Before clients can connect, the backend initializes its core infrastructure.

Typical startup sequence:

```text
Load Environment

↓

Create Application

↓

Initialize Database

↓

Load Configuration

↓

Initialize Registries

↓

Register Routes

↓

Start Server

```

The backend startup is deterministic and completes before accepting requests.

---

## Backend Initialization Components

Typical initialization order:

1. Environment
2. Logging
3. Dependency Injection
4. Database
5. Configuration Service
6. Model Registry
7. Tool Registry
8. API Routes
9. Middleware
10. HTTP Server

Each component depends only on previously initialized services.

---

## Client Bootstrap

After the frontend starts, it immediately requests:

```http
GET /api/v1/bootstrap
```

This request provides all metadata required to initialize the client.

---

## Bootstrap Response

Typical information includes:

- application name
- application version
- deployment profile
- security profile
- current user
- available endpoints
- supported capabilities
- feature flags
- contract versions
- registry revisions

Example:

```text
Bootstrap

↓

Application

↓

Capabilities

↓

Versions

↓

Endpoints

↓

Revisions

```

---

## Application Metadata

The frontend receives:

```json
{
  "application": {
    "name": "Kernschmied",
    "version": "0.1.0"
  }
}
```

This information is primarily informational.

---

## Deployment Profile

The bootstrap response identifies the active deployment profile.

Example:

```json
{
  "environment": {
    "profile": "development"
  }
}
```

Possible values include:

- development
- intranet
- internet

The frontend may adapt diagnostics or presentation but never security decisions.

---

## Security Profile

Bootstrap exposes the active security profile.

Example:

```json
{
  "security": {
    "profile": "internet"
  }
}
```

Authorization always remains server-side.

---

## Capability Discovery

Capabilities describe which platform features are available.

Example:

```json
{
  "capabilities": {
    "chat_streaming": true,
    "tool_registry": true,
    "ui_schema": true
  }
}
```

Clients use capability discovery instead of hardcoded assumptions.

---

## Feature Discovery

Features represent optional frontend behavior.

Examples:

- schema_driven_ui
- recursive_hierarchy
- streaming

Feature flags should influence presentation only.

---

## Endpoint Discovery

Bootstrap publishes canonical endpoint locations.

Example:

```json
{
  "endpoints": {
    "hierarchy": "/api/v1/hierarchy",
    "chat_stream": "/api/v1/chat/stream"
  }
}
```

This removes endpoint knowledge from frontend source code.

---

## Version Discovery

Each public contract exposes its version.

Example:

```json
{
  "versions": {
    "bootstrap": 1,
    "chat": 1,
    "ui_schema": 1
  }
}
```

Clients compare versions before using optional functionality.

---

## Revision Discovery

Bootstrap also publishes mutable runtime revisions.

Typical revisions include:

- configuration
- model registry
- tool registry

Example:

```text
Configuration Revision

↓

17

```

Clients invalidate cached resources when revisions change.

---

## Frontend Initialization Pipeline

After bootstrap completes successfully, the frontend continues initialization.

Typical sequence:

```text
Bootstrap

↓

Load UI Schemas

↓

Load Hierarchy

↓

Load Models

↓

Load Tools

↓

Initialize Stores

↓

Render UI

```

The exact order may evolve while preserving dependencies.

---

## Bootstrap Dependency Graph

```text
Bootstrap

├── UI Schema

├── Hierarchy

├── Models

├── Tools

└── Configuration

```

Every subsequent API depends on bootstrap metadata.

---

## Cache Management

Bootstrap supports efficient client caching.

The frontend may cache:

- endpoints
- capabilities
- versions

Resources tied to revisions are reloaded only when revisions change.

---

## Configuration Changes

When runtime configuration changes:

```text
Configuration Updated

↓

Revision++

↓

Bootstrap Reflects New Revision

↓

Frontend Reloads Configuration

```

This minimizes unnecessary API requests.

---

## Authentication Flow

Depending on the deployment profile:

```text
Frontend

↓

Authentication

↓

Bootstrap

↓

Application Initialization

```

Unauthenticated clients receive standard authorization errors.

---

## Failure Handling

If bootstrap fails:

```text
Application Start

↓

Bootstrap Error

↓

Show Error Screen

↓

Retry

```

The application should not continue initialization with incomplete bootstrap information.

---

## Startup Validation

The frontend should validate:

- supported API version
- bootstrap version
- required capabilities
- endpoint availability

Unsupported platforms should fail gracefully with a meaningful message.

---

## Error Handling

Bootstrap errors follow the standard error contract.

Example:

```json
{
  "code": "internal_error",
  "message": "Bootstrap generation failed.",
  "details": {},
  "request_id": "8d4d8c17"
}
```

---

## Performance Considerations

Bootstrap should:

- execute in a few milliseconds
- avoid expensive database queries
- avoid registry traversal
- avoid loading large datasets
- remain highly cacheable

Large payloads are intentionally delegated to specialized APIs.

---

## Security Considerations

Bootstrap intentionally excludes:

- API keys
- provider credentials
- internal configuration
- filesystem paths
- secrets
- private implementation details

Only information required for application initialization is exposed.

---

## Extension Points

Future bootstrap versions may expose additional metadata, including:

- plugin revisions
- localization support
- supported media types
- deployment capabilities
- feature negotiation

New fields should be additive to preserve backward compatibility.

---

## Relationship to Other APIs

Bootstrap initializes the client before any other API is used.

Typical request order:

```text
GET /bootstrap

↓

GET /ui/schema

↓

GET /hierarchy

↓

GET /models

↓

GET /tools

↓

POST /chat/stream

```

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[System-Context]]
- [[Request-Lifecycle]]
- [[Deployment-Architecture]]
- [[Configuration-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Configuration]]
- [[Hierarchy]]
- [[Models]]
- [[Tools]]
- [[Chat]]

---

## ADRs

- [[ADR-0002-Bootstrap]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0014-Deployment-Profiles]]

---

## Summary

The Bootstrap Lifecycle defines the deterministic startup process for every Kernschmied client.

By exposing application metadata, deployment information, capabilities, endpoint locations, contract versions, and runtime revisions through a lightweight and stable initialization contract, the bootstrap process enables a fully schema-driven, provider-independent, and dynamically configurable platform without embedding deployment-specific knowledge into the frontend.

---

Back to [[Home]].
