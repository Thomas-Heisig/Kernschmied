# ADR-0019: Audit and Revision Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable platform whose behavior is primarily defined through runtime configuration rather than hardcoded business logic.

Administrators may change:

- hierarchy structures
- runtime configuration
- prompts
- AI models
- tools
- widgets
- actions
- resources
- workflows
- permissions
- plugin configuration
- integrations

Every configuration change potentially affects application behavior.

The platform therefore requires complete traceability of all modifications.

At the same time, frontend clients, backend services and distributed components must detect configuration changes efficiently without repeatedly downloading unchanged data.

---

# Problem

Many systems only store the current state of configuration.

Typical problems include:

- no history of changes
- unknown author of modifications
- difficult troubleshooting
- impossible rollback
- inconsistent client caches
- missing compliance evidence
- race conditions during concurrent updates

Without revisions, clients cannot reliably determine whether locally cached data is still valid.

---

# Decision

Kernschmied adopts a combined **Audit and Revision Architecture**.

The architecture separates two independent concerns:

- **Audit** records who changed what and why.
- **Revision** identifies the current version of configuration and data.

Every mutable object participates in the revision system.

Every administrative change is written to the audit log.

---

# Architectural Principle

> **Every relevant change is traceable.**
>
> **Every mutable object has a revision.**
>
> **Revisions enable synchronization.**
>
> **Audit records enable accountability.**

---

# High-Level Architecture

```text
User

        │

        ▼

Administrative Action

        │

        ▼

Authorization

        │

        ▼

Validation

        │

        ▼

Business Service

        │

 ┌──────┴────────┐
 │               │
 ▼               ▼

Revision      Audit Log

 │               │
 └──────┬────────┘

        ▼

Persistence
```

---

# Audit

Audit records answer the following questions:

- Who performed the change?
- What was changed?
- When was it changed?
- Why was it changed?
- Which request caused the change?
- Which revision resulted?

Audit information is immutable.

Existing audit entries are never modified.

---

# Revision

A revision represents the current version of an object.

Whenever an object changes:

- its revision increases
- cache validity changes
- synchronization becomes possible

Revisions do not describe *what* changed.

They describe only *that* something changed.

---

# Revision Scope

Revisions exist at multiple levels.

Examples include:

- global configuration
- runtime configuration
- hierarchy
- prompts
- resources
- widgets
- actions
- workflows
- registries
- permissions
- plugins
- integrations

Each subsystem maintains its own revision sequence.

---

# Effective Revision Set

Clients rarely need only one revision.

Instead, the platform exposes an effective revision set.

Example:

```text
Configuration

↓

Revision 42

Hierarchy

↓

Revision 18

Widgets

↓

Revision 31

Prompts

↓

Revision 11

Registries

↓

Revision 9
```

Clients compare revision sets to determine whether cached information remains valid.

---

# Optimistic Concurrency

Every mutable object carries a revision.

Update requests may include the expected revision.

Example:

```text
Client

↓

Revision 12

↓

Update Request

↓

Backend

↓

Current Revision 13

↓

Conflict
```

The backend rejects conflicting updates.

This prevents accidental overwriting of concurrent changes.

---

# Cache Invalidation

Clients never poll complete configuration unnecessarily.

Instead they compare revision numbers.

If revisions match:

- cached data remains valid

If revisions differ:

- affected data is reloaded

This minimizes network traffic.

---

# Audit Events

Typical audit events include:

- create
- update
- delete
- move
- activate
- deactivate
- archive
- restore
- permission change
- login
- logout
- failed authorization
- configuration import
- configuration export

Additional event types may be introduced without changing the architecture.

---

# Audit Record

An audit record typically contains:

- audit identifier
- timestamp
- user identifier
- tenant identifier
- request identifier
- operation
- affected object
- object type
- previous revision
- new revision
- reason
- metadata

Sensitive information is excluded or masked.

---

# Request Correlation

Every request receives a unique request identifier.

The identifier connects:

- API requests
- audit records
- log entries
- error reports
- background jobs

This simplifies diagnostics.

---

# Security

Audit logs are append-only.

Administrative users cannot modify historical audit records.

Deletion of audit information is only permitted through explicitly defined retention policies.

---

# Privacy

Audit logging follows data protection principles.

The platform avoids storing unnecessary personal information.

Sensitive values such as:

- passwords
- API keys
- access tokens
- secrets

must never appear in audit records.

---

# Revision Propagation

When configuration changes occur:

```text
Configuration

↓

Revision Increased

↓

Effective Context Updated

↓

Clients Detect Change

↓

Reload Required Data
```

This mechanism avoids unnecessary full reloads.

---

# Registry Integration

Runtime registries participate in the revision system.

Examples:

- Model Registry
- Tool Registry
- Widget Registry
- Resource Registry
- Action Registry

Whenever definitions change, the corresponding registry revision increases.

---

# Hierarchy Integration

Hierarchy operations also create revisions.

Examples include:

- create node
- rename node
- move node
- reorder node
- archive node

Clients therefore recognize hierarchy changes immediately.

---

# Runtime Configuration Integration

Runtime configuration changes always:

- create audit records
- increase revisions
- invalidate affected caches

No restart is required.

---

# Plugin Integration

Plugin lifecycle operations generate audit records.

Examples:

- installation
- activation
- deactivation
- removal
- upgrade

Plugin state changes also update corresponding registry revisions.

---

# Event Integration

Revision changes may generate events.

Examples include:

- configuration.changed
- registry.changed
- hierarchy.changed
- permissions.changed

Clients can update automatically.

---

# Backup Integration

Audit records are included in backups.

Restoring a backup preserves both:

- configuration state
- historical audit information

---

# Consequences

## Positive

### Complete Traceability

Administrative actions remain fully auditable.

---

### Efficient Synchronization

Clients compare revisions instead of downloading unchanged data.

---

### Safe Concurrent Editing

Optimistic locking prevents accidental overwrites.

---

### Improved Diagnostics

Audit records simplify troubleshooting.

---

### Better Compliance

Administrative changes remain accountable.

---

### Scalable Cache Management

Revision-based cache invalidation minimizes unnecessary requests.

---

## Negative

### Additional Storage

Audit history increases database size.

---

### More Complex Infrastructure

Revision management requires careful implementation.

---

### Additional Validation

Concurrent updates require conflict handling.

---

### Retention Management

Audit history requires configurable retention policies.

---

# Alternatives Considered

## No Audit Logging

Advantages

- Simple implementation

Disadvantages

- No accountability
- Difficult diagnostics
- Poor compliance

Rejected.

---

## Timestamp-Based Synchronization

Advantages

- Easy implementation

Disadvantages

- Clock synchronization issues
- Difficult comparison
- Less deterministic

Rejected.

---

## Full Configuration Reload

Advantages

- Simple client implementation

Disadvantages

- High bandwidth usage
- Poor scalability
- Slow user experience

Rejected.

---

## Database Triggers Only

Advantages

- Automatic recording

Disadvantages

- Limited business context
- Difficult request correlation
- Harder application-level validation

Rejected.

---

# Related ADRs

- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0007 — Generic Hierarchy and Context Architecture
- ADR-0009 — Runtime Registry Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0015 — Chat and Conversation Architecture
- ADR-0018 — Plugin and Package Architecture
- ADR-0024 — Identity and Authorization
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching
- ADR-0032 — Backup and Disaster Recovery

---

# Implementation Notes

The MVP implements revision tracking for runtime configuration, hierarchy and chat persistence.

The architecture is intentionally designed to extend revision management to all mutable platform objects, including registries, widgets, actions, workflows, plugins and integrations, without requiring changes to the public contracts.