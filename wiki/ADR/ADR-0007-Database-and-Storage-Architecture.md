# ADR-0007: Database and Storage Architecture

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a long-lived, configurable platform rather than a traditional CRUD application.

The platform stores both business and platform data, including:

- Runtime configuration
- Generic hierarchy
- Chats
- Messages
- Model configuration
- Tool configuration
- UI schemas
- Audit logs
- Configuration revisions
- Future plugins
- Future user preferences

The persistence layer must therefore provide:

- reliability
- transactional consistency
- strong typing
- migration support
- database independence
- asynchronous access
- future scalability

The MVP intentionally targets **SQLite** for ease of installation while allowing migration to **PostgreSQL** without architectural changes.

---

# Problem

Many applications tightly couple themselves to a specific database engine.

Typical examples include:

- vendor-specific SQL
- proprietary extensions
- database-specific JSON handling
- stored procedures
- application logic inside triggers

This creates several problems:

- difficult migrations
- limited portability
- vendor lock-in
- increased testing complexity

Kernschmied should instead depend on a database abstraction while still supporting advanced database capabilities where appropriate.

---

# Decision

Kernschmied adopts a **database-agnostic persistence architecture** based on:

- SQLAlchemy 2.x Async ORM
- AsyncSession
- Alembic migrations
- Repository / Service separation
- SQLite for the MVP
- PostgreSQL for larger deployments

Business logic never depends directly on SQLite-specific behavior.

---

# Architectural Principle

> The database stores state.
>
> Business logic belongs in services.
>
> Persistence remains replaceable.

---

# High-Level Architecture

```text
Application

        │

        ▼

Business Service

        │

        ▼

Repository

        │

        ▼

SQLAlchemy Async ORM

        │

        ▼

SQLite / PostgreSQL
```

---

# Technology Stack

The persistence layer is built upon:

| Technology       | Purpose             |
| ---------------- | ------------------- |
| SQLAlchemy Async | ORM                 |
| AsyncSession     | Transactions        |
| Alembic          | Schema migrations   |
| SQLite           | MVP database        |
| PostgreSQL       | Production database |

---

# Why SQLite?

SQLite is chosen for the MVP because it offers:

- zero configuration
- embedded deployment
- no external service
- easy backups
- rapid development
- excellent testability

SQLite allows developers to clone the repository and start the application immediately.

---

# Why PostgreSQL Later?

As deployments grow, PostgreSQL provides:

- concurrent writers
- advanced indexing
- connection pooling
- replication
- backup tooling
- high availability
- monitoring

The persistence architecture is designed so that switching databases requires only infrastructure changes.

---

# Database Independence

Business services communicate only with repositories.

They never execute raw SQL directly.

Example:

```text
Chat Service

↓

Chat Repository

↓

ORM

↓

Database
```

---

# Data Categories

The platform stores several categories of information.

---

## Runtime Configuration

Examples:

- system settings
- provider settings
- tool settings
- UI configuration
- runtime options

Configuration is versioned and validated.

---

## Generic Hierarchy

The hierarchy represents the logical organization of the platform.

Examples:

- User
- Workspace
- Project
- Folder
- Chat
- Configuration Node

The hierarchy remains generic and extensible.

---

## Chats

A chat stores conversation metadata.

Typical fields include:

- identifier
- title
- hierarchy node
- timestamps
- metadata

Messages are stored separately.

---

## Messages

Messages belong to chats.

Typical fields include:

- role
- content
- timestamps
- usage
- reasoning
- tool calls
- metadata

---

## Audit Log

Administrative actions are recorded.

Examples:

- configuration changes
- permission changes
- runtime updates
- registry updates

Audit entries should be immutable.

---

## Configuration State

Configuration revisions are tracked independently.

Revision numbers allow:

- cache invalidation
- synchronization
- runtime reload

---

# Data Ownership

Every entity has a single owner.

Example:

```text
Chat

↓

Messages

↓

Streaming Events
```

Ownership remains explicit.

---

# Transactions

Every business operation executes within a transaction.

Example:

```text
Begin Transaction

↓

Modify Data

↓

Validate

↓

Commit

↓

Rollback on Error
```

Transactions guarantee consistency.

---

# AsyncSession

The platform uses SQLAlchemy AsyncSession.

Benefits include:

- asynchronous I/O
- improved scalability
- integration with FastAPI
- predictable lifecycle

Sessions are short-lived and request-scoped.

---

# Session Lifecycle

Typical lifecycle:

```text
Request

↓

Create AsyncSession

↓

Business Service

↓

Commit

↓

Close Session
```

Sessions are never shared across concurrent requests.

---

# Repository Pattern

Repositories encapsulate persistence.

Responsibilities include:

- querying
- inserting
- updating
- deleting

Repositories do **not** implement business rules.

