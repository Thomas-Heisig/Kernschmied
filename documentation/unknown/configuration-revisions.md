# Configuration Revisions

Configuration Revisions are the mechanism that allows the Kernschmied backend to detect configuration changes efficiently without requiring expensive polling, unnecessary database queries, or application restarts.

Instead of comparing entire configuration objects, the backend maintains lightweight revision numbers that represent the current state of runtime configuration. Whenever configuration changes, the corresponding revision is incremented. Clients and backend services can compare revisions to determine whether cached data is still valid.

This approach provides deterministic cache invalidation, efficient synchronization between frontend and backend, and a foundation for future distributed deployments.

---

## Goals

The Configuration Revision system is designed to provide:

- Efficient cache invalidation
- Deterministic synchronization
- Runtime configuration updates
- Lightweight change detection
- Distributed compatibility
- Stable public contracts
- High performance
- Future scalability

---

## Why Revisions?

Without revisions, clients would have to repeatedly download configuration or compare large configuration objects.

```text
Client

↓

Download Configuration

↓

Compare Objects

↓

Detect Changes

```

This approach becomes increasingly inefficient as configuration grows.

Instead, Kernschmied exposes lightweight revision numbers.

```text
Client

↓

Revision = 42

↓

Backend Revision = 42

↓

No Reload Required

```

---

## Basic Principle

Every successful configuration modification increments a revision number.

```text
Revision 10

↓

Configuration Updated

↓

Revision 11

```

The revision represents the current logical state of the configuration.

---

## Revision Lifecycle

Configuration updates follow a deterministic workflow.

```text
Configuration Request

↓

Validation

↓

Authorization

↓

Persist Changes

↓

Increment Revision

↓

Invalidate Cache

↓

Return Updated Revision

```

Clients receive the new revision together with the successful response.

---

## Revision Storage

Revision information is stored separately from configuration values.

Typical stored information includes:

- current revision
- update timestamp
- update metadata
- revision source

Separating revisions from configuration simplifies synchronization.

---

## Immutable History

A revision number is never reused.

Example:

```text
1

2

3

4

5

```

If revision **5** exists, revisions **1–4** always refer to earlier states.

---

## Monotonic Growth

Revisions always increase.

Invalid sequence:

```text
7

8

6

```

Valid sequence:

```text
7

8

9

```

This property makes synchronization deterministic.

---

## Backend Usage

Application services compare revisions before using cached configuration.

```text
Cached Revision

↓

Current Revision

↓

Equal?

↓

Use Cache

```

Otherwise:

```text
Reload Configuration

↓

Replace Cache

```

---

## Frontend Usage

The frontend receives revision information through Bootstrap and configuration endpoints.

Example:

```text
Bootstrap

↓

configuration_revision = 17

```

If the revision changes later:

```text
17

↓

18

↓

Reload Configuration

```

The frontend never needs to compare complete configuration objects.

---

## Bootstrap Integration

The Bootstrap endpoint exposes current revision information.

Example:

```text
Bootstrap

↓

Configuration Revision

↓

Hierarchy Revision

↓

Registry Revisions

```

Clients can synchronize all runtime metadata immediately after startup.

---

## Cache Invalidation

Revision changes invalidate cached configuration automatically.

```text
Configuration Updated

↓

Revision++

↓

Cache Invalid

↓

Next Request Reloads

```

The cache never needs to inspect individual configuration values.

---

## Scope Awareness

Future versions may maintain revisions for multiple scopes.

Example:

```text
System

↓

Organization

↓

Project

↓

Conversation

```

Each scope could evolve independently while preserving deterministic behavior.

---

## Relationship to Configuration

Configuration stores business values.

Revision numbers describe the version of those values.

```text
Configuration

↓

Revision

↓

Cache Synchronization

```

The two concepts remain separate.

---

## Relationship to Hierarchy

Hierarchy changes may also affect effective configuration.

Therefore hierarchy maintains its own revision.

```text
Hierarchy Updated

↓

Hierarchy Revision++

↓

Configuration Recalculated

```

Clients compare both revisions independently.

---

## Relationship to Registries

Model and Tool Registries maintain independent revisions.

```text
Configuration Revision

Model Registry Revision

Tool Registry Revision

```

A change in one subsystem does not invalidate unrelated caches.

---

## Runtime Updates

Runtime-editable configuration becomes active immediately.

```text
Administrator

↓

Update Configuration

↓

Revision++

↓

Next Request Uses New Configuration

```

No application restart is required.

---

## Distributed Systems

Revision numbers become even more important in multi-worker deployments.

```text
Worker A

↓

Revision 25

────────────

Worker B

↓

Revision 25

```

After an update:

```text
Revision 26

↓

Workers Detect Change

↓

Invalidate Local Cache

```

Workers remain synchronized without exchanging complete configuration data.

---

## Performance

Revision comparison is extremely inexpensive.

Instead of:

```text
Compare Hundreds of Values

```

the backend performs:

```text
Compare Integer

```

This significantly reduces synchronization overhead.

---

## Error Handling

Revision updates occur only after successful persistence.

Invalid sequence:

```text
Increment Revision

↓

Save Configuration

↓

Failure

```

Correct sequence:

```text
Save Configuration

↓

Commit Transaction

↓

Increment Revision

↓

Return Success

```

This guarantees consistency.

---

## Security

Revision values contain no sensitive information.

Clients may safely receive:

- current revision
- registry revisions
- hierarchy revision

The revision reveals only that something changed—not what changed.

---

## Future Extensions

The revision architecture supports future enhancements including:

- distributed cache invalidation
- WebSocket notifications
- SSE configuration events
- tenant-specific revisions
- scoped revision trees
- configuration history
- revision-based synchronization APIs

These features can be introduced without changing the core revision concept.

---

## Relationship to Other Concepts

Configuration Revisions interact closely with:

- [[Configuration]]
- [[Configuration-Architecture]]
- [[Bootstrap]]
- [[Hierarchy]]
- [[Registry-Architecture]]

---

## Related Documentation

## Concepts

- [[Configuration]]
- [[Caching]]
- [[Versioning]]
- [[Hierarchy]]
- [[Runtime Configuration]]

---

## Architecture

- [[Configuration-Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Request-Lifecycle]]

---

## Backend

- [[Configuration]]
- [[Bootstrap]]
- [[Database]]

---

## Summary

Configuration Revisions provide a lightweight, deterministic mechanism for detecting runtime configuration changes throughout the Kernschmied platform. Instead of comparing complete configuration objects, clients and backend services compare simple revision numbers to determine whether cached information remains valid.

By incrementing revisions only after successful configuration updates, integrating revision metadata into Bootstrap and runtime APIs, and maintaining separate revisions for configuration, hierarchy, and registries, Kernschmied achieves efficient cache invalidation, reliable synchronization, and a scalable foundation for future distributed deployments.

---

Back to [[Home]].
