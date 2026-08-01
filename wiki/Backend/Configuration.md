# Configuration Management

The **Configuration Management** subsystem is responsible for storing, validating, resolving, versioning, and distributing all runtime configuration within the Kernschmied backend.

Unlike traditional applications where configuration is primarily stored in files or environment variables, Kernschmied separates **infrastructure configuration** from **business configuration**.

Infrastructure settings required to start the application remain in the environment, while business configuration is stored in the database, validated against schemas, and resolved dynamically for every request.

This architecture enables runtime updates, hierarchical inheritance, auditability, and deterministic configuration resolution without requiring application restarts.

---

## Goals

The Configuration Management subsystem is designed to provide:

- Runtime-editable configuration
- Deterministic configuration resolution
- Hierarchical inheritance
- Versioned schemas
- Strong validation
- Auditability
- Revision tracking
- Efficient caching
- Stable public contracts

---

## Design Principles

## Infrastructure vs Business Configuration

Configuration is divided into two distinct categories.

### Infrastructure Configuration

Infrastructure configuration is required before the application starts.

Typical examples include:

- deployment profile
- database connection
- logging configuration
- provider bootstrap settings
- network configuration

These values are typically provided through environment variables.

---

### Business Configuration

Business configuration controls application behavior during runtime.

Typical examples include:

- prompts
- available features
- UI schemas
- hierarchy settings
- generation parameters
- model defaults
- tool configuration

Business configuration is stored in the database.

---

## Configuration as Data

Configuration is treated as structured data rather than executable code.

Configuration is:

- validated
- versioned
- audited
- inherited
- cached

The application interprets configuration but never executes arbitrary code contained within it.

---

## Deterministic Resolution

Given the same hierarchy and revisions, configuration resolution always produces the same result.

```text
Configuration Sources

↓

Configuration Resolver

↓

Resolved Configuration

```

Deterministic resolution simplifies debugging and reproducibility.

---

## Configuration Architecture

```text
Environment

↓

Database

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

## Configuration Storage

Runtime configuration is stored in the application database.

Typical stored information includes:

- configuration values
- schema version
- revision number
- metadata
- audit references

Database storage enables centralized runtime management.

---

## Configuration Scopes

Configuration is resolved from multiple scopes.

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

```

Each scope contributes configuration according to the configured merge strategy.

---

## System Scope

The system scope defines global application behavior.

Examples include:

- default model
- prompt defaults
- feature flags
- global UI settings
- platform policies

Every request inherits the system scope.

---

## Node Scope

Hierarchy nodes may define additional configuration.

Examples include:

- organization settings
- department policies
- workspace defaults

Node configuration applies to descendants within the hierarchy.

---

## Project Scope

Projects may override inherited configuration.

Typical examples include:

- coding standards
- project prompts
- enabled tools
- preferred models

Project configuration remains isolated from unrelated projects.

---

## Chat Scope

Chat-specific configuration applies only to the current conversation.

Examples include:

- conversation metadata
- temporary model settings
- context limits

Chat configuration is not shared with other conversations.

---

## User Scope

User configuration represents personal preferences.

Examples include:

- preferred language
- response style
- default model
- interface preferences

Mandatory system policies cannot be overridden.

---

## Request Scope

The request scope has the highest priority.

Typical examples include:

- temporary generation parameters
- selected model
- explicit instructions
- request metadata

Request configuration exists only for a single request.

---

## Configuration Resolution

Configuration is resolved using the Configuration Resolver.

```text
System

↓

Hierarchy

↓

Project

↓

Chat

↓

User

↓

Request

↓

Final Configuration

```

The resolver produces a single immutable configuration object.

---

## Merge Strategies

Different configuration sections may use different merge strategies.

Supported strategies include:

| Strategy   | Description                  |
| ---------- | ---------------------------- |
| Replace    | Replace inherited value      |
| Extend     | Append inherited collections |
| Deep Merge | Merge structured objects     |

The merge strategy is defined by the configuration schema.

---

## Configuration Schemas

Every configuration section is validated against a versioned schema.

Typical schema responsibilities include:

- required properties
- value types
- ranges
- enumerations
- merge behavior

Schema validation occurs before configuration becomes active.

---

## Validation

Configuration updates are validated before being persisted.

Validation includes:

- schema compatibility
- required fields
- supported values
- reference integrity
- identifier validation

Invalid configuration changes are rejected.

---

