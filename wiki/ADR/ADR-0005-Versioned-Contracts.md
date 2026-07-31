# ADR-0005: Versioned Contracts and Schema Evolution

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a long-lived platform whose frontend, backend, plugins, AI providers, tools, and configuration system evolve independently over time.

The platform contains numerous contracts between subsystems, including:

- REST APIs
- Server-Sent Events (SSE)
- UI Schemas
- Hierarchy Schemas
- Configuration Schemas
- Model Manifests
- Tool Manifests
- Plugin Manifests
- Bootstrap Responses
- Internal Service Contracts

These contracts must remain stable over many years while allowing the platform to introduce new capabilities.

Without explicit versioning, even small changes can unintentionally break existing clients, plugins, or integrations.

---

# Problem

Software systems frequently evolve by modifying data structures directly.

Examples include:

- Renaming properties
- Changing data types
- Removing fields
- Altering event formats
- Changing endpoint behavior

While these modifications may appear harmless during development, they often introduce breaking changes into existing deployments.

Typical consequences include:

- Older frontends no longer working with newer backends
- Plugins becoming incompatible
- Configuration files becoming unreadable
- Failed deployments
- Difficult rollback procedures
- Hidden production failures

For a configurable platform such as Kernschmied, this risk is unacceptable.

---

# Decision

Kernschmied adopts **explicit versioning for every externally visible contract**.

Every contract exchanged between independently evolving subsystems must define its own version.

Breaking changes require a new version.

Backward-compatible extensions should preserve the existing version whenever possible.

---

# Architectural Principle

> **Contracts evolve deliberately, never accidentally.**

Every breaking change must be intentional, documented, and versioned.

---

# Scope

This decision applies to all stable contracts, including:

- REST APIs
- SSE Events
- UI Schemas
- Bootstrap Responses
- Hierarchy Schemas
- Configuration Schemas
- Model Manifests
- Tool Manifests
- Plugin Manifests
- Extension Interfaces

Internal implementation details are not considered public contracts.

---

# High-Level Architecture

```text
Producer

        │

        ▼

Versioned Contract

        │

        ▼

Validation

        │

        ▼

Consumer
```

Both producer and consumer understand exactly which contract version is being exchanged.

---

# Contract Categories

---

## API Contracts

Every REST endpoint returns data conforming to a defined contract.

Example:

```text
GET /api/v1/bootstrap

↓

BootstrapResponse v1
```

API versions remain stable for their supported lifecycle.

---

## UI Schemas

Every UI schema contains an explicit schema version.

Example:

```json
{
  "schema_version": "1.0",
  "layout": "...",
  "sections": []
}
```

The frontend validates compatibility before rendering.

---

## SSE Contracts

Streaming events follow a stable event contract.

Example event types:

- start
- token
- message
- reasoning
- tool_call
- tool_result
- usage
- complete
- error
- heartbeat

New event types may be introduced without breaking existing consumers, provided unknown events can be ignored safely.

---

## Bootstrap Contract

The bootstrap endpoint provides version information for the platform itself.

Example:

```json
{
  "versions": {
    "bootstrap": 1,
    "ui_schema": 1,
    "chat": 1,
    "tool_registry": 1
  }
}
```

Clients can use this information during initialization.

---

## Configuration Schemas

Configuration objects are versioned independently from application versions.

Migration procedures may transform older configuration revisions into newer representations.

---

## Manifest Contracts

Every manifest defines its own schema version.

Examples:

```text
model.json

tool.json

plugin.json
```

The registry validates manifests before registration.

---

# Compatibility Model

The platform distinguishes between two categories of changes.

## Backward-Compatible Changes

These changes preserve the current contract version.

Examples include:

- Adding optional fields
- Adding optional capabilities
- Adding new metadata
- Improving documentation
- Expanding enumerations where consumers tolerate unknown values

Older consumers continue to function correctly.

---

## Breaking Changes

Breaking changes require a new version.

Examples include:

- Removing fields
- Renaming fields
- Changing field types
- Changing endpoint semantics
- Removing event types
- Altering validation rules incompatibly

These changes must not silently replace existing contracts.

---

# Version Negotiation

Where appropriate, producer and consumer may negotiate supported versions.

Typical process:

```text
Consumer

↓

Supported Versions

↓

Producer

↓

Highest Compatible Version

↓

Communication
```

When negotiation is not supported, incompatible versions result in a controlled failure.

---

# Validation

Every contract is validated before use.

Validation occurs:

- during application startup
- when loading manifests
- before rendering UI schemas
- before processing configuration
- before executing plugins

