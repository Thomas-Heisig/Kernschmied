# Schema Versioning

Schema Versioning defines how Kernschmied evolves its public contracts while preserving compatibility between the backend, frontend, plugins, configuration, and external integrations.

Instead of treating schemas as implementation details, Kernschmied considers every schema to be a versioned contract. Each contract has an explicit version, a defined lifecycle, and compatibility guarantees that allow the platform to evolve without breaking existing clients.

Schema Versioning is a fundamental building block of the platform's long-term stability and extensibility.

---

# Goals

The Schema Versioning architecture is designed to provide:

- Stable public contracts
- Explicit compatibility guarantees
- Predictable platform evolution
- Independent frontend and backend development
- Safe plugin integration
- Reliable API evolution
- Deterministic validation
- Long-term maintainability

---

# Core Principle

Every schema exposed by the platform has an explicit version.

```text
Schema

↓

Version

↓

Validation

↓

Consumer
```

Schemas are never considered unversioned implementation details.

---

# Why Version Schemas?

Without explicit versioning, even small changes may unintentionally break consumers.

```text
Backend

↓

Changed Property

↓

Frontend Failure
```

With versioned schemas:

```text
Schema v1

↓

Schema v2

↓

Compatibility Rules

↓

Safe Evolution
```

Consumers always know which contract they are processing.

---

# What Is a Schema?

Within Kernschmied, a schema describes structured data exchanged between components.

Examples include:

- UI schemas
- configuration schemas
- plugin manifests
- model manifests
- tool manifests
- API payloads
- hierarchy definitions
- bootstrap responses

Every schema represents a contract rather than an implementation.

---

# High-Level Architecture

```text
Schema Definition

↓

Version Identifier

↓

Validation

↓

Registry

↓

Consumer
```

Versioning is integrated into every stage of the schema lifecycle.

---

# Explicit Version Numbers

Every schema contains an explicit version identifier.

Example:

```text
schema_version = 1
```

Consumers validate compatibility before processing the schema.

---

# Compatibility

Schema compatibility is intentional and predictable.

Typical compatibility rules include:

| Change | Compatible |
|---------|------------|
| Add optional field | Yes |
| Add optional metadata | Yes |
| Remove required field | No |
| Rename required field | No |
| Change data type | No |
| Remove enum value | Usually No |

Breaking changes require a new schema version.

---

# Backward Compatibility

Whenever practical, newer platform versions continue supporting older schema versions.

```text
Backend

↓

Supports

↓

Schema v1

Schema v2
```

This allows gradual upgrades.

---

# Forward Compatibility

Consumers should ignore unknown optional fields whenever possible.

Example:

```text
Known Fields

+

Unknown Metadata

↓

Continue Processing
```

This enables incremental platform evolution.

---

# Validation

Every schema is validated before use.

Validation includes:

- schema version
- required properties
- property types
- enumerations
- references
- structural consistency

Unsupported schema versions are rejected.

---

# Schema Evolution

Schemas evolve deliberately.

Typical evolution path:

```text
Version 1

↓

Version 2

↓

Version 3
```

Each version represents a stable contract.

---

# API Versioning

API payloads rely on versioned schemas.

```text
REST Endpoint

↓

Schema Version

↓

Validation

↓

Consumer
```

API evolution remains independent from implementation details.

---

# UI Schema Versioning

The frontend validates UI schema versions before rendering.

```text
UI Schema

↓

Version Check

↓

Schema Renderer

↓

Rendered Interface
```

Unsupported versions produce a safe error instead of undefined behavior.

---

# Configuration Schemas

Runtime configuration also follows explicit schema versions.

```text
Configuration

↓

Schema Version

↓

Validation

↓

Configuration Service
```

Configuration migrations become deterministic.

---

# Manifest Versioning

Plugin, tool, and model manifests are versioned independently.

Examples include:

- plugin manifest version
- model manifest version
- tool manifest version

Each manifest evolves according to its own lifecycle.

---

# Registry Integration

Registries validate schema compatibility before registration.

```text
Manifest

↓

Schema Validation

↓

Registry

↓

Available Component
```

Invalid or unsupported schemas are rejected.

---

# Bootstrap Integration

Bootstrap exposes schema version information to clients.

Example:

```text
Bootstrap

↓

Versions

↓

Frontend Initialization
```

The frontend immediately knows which contracts are supported.

---

# Plugin Compatibility

Plugins declare the schema versions they support.

```text
Plugin

↓

Supported Schema Versions

↓

Compatibility Check
```

Incompatible plugins are rejected during startup.

---

# Migration

Schema changes should be introduced through controlled migrations.

Typical migration process:

```text
Old Schema

↓

Migration

↓

Validated Schema

↓

New Version
```

Migrations preserve data integrity while enabling evolution.

---

# Deprecation

Schemas may be deprecated before removal.

Lifecycle example:

```text
Supported

↓

Deprecated

↓

Removed
```

Deprecation gives consumers time to migrate.

---

# Error Handling

Unsupported schema versions produce structured errors.

Example:

```text
Unknown Version

↓

Validation Failed

↓

Structured Error Response
```

Consumers never process incompatible schemas.

---

# Security

Schema Versioning contributes to platform security by ensuring that only validated contracts are accepted.

Validation prevents:

- unsupported payloads
- malformed manifests
- incompatible plugins
- undefined runtime behavior

Unknown versions are rejected rather than interpreted heuristically.

---

# Performance

Version validation is inexpensive.

Typical workflow:

```text
Read Version

↓

Lookup Validator

↓

Validate

↓

Continue
```

The overhead is negligible compared to application logic.

---

# Best Practices

Recommended practices include:

- version every public schema
- never silently change contracts
- keep compatibility rules documented
- validate versions before processing
- introduce breaking changes intentionally
- deprecate before removal

These principles keep the ecosystem predictable.

---

# Future Extensions

The Schema Versioning architecture supports future capabilities including:

- automated schema migration
- schema negotiation
- compatibility matrices
- multi-version validators
- generated migration reports
- semantic version metadata
- schema lifecycle dashboards

These capabilities can be added without changing the existing versioning model.

---

# Relationship to Other Concepts

Schema Versioning integrates closely with:

- [[Versioning]]
- [[Configuration]]
- [[Dynamic-UI]]
- [[Plugin-System]]
- [[Runtime Configuration]]

---

# Related Documentation

## Concepts

- [[Versioning]]
- [[Configuration]]
- [[Dynamic-UI]]
- [[Plugin-System]]
- [[Runtime Configuration]]

---

## Architecture

- [[Contract-Versioning]]
- [[Manifest-System]]
- [[Registry-Architecture]]
- [[UI-Schema-Pipeline]]

---

## Backend

- [[Configuration]]
- [[Bootstrap]]
- [[Model-Registry]]
- [[Tool-Registry]]

---

## Frontend

- [[UI-Schema]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]

---

# Summary

Schema Versioning ensures that every public contract within Kernschmied evolves in a controlled, predictable, and compatible manner. By assigning explicit versions to schemas, validating compatibility before use, and supporting structured migration and deprecation strategies, the platform can evolve without breaking existing integrations.

Through consistent versioning across APIs, UI schemas, runtime configuration, manifests, registries, and plugins, Schema Versioning provides the foundation for long-term stability, independent component evolution, and reliable interoperability throughout the Kernschmied ecosystem.

---

Back to [[Home]].
