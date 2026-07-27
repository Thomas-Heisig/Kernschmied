# ADR-0003: Registry-Based Extension Architecture

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable platform rather than a single-purpose business application.

The platform must support the addition of new capabilities throughout its lifetime without requiring extensive modifications to the existing codebase.

Examples include:

- AI model providers
- AI models
- backend tools
- frontend components
- frontend actions
- hierarchy node types
- prompt providers
- authentication providers (future)
- storage providers (future)
- import/export formats
- plugins

A central architectural challenge is ensuring that these extension points remain:

- predictable
- secure
- testable
- maintainable
- discoverable

The platform therefore requires a consistent mechanism for managing extensible functionality.

---

# Problem

Without a common extension mechanism, new functionality tends to be integrated directly into existing code.

Typical examples include:

```python
if provider == "ollama":
    ...

elif provider == "openai":
    ...

elif provider == "transformers":
    ...
```

or

```tsx
if (component.type === "table") {
    ...
}

if (component.type === "tree") {
    ...
}
```

As the application evolves, this approach creates several problems.

---

## Growing Conditional Logic

Every new implementation requires another conditional branch.

Over time these become increasingly difficult to understand and maintain.

---

## Tight Coupling

Core application code becomes directly dependent upon every supported implementation.

Adding one provider often requires modifying multiple files.

---

## Limited Extensibility

Third-party extensions become difficult because new functionality must be inserted into existing code rather than registered independently.

---

## Increased Testing Complexity

Every modification risks affecting unrelated implementations.

Regression testing becomes progressively more expensive.

---

## Violated Open/Closed Principle

Core components remain in constant modification instead of being extended through composition.

---

# Decision

Kernschmied adopts a **registry-based extension architecture**.

Every extensible subsystem is represented by an explicit registry responsible for:

- registration
- discovery
- lookup
- validation
- lifecycle management
- capability metadata

The application core communicates only with registries and never directly with individual implementations.

---

# Architectural Principle

> **Core systems depend on registries.  
> Registries depend on implementations.  
> Implementations never modify the core.**

---

# High-Level Architecture

```text
                Application

                     │

                     ▼

              Registry Interface

                     │

      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼

 Implementation   Implementation   Implementation
       A               B               C
```

---

# Why Registries?

Registries provide several important architectural advantages.

## Explicit Discovery

Every supported implementation is registered intentionally.

Nothing becomes available merely because code exists.

---

## Stable Contracts

The application communicates with interfaces instead of concrete implementations.

---

## Central Validation

Registration can verify:

- unique identifiers
- supported versions
- manifests
- required capabilities

before the implementation becomes available.

---

## Runtime Introspection

Administrative interfaces can inspect available extensions through the registry.

---

## Consistent Lifecycle

Every extension follows the same initialization process.

---

# Registry Responsibilities

Every registry should support the following responsibilities.

## Registration

New implementations register themselves during application startup.

---

## Lookup

Applications request implementations by identifier.

Example:

```text
"ollama"

↓

Model Registry

↓

Ollama Provider
```

---

## Validation

Registries verify:

- unique IDs
- compatibility
- manifest correctness
- dependencies

---

## Metadata

Registries expose metadata for administration and diagnostics.

Typical metadata includes:

- identifier
- version
- description
- capabilities
- supported features

---

## Lifecycle

Registries control:

- initialization
- activation
- shutdown
- health status

---

# Registry Types

Kernschmied contains several specialized registries.

---

## Model Registry

Responsible for:

- model providers
- model manifests
- model capabilities
- inference configuration

Examples:

- Ollama
- Transformers
- llama.cpp
- OpenAI-compatible APIs

---

## Tool Registry

Responsible for backend tools.

Examples:

- calculator
- filesystem
- web search
- email
- OCR
- SQL

The registry validates every tool before activation.

---

## Component Registry

Frontend registry that maps schema component types to React components.

Example:

```text
"text"

↓

TextField
```

---

## Action Registry

Maps schema actions to frontend action handlers.

Example:

```text
"submit"

↓

Submit Handler
```

---

## Hierarchy Registry

Responsible for supported hierarchy node types.

Examples:

- project
- folder
- workspace
- configuration
- prompt
- model

---

## Layout Registry

Maps layout identifiers to layout implementations.

Examples:

- grid
- tabs
- accordion
- split-view

---

## Prompt Provider Registry

Future registry responsible for prompt inheritance providers.

---

# Registration Process

Every registry follows the same lifecycle.

```text
Application Startup

↓

Load Manifest

↓

Validate

↓

Register

↓

Registry Ready
```

Invalid implementations are rejected before the application becomes operational.

---

# Registration Requirements

Every implementation should provide:

- unique identifier
- version
- description
- supported capabilities
- manifest
- implementation object