Invalid contracts are rejected before entering the runtime.

---

# Unknown Fields

Consumers should ignore unknown optional fields whenever possible.

This allows newer producers to communicate with older consumers without introducing breaking changes.

Example:

```json
{
  "name": "Example",
  "description": "...",
  "future_property": "..."
}
```

If `future_property` is optional, older consumers simply ignore it.

---

# Unknown Versions

Unknown versions must never be processed blindly.

Instead:

```text
Receive Contract

↓

Version Check

↓

Supported?

↓

Yes → Continue

↓

No → Reject Gracefully
```

This prevents undefined behavior.

---

# Deprecation

Contracts may be deprecated before removal.

A typical lifecycle is:

```text
Introduced

↓

Supported

↓

Deprecated

↓

Removal Announced

↓

Removed in Next Major Version
```

Deprecation periods provide consumers sufficient time to migrate.

---

# Migration

Configuration and data migrations should be explicit.

Example:

```text
Version 1

↓

Migration

↓

Version 2
```

Migration logic should remain deterministic and testable.

---

# Error Handling

Version mismatches should produce structured errors.

Example:

```json
{
  "code": "unsupported_version",
  "message": "UI Schema version 3 is not supported.",
  "details": {
    "supported_versions": ["1", "2"]
  }
}
```

Consumers receive actionable diagnostics instead of generic failures.

---

# Security Considerations

Version validation improves security by ensuring:

- predictable parsing
- known semantics
- controlled upgrades
- validated manifests
- deterministic processing

Unsupported contract versions must never bypass validation.

---

# Operational Impact

Versioned contracts simplify:

- rolling upgrades
- staged deployments
- plugin compatibility
- diagnostics
- rollback procedures
- long-term maintenance

Operations teams can identify incompatibilities before users encounter runtime failures.

---

# Consequences

## Positive

### Stable Integrations

Clients evolve independently while maintaining compatibility.

---

### Predictable Evolution

Breaking changes become explicit architectural decisions.

---

### Better Diagnostics

Version mismatches are detected immediately.

---

### Safer Deployments

Rolling upgrades and rollback procedures become easier.

---

### Improved Plugin Support

Plugins can declare supported contract versions before registration.

---

## Negative

### Additional Maintenance

Every public contract requires:

- documentation
- validation
- compatibility testing

---

### Migration Logic

Some contract changes require explicit migration code.

---

# Alternatives Considered

## Unversioned Contracts

Advantages:

- minimal implementation effort

Disadvantages:

- accidental breaking changes
- poor compatibility
- difficult maintenance

Rejected.

---

## Application Version Only

Using the application version as the only compatibility indicator.

Advantages:

- simple

Disadvantages:

- unrelated subsystems evolve independently
- unnecessary coupling
- coarse compatibility information

Rejected.

---

## Automatic Compatibility

Attempting to infer compatibility dynamically.

Advantages:

- minimal manual version management

Disadvantages:

- unpredictable behavior
- ambiguous semantics
- difficult debugging

Rejected.

---

# Risks

Potential risks include:

- forgetting to version new contracts
- inconsistent version numbering
- undocumented compatibility rules
- excessive parallel versions

Mitigation strategies include:

- architecture reviews
- automated validation
- CI compatibility tests
- comprehensive documentation
- clear deprecation policies

---

# Implementation Notes

Every public contract should provide:

- explicit version identifier
- schema validation
- compatibility checks
- structured error reporting
- automated tests
- migration strategy where required

Breaking changes must never replace an existing contract silently.

---

# Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0004-Security-Profiles]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Contract-Versioning]]
- [[Manifest-System]]
- [[Bootstrap-Lifecycle]]

---

## Backend

- [[Contracts]]
- [[REST-API]]
- [[Streaming]]
- [[Configuration]]

---

## Frontend

- [[UI-Schema]]
- [[Schema-Renderer]]
- [[API-Client]]

---

## Concepts

- [[Semantic-Versioning]]
- [[Plugin-System]]
- [[Runtime-Configuration]]

---

# Decision Summary

Kernschmied adopts **explicit versioning for every public contract** exchanged between independently evolving parts of the platform.

Each contract defines its own version, is validated before use, and evolves according to documented compatibility rules.

Breaking changes always require a new contract version, while backward-compatible extensions preserve existing versions whenever possible.

This decision provides a stable foundation for long-term evolution, plugin compatibility, rolling upgrades, and independent frontend/backend development while minimizing the risk of accidental breaking changes.

---

Back to [[Home]].