---

# Service Layer

Business services coordinate:

- validation
- authorization
- repositories
- registries
- configuration

Services remain independent from database details.

---

# Schema Migrations

All schema changes are managed through Alembic.

Typical workflow:

```text
Model Change

↓

Generate Migration

↓

Review

↓

Apply Migration

↓

Update Schema
```

Direct manual schema modifications are discouraged.

---

# Migration Strategy

Migration principles:

- additive whenever possible
- explicit version history
- deterministic execution
- reversible when practical

Every migration is tracked.

---

# JSON Storage

Some entities contain structured configuration.

Examples:

- provider configuration
- tool configuration
- metadata
- UI settings

Structured data should remain validated by Pydantic before persistence.

---

# Configuration Storage

Configuration is stored as structured records rather than environment variables.

Typical fields include:

- key
- value
- scope
- merge strategy
- revision
- validation metadata

---

# Hierarchy Storage

The hierarchy uses generic node relationships.

Example:

```text
Workspace

↓

Project

↓

Folder

↓

Chat
```

No business-specific node tables are required.

---

# Soft Deletes

Where appropriate, entities may use soft deletion.

Benefits include:

- auditability
- recovery
- historical analysis

Permanent deletion remains an explicit administrative action.

---

# Concurrency

SQLite has limited concurrent write capabilities.

The architecture minimizes contention through:

- short transactions
- request-scoped sessions
- asynchronous processing

PostgreSQL provides significantly improved concurrency for production deployments.

---

# Indexing

Indexes should exist for:

- identifiers
- foreign keys
- hierarchy traversal
- timestamps
- configuration lookups

Indexes should be reviewed as the platform evolves.

---

# Backup Strategy

SQLite:

- file-level backups

PostgreSQL:

- logical backups
- physical backups
- point-in-time recovery

Backup procedures remain operational concerns rather than application logic.

---

# Security Considerations

The persistence layer enforces:

- parameterized queries
- ORM-generated SQL
- transaction isolation
- validation before persistence

Secrets should never be stored unencrypted unless explicitly intended.

Sensitive configuration should be protected appropriately.

---

# Performance Considerations

Performance techniques include:

- asynchronous access
- efficient indexes
- request-scoped sessions
- lazy loading where appropriate
- eager loading where beneficial
- minimized transaction duration

Performance optimizations should never compromise correctness.

---

# Operational Impact

The architecture supports:

- SQLite development
- PostgreSQL production
- automated migrations
- backup automation
- monitoring
- future clustering

Database replacement should not require changes to business services.

---

# Consequences

## Positive

- Database independence
- Easy local development
- Production scalability
- Strong transaction support
- Maintainable persistence layer
- Automated migrations

## Negative

- Additional abstraction
- Migration maintenance
- ORM learning curve
- Slight startup complexity

---

# Alternatives Considered

## Raw SQL

Advantages:

- maximum control

Disadvantages:

- duplicated SQL
- poor portability
- harder testing

Rejected.

---

## SQLite Only

Advantages:

- simplicity

Disadvantages:

- limited scalability
- weaker concurrency

Rejected for long-term deployments.

---

## PostgreSQL Only

Advantages:

- production-ready

Disadvantages:

- higher entry barrier
- external infrastructure required

Rejected for the MVP.

---

## No Migration Framework

Manual schema evolution.

Rejected because it cannot provide reproducible deployments.

---

# Risks

Potential risks include:

- long-running transactions
- missing indexes
- migration conflicts
- schema drift
- SQLite write contention

Mitigation includes:

- Alembic
- automated testing
- schema reviews
- monitoring
- transaction discipline

---

# Implementation Notes

The persistence layer should provide:

- SQLAlchemy Async ORM
- AsyncSession
- Alembic migrations
- Repository pattern
- Dependency injection
- Request-scoped sessions
- Typed models
- Structured validation

Business services must never depend directly on SQL dialects.

---

# Related Decisions

- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0010-Configuration-Management]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]

---

## Backend

- [[Database]]
- [[Configuration]]
- [[Hierarchy]]
- [[Chats]]
- [[Messages]]

---

## Concepts

- [[Repository-Pattern]]
- [[Dependency-Injection]]
- [[Runtime-Configuration]]
- [[Alembic-Migrations]]

---

# Decision Summary

Kernschmied adopts a **database-independent persistence architecture** based on SQLAlchemy Async, Alembic migrations, and a clear separation between business services and persistence.

SQLite serves as the default database for development and MVP deployments because of its simplicity and zero-configuration setup, while PostgreSQL is the preferred production database for larger installations requiring higher concurrency and operational capabilities.

This architecture provides a stable foundation for long-term evolution, reliable migrations, transactional consistency, and future scalability without coupling the application to a specific database engine.

---

Back to [[Home]].