## Runtime Updates

Configuration marked as runtime editable becomes active immediately.

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

Next Request

```

No application restart is required.

---

## Configuration Revision

Every successful configuration update increments the configuration revision.

Example:

```text
Revision 41

↓

Configuration Updated

↓

Revision 42

```

Clients use revisions to determine when cached data should be refreshed.

---

## Caching

Resolved configuration may be cached.

Typical cache key:

```text
Configuration Revision

+

Hierarchy Revision

+

Scope

```

Caches are invalidated whenever a relevant revision changes.

---

## Audit Logging

Configuration changes generate audit records.

Typical audit information includes:

- user
- timestamp
- affected scope
- previous value
- new value
- revision number

Audit logging ensures complete traceability.

---

## Security

Configuration updates require authorization.

Typical security controls include:

- authentication
- authorization
- validation
- audit logging
- revision tracking

The frontend never modifies configuration directly.

---

## Configuration Service

The Configuration Service coordinates configuration management.

Responsibilities include:

- reading configuration
- updating configuration
- validation
- revision tracking
- cache invalidation
- audit generation

Application services communicate only with the Configuration Service.

---

## Configuration Resolver

The Configuration Resolver computes effective runtime configuration.

Responsibilities include:

- scope traversal
- inheritance
- merge strategies
- validation
- immutable result generation

Business services never resolve configuration manually.

---

## API Integration

Configuration is exposed through dedicated API endpoints.

Typical operations include:

- retrieve configuration
- update configuration
- validate changes
- retrieve revision metadata

The API exposes stable contracts independent of internal storage.

---

## Interaction with Hierarchy

Hierarchy determines the inheritance path.

```text
Hierarchy

↓

Configuration Resolver

↓

Resolved Configuration

```

Changing hierarchy relationships automatically affects configuration inheritance.

---

## Interaction with Prompt Resolution

Prompt fragments are resolved through the same inheritance mechanism.

Prompt generation therefore becomes an extension of configuration resolution rather than a separate subsystem.

---

## Interaction with UI Schema

UI schemas are generated using resolved configuration.

Configuration therefore directly influences:

- layouts
- available actions
- visible features
- navigation

The frontend remains unaware of how configuration is resolved.

---

## Error Handling

Configuration failures return structured error responses.

Example:

```json
{
  "code": "configuration_validation_failed",
  "message": "Configuration is invalid.",
  "details": {},
  "request_id": "d4c91ef8"
}
```

Partial updates are not applied.

---

## Performance

The subsystem is optimized for:

- revision-based caching
- immutable configuration objects
- deterministic resolution
- asynchronous database access
- efficient merge algorithms

Configuration resolution is lightweight enough to occur for every request.

---

## Future Extensions

The architecture supports future capabilities including:

- tenant-specific configuration
- scheduled configuration activation
- reusable configuration templates
- configuration packages
- policy-driven configuration
- distributed configuration storage
- configuration diagnostics

These enhancements can be introduced without changing existing application services.

---

## Relationship to Other Backend Components

Configuration Management is used throughout the backend.

```text
Configuration Service

↓

Configuration Resolver

↓

Application Services

↓

Providers

↓

Responses

```

Nearly every request depends on resolved runtime configuration.

---

## Relationship to Architecture

Configuration Management is closely integrated with:

- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Prompt-Inheritance]]
- [[Registry-Architecture]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

## Related Documentation

## Backend

- [[Backend-Overview]]
- [[Bootstrap]]
- [[Hierarchy-Management]]
- [[Prompt-Resolution]]
- [[Services]]
- [[Validation]]

---

## Architecture

- [[Configuration-Architecture]]
- [[Prompt-Inheritance]]
- [[Hierarchy-Architecture]]
- [[Registry-Architecture]]
- [[Request-Lifecycle]]

---

## APIs

- [[Configuration]]
- [[Bootstrap]]
- [[Hierarchy]]

---

## Summary

The Configuration Management subsystem provides the foundation for all runtime behavior within the Kernschmied backend by separating infrastructure configuration from business configuration and resolving effective settings through deterministic inheritance across multiple scopes.

Through versioned schemas, strong validation, runtime updates, revision tracking, audit logging, efficient caching, and close integration with the hierarchy, prompt, and UI schema systems, Configuration Management enables a flexible yet predictable platform that can evolve dynamically without requiring application restarts or compromising architectural stability.

---

Back to [[Home]].
