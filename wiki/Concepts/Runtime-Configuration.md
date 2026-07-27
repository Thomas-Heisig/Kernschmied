# Runtime Configuration

The **Runtime Configuration** concept defines how Kernschmied stores, resolves, validates, and applies application behavior while the system is running.

Unlike traditional applications that require configuration changes to be written into files and followed by a restart, Kernschmied treats business configuration as structured runtime data. Configuration is stored in the database, validated against versioned schemas, resolved through deterministic inheritance, and applied automatically to subsequent requests.

This architecture allows administrators to modify application behavior without redeploying or restarting the backend while preserving strong validation, auditability, and stable public contracts.

---

# Goals

The Runtime Configuration architecture is designed to provide:

- Runtime-editable behavior
- Deterministic configuration resolution
- Schema validation
- Versioned configuration
- Revision tracking
- Auditability
- Secure administration
- Future scalability

---

# Core Principle

Runtime configuration separates **how the application behaves** from **how the application starts**.

```text
Environment

↓

Bootstrap

↓

Runtime Configuration

↓

Application Behavior
```

Infrastructure remains static during startup, while business behavior can evolve during operation.

---

# Why Runtime Configuration?

Traditional applications often store nearly all settings in configuration files.

```text
config.yml

↓

Restart Application

↓

New Behavior
```

This approach creates operational challenges:

- application downtime
- duplicated configuration
- difficult administration
- deployment-dependent changes

Kernschmied instead stores business configuration in the database.

```text
Configuration Update

↓

Validation

↓

Database

↓

Revision++

↓

Next Request Uses New Configuration
```

No restart is required.

---

# Infrastructure vs Runtime Configuration

A clear separation exists between infrastructure configuration and runtime configuration.

## Infrastructure Configuration

Infrastructure configuration is required before the application starts.

Typical examples include:

- database connection
- deployment profile
- logging
- secret keys
- provider endpoints

These values belong in environment variables.

---

## Runtime Configuration

Runtime configuration controls application behavior.

Examples include:

- default models
- prompt fragments
- UI schemas
- enabled tools
- feature flags
- hierarchy behavior
- generation parameters

These values are stored in the database.

---

# High-Level Architecture

```text
Environment

↓

Bootstrap

↓

Configuration Service

↓

Configuration Resolver

↓

Resolved Configuration

↓

Application Services
```

Each component has a clearly defined responsibility.

---

# Runtime Configuration Lifecycle

Configuration changes follow a deterministic lifecycle.

```text
Administrator

↓

Configuration API

↓

Validation

↓

Database

↓

Revision++

↓

Cache Invalidation

↓

Next Request
```

Every successful update becomes effective for future requests.

---

# Configuration Storage

Runtime configuration is stored as structured data.

Typical information includes:

- configuration values
- schema version
- metadata
- revision information
- audit references

The database acts as the authoritative source of runtime behavior.

---

# Configuration Resolution

Application services never read configuration directly.

Instead:

```text
Configuration

↓

Configuration Resolver

↓

Resolved Configuration

↓

Business Service
```

The resolver applies inheritance, merge rules, and validation before returning an immutable configuration object.

---

# Configuration Scopes

Runtime configuration may be defined at multiple levels.

Typical scopes include:

```text
System

↓

Organization

↓

Workspace

↓

Project

↓

Conversation

↓

User

↓

Request
```

Lower scopes extend or override inherited configuration according to defined merge strategies.

---

# Inheritance

Configuration follows the hierarchy.

Example:

```text
System

↓

Organization

↓

Project

↓

Conversation

↓

Effective Configuration
```

Every request receives exactly one resolved configuration.

---

# Merge Strategies

Configuration sections may define different merge strategies.

Common strategies include:

| Strategy | Description |
|----------|-------------|
| Replace | Replace inherited value |
| Append | Extend inherited collection |
| Deep Merge | Merge structured objects |
| Disable | Remove inherited configuration |

Merge behavior is determined by configuration schemas rather than application code.

---

# Schema Validation

Every runtime configuration entry is validated.

Validation includes:

- schema version
- required properties
- value types
- enumerations
- ranges
- reference integrity

Invalid configuration is rejected before activation.

---

# Configuration Revisions

Each successful configuration update increments the configuration revision.

```text
Revision 24

↓

Configuration Updated

↓

Revision 25
```

