# Bootstrap API

The Bootstrap API is the first endpoint every Kernschmied client calls after startup.

It provides all information required to initialize the application without hardcoding deployment-specific knowledge into the frontend.

The bootstrap endpoint intentionally contains only lightweight metadata. Large resources such as hierarchy trees, UI schemas or configuration data are retrieved through their dedicated APIs.

---

## Goals

The Bootstrap endpoint is designed to provide:

- Application identification
- API compatibility information
- Deployment profile
- Security profile
- Supported capabilities
- Available endpoint locations
- Contract versions
- Configuration revisions
- Feature flags
- Startup metadata

The bootstrap response should remain small, deterministic and cacheable.

---

## Endpoint

```http
GET /api/v1/bootstrap
```

---

## Authentication

Authentication depends on the active deployment profile.

| Profile     | Authentication |
| ----------- | -------------- |
| development | Optional       |
| intranet    | Required       |
| internet    | Required       |

---

## Response

Example:

```json
{
  "application": {
    "name": "Kernschmied",
    "version": "0.1.0"
  },
  "environment": {
    "profile": "development"
  },
  "user": {
    "id": "local-user",
    "display_name": "Development User"
  },
  "security": {
    "profile": "development"
  },
  "capabilities": {
    "hierarchy": true,
    "ui_schema": true,
    "chat_streaming": true,
    "configuration": true,
    "model_registry": true,
    "tool_registry": true
  },
  "features": {
    "schema_driven_ui": true,
    "recursive_hierarchy": true,
    "streaming": true
  },
  "versions": {
    "api": 1,
    "bootstrap": 1,
    "ui_schema": 1,
    "hierarchy": 1,
    "chat": 1,
    "model_registry": 1,
    "tool_registry": 1,
    "configuration": 1
  },
  "endpoints": {
    "hierarchy": "/api/v1/hierarchy",
    "ui_schema": "/api/v1/ui/schema",
    "chat_stream": "/api/v1/chat/stream",
    "models": "/api/v1/models",
    "tools": "/api/v1/tools",
    "configuration": "/api/v1/config"
  },
  "revisions": {
    "configuration": 17,
    "model_registry": 3,
    "tool_registry": 8
  },
  "request_id": "3d52fef3"
}
```

---

## Response Sections

## Application

Provides application metadata.

```json
{
  "name": "Kernschmied",
  "version": "0.1.0"
}
```

This information is displayed by the frontend and used for diagnostics.

---

## Environment

Describes the active deployment profile.

Example:

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

## User

Contains information about the current authenticated user.

Example:

```json
{
  "id": "local-user",
  "display_name": "Development User"
}
```

The frontend should treat this information as informational only.

Authorization decisions remain server-side.

---

## Security

Indicates the active security profile.

Example:

```json
{
  "profile": "internet"
}
```

The frontend may adapt its presentation accordingly.

---

## Capabilities

Capabilities describe backend functionality.

Example:

```json
{
  "chat_streaming": true,
  "tool_registry": true,
  "configuration": true
}
```

Capabilities allow older clients to hide unsupported functionality.

---

## Features

Features describe optional frontend behavior.

Examples:

- schema_driven_ui
- recursive_hierarchy
- streaming

Features are intentionally coarse-grained.

---

## Versions

Every public contract exposes its version independently.

Example:

```json
{
  "api": 1,
  "chat": 1,
  "ui_schema": 1
}
```

Clients should compare versions before assuming compatibility.

---

## Endpoints

The bootstrap endpoint publishes the canonical API locations.

Example:

```json
{
  "chat_stream": "/api/v1/chat/stream"
}
```

This avoids hardcoded URLs inside frontend modules.

---

## Revisions

Revision numbers identify mutable runtime state.

Examples:

- configuration
- model registry
- tool registry

Whenever a revision changes the frontend knows cached data may no longer be valid.

---

## Request ID

Every bootstrap request returns a request identifier.

Example:

```json
{
  "request_id": "e3f5b4e9"
}
```

This identifier supports diagnostics and support requests.

---

## Startup Sequence

Typical startup flow:

```text
Frontend

↓

GET /bootstrap

↓

Load Endpoints

↓

Load UI Schema

↓

Load Hierarchy

↓

Initialize Application

↓

Ready

```

The bootstrap endpoint should always be the first API request.

---

## Why Not Return Everything?

Bootstrap intentionally does **not** return:

- hierarchy tree
- UI schema
- chats
- configuration
- model definitions
- tool definitions

Reasons:

- smaller responses
- faster startup
- independent caching
- independent versioning
- lower bandwidth

---

## Versioning

The Bootstrap API follows the REST API version.

Current endpoint:

```text
/api/v1/bootstrap

```

The bootstrap payload also contains independent contract versions.

---

## Error Responses

Errors follow the standard platform contract.

Example:

```json
{
  "code": "internal_error",
  "message": "Bootstrap could not be generated.",
  "details": {},
  "request_id": "..."
}
```

---

## Caching

The bootstrap response may be cached briefly.

However, clients should invalidate cached information whenever:

- application restarts
- configuration revisions change
- deployment changes
- authentication changes

---

## Security Considerations

Bootstrap intentionally excludes sensitive information.

It must never expose:

- API keys
- passwords
- provider secrets
- internal file paths
- private configuration

The response should be safe for authenticated clients.

---

## Performance Considerations

The endpoint should:

- execute quickly
- avoid database-heavy operations
- avoid loading registries unnecessarily
- avoid large payloads

Bootstrap should typically complete within a few milliseconds.

---

## Related Endpoints

After bootstrap, clients typically request:

```text
GET /api/v1/ui/schema

GET /api/v1/hierarchy

GET /api/v1/models

GET /api/v1/tools

```

---

## Related Documentation

- [[REST-API]]
- [[Architecture]]
- [[Configuration]]
- [[UI-Schema]]
- [[Hierarchy]]
- [[Streaming]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0005-Versioned-Contracts]]

---

## Summary

The Bootstrap API provides a lightweight initialization contract for every Kernschmied client.

Rather than embedding deployment knowledge into the frontend, the backend communicates application metadata, supported capabilities, endpoint locations, contract versions and runtime revisions through a single, stable endpoint.

This approach enables independent evolution of frontend and backend while minimizing startup complexity and maintaining long-term compatibility.

---

Back to [[Home]].