Optional metadata may include:

- documentation
- author
- homepage
- deprecation information

---

# Manifests

Registries use manifests to describe implementations.

Examples:

- `model.json`
- `tool.json`

Manifests are declarative.

They describe an implementation without executing it.

This improves validation and security.

---

# Lookup

Registry lookup should be deterministic.

```text
Identifier

↓

Registry

↓

Implementation
```

Unknown identifiers return a controlled failure rather than causing application instability.

---

# Duplicate Registration

Identifiers must be globally unique within a registry.

Example:

```text
calculator

↓

Implementation A

↓

Implementation B
```

Duplicate registrations are rejected during startup.

---

# Version Compatibility

Registries validate compatibility between:

- application version
- manifest version
- schema version
- implementation version

Unsupported versions are rejected before activation.

---

# Dependency Resolution

Implementations may depend on other platform capabilities.

Registries should validate these dependencies before registration.

Example:

```text
Plugin

↓

Requires

↓

Tool Registry

↓

Calculator
```

If dependencies are unavailable, registration fails gracefully.

---

# Runtime Discovery

Administrative interfaces may query registries to display available functionality.

Typical information includes:

- installed implementations
- versions
- capabilities
- health status
- configuration state

---

# Error Handling

Registration failures should be isolated.

```text
Plugin

↓

Validation Error

↓

Registration Failed

↓

Continue Startup
```

A faulty extension should not prevent unrelated extensions from functioning unless the failed extension is mandatory.

---

# Security Considerations

Registries follow a strict allow-list model.

Only validated implementations become available.

Registries must never:

- execute arbitrary code during discovery
- load implementations from untrusted locations
- bypass validation
- allow duplicate identifiers
- expose unvalidated implementations

Registration is explicit and deterministic.

---

# Performance Considerations

Registries should provide:

- constant-time lookup
- cached metadata
- immutable registration after startup
- lightweight discovery
- lazy initialization where appropriate

Lookup performance should remain effectively independent of registry size.

---

# Consequences

## Positive

### Open/Closed Architecture

The platform grows through extension rather than modification.

---

### Reduced Coupling

Core services remain independent from concrete implementations.

---

### Better Testing

Individual implementations can be tested independently of the registry.

---

### Consistent Extension Model

Every extensible subsystem follows the same architectural pattern.

---

### Improved Diagnostics

Registries expose implementation metadata for administration and troubleshooting.

---

## Negative

### Additional Infrastructure

Registries require:

- interfaces
- validation
- lifecycle management
- documentation

---

### More Startup Work

Registration and validation increase startup complexity, although only once during initialization.

---

# Alternatives Considered

## Conditional Logic

Advantages:

- simple
- familiar

Disadvantages:

- poor scalability
- tight coupling
- repeated modification

Rejected.

---

## Dynamic Reflection

Automatically discovering implementations via unrestricted reflection.

Advantages:

- minimal registration effort

Disadvantages:

- unpredictable behavior
- weaker validation
- security concerns
- reduced startup determinism

Rejected.

---

## Dependency Injection Alone

Dependency injection manages object creation but does not provide discovery, metadata, validation, or runtime lookup.

Dependency injection complements registries but does not replace them.

Rejected as the sole extension mechanism.

---

# Risks

Potential risks include:

- overly large registries
- inconsistent registration APIs
- missing validation
- circular dependencies
- undocumented capabilities

Mitigation strategies include:

- common registry interfaces
- strict manifest validation
- startup diagnostics
- automated testing
- architectural reviews

---

# Implementation Notes

All registries should provide:

- strongly typed interfaces
- immutable registrations after initialization
- structured error reporting
- capability metadata
- deterministic lookup
- comprehensive unit tests

Registries should be registered using dependency injection rather than global mutable state.

---

# Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0004-Versioned-Contracts]]
- [[ADR-0005-Deny-by-Default-Security]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Registry-Architecture]]
- [[Manifest-System]]

---

## Frontend

- [[Component-Registry]]
- [[Action-Registry]]

---

## Backend

- [[Model-Registry]]
- [[Tool-Registry]]
- [[Hierarchy]]
- [[Configuration]]

---

## Concepts

- [[Plugin-System]]
- [[Dependency-Injection]]
- [[Runtime-Configuration]]
- [[Contracts]]

---

# Decision Summary

Kernschmied adopts a **registry-based extension architecture** for every major extension point in the platform.

Rather than embedding implementation-specific logic into the application core, functionality is introduced through explicit registries that provide deterministic registration, validation, discovery, metadata, and lifecycle management.

This decision enables a modular, secure, and maintainable platform that can evolve over many years while preserving stable contracts and minimizing coupling between the application core and its extensions.

---

Back to [[Home]].