Revision numbers allow efficient cache invalidation and synchronization between frontend and backend.

---

# Cache Invalidation

Configuration changes invalidate cached configuration automatically.

```text
Configuration Updated

↓

Revision++

↓

Cache Invalid

↓

Reload Configuration
```

Neither the backend nor the frontend compares complete configuration objects.

---

# Audit Logging

Every configuration change generates an audit record.

Typical information includes:

- authenticated user
- timestamp
- changed scope
- previous value
- new value
- revision

Audit logs provide traceability for administrative actions.

---

# Runtime Updates

Runtime-editable configuration becomes active immediately after successful validation and persistence.

Examples include:

- changing the default model
- updating prompt fragments
- enabling new UI features
- modifying hierarchy behavior
- adjusting generation parameters

Existing requests continue using the configuration that was resolved when they started.

---

# Backend Integration

Many backend subsystems depend on runtime configuration.

Examples include:

- Chat Service
- Prompt Resolver
- Model Registry
- Tool Registry
- UI Schema generation
- authorization policies

The Configuration Service acts as the single source of truth.

---

# Frontend Integration

The frontend does not resolve configuration itself.

Instead:

```text
Backend

↓

Resolved Configuration

↓

Generated UI Schema

↓

Frontend
```

The frontend only consumes backend-generated contracts.

---

# Bootstrap Integration

Bootstrap initializes the runtime configuration subsystem.

```text
Bootstrap

↓

Load Configuration

↓

Validate

↓

Initialize Resolver

↓

Application Ready
```

After startup, configuration updates occur dynamically.

---

# Security

Runtime configuration is protected through multiple layers.

Configuration updates require:

- authentication
- authorization
- schema validation
- audit logging
- revision tracking

Only authorized administrators may modify runtime configuration.

---

# Error Handling

Configuration updates fail atomically.

```text
Validate

↓

Persist

↓

Commit

↓

Revision++
```

If validation or persistence fails:

```text
Validation Failed

↓

Rollback

↓

Revision Unchanged
```

The previous configuration remains active.

---

# Performance

Runtime configuration is optimized through:

- immutable configuration snapshots
- revision-aware caching
- efficient hierarchy traversal
- lightweight merge algorithms
- asynchronous persistence

Configuration resolution is inexpensive enough to occur for every request.

---

# Benefits

The Runtime Configuration architecture provides several important advantages.

## Operational Flexibility

Behavior changes without restarting the application.

---

## Centralized Administration

Business configuration is managed through APIs rather than deployment files.

---

## Consistency

Every request follows the same deterministic configuration resolution process.

---

## Security

Configuration changes are validated, authorized, and audited.

---

## Scalability

The architecture supports increasingly complex applications without introducing configuration sprawl.

---

# Future Extensions

The architecture supports future capabilities including:

- scheduled configuration activation
- configuration templates
- tenant-specific configuration
- staged configuration deployment
- configuration rollback
- configuration comparison
- distributed configuration synchronization

These features can be introduced without changing the existing configuration model.

---

# Relationship to Other Concepts

Runtime Configuration integrates closely with:

- [[Configuration]]
- [[Configuration Revisions]]
- [[Hierarchy]]
- [[Prompt Inheritance]]
- [[Dynamic-UI]]

---

# Related Documentation

## Concepts

- [[Configuration]]
- [[Configuration Revisions]]
- [[Hierarchy]]
- [[Dynamic-UI]]
- [[Versioning]]

---

## Architecture

- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Prompt-Inheritance]]
- [[Request-Lifecycle]]
- [[Bootstrap-Lifecycle]]

---

## Backend

- [[Configuration]]
- [[Database]]
- [[Hierarchy]]
- [[Chat]]
- [[Security]]

---

## APIs

- [[Configuration]]
- [[Bootstrap]]
- [[Hierarchy]]

---

# Summary

Runtime Configuration enables Kernschmied to modify application behavior dynamically while the system is running by storing business configuration in the database instead of static configuration files.

Through deterministic configuration resolution, hierarchical inheritance, schema validation, revision tracking, audit logging, and seamless integration with the hierarchy, prompt, registry, and UI systems, Runtime Configuration provides a flexible, secure, and scalable foundation for managing application behavior without requiring service restarts or compromising architectural stability.

---

Back to [[Home]].
