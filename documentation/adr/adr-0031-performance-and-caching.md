# ADR-0031: Performance and Caching

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as an interactive, AI-native platform.

Users expect low latency regardless of whether requests access local resources, remote services or AI providers.

Performance must remain predictable while preserving correctness, security and consistency.

Typical performance-sensitive areas include:

- API requests
- hierarchy loading
- runtime configuration
- registry lookups
- prompt resolution
- AI model routing
- tool execution
- workflow execution
- frontend schemas
- search
- document loading
- cacheable metadata

The platform therefore requires a unified Performance and Caching Architecture.

---

# Problem

Without a dedicated performance strategy, applications gradually become slower as functionality increases.

Typical problems include:

- duplicated database queries
- repeated configuration loading
- unnecessary provider requests
- expensive hierarchy resolution
- slow startup
- inconsistent cache invalidation
- stale runtime data
- unpredictable latency

As the platform evolves, these issues become increasingly difficult to diagnose and optimize.

---

# Decision

Kernschmied adopts a **layered Performance and Caching Architecture**.

Caching is considered an optimization layer rather than a source of truth.

Persistent storage always remains authoritative.

Caching is introduced only where correctness can be preserved.

---

# Architectural Principle

> **Persistent storage is authoritative.**
>
> **Caches improve performance but never define system state.**
>
> **Cache invalidation follows revision-based consistency.**

---

# High-Level Architecture

```text
Application

        │

        ▼

Business Services

        │

        ▼

Cache Layer

        │

   ┌────┴────┐

   ▼         ▼

Memory     Distributed Cache

   │         │

   └────┬────┘

        ▼

Persistent Storage
```

---

# Cache Layers

The platform supports multiple cache layers.

Typical layers include:

- request cache
- process memory cache
- distributed cache
- browser cache
- client-side cache

Each layer has clearly defined responsibilities.

---

# Request Cache

Request-local caching avoids duplicate work within a single request.

Typical examples include:

- Effective Context
- permission evaluation
- configuration lookup
- hierarchy path resolution

Request caches are discarded after request completion.

---

# In-Memory Cache

Process-local memory caches improve performance for frequently accessed data.

Typical examples include:

- runtime configuration
- registry entries
- schema definitions
- model metadata
- tool metadata

Memory caches are invalidated through revision changes.

---

# Distributed Cache

Distributed caches synchronize state across multiple application instances.

Typical cached data includes:

- registry definitions
- configuration
- permissions
- schema metadata
- search indexes

Distributed caches support clustered deployments.

---

# Frontend Cache

Frontend applications cache read-only metadata.

Typical examples include:

- bootstrap response
- UI schemas
- hierarchy definitions
- component metadata
- localization

Frontend caches always validate revision information.

---

# Cacheable Objects

Typical cache candidates include:

- runtime configuration
- hierarchy metadata
- registry entries
- model definitions
- tool definitions
- widget definitions
- action definitions
- prompt definitions
- search metadata

Mutable business data is cached only where consistency can be guaranteed.

---

# Cache Invalidation

Cache invalidation is revision driven.

Typical invalidation triggers include:

- configuration changes
- registry activation
- schema updates
- permission changes
- hierarchy changes
- prompt changes

Revision changes automatically invalidate dependent caches.

---

# Revision Strategy

Every cacheable object exposes a revision.

Typical revision sources include:

- configuration revision
- registry revision
- hierarchy revision
- prompt revision
- permission revision

Clients compare revisions before using cached data.

---

# Performance Optimization

Optimization is evidence based.

Typical optimization techniques include:

- query optimization
- lazy loading
- batching
- pagination
- asynchronous processing
- streaming
- caching

Premature optimization is avoided.

---

# AI Performance

Model execution may use performance optimizations.

Typical examples include:

- model warm-up
- connection reuse
- request batching
- streaming responses
- provider selection

Optimization never changes model contracts.

---

# Tool Performance

Tool execution may be optimized.

Examples include:

- connection pooling
- reusable sessions
- asynchronous execution
- parallel execution
- response caching

Execution correctness always takes priority.

---

# Workflow Performance

Workflow execution supports:

- asynchronous processing
- resumable execution
- queue optimization
- parallel branches

Workflow optimization follows ADR-0026.

---

# Database Performance

Persistence is optimized through:

- indexing
- optimized queries
- pagination
- batching
- connection pooling

Business services remain independent of storage optimizations.

---

# Search Performance

Search operations may maintain optimized indexes.

Examples include:

- full-text indexes
- vector indexes
- metadata indexes

Indexes are synchronized automatically.

---

# Runtime Configuration

Caching behaviour is configurable.

Typical options include:

- cache enablement
- cache size
- cache duration
- revision strategy
- eviction policy

Configuration follows ADR-0014.

---

# Monitoring

Performance metrics include:

- response time
- cache hit ratio
- cache miss ratio
- query duration
- provider latency
- memory usage
- queue length

Monitoring integrates with ADR-0030.

---

# Security

Caches never expose:

- secrets
- credentials
- private keys
- unresolved permissions

Sensitive data is never shared across tenants.

---

# Multi-Tenant Support

Caches respect tenant isolation.

Cache keys always include the effective tenant context where required.

Tenant data must never leak across cache boundaries.

---

# Versioning

Caching contracts evolve independently.

Changes remain backward compatible whenever possible.

All contracts follow ADR-0005.

---

# API Contracts

Future APIs may include:

- Cache Statistics
- Cache Invalidation
- Cache Configuration
- Performance Metrics
- Warm-Up
- Cache Health

All contracts are versioned.

---

# Consequences

## Positive

### Improved Responsiveness

Frequently accessed data becomes significantly faster.

---

### Reduced Database Load

Repeated queries are minimized.

---

### Better Scalability

Caching reduces pressure on backend services.

---

### Lower AI Costs

Repeated provider requests may be avoided where appropriate.

---

### Consistent Runtime Behaviour

Revision-based invalidation prevents stale configuration.

---

### Future Readiness

Additional cache layers may be introduced without changing business services.

---

## Negative

### Additional Complexity

Caching introduces additional runtime behaviour.

---

### Memory Consumption

Caches require additional memory resources.

---

### Invalidation Complexity

Cache invalidation must remain reliable.

---

### Distributed Infrastructure

Clustered deployments require distributed cache services.

---

# Alternatives Considered

## No Caching

### Advantages

- Simple implementation
- Always current data

### Disadvantages

- Poor performance
- Increased provider load
- Higher latency

Rejected.

---

## Database-Only Optimization

### Advantages

- No additional cache layer

### Disadvantages

- Limited scalability
- Higher database utilization

Rejected.

---

## Aggressive Global Caching

### Advantages

- Excellent performance

### Disadvantages

- High risk of stale data
- Difficult invalidation
- Security concerns

Rejected.

---

# Related ADRs

- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0020 — Multi-Tenant Architecture
- ADR-0021 — Search Architecture
- ADR-0026 — Workflow Engine
- ADR-0027 — Scheduling and Automation Architecture
- ADR-0028 — AI Model Architecture
- ADR-0029 — Tool Execution Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0032 — Backup and Disaster Recovery

---

# Implementation Notes

The MVP initially uses request-local caching and process-local in-memory caches for runtime configuration, registry entries and schema metadata. Revision-based cache invalidation ensures consistency without requiring application restarts.

Future releases may introduce distributed caches, Redis integration, automatic cache warming, intelligent prefetching, vector cache layers, CDN support, adaptive eviction strategies and predictive performance optimization without changing the public caching contracts.