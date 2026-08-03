# Contract Versioning

The **Contract Versioning** strategy defines how public interfaces evolve over time while maintaining compatibility between clients and servers.

In Kernschmied, **contracts are considered long-lived public interfaces**. Every REST endpoint, Server-Sent Event stream, UI schema, manifest, and configuration schema is versioned independently.

This allows the platform to evolve without forcing simultaneous upgrades of every client or component.

---

## Goals

The versioning strategy is designed to provide:

- Stable public APIs
- Backward compatibility
- Independent evolution of subsystems
- Predictable migrations
- Safe deployment
- Incremental feature introduction
- Long-term maintainability

---

## What is a Contract?

A contract defines the agreed structure and behavior between two independent components.

Examples include:

- REST request bodies
- REST responses
- Server-Sent Event payloads
- UI schemas
- Model manifests
- Tool manifests
- Configuration schemas
- Bootstrap metadata

The implementation may change internally as long as the public contract remains compatible.

---

## Architectural Principles

The versioning strategy follows several core principles.

## Stable Public Interfaces

Public interfaces should remain stable for as long as possible.

Breaking changes require:

- a new version
- migration documentation
- compatibility strategy

---

## Independent Versioning

Every contract evolves independently.

For example:

```text
Bootstrap API

Version 1

Chat API

Version 3

UI Schema

Version 2

Manifest Schema

Version 4

```

Updating one contract does not require updating unrelated contracts.

---

## Additive Evolution

Whenever possible, contracts evolve by **adding** new capabilities.

Examples:

- new optional fields
- additional event types
- new capabilities
- additional metadata

Removing existing fields is avoided.

---

## Versioned Contracts

The following contracts are versioned independently.

| Contract             | Versioned |
| -------------------- | --------- |
| Bootstrap            | ✔         |
| Chat API             | ✔         |
| Configuration API    | ✔         |
| Hierarchy API        | ✔         |
| UI Schema            | ✔         |
| Model Manifest       | ✔         |
| Tool Manifest        | ✔         |
| SSE Stream           | ✔         |
| Configuration Schema | ✔         |

---

## Version Discovery

Clients discover supported versions during bootstrap.

Example:

```json
{
  "versions": {
    "bootstrap": 1,
    "chat": 1,
    "ui_schema": 2,
    "tool_registry": 1,
    "model_registry": 1
  }
}
```

The frontend never hardcodes expected versions.

---

## API Versioning

REST APIs are versioned through the URL.

Example:

```text
/api/v1/bootstrap

/api/v1/chat/stream

/api/v1/models

```

Future versions remain side-by-side.

Example:

```text
/api/v2/chat/stream

```

Older clients continue using the previous version.

---

## Bootstrap Version

The Bootstrap contract evolves independently.

It defines:

- application metadata
- endpoint discovery
- versions
- capabilities
- revisions

Clients use Bootstrap to determine compatibility.

---

## Chat API Version

The Chat API version controls:

- request structure
- response structure
- streaming behavior
- tool execution
- metadata

Streaming and request versions evolve together.

---

## SSE Versioning

The streaming protocol has its own contract version.

Possible additions include:

- new event types
- additional metadata
- optional fields

Existing event types remain unchanged.

---

## UI Schema Version

UI schemas are versioned independently of the REST API.

This allows frontend rendering capabilities to evolve without changing endpoint behavior.

Example:

```json
{
  "schema_version": 2
}
```

---

## Manifest Versioning

Both model and tool manifests include schema versions.

Example:

```json
{
  "schema": 1
}
```

Manifest loaders validate the schema version before loading.

---

## Configuration Schema Versioning

Configuration entries are validated against versioned schemas.

Each schema defines:

- supported fields
- data types
- defaults
- migration rules

---

## Semantic Versioning

Application releases follow Semantic Versioning.

```text
MAJOR.MINOR.PATCH

```

Example:

```text
0.1.0
0.2.0
1.0.0

```

Meaning:

| Change            | Version |
| ----------------- | ------- |
| Breaking changes  | Major   |
| New functionality | Minor   |
| Bug fixes         | Patch   |

Application versioning is independent of API contract versions.

---

## Compatible Changes

The following changes are considered backward compatible.

- Adding optional fields
- Adding new endpoints
- Adding new capabilities
- Adding new event types
- Adding metadata
- Extending enumerations where documented

Existing clients continue functioning.

---

## Breaking Changes

Examples of breaking changes include:

- Removing fields
- Renaming fields
- Changing data types
- Changing endpoint semantics
- Removing event types
- Modifying required fields

Breaking changes require a new contract version.

---

## Optional Fields

Optional fields are the preferred mechanism for extending contracts.

Example:

Version 1

```json
{
  "message": "Hello"
}
```

Version 2

```json
{
  "message": "Hello",
  "metadata": {}
}
```

Version 1 clients simply ignore the new field.

---

## Unknown Fields

Clients should ignore unknown fields whenever possible.

This allows servers to evolve without breaking older clients.

---

## Unknown Event Types

Streaming clients should safely ignore unsupported event types.

Example:

```text
Unknown Event

↓

Ignored

↓

Continue Streaming

```

The stream should remain usable.

---

## Version Negotiation

Currently, the backend publishes supported versions.

Future extensions may introduce explicit version negotiation.

Example:

```text
Client

↓

Supported Versions

↓

Server

↓

Selected Version

```

---

## Deprecation Strategy

Deprecated features remain available for a defined transition period.

Typical lifecycle:

```text
Introduced

↓

Supported

↓

Deprecated

↓

Removed

```

Deprecation should always be documented.

---

## Migration Strategy

When introducing a new version:

1. Publish the new version.
2. Preserve the previous version.
3. Update documentation.
4. Provide migration guidance.
5. Remove obsolete versions only after sufficient transition time.

---

## Validation

Every contract is validated before use.

Validation includes:

- schema version
- required fields
- data types
- compatibility
- references

Invalid contracts are rejected.

---

## Versioning and Bootstrap

Bootstrap exposes all active contract versions.

Clients rely on this information to determine compatibility before loading additional resources.

---

## Versioning and Registries

Registries validate manifest versions during discovery.

Only supported schema versions are accepted.

Unsupported manifests remain unloaded.

---

## Versioning and Configuration

Configuration schemas evolve independently.

Older configuration may be migrated during application startup or administrative updates.

---

## Versioning and Extensions

Plugins and future extensions should define their own versioned contracts.

This ensures that independently developed modules can evolve without affecting the core platform.

---

## Best Practices

Recommended guidelines:

- Never reuse version numbers.
- Prefer additive changes.
- Avoid breaking changes whenever possible.
- Document migrations.
- Validate versions before loading.
- Preserve compatibility for public contracts.

---

## Future Evolution

Potential future enhancements include:

- API negotiation
- Client capability negotiation
- Plugin compatibility matrices
- Multi-version support
- Automatic schema migration
- Compatibility reporting

The current architecture already supports these extensions.

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Manifest-System]]
- [[Registry-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[UI-Schema]]

---

## ADRs

- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0006-API-Contracts-and-Versioning]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

## Summary

Contract Versioning ensures that Kernschmied can evolve without disrupting existing clients or integrations.

By versioning every public contract independently, preferring additive evolution, validating schema compatibility, and exposing supported versions through the Bootstrap API, the platform provides a predictable and future-proof foundation for long-term development while minimizing the impact of architectural change.

---

Back to [[Home]].
