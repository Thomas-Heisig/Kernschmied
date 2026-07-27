# Configuration API

The Configuration API provides centralized access to the runtime configuration of the Kernschmied platform.

Unlike infrastructure settings stored in `.env`, the Configuration API manages **business configuration** that can evolve during runtime without requiring an application restart.

The Configuration API is one of the core platform services and is used by:

- Administration UI
- Bootstrap
- Configuration Resolver
- Hierarchy Service
- Model Registry
- Tool Registry
- Chat Service
- Future plugins

The API intentionally exposes validated configuration rather than direct database records.

---

# Goals

The Configuration API provides:

- Runtime configuration
- Strong validation
- Version tracking
- Configuration revisions
- Audit logging
- Hierarchical scopes
- Merge strategies
- Stable REST contracts

---

# Endpoints

## Read Effective Configuration

```http
GET /api/v1/config
```

Returns the effective runtime configuration.

---

## Update Configuration

```http
PUT /api/v1/config
```

Updates configuration values.

Requires administrative permissions.

---

## Future Endpoints

Possible future extensions include:

```http
GET /api/v1/config/scopes

GET /api/v1/config/history

GET /api/v1/config/revisions

POST /api/v1/config/validate

POST /api/v1/config/import

POST /api/v1/config/export
```

---

# Architecture

```text
REST API

        │

        ▼

Configuration Service

        │

        ▼

Configuration Resolver

        │

        ▼

Database

        │

        ▼

Effective Configuration
```

Business services never access configuration tables directly.

---

# Configuration Categories

Configuration is divided into two categories.

## Infrastructure Configuration

Loaded during startup.

Examples:

- database connection
- deployment profile
- HTTPS
- logging bootstrap
- secret keys

Infrastructure configuration is **not** managed by this API.

---

## Runtime Configuration

Managed by this API.

Examples:

- prompts
- default models
- enabled tools
- feature flags
- UI configuration
- hierarchy defaults
- provider configuration

---

# Read Configuration

```http
GET /api/v1/config
```

Example response:

```json
{
  "revision": 42,
  "configuration": {
    "default_model": "qwen2.5:7b",
    "streaming": true,
    "default_temperature": 0.3
  }
}
```

---

# Update Configuration

```http
PUT /api/v1/config
```

Example request:

```json
{
  "default_model": "qwen2.5:14b",
  "streaming": true,
  "default_temperature": 0.2
}
```

Successful updates increment the global configuration revision.

---

# Configuration Scopes

Configuration values exist in hierarchical scopes.

Supported scopes include:

| Scope | Purpose |
|--------|---------|
| SYSTEM | Global defaults |
| NODE | Hierarchy defaults |
| PROJECT | Project configuration |
| CHAT | Chat configuration |
| USER | User preferences |
| REQUEST | Temporary overrides |

---

# Configuration Resolution

The Configuration Resolver combines all scopes into one immutable configuration.

```text
SYSTEM

↓

NODE

↓

PROJECT

↓

CHAT

↓

USER

↓

REQUEST

↓

Effective Configuration
```

Business services consume only the effective configuration.

---

# Merge Strategies

Every configuration entry defines how inheritance behaves.

Supported strategies include:

## Replace

The child value replaces the inherited value.

---

## Extend

Collections are merged by appending new values.

---

## Deep Merge

Nested objects are merged recursively.

---

# Runtime Editable Values

Some configuration can be changed without restarting the application.

Examples:

- prompts
- default models
- feature flags
- enabled tools

Infrastructure settings remain immutable during runtime.

---

# Validation

Every configuration update is validated before persistence.

Validation includes:

- JSON Schema
- Pydantic models
- required fields
- enums
- numeric ranges
- custom validators

Invalid configuration is rejected.

---

# Configuration Revision

Every successful update increases the global revision.

Example:

```text
Revision 12

↓

Configuration Updated

↓

Revision 13
```

The revision is returned by:

- Bootstrap API
- Configuration API

Clients use revisions for cache invalidation.

---

# Cache Invalidation

Configuration is cached.

When the revision changes:

```text
Configuration Updated

↓

Revision++

↓

Invalidate Cache

↓

Reload
```

This mechanism supports multiple backend workers.

---

# Audit Logging

Every configuration modification generates an immutable audit entry.

Audit information typically includes:

- timestamp
- user
- request id
- previous value
- new value
- revision
- affected key

---

# Authorization

Reading configuration may require authentication depending on the deployment profile.

Updating configuration always requires administrative permissions.

Typical permission:

```text
configuration.write
```

Backend authorization is always authoritative.

---

# Error Responses

Errors follow the standard platform contract.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid configuration value.",
  "details": {
    "field": "default_temperature"
  },
  "request_id": "c8c6d2fd"
}
```

---

# Versioning

Configuration follows the REST API version.

```text
/api/v1/config
```

The configuration schema itself may evolve independently through schema versioning.

---

# Security Considerations

The Configuration API never exposes:

- secret keys
- passwords
- authentication tokens
- private certificates

Sensitive infrastructure configuration remains outside runtime configuration.

---

# Performance Considerations

Performance is achieved through:

- immutable snapshots
- resolver caching
- revision-based invalidation
- request-local reuse

Configuration should not require repeated database queries during a single request.

---

# Typical Workflow

```text
Administrator

↓

PUT /config

↓

Validation

↓

Persist

↓

Revision++

↓

Audit Log

↓

Invalidate Cache

↓

Done
```

---

# Related Endpoints

```http
GET /api/v1/bootstrap

GET /api/v1/hierarchy

GET /api/v1/models

GET /api/v1/tools
```

---

# Related Documentation

- [[Architecture]]
- [[Bootstrap]]
- [[Hierarchy]]
- [[Configuration-Architecture]]
- [[REST-API]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]

---

# Summary

The Configuration API provides centralized management of Kernschmied's runtime configuration.

It separates mutable business configuration from immutable infrastructure settings, validates every modification, tracks revisions for cache invalidation, records audit information, and resolves hierarchical configuration through deterministic merge strategies.

This architecture enables safe runtime administration, consistent platform behavior, and scalable multi-instance deployments while preserving long-term compatibility and strong operational control.

---

Back to [[Home]].