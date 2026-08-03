# ADR-0006: API Contracts and Versioning

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

## Context

Kernschmied consists of multiple independently evolving subsystems:

- Backend
- Frontend
- Model Providers
- Tool Providers
- Plugins
- Administrative Interfaces
- Future Desktop Clients
- Future Mobile Clients

All communication between these systems is performed through explicit contracts.

Examples include:

- REST APIs
- Server-Sent Events
- Bootstrap responses
- UI Schemas
- Hierarchy Schemas
- Configuration Schemas
- Model Contracts
- Tool Contracts

Because these systems evolve independently, every contract must remain stable over time.

---

## Problem

Without a clear API versioning strategy, even small backend changes may unintentionally break existing clients.

Typical examples include:

- Renaming JSON properties
- Removing fields
- Changing response formats
- Modifying endpoint semantics
- Introducing incompatible validation

These problems become increasingly severe as external integrations grow.

---

## Decision

Kernschmied adopts a **contract-first API architecture** with explicit versioning.

API evolution follows these principles:

- Stable contracts
- Explicit versions
- Backward compatibility whenever possible
- Breaking changes require new versions
- Schema validation
- Graceful deprecation

---

## Architectural Principle

> APIs are products.
>
> Every public contract must evolve deliberately and predictably.

---

## High-Level Architecture

```text
Frontend

        │

        ▼

 REST API v1

        │

        ▼

FastAPI Backend

        │

        ▼

Business Services

```

---

## Versioning Strategy

API versioning is based on the URL.

Example:

```text
/api/v1/bootstrap

/api/v1/chat

/api/v1/config

```

Future versions may exist alongside previous ones.

Example:

```text
/api/v1/...

/api/v2/...

```

---

## Why URL Versioning?

Alternative approaches were evaluated:

- HTTP Headers
- Content Negotiation
- Media Types
- Query Parameters

URL versioning was selected because it is:

- explicit
- easy to document
- easy to debug
- reverse-proxy friendly
- compatible with OpenAPI

---

## API Stability

Once published:

- endpoint paths remain stable
- request structures remain stable
- response structures remain stable
- status codes remain stable

Only additive changes are allowed within the same version.

---

## Contract Categories

Kernschmied defines several independent contract versions.

Examples include:

| Contract         | Purpose                     |
| ---------------- | --------------------------- |
| API              | REST interface              |
| Bootstrap        | Initial application state   |
| UI Schema        | Dynamic frontend            |
| Hierarchy Schema | Generic hierarchy           |
| Chat             | Chat requests and responses |
| Model Registry   | Model metadata              |
| Tool Registry    | Tool metadata               |
| Configuration    | Runtime configuration       |

Each contract evolves independently.

---

## Bootstrap Version

The bootstrap endpoint communicates supported versions.

Example:

```json
{
  "versions": {
    "api": 1,
    "bootstrap": 1,
    "ui_schema": 1,
    "hierarchy": 1,
    "chat": 1,
    "model_registry": 1,
    "tool_registry": 1,
    "configuration": 1
  }
}
```

Clients use this information during initialization.

---

## Schema Versioning

Every schema contains its own version.

Example:

```json
{
  "schema_version": 1,
  "type": "form"
}
```

Unknown schema versions are rejected before rendering.

---

## Backward-Compatible Changes

The following changes do **not** require a new API version:

- Adding optional fields
- Adding optional endpoints
- Adding optional metadata
- Adding optional capabilities

Existing clients continue to function.

---

## Breaking Changes

Breaking changes require a new API version.

Examples include:

- Removing properties
- Renaming fields
- Changing field types
- Changing endpoint semantics
- Removing endpoints
- Changing authentication requirements

---

## Client Compatibility

Older clients continue using:

```text
/api/v1/

```

New clients may migrate to:

```text
/api/v2/

```

Multiple API versions may coexist during migration.

---

## Error Contracts

Every endpoint returns structured errors.

Example:

```json
{
  "code": "validation_error",
  "message": "The request is invalid.",
  "details": {},
  "request_id": "..."
}
```

The error structure itself is versioned.

