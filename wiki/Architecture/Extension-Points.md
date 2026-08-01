# Extension Points

The **Extension Points** architecture defines the officially supported mechanisms for extending the Kernschmied platform without modifying the core application.

Kernschmied is designed as a **schema-driven, manifest-based, and registry-oriented platform**. New functionality is introduced through well-defined extension points rather than direct modifications to the existing source code.

This architecture allows the platform to evolve while maintaining stable contracts, predictable behavior, and strong security boundaries.

---

## Goals

The Extension Point architecture is designed to provide:

- Modular extensibility
- Stable public contracts
- Provider independence
- Controlled customization
- Runtime discoverability
- Safe integration
- Forward compatibility
- Maintainable evolution

---

## Design Principles

The extension architecture follows several fundamental principles.

## Explicit Registration

Nothing becomes available automatically.

Every extension must be explicitly:

- discovered
- validated
- registered
- authorized

Automatic execution of unknown code is never permitted.

---

## Stable Contracts

Every extension communicates through stable public contracts.

Examples include:

- manifests
- schemas
- registries
- REST APIs
- configuration contracts

Internal implementation details remain hidden.

---

## Separation of Core and Extensions

The platform separates the immutable core from optional extensions.

```text
                 Kernschmied

                      │

          ┌───────────┴────────────┐

          │                        │

     Core Platform            Extensions

```

The core platform defines extension mechanisms but remains independent of individual extensions.

---

## Extension Categories

The platform currently supports several categories of extensions.

| Category      | Description              |
| ------------- | ------------------------ |
| Models        | AI model providers       |
| Tools         | Callable tools           |
| UI Schemas    | Dynamic user interfaces  |
| Configuration | Runtime behavior         |
| Hierarchy     | Organizational structure |
| Prompts       | Context inheritance      |
| Actions       | Frontend actions         |
| Components    | Frontend rendering       |

Each category has its own validation rules and lifecycle.

---

## Overview

```text
                 Extension

                      │

      ┌───────────────┼────────────────┐

      │               │                │

   Backend        Frontend        Runtime

```

Extensions may affect one or more architectural layers.

---

## Backend Extension Points

The backend exposes the following extension points:

- Model Registry
- Tool Registry
- Configuration Resolver
- Prompt Resolver
- Manifest Loader
- Provider Factory

Each extension point has a dedicated validation process.

---

## Frontend Extension Points

Frontend extensions are intentionally limited.

Supported extension mechanisms include:

- UI Schema
- Component Registry
- Action Registry
- Generic Tree
- Schema Renderer

Unknown components are displayed safely rather than executed.

---

## Model Extensions

New AI providers are integrated through the Model Registry.

```text
model.json

↓

Validation

↓

Model Registry

↓

Provider Factory

↓

Available Model

```

The chat service remains provider-independent.

---

## Tool Extensions

New tools are added through tool manifests.

```text
tool.json

↓

Validation

↓

Tool Registry

↓

Execution

```

Tools cannot bypass authorization or configuration policies.

---

## UI Schema Extensions

The frontend renders interfaces from schemas supplied by the backend.

```text
UI Schema

↓

Schema Renderer

↓

Component Registry

↓

Rendered View

```

Unknown schema elements are rejected or rendered using fallback components.

---

## Component Registry

The Component Registry maps schema component types to React components.

```text
Schema Component

↓

Component Registry

↓

React Component

```

Only registered component types may be rendered.

---

## Action Registry

User interactions are handled through the Action Registry.

```text
Action

↓

Action Registry

↓

Handler

↓

API

```

Unknown actions are never executed.

---

## Configuration Extensions

Configuration schemas allow runtime customization.

Examples:

- default model
- provider options
- UI behavior
- hierarchy settings
- feature configuration

Configuration is always validated before activation.

---

## Hierarchy Extensions

Hierarchy nodes support dynamic specialization.

Examples:

- Project
- Department
- Team
- Customer
- Workspace

New node types can be introduced without changing the hierarchy engine.

---

## Prompt Extensions

