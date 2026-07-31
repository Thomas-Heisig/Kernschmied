# ADR-0010: Configuration Management

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable platform rather than a statically configured application.

Almost every functional aspect of the system may evolve over time without requiring source code modifications.

Examples include:

- available AI models
- tool configuration
- hierarchy defaults
- prompt inheritance
- security policies
- feature flags
- UI configuration
- runtime behavior
- deployment-specific settings

Traditional applications frequently store configuration inside:

- environment variables
- configuration files
- hardcoded constants

These approaches work for infrastructure settings but become increasingly difficult to maintain for business configuration.

---

# Problem

Environment variables are immutable during runtime.

Hardcoded configuration requires redeployment.

Configuration files introduce synchronization issues in multi-instance deployments.

The platform therefore requires a configuration architecture that supports:

- runtime updates
- validation
- versioning
- inheritance
- auditing
- caching
- deterministic resolution

without compromising security.

---

# Decision

Kernschmied adopts a **database-driven configuration architecture**.

Infrastructure settings remain inside `.env`.

Business configuration is stored inside the database and managed through dedicated services.

Configuration is:

- versioned
- validated
- scoped
- cached
- audited
- mergeable

---

# Architectural Principle

> Infrastructure belongs in `.env`.
>
> Business configuration belongs in the database.

---

# Configuration Categories

Configuration is divided into two independent categories.

---

## Infrastructure Configuration

Infrastructure configuration contains values required before the application can start.

Examples include:

- database connection
- secret keys
- HTTPS configuration
- CORS bootstrap
- deployment profile
- logging bootstrap

These values are loaded from `.env`.

---

## Runtime Configuration

Runtime configuration controls application behavior.

Examples include:

- available providers
- model defaults
- prompt templates
- enabled tools
- hierarchy settings
- feature flags
- administrator options
- UI behavior

Runtime configuration is stored in the database.

---

# High-Level Architecture

```text
.env

        │

Bootstrap

        │

        ▼

Configuration Service

        │

        ▼

Configuration Resolver

        │

        ▼

Effective Configuration

        │

        ▼

Business Services
```

---

# Goals

The configuration architecture should provide:

- runtime updates
- validation
- inheritance
- deterministic resolution
- auditing
- version tracking
- security
- scalability

---

# Configuration Service

The **Configuration Service** manages configuration persistence.

Responsibilities include:

- reading configuration
- writing configuration
- validation
- revision updates
- audit logging
- cache invalidation

Business services never access configuration tables directly.

---

# Configuration Resolver

The **Configuration Resolver** calculates the effective configuration for a specific execution context.

The resolver merges configuration from multiple scopes into a single immutable configuration object.

---

# Configuration Scopes

Configuration exists at multiple hierarchical scopes.

Supported scopes include:

| Scope   | Purpose                        |
| ------- | ------------------------------ |
| SYSTEM  | Global defaults                |
| NODE    | Hierarchy node defaults        |
| PROJECT | Project-specific configuration |
| CHAT    | Chat-specific configuration    |
| USER    | User preferences               |
| REQUEST | Temporary request overrides    |

---

# Scope Hierarchy

Configuration is resolved from the least specific scope to the most specific.

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

Every subsequent scope may override or extend previous values according to its merge strategy.

---

# Effective Configuration

Business services receive only the **effective configuration**.

Example:

```text
Configuration Resolver

↓

Merge

↓

Validation

↓

Effective Configuration
```

Services never need to know where a configuration value originated.

---

# Merge Strategies

Different configuration values require different merge behavior.

Each configuration entry declares its merge strategy.

Supported strategies include:

---

## Replace

The new value completely replaces the inherited value.

Example:

```text
SYSTEM

temperature = 0.7

↓

PROJECT

temperature = 0.2

↓

Effective

temperature = 0.2
```

---

## Extend

Collections are extended.

Example:

```text
SYSTEM

tools:
- calculator

↓

PROJECT

tools:
- web_search

↓

Effective

calculator
web_search
```

---

## Deep Merge

Nested objects are recursively merged.

Example:

```text
SYSTEM

{
  "chat": {
    "streaming": true
  }
}

↓

PROJECT

{
  "chat": {
    "max_tokens": 4096
  }
}

↓

Effective

{
  "chat": {
    "streaming": true,
    "max_tokens": 4096
  }
}
```

---

# Validation

Every configuration entry is validated before being stored.

Validation may include:

- JSON Schema
- Pydantic models
- enumerations
- ranges
- required fields
- custom validators