---

## Request IDs

Every request receives a unique identifier.

Example:

```text
Request

↓

request_id

↓

Logs

↓

Support

↓

Diagnostics

```

Request IDs improve troubleshooting across distributed systems.

---

## HTTP Status Codes

Standard HTTP status codes are used consistently.

| Status | Meaning          |
| ------ | ---------------- |
| 200    | Success          |
| 201    | Created          |
| 204    | No Content       |
| 400    | Bad Request      |
| 401    | Unauthorized     |
| 403    | Forbidden        |
| 404    | Not Found        |
| 409    | Conflict         |
| 422    | Validation Error |
| 429    | Rate Limited     |
| 500    | Internal Error   |

---

## OpenAPI

Every public REST endpoint is documented using OpenAPI.

Documentation should remain synchronized with implementation.

OpenAPI represents the authoritative machine-readable API documentation.

---

## Streaming Contracts

Chat streaming uses Server-Sent Events.

Supported event types include:

- start
- token
- message
- reasoning
- tool_call
- tool_result
- usage
- complete
- error
- heartbeat

Unknown event types should be ignored unless explicitly required.

---

## Deprecation Policy

The lifecycle of an API contract is:

```text
Introduced

↓

Stable

↓

Deprecated

↓

Removal Announced

↓

Removed in Next Major Version

```

Deprecation periods allow consumers sufficient migration time.

---

## Validation

All requests are validated using Pydantic models.

Validation occurs before business logic executes.

Invalid requests receive structured validation errors.

---

## Security Considerations

API contracts contribute to security through:

- explicit validation
- predictable semantics
- immutable contracts
- version isolation
- structured errors

Clients must never rely on undocumented behavior.

---

## Performance Considerations

Stable contracts improve performance by enabling:

- client-side caching
- proxy caching
- schema caching
- generated SDKs
- efficient serialization

Version stability also reduces unnecessary compatibility checks.

---

## Operational Impact

Versioned APIs simplify:

- rolling upgrades
- staged deployments
- debugging
- compatibility testing
- long-term maintenance

Operations teams can run multiple client versions simultaneously.

---

## Consequences

## Positive

- Stable integrations
- Predictable evolution
- Easier documentation
- Independent frontend/backend releases
- Improved tooling
- Better diagnostics

## Negative

- Additional maintenance
- Version lifecycle management
- Parallel endpoint support during migrations

---

## Alternatives Considered

## Header-Based Versioning

Advantages:

- Clean URLs

Disadvantages:

- Harder debugging
- Poor browser visibility
- Less discoverable

Rejected.

---

## Query Parameter Versioning

Example:

```text
/api/bootstrap?version=2

```

Rejected due to unclear semantics.

---

## No Versioning

Rejected because it inevitably leads to accidental breaking changes.

---

## Risks

Potential risks include:

- Version proliferation
- Undocumented changes
- Long-lived deprecated APIs
- Inconsistent implementations

Mitigation includes:

- Architecture reviews
- OpenAPI validation
- CI compatibility tests
- Contract testing
- Explicit deprecation policy

---

## Implementation Notes

The implementation should provide:

- URL-based API versioning
- Independent contract versions
- Pydantic validation
- Structured error responses
- OpenAPI documentation
- Compatibility testing
- Request IDs
- Stable serialization

---

## Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Contract-Versioning]]
- [[Bootstrap-Lifecycle]]

---

## Backend

- [[REST-API]]
- [[Configuration]]
- [[Streaming]]

---

## Frontend

- [[API-Client]]
- [[UI-Schema]]

---

## Decision Summary

Kernschmied adopts a **contract-first, URL-versioned API architecture** in which every public interface evolves through explicit, documented versions.

REST endpoints are versioned via the URL (`/api/v1/...`), while domain-specific contracts such as Bootstrap, UI Schema, Hierarchy, Chat, Model Registry, Tool Registry, and Configuration maintain their own independent schema versions.

This strategy enables long-term compatibility, predictable upgrades, independent client evolution, and a stable foundation for plugins and future integrations.

---

Back to [[Home]].