Prompt inheritance extends conversational behavior.

```text
System

↓

Department

↓

Project

↓

Chat

↓

Resolved Prompt

```

Prompt resolution uses the standard configuration pipeline.

---

## Manifest-Based Extensions

Most backend extensions are manifest-driven.

Supported manifests include:

```text
model.json

tool.json

```

Future manifests may include:

- plugin.json
- schema.json
- workflow.json

---

## Registry-Based Extensions

Registries provide controlled discovery.

Examples:

```text
Registry

↓

Validation

↓

Registration

↓

Lookup

↓

Usage

```

Registries isolate extension loading from application logic.

---

## Factory Extensions

Factories create implementation instances.

Examples:

- provider factories
- tool factories

Factories separate contracts from concrete implementations.

---

## Configuration-Driven Extensions

Many behaviors are enabled through configuration.

Examples:

- default providers
- enabled tools
- prompt templates
- feature flags

No code modification is required.

---

## API Extensions

Future versions may introduce additional REST endpoints.

Requirements:

- versioned
- documented
- authenticated
- authorized
- backward compatible

Public APIs remain stable.

---

## Event Extensions

The SSE protocol supports additional event types.

Example:

```text
token

↓

message

↓

tool_call

↓

custom_event

```

Clients should safely ignore unknown events.

---

## Validation

Every extension undergoes validation before activation.

Typical validation includes:

- schema version
- required fields
- uniqueness
- references
- compatibility
- permissions

Invalid extensions are rejected.

---

## Security

Extensions operate within strict security boundaries.

Extensions may **not**:

- bypass authorization
- access secrets directly
- execute arbitrary code
- modify internal state outside defined APIs

All execution remains under backend control.

---

## Lifecycle

A typical extension lifecycle:

```text
Discovery

↓

Validation

↓

Registration

↓

Activation

↓

Runtime Usage

↓

Deactivation

↓

Removal

```

Every stage is deterministic.

---

## Error Handling

Extension failures remain isolated.

```text
Extension Error

↓

Registry

↓

Structured Error

↓

Continue Platform

```

One faulty extension should not prevent the platform from starting whenever possible.

---

## Versioning

Every extension contract is versioned independently.

Examples:

- manifest schema
- configuration schema
- API version
- UI schema version

Version validation occurs before registration.

---

## Dependency Management

Extensions should depend only on public contracts.

Allowed dependencies:

```text
Extension

↓

Registry

↓

Public Interface

```

Extensions must not depend on internal implementation details.

---

## Future Extension Types

The architecture allows future support for:

- plugins
- workflows
- automation
- notification providers
- storage providers
- authentication providers
- localization packages
- reporting modules

These additions can be introduced without redesigning the platform.

---

## Best Practices

Recommended guidelines:

- Prefer configuration over code.
- Use manifests for discovery.
- Register extensions explicitly.
- Validate before activation.
- Keep contracts stable.
- Never expose internal APIs.
- Isolate failures.
- Version every public contract.

---

## Relationship to Other Architecture

Extension Points build upon several architectural subsystems.

```text
Extension

↓

Manifest System

↓

Registry Architecture

↓

Configuration

↓

Runtime

```

The extension architecture therefore depends on:

- manifests
- registries
- configuration
- dependency injection
- versioned contracts

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Manifest-System]]
- [[Registry-Architecture]]
- [[Configuration-Architecture]]
- [[Contract-Versioning]]
- [[Prompt-Inheritance]]
- [[Hierarchy-Architecture]]

---

## APIs

- [[Models]]
- [[Tools]]
- [[Configuration]]
- [[UI-Schema]]
- [[Bootstrap]]

---

## ADRs

- [[ADR-0003-Registries]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

## Summary

The Extension Point architecture defines the controlled mechanisms through which Kernschmied can be expanded while preserving stability, security, and maintainability.

By combining manifest-based discovery, registry-driven integration, schema validation, configuration-based customization, and strict authorization boundaries, the platform enables continuous evolution without compromising the integrity of the core system or the stability of its public contracts.

---

Back to [[Home]].
