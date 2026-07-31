# Manifest System

The **Manifest System** defines how extensible components are described, discovered, validated, and registered within the Kernschmied platform.

Rather than relying on hardcoded configuration or executable discovery logic, Kernschmied uses **declarative manifests** to describe models, tools, providers, and future extension types.

A manifest contains metadata—not implementation. It tells the platform **what a component is**, **what it supports**, and **how it should be registered**, while the implementation remains isolated inside the corresponding backend module.

The Manifest System forms one of the fundamental building blocks of Kernschmied's modular architecture.

---

# Goals

The Manifest System is designed to provide:

- Declarative extension discovery
- Stable metadata contracts
- Versioned schemas
- Safe validation
- Runtime discoverability
- Provider independence
- Forward compatibility
- Controlled extensibility

---

# Design Principles

The Manifest System follows several core architectural principles.

## Metadata, Not Code

A manifest describes a component.

It does **not** contain executable business logic.

Example:

```text
Manifest

↓

Metadata

↓

Validation

↓

Registry

↓

Runtime
```

---

## Explicit Discovery

Components are never loaded automatically simply because they exist.

Each manifest must be:

- discovered
- parsed
- validated
- registered
- authorized

Only then does the component become available.

---

## Versioned Contracts

Every manifest is validated against a versioned schema.

Example:

```json
{
  "schema": 1
}
```

Schema evolution remains independent from application releases.

---

# Manifest Overview

```text
                 Manifest

                      │

      ┌───────────────┼───────────────┐

      │                               │

   Metadata                      Runtime

      │                               │

Validation                   Registry
```

The manifest serves as the bridge between implementation and runtime.

---

# Supported Manifest Types

Current manifest types include:

| Manifest     | Purpose             |
| ------------ | ------------------- |
| `model.json` | AI model definition |
| `tool.json`  | Tool definition     |

Future versions may introduce:

- `plugin.json`
- `workflow.json`
- `schema.json`
- `provider.json`

---

# Manifest Lifecycle

Every manifest follows the same lifecycle.

```text
Discovery

↓

Read

↓

Validation

↓

Registration

↓

Runtime Usage

↓

Reload (optional)
```

This lifecycle is deterministic.

---

# Discovery

The application scans predefined locations during startup.

Example:

```text
/models

/tools
```

Only expected directories are searched.

Arbitrary filesystem traversal is intentionally avoided.

---

# Loading

Each discovered manifest is read as structured JSON.

```text
model.json

↓

JSON Parser

↓

Object Model
```

Malformed files are rejected immediately.

---

# Validation

Every manifest is validated before registration.

Typical validation includes:

- schema version
- required fields
- identifier uniqueness
- supported capabilities
- data types
- references

Invalid manifests never become active.

---

# Registration

Validated manifests are passed to the appropriate registry.

Example:

```text
Manifest

↓

Model Registry

↓

Available Model
```

The registry owns runtime visibility.

---

# Runtime Usage

Application services query registries rather than manifests directly.

```text
Chat Service

↓

Model Registry

↓

Resolved Model
```

Manifests remain immutable metadata.

---

# Model Manifest

Model manifests describe available AI models.

Typical information includes:

- identifier
- display name
- provider
- capabilities
- context length
- supported features

Example structure:

```json
{
  "schema": 1,
  "id": "qwen25-7b",
  "provider": "ollama"
}
```

---

# Tool Manifest

Tool manifests describe callable tools.

Typical information includes:

- identifier
- display name
- category
- permissions
- input schema
- output schema

Example:

```json
{
  "schema": 1,
  "id": "calculator"
}
```

---

# Manifest Schema

Every manifest type has a dedicated schema.

Example:

```text
Manifest

↓

Schema

↓

Validation

↓

Registry
```

Schemas evolve independently.

---

# Required Fields

Although manifest types differ, common fields include:

- schema
- id
- name
- description

Additional fields depend on the manifest category.

---

# Unique Identifiers

Each manifest identifier must be unique within its registry.

Example:

```text
calculator

weather

filesystem
```

Duplicate identifiers are rejected during registration.

