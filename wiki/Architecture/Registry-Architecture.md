# Registry Architecture

The **Registry Architecture** is one of the core architectural patterns of the Kernschmied platform. It provides a centralized, deterministic, and extensible mechanism for discovering, validating, registering, and resolving runtime components.

Rather than hardcoding implementations throughout the application, Kernschmied uses specialized registries that expose stable public contracts while hiding implementation details. This enables the platform to support multiple providers, tools, schemas, and future extension types without modifying the application core.

The Registry Architecture works closely with the **Manifest System**, **Configuration Architecture**, and **Dependency Injection** to create a modular and maintainable platform.

---

# Goals

The Registry Architecture is designed to provide:

- Centralized component discovery
- Deterministic runtime behavior
- Stable public contracts
- Provider independence
- Safe extensibility
- Runtime validation
- Version compatibility
- Efficient lookup
- Failure isolation

---

# Architectural Principles

The registry subsystem follows several fundamental principles.

## Explicit Registration

Components never become available automatically.

Every component must be:

- discovered
- validated
- registered
- activated

Only registered components may be used.

---

## Separation of Metadata and Implementation

Registries store metadata and references to implementations.

They do **not** implement business logic themselves.

```text
Manifest

↓

Registry

↓

Implementation

↓

Runtime
```

---

## Stable Runtime Contracts

Application services communicate only with registries.

They never access:

- filesystem structures
- manifests
- provider implementations

This isolates implementation changes from business logic.

---

# Registry Overview

```text
                    Registry Layer

                          │

      ┌───────────────────┼───────────────────┐

      │                   │                   │

 Model Registry     Tool Registry     Future Registries

      │                   │

      └─────────────┬─────┘

                    │

             Application Services
```

Each registry owns a single category of runtime components.

---

# Why Registries?

Without registries, services would need to know:

- filesystem layout
- provider classes
- tool implementations
- configuration locations

Instead:

```text
Service

↓

Registry

↓

Resolved Component
```

The service remains independent of implementation details.

---

# Registry Lifecycle

Every registry follows the same lifecycle.

```text
Startup

↓

Discovery

↓

Validation

↓

Registration

↓

Ready

↓

Runtime Lookup
```

This lifecycle is deterministic and repeatable.

---

# Discovery

Registries discover components through the Manifest System.

Examples:

```text
models/

↓

model.json

↓

Model Registry
```

```text
tools/

↓

tool.json

↓

Tool Registry
```

Discovery never executes arbitrary code.

---

# Validation

Before registration, every component is validated.

Typical validation includes:

- schema version
- required fields
- unique identifier
- manifest integrity
- capability definitions
- provider compatibility

Invalid components are rejected.

---

# Registration

Validated components are added to the registry.

```text
Validated Manifest

↓

Registry

↓

Available Component
```

Registration creates the runtime metadata used by the application.

---

# Runtime Lookup

Application services resolve components through identifiers.

Example:

```text
Chat Service

↓

Model Registry

↓

"qwen2.5"

↓

Provider Instance
```

The service remains unaware of provider implementations.

---

# Registry Responsibilities

A registry is responsible for:

- discovery
- validation
- registration
- lookup
- capability exposure
- version validation
- runtime metadata
- lifecycle management

Registries do **not** perform business operations.

---

# Model Registry

The Model Registry manages all available AI models.

Responsibilities include:

- loading `model.json`
- validating manifests
- exposing available models
- resolving providers
- reporting capabilities
- maintaining registry revision

The Chat Service depends exclusively on the Model Registry.

---

# Tool Registry

The Tool Registry manages executable tools.

Responsibilities include:

- loading `tool.json`
- validating manifests
- permission metadata
- input/output schemas
- runtime lookup
- execution metadata

The Chat Service never scans the filesystem directly.

---

# Future Registries

The architecture allows additional registries.

Possible examples:

- Plugin Registry
- Workflow Registry
- Notification Registry
- Storage Registry
- Authentication Registry
- Localization Registry
- Policy Registry

These can be introduced without modifying existing registries.

---

# Registry Data Model

Every registered component exposes common metadata.

Typical attributes include:

- identifier
- display name
- description
- version
- capabilities
- provider
- schema version
- availability

Business-specific metadata remains component-specific.

---