Invalid configuration is rejected immediately.

---

# Versioning

Each configuration change increments a global revision number.

Example:

```text
Revision 42

↓

Configuration Updated

↓

Revision 43
```

The revision is exposed through the Bootstrap endpoint.

---

# Cache Invalidation

Configuration is cached to reduce database access.

Whenever the revision changes:

```text
Configuration Updated

↓

Revision Increased

↓

Caches Invalidated

↓

Reload on Next Access
```

Workers detect configuration changes without requiring a restart.

---

# Runtime Editable Configuration

Some configuration values may be modified while the application is running.

Examples:

- prompt templates
- enabled tools
- default models
- feature flags

Other values require a restart.

Example:

- HTTPS certificate
- database connection
- deployment profile

Each configuration entry declares whether it is runtime editable.

---

# Audit Logging

Every configuration modification is recorded.

Typical audit information includes:

- timestamp
- user
- configuration key
- previous value
- new value
- revision
- request id

Audit entries are immutable.

---

# Security Considerations

Configuration changes may significantly affect platform behavior.

Therefore:

- write access requires explicit permissions
- validation is mandatory
- changes are audited
- secrets are not stored in plaintext
- backend authorization is always enforced

---

# Secrets

Sensitive values should not be stored directly inside general runtime configuration.

Examples include:

- API keys
- OAuth secrets
- database passwords

Infrastructure secrets belong in secure secret storage or environment variables.

---

# Configuration API

Administrative endpoints expose configuration management.

Typical operations include:

- read configuration
- update configuration
- validate configuration
- inspect revisions
- view audit history

Clients interact exclusively through the API.

---

# Configuration Resolution Example

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

Every request receives a deterministic result.

---

# Failure Handling

Configuration failures are handled gracefully.

Examples:

- validation failure
- unknown schema
- invalid merge strategy
- missing required values

Errors are returned using structured error responses.

---

# Performance Considerations

Performance is achieved through:

- immutable configuration snapshots
- revision-based cache invalidation
- resolver caching
- request-local configuration reuse

Configuration resolution should remain inexpensive.

---

# Operational Impact

The configuration architecture enables:

- live administration
- centralized management
- deployment consistency
- rollback
- auditing
- monitoring

Operations teams can modify business behavior without redeploying the application.

---

# Consequences

## Positive

- Runtime configuration
- Strong validation
- Auditability
- Deterministic resolution
- Scalable architecture
- Centralized administration

## Negative

- Additional infrastructure
- Resolver complexity
- Cache management
- Migration of configuration schemas

---

# Alternatives Considered

## Environment Variables Only

Rejected because runtime updates are impossible.

---

## Configuration Files

Rejected because synchronization across multiple instances becomes difficult.

---

## Hardcoded Constants

Rejected because business configuration should not require source code changes.

---

## Mixed Ad-hoc Configuration

Rejected because it leads to inconsistent behavior and duplicated logic.

---

# Risks

Potential risks include:

- invalid configuration
- excessive configuration complexity
- conflicting overrides
- stale caches
- schema drift

Mitigation strategies include:

- JSON Schema validation
- revision tracking
- automated testing
- audit logging
- deterministic merge strategies

---

# Implementation Notes

The implementation should provide:

- Configuration Service
- Configuration Resolver
- revision tracking
- cache invalidation
- merge strategies
- JSON Schema validation
- Pydantic validation
- audit logging
- runtime editable metadata

Business services should always consume immutable effective configuration rather than raw database records.

---

# Related Decisions

- [[ADR-0002-Bootstrap]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0007-Database-and-Storage-Architecture]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Configuration-Architecture]]
- [[Runtime-Configuration]]

---

## Backend

- [[Configuration]]
- [[Bootstrap]]
- [[Hierarchy]]
- [[REST-API]]

---

## Concepts

- [[Configuration-Resolver]]
- [[Configuration-Service]]
- [[Merge-Strategies]]
- [[Configuration-Revisions]]
- [[Audit-Log]]

---

# Decision Summary

Kernschmied adopts a **database-driven configuration architecture** that separates immutable infrastructure configuration from mutable runtime configuration.

Infrastructure settings remain in `.env`, while business configuration is stored in the database, validated through schemas, merged across hierarchical scopes, versioned using configuration revisions, cached with automatic invalidation, and fully audited.

This architecture enables safe runtime administration, deterministic configuration resolution, scalable deployments, and long-term extensibility without requiring application redeployment for business-level changes.

---

Back to [[Home]].