---

# Versioning

Manifest schemas evolve independently from application releases.

Example:

```text
Application

0.4.0

↓

Manifest Schema

Version 2
```

This allows gradual evolution.

---

# Backward Compatibility

New schema versions should remain backward compatible whenever possible.

Preferred strategy:

- add optional fields
- preserve existing semantics
- avoid removing required properties

Breaking changes require a new schema version.

---

# Manifest Discovery Rules

Discovery follows strict rules.

Allowed:

- predefined directories
- expected filenames
- version validation

Not allowed:

- arbitrary recursion
- executable manifests
- remote code loading

---

# Security

Manifests are treated as untrusted input.

Validation includes:

- structure
- types
- supported versions
- identifier validation

A valid manifest does **not** automatically imply a trusted implementation.

---

# Relationship to Registries

Registries consume manifests.

```text
Manifest

↓

Registry

↓

Lookup

↓

Runtime
```

The registry is responsible for runtime management.

---

# Relationship to Providers

Model manifests reference providers.

Example:

```text
Model Manifest

↓

Provider ID

↓

Provider Registry

↓

Backend
```

The manifest never instantiates providers directly.

---

# Relationship to Configuration

Configuration may enable or disable components described by manifests.

```text
Manifest

↓

Registry

↓

Configuration

↓

Runtime Availability
```

A valid manifest may still be disabled through configuration.

---

# Relationship to Bootstrap

Bootstrap exposes registry revisions.

Clients may detect changes in:

- model manifests
- tool manifests

without downloading every manifest individually.

---

# Manifest Reloading

Future versions may support runtime reloads.

Typical sequence:

```text
Manifest Changed

↓

Validation

↓

Registry Refresh

↓

Revision++

↓

Clients Reload
```

The architecture already supports this behavior.

---

# Error Handling

Manifest loading errors are isolated.

```text
Invalid Manifest

↓

Registry Error

↓

Skip Manifest

↓

Continue Startup
```

One invalid manifest should not prevent unrelated components from loading.

---

# Performance

Manifest loading occurs primarily during startup.

Optimizations include:

- one-time parsing
- cached metadata
- incremental reloads
- registry indexing

Runtime services never repeatedly parse manifests.

---

# Best Practices

Recommended guidelines:

- Keep manifests declarative.
- Never embed executable code.
- Version every schema.
- Validate everything.
- Use stable identifiers.
- Document optional fields.
- Preserve backward compatibility.
- Separate metadata from implementation.

---

# Future Manifest Types

The architecture allows additional manifest categories.

Possible examples:

- Authentication providers
- Storage providers
- Notification providers
- Workflow definitions
- Localization packages
- Reporting modules
- Automation rules

No architectural redesign is required.

---

# Manifest Directory Structure

Typical layout:

```text
backend/

├── models/
│   ├── ollama/
│   │   ├── model.json
│   │   └── provider.py
│   └── openai/
│       ├── model.json
│       └── provider.py
│
├── tools/
│   ├── calculator/
│   │   ├── tool.json
│   │   └── tool.py
│   └── weather/
│       ├── tool.json
│       └── tool.py
```

This organization keeps metadata and implementation together while preserving separation of concerns.

---

# Relationship to Other Architecture

The Manifest System forms the entry point for several architectural subsystems.

```text
Manifest

↓

Validation

↓

Registry

↓

Configuration

↓

Runtime

↓

Application Services
```

It therefore connects:

- Registry Architecture
- Configuration Architecture
- Contract Versioning
- Extension Points

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Registry-Architecture]]
- [[Extension-Points]]
- [[Configuration-Architecture]]
- [[Contract-Versioning]]

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

The Manifest System provides a declarative, versioned, and secure mechanism for describing extensible platform components without embedding implementation details into runtime configuration.

By separating metadata from executable code, validating every manifest against versioned schemas, and integrating manifests through controlled registries, Kernschmied achieves a highly modular architecture that supports safe extensibility, deterministic startup behavior, and long-term maintainability while preserving stable public contracts.

---

Back to [[Home]].
