# ADR-0033: Storage Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a modular, extensible and long-lived platform.

The platform manages many different categories of information throughout its lifecycle.

Typical examples include:

- runtime configuration
- hierarchy structures
- chats
- messages
- prompts
- runtime registries
- workflows
- resources
- widgets
- actions
- documents
- uploaded files
- audit logs
- search indexes
- AI metadata

These information categories have different consistency, scalability and lifecycle requirements.

The platform therefore requires a generic storage architecture that separates logical data models from physical storage implementations.

---

# Problem

Without a dedicated storage architecture, persistence logic becomes tightly coupled to business services.

Typical problems include:

- duplicated persistence logic
- technology-specific business code
- difficult database migration
- inconsistent transactions
- poor scalability
- limited extensibility
- vendor lock-in
- inconsistent backup strategies

As the platform evolves, changing storage technologies becomes increasingly expensive.

---

# Decision

Kernschmied adopts a **generic Storage Architecture**.

Business services never communicate directly with storage technologies.

Instead, all persistence is performed through repository abstractions and storage services.

Storage implementations remain interchangeable.

---

# Architectural Principle

> **Business Services define what is stored.**
>
> **Repositories define how data is accessed.**
>
> **Storage Providers define where data is stored.**
>
> **Applications never depend on physical storage technologies.**

---

# High-Level Architecture

```text
Business Services

        │

        ▼

Repository Layer

        │

        ▼

Storage Service

        │

        ▼

Storage Provider

        │

        ▼

Physical Storage
```

---

# Storage Categories

The platform distinguishes multiple storage categories.

Typical categories include:

- relational data
- document storage
- binary storage
- configuration storage
- cache storage
- search indexes
- audit storage
- temporary storage

Each category may use an optimized storage implementation.

---

# Relational Storage

Structured business data is stored in relational databases.

Typical examples include:

- hierarchy
- runtime configuration
- users
- permissions
- conversations
- registries
- workflows

SQLite is used for the MVP.

PostgreSQL is the primary production target.

---

# Document Storage

Large structured documents are stored independently.

Typical examples include:

- Markdown documents
- generated reports
- exported files
- templates

Document storage is abstracted through the Storage Service.

---

# Binary Storage

Binary objects are managed separately.

Typical examples include:

- images
- PDFs
- Office documents
- audio
- video
- attachments

Binary storage is independent of database technology.

---

# Search Storage

Search functionality maintains optimized indexes.

Typical examples include:

- full-text indexes
- vector indexes
- metadata indexes

Indexes are considered derived data and may be rebuilt.

---

# Cache Storage

Caches are not authoritative storage.

Typical cache implementations include:

- in-memory cache
- distributed cache

Cache architecture follows ADR-0031.

---

# Repository Pattern

Every storage category is accessed through repositories.

Repositories provide:

- create
- read
- update
- delete
- search
- pagination

Repositories never contain business logic.

---

# Transactions

Transactional consistency is managed centrally.

Transactions may span:

- multiple repositories
- configuration updates
- registry activation
- workflow execution

Business services never manage database transactions directly.

---

# Object Identity

Every persistent object has a stable identifier.

Typical metadata includes:

- identifier
- revision
- schema version
- creation timestamp
- update timestamp

Identifiers remain independent of storage implementation.

---

# Versioning

Persistent objects are versioned independently.

Typical version information includes:

- schema version
- object revision
- migration version

Versioning follows ADR-0005.

---

# Runtime Configuration

Storage behaviour is configurable.

Typical options include:

- storage provider
- connection settings
- retention policy
- compression
- encryption

Configuration follows ADR-0014.

---

# Multi-Tenant Support

Storage respects tenant isolation.

Tenant boundaries are enforced by repositories and business services.

Tenant data must never become visible outside its effective context.

---

# Security

Storage providers never expose:

- secrets
- credentials
- encryption keys
- unrestricted tenant data

Sensitive information is protected according to deployment profile.

---

# Audit

Storage operations generate audit events where required.

Typical events include:

- create
- update
- delete
- restore
- migration

Audit follows ADR-0019.

---

# Monitoring

Storage exposes operational metrics.

Typical metrics include:

- query duration
- transaction duration
- storage utilization
- connection count
- migration status
- backup status

Monitoring integrates with ADR-0030.

---

# Migration

Storage technologies may evolve independently.

Examples include:

- SQLite → PostgreSQL
- local storage → object storage
- local search → distributed search

Business services remain unchanged during migrations.

---

# Storage Providers

Future storage providers may include:

- SQLite
- PostgreSQL
- SQL Server
- MySQL
- Object Storage
- Azure Blob Storage
- Amazon S3
- Local File Storage

Providers implement standardized contracts.

---

# API Contracts

Future APIs may include:

- Storage Health
- Storage Statistics
- Storage Migration
- Storage Configuration
- Repository Diagnostics

All contracts are versioned.

---

# Consequences

## Positive

### Technology Independence

Business services remain independent of storage technologies.

---

### Better Maintainability

Persistence logic is centralized.

---

### Improved Scalability

Different storage technologies can be introduced independently.

---

### Runtime Flexibility

Storage providers may evolve without changing business logic.

---

### Future Readiness

Additional storage technologies integrate through providers.

---

## Negative

### Additional Abstraction

Repositories introduce another architectural layer.

---

### More Components

Storage services require additional implementation.

---

### Migration Complexity

Schema migrations require careful planning.

---

### Performance Optimization

Repository abstractions require continuous optimization.

---

# Alternatives Considered

## Direct Database Access

### Advantages

- Simple implementation
- Fast development

### Disadvantages

- Strong coupling
- Difficult migration
- Code duplication

Rejected.

---

## ORM-Only Architecture

### Advantages

- Less code

### Disadvantages

- Business logic leaks into persistence
- Limited flexibility

Rejected.

---

## Storage per Feature

### Advantages

- Independent implementations

### Disadvantages

- Inconsistent architecture
- Difficult maintenance
- Duplicate functionality

Rejected.

---

# Related ADRs

- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0016 — Knowledge Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0020 — Multi-Tenant Architecture
- ADR-0021 — Search Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching
- ADR-0032 — Backup and Disaster Recovery

---

# Implementation Notes

The MVP initially uses SQLite for structured business data and the local filesystem for binary documents and uploads. Repository abstractions isolate all storage access from business services, enabling a later migration to PostgreSQL and object storage without changing the application architecture.

Future releases may introduce distributed storage providers, object storage backends, vector databases, cloud-native storage services, transparent replication, sharding and online storage migrations without changing the public storage contracts.