# Registry Identifiers

Identifiers uniquely identify components.

Example:

```text
calculator

weather

filesystem

qwen25

gemma3
```

Identifiers are immutable after registration.

---

# Registry Revisions

Every registry maintains an independent revision number.

Example:

```text
Model Registry

Revision 12

↓

Tool Registry

Revision 8
```

Clients use revisions to detect runtime changes.

---

# Bootstrap Integration

Bootstrap exposes registry revisions.

Example:

```json
{
  "revisions": {
    "model_registry": 12,
    "tool_registry": 8
  }
}
```

Clients reload registry data only when revisions change.

---

# Registry Lookup

Typical lookup process:

```text
Identifier

↓

Registry

↓

Validation

↓

Resolved Metadata

↓

Implementation
```

Lookup should execute in constant or near-constant time.

---

# Dependency Injection

Application services receive registries through dependency injection.

```text
Dependency Injection

↓

Model Registry

↓

Chat Service
```

Services never instantiate registries manually.

---

# Provider Resolution

The Model Registry delegates provider creation to provider factories.

```text
Model ID

↓

Model Registry

↓

Provider Factory

↓

Provider Backend
```

Provider implementations remain isolated.

---

# Capability Discovery

Registries expose supported capabilities.

Example:

```text
Model

↓

Capabilities

↓

Streaming

↓

Tool Use

↓

Vision
```

Application services use capabilities instead of provider-specific checks.

---

# Runtime Availability

Configuration may disable registered components.

```text
Registry

↓

Configuration

↓

Available Models
```

Registration and availability are separate concerns.

---

# Caching

Registries cache validated metadata.

Cached information may include:

- manifests
- identifiers
- capabilities
- provider mappings

Caches are refreshed only when revisions change.

---

# Error Handling

Registry failures are isolated.

Example:

```text
Invalid Manifest

↓

Validation Error

↓

Registry Skips Component

↓

Continue Startup
```

One faulty component should not prevent unrelated components from loading.

---

# Security

Registries enforce multiple security boundaries.

Components cannot:

- self-register
- bypass validation
- bypass authorization
- execute before registration

Only validated components become available.

---

# Performance

Registries are optimized for:

- startup discovery
- fast lookup
- minimal allocations
- immutable metadata
- revision-based caching

Runtime lookups should avoid filesystem access entirely.

---

# Version Compatibility

Registries validate manifest versions before registration.

Example:

```text
Manifest

Schema Version

↓

Supported?

↓

Register / Reject
```

Unsupported manifests remain inactive.

---

# Runtime Reload

Future implementations may support hot reload.

Typical sequence:

```text
Manifest Updated

↓

Validation

↓

Registry Refresh

↓

Revision++

↓

Clients Reload
```

The architecture already accommodates this workflow.

---

# Relationship to Other Architecture

The Registry Architecture connects several architectural subsystems.

```text
Manifest System

↓

Registry

↓

Configuration

↓

Dependency Injection

↓

Application Services
```

Registries therefore act as the central integration layer between metadata and runtime execution.

---

# Best Practices

Recommended guidelines:

- One responsibility per registry.
- Keep metadata immutable after registration.
- Never expose implementation details.
- Validate before registration.
- Use stable identifiers.
- Version every public contract.
- Keep lookups deterministic.
- Isolate registry failures.

---

# Future Evolution

The Registry Architecture supports future capabilities including:

- distributed registries
- remote registries
- plugin registries
- dynamic module loading
- registry diagnostics
- dependency graphs
- registry health monitoring

These enhancements can be implemented without changing existing application services.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Manifest-System]]
- [[Extension-Points]]
- [[Configuration-Architecture]]
- [[Contract-Versioning]]
- [[Repository-Structure]]

---

## APIs

- [[Models]]
- [[Tools]]
- [[Bootstrap]]

---

## ADRs

- [[ADR-0003-Registries]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

The Registry Architecture provides a centralized and deterministic mechanism for discovering, validating, registering, and resolving extensible platform components.

By separating metadata from implementation, integrating tightly with the Manifest System, exposing stable runtime contracts, and using revision-based caching and dependency injection, the registry layer enables Kernschmied to remain modular, extensible, secure, and maintainable while supporting future expansion without architectural redesign.

---

Back to [[Home]].
