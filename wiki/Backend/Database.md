# Database

The **Database** is the persistent foundation of the Kernschmied backend. It stores runtime configuration, hierarchy information, conversations, audit data, and application metadata while remaining completely independent of business logic and AI providers.

Kernschmied intentionally separates **persistent state** from **application behavior**. The database stores data, while services, repositories, and registries interpret and operate on that data.

The default database for development is **SQLite**, while the architecture is designed to support **PostgreSQL** and other SQL databases without requiring architectural changes.

---

# Goals

The database architecture is designed to provide:

- Reliable persistence
- Provider independence
- Transactional consistency
- Runtime configuration storage
- Hierarchy persistence
- Auditability
- Future scalability
- Database portability

---

# Design Principles

## Database Agnostic

The application should not depend on database-specific behavior.

Supported databases include:

- SQLite (default)
- PostgreSQL (production)
- Future SQL-compatible databases

Business logic remains independent of the chosen database engine.

---

## Persistence Only

The database stores data.

It does **not** contain business logic.

```text
Application Service

↓

Repository

↓

Database
```

Validation, authorization, and configuration resolution always occur before data reaches the database.

---

## Repository Pattern

Application services never communicate directly with SQLAlchemy models or SQL queries.

Instead:

```text
Service

↓

Repository

↓

Database
```

Repositories encapsulate persistence logic and isolate storage details.

---

# High-Level Architecture

```text
Application Services

↓

Repositories

↓

SQLAlchemy Async

↓

Database Engine

↓

SQLite / PostgreSQL
```

Each layer has a single responsibility.

---

# Responsibilities

The database is responsible for storing:

- runtime configuration
- hierarchy nodes
- conversations
- messages
- audit logs
- registry metadata
- application state
- revision information

Transient runtime objects are not persisted.

---

# Database Technologies

The backend uses:

| Technology | Purpose |
|------------|---------|
| SQLAlchemy Async | ORM and query abstraction |
| Alembic | Schema migrations |
| SQLite | Development database |
| PostgreSQL | Production database |

The ORM layer hides database-specific implementation details.

---

# Database Sessions

Database access is performed through asynchronous sessions.

```text
HTTP Request

↓

Dependency Injection

↓

Async Session

↓

Repository

↓

Database
```

Sessions are scoped to individual requests.

---

# Transaction Management

Repositories perform operations within transactions.

Typical lifecycle:

```text
Open Transaction

↓

Execute Changes

↓

Commit

↓

Close
```

If an error occurs:

```text
Open Transaction

↓

Error

↓

Rollback

↓

Close
```

This guarantees data consistency.

---

# Entity Categories

The database stores several categories of entities.

Typical categories include:

- configuration
- hierarchy
- conversations
- users
- audit logs
- metadata
- revisions

Each category has its own persistence model.

---

# Runtime Configuration

Business configuration is stored in the database.

Examples include:

- prompt definitions
- UI settings
- feature flags
- hierarchy configuration
- model defaults
- tool configuration

Configuration is validated before persistence.

---

# Hierarchy Storage

The hierarchy is persisted independently of the frontend.

Typical node information includes:

- identifier
- parent identifier
- node type
- schema
- metadata

Hierarchy relationships are resolved by backend services.

---

# Conversation Storage

Conversation persistence is separated from chat generation.

Typical conversation data includes:

- conversation identifier
- timestamps
- participants
- hierarchy references
- metadata

Conversation storage policies remain configurable.

---

# Message Storage

Messages may contain:

- user messages
- assistant responses
- system messages
- tool interactions
- timestamps

Streaming transport is independent of persistence.

---

# Audit Log

Audit information is stored separately from operational data.

Typical audit entries include:

- user
- action
- timestamp
- affected resource
- previous state
- new state

Audit logs support traceability and compliance.

---

# Revision Storage

The database maintains revision information used for cache invalidation.

Typical revisions include:

- configuration revision
- registry revisions
- hierarchy revision

Clients use these revisions to determine when cached data should be refreshed.

---

# Metadata

Application metadata may include:

- schema versions
- migration version
- deployment information
- application state

Metadata supports runtime diagnostics and compatibility checks.

---

# Repository Layer

Repositories provide the exclusive interface to persistent storage.

Typical repositories include:

```text
ConfigurationRepository

HierarchyRepository

ConversationRepository

AuditRepository
```

Repositories isolate SQLAlchemy from business services.

---

# SQLAlchemy Models

ORM models represent the database structure.

Responsibilities include:

- table mapping
- relationships
- column definitions
- constraints

ORM models are internal implementation details and are not exposed through public APIs.

---

# Alembic Migrations

Database schema changes are managed through Alembic.

Typical workflow:

```text
Model Changes

↓

Migration

↓

Review

↓

Apply

↓

Database Updated
```

Manual schema modifications should be avoided.

---

# Migration Strategy

Schema evolution follows versioned migrations.

Migration files should:

- be deterministic
- be reversible where practical
- preserve existing data
- remain under version control

Production databases should never be modified outside the migration system.

---

# Constraints

Database constraints complement application validation.

Typical constraints include:

- primary keys
- foreign keys
- uniqueness
- non-null fields
- indexes

Business rules remain enforced by application services.

---

# Indexing

Indexes improve lookup performance.

Typical indexed fields include:

- identifiers
- parent relationships
- revision numbers
- timestamps

Indexes should be introduced based on measured requirements.

---

# Asynchronous Access

The backend uses asynchronous database communication.

Benefits include:

- improved scalability
- non-blocking request handling
- efficient resource utilization

All repositories should use asynchronous SQLAlchemy APIs.

---

# Performance

Database performance is improved through:

- asynchronous sessions
- indexed lookups
- efficient queries
- transaction scoping
- revision-based caching

Caching reduces unnecessary database access for frequently used runtime data.

---

# Security

Database access is restricted to repositories.

Additional protections include:

- validated input
- authorization before persistence
- transaction rollback on failure
- least-privilege database credentials

Sensitive information should never be exposed through public APIs.

---

# Backup Strategy

Production deployments should implement regular backups.

Recommended practices include:

- scheduled backups
- off-site storage
- backup verification
- restore testing

Backup procedures are deployment-specific and remain independent of application logic.

---

# Future Scalability

The database architecture supports future enhancements such as:

- PostgreSQL clustering
- read replicas
- partitioning
- full-text search
- distributed storage
- multi-tenant deployments

These enhancements should not require changes to application services.

---

# Relationship to Other Backend Components

The database supports nearly every backend subsystem.

```text
Application Services

↓

Repositories

↓

Database

↓

Persistent State
```

Repositories remain the only components responsible for database interaction.

---

# Relationship to Architecture

The database integrates closely with:

- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Request-Lifecycle]]
- [[Repository-Structure]]
- [[Security-Architecture]]

---

# Related Documentation

## Backend

- [[Backend-Overview]]
- [[Configuration]]
- [[Hierarchy-Management]]
- [[Repositories]]
- [[Dependency-Injection]]
- [[Validation]]

---

## Architecture

- [[Repository-Structure]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

## APIs

- [[Configuration]]
- [[Hierarchy]]
- [[Bootstrap]]
- [[Chat]]

---

# Summary

The Database provides the persistent foundation of the Kernschmied backend by storing configuration, hierarchy information, conversations, audit records, revisions, and application metadata in a database-independent manner.

Through asynchronous SQLAlchemy access, repository-based persistence, versioned Alembic migrations, transactional consistency, and strict separation between storage and business logic, the database architecture remains scalable, maintainable, portable, and capable of supporting future enterprise deployments without requiring changes to higher application layers.

---

Back to [[Home]].
