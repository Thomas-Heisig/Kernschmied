# ADR-0020: Multi-Tenant Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a long-lived platform capable of operating in different organizational environments.

The first MVP targets a single organization, but the architecture must support future expansion without requiring fundamental redesign.

Future deployment scenarios include:

- Multiple companies
- Multiple departments
- Multiple customers
- Software-as-a-Service (future)
- Managed hosting
- Independent installations
- Hybrid deployments
- White-label deployments

Each organization must operate independently while sharing the same application architecture.

---

# Problem

Many applications begin as single-tenant systems.

As requirements grow, tenant separation is often introduced later.

Typical problems include:

- tenant information scattered throughout the codebase
- inconsistent data isolation
- duplicated business logic
- difficult migrations
- security vulnerabilities
- configuration leakage
- shared caches containing tenant data

Retrofitting tenant isolation into an existing system is expensive and error-prone.

---

# Decision

Kernschmied adopts a **Tenant-Aware Architecture** from the beginning.

Although the MVP operates with a single tenant, every public contract and architectural component is designed to support multiple tenants.

Multi-tenancy is therefore an architectural capability rather than an immediately required runtime feature.

---

# Architectural Principle

> **Every business object belongs to exactly one tenant.**
>
> **Tenant isolation is enforced by the backend.**
>
> **The frontend never decides tenant visibility.**
>
> **Single-tenant operation is a special case of the multi-tenant architecture.**

---

# High-Level Architecture

```text
Platform

        │

        ▼

Tenant

        │

        ▼

Hierarchy

        │

        ▼

Workspace

        │

        ▼

Project

        │

        ▼

Chat

        │

        ▼

Resources
```

---

# Tenant

A tenant represents the highest logical business boundary.

A tenant owns:

- hierarchy
- runtime configuration
- prompts
- resources
- widgets
- actions
- workflows
- AI models
- tool assignments
- users
- permissions
- knowledge
- integrations

No business object exists outside a tenant.

---

# Tenant Isolation

Every request executes within exactly one tenant context.

The backend guarantees that:

- objects from other tenants cannot be accessed
- identifiers cannot cross tenant boundaries
- permissions are evaluated per tenant
- configuration remains isolated
- caches respect tenant boundaries

Tenant isolation is never delegated to the frontend.

---

# Tenant Context

Each request receives an effective tenant context.

Typical information includes:

- tenant identifier
- user identifier
- active hierarchy node
- active workspace
- active project
- active chat
- permissions
- capabilities
- revision set

Business services operate exclusively on the effective context.

---

# Tenant Identification

The architecture supports multiple identification mechanisms.

Examples include:

- authenticated user
- domain mapping
- subdomain
- organization identifier
- API token
- service account

The identification mechanism may vary without affecting business services.

---

# Runtime Configuration

Runtime configuration is tenant-specific.

Examples include:

- branding
- hierarchy definitions
- prompts
- widgets
- actions
- workflows
- AI model selection
- integrations
- permissions

Changing one tenant's configuration never affects another tenant.

---

# Registry Integration

Registries distinguish between:

- system definitions
- tenant definitions

System definitions are provided by packages.

Tenant definitions are stored as runtime configuration.

Examples include:

- resource types
- widget types
- action definitions
- prompt definitions
- workflow definitions

Tenant-specific definitions extend rather than modify system definitions.

---

# Hierarchy Integration

Each tenant owns an independent hierarchy.

Example:

```text
Tenant A

Workspace

↓

Project

↓

Chat
```

```text
Tenant B

Workspace

↓

Department

↓

Knowledge

↓

Chat
```

Hierarchy structures may differ completely between tenants.

---

# User Membership

A user may belong to:

- one tenant
- multiple tenants

Membership does not automatically grant permissions.

Permissions are evaluated independently within each tenant.

---

# Authorization

Authorization always considers:

- tenant
- identity
- permissions
- scope
- policies

Users with administrative rights in one tenant receive no implicit rights in another tenant.

---

# Resource Isolation

Every mutable object belongs to exactly one tenant.

Examples include:

- hierarchy nodes
- chats
- messages
- prompts
- resources
- widgets
- workflows
- configuration
- audit entries

Cross-tenant references are prohibited unless explicitly supported by the platform.

---

# AI Models

Model definitions may exist at multiple levels.

Examples include:

- global system models
- tenant-specific models

Tenants choose which available models become active.

---

# Knowledge Isolation

Knowledge remains tenant-specific.

Examples include:

- documentation
- notes
- uploaded files
- semantic search
- embeddings

Knowledge indexes never mix tenant data.

---

# Search

Search operations execute only within the active tenant.

Future cross-tenant search requires explicit administrative permissions and remains outside the MVP.

---

# Audit Integration

Audit records include the tenant identifier.

This allows:

- complete traceability
- tenant-specific reporting
- isolated compliance records

Audit information never crosses tenant boundaries.

---

# Backup Integration

Backups support multiple strategies.

Examples include:

- complete platform backup
- tenant backup
- tenant export
- tenant restore

Tenant restoration does not require restoring the complete platform.

---

# Deployment Modes

The architecture supports:

- single organization
- private cloud
- managed hosting
- SaaS

The deployment model does not change public contracts.

---

# Migration Strategy

The MVP starts with a default tenant.

Example:

```text
Default Tenant

↓

All Existing Data
```

Future migration simply assigns tenant identifiers to existing objects.

No contract changes are required.

---

# Security

Tenant separation is enforced by:

- backend authorization
- repository filtering
- effective context
- permission evaluation
- audit logging
- revision tracking

Clients cannot bypass tenant isolation.

---

# Performance

Tenant-aware caching prevents unnecessary cache invalidation.

Examples include:

- tenant configuration cache
- hierarchy cache
- registry cache
- search cache

Each cache entry belongs to exactly one tenant.

---

# Consequences

## Positive

### Future-Proof Architecture

The platform supports SaaS and managed hosting without redesign.

---

### Strong Isolation

Business data remains separated between organizations.

---

### Flexible Configuration

Each tenant can evolve independently.

---

### Better Security

Tenant isolation becomes a core architectural property.

---

### Independent Evolution

Hierarchy, workflows and configuration may differ between tenants.

---

### Easier Operations

Tenant-specific backup and restore become possible.

---

## Negative

### Higher Initial Complexity

Every service must be tenant-aware.

---

### Additional Validation

Tenant ownership must be verified throughout the application.

---

### More Metadata

Business objects require tenant identifiers.

---

### Increased Testing

Isolation must be verified in all repositories and APIs.

---

# Alternatives Considered

## Single-Tenant Architecture

Advantages

- Very simple implementation
- Minimal metadata

Disadvantages

- Difficult future migration
- Poor scalability
- High redesign cost

Rejected.

---

## Separate Application per Customer

Advantages

- Strong isolation

Disadvantages

- High operational overhead
- Duplicate deployments
- Difficult maintenance

Rejected.

---

## Shared Data Without Tenant Boundaries

Advantages

- Simple implementation

Disadvantages

- Serious security risks
- Impossible access control
- No customer isolation

Rejected.

---

## Database per Tenant

Advantages

- Strong physical isolation

Disadvantages

- Operational complexity
- Difficult reporting
- Harder upgrades

Deferred.

The initial architecture assumes logical tenant isolation while remaining compatible with future physical isolation if required.

---

# Related ADRs

- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0004 — Security Profiles and Deployment Modes
- ADR-0007 — Generic Hierarchy and Context Architecture
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0015 — Chat and Conversation Architecture
- ADR-0016 — Knowledge Architecture
- ADR-0018 — Plugin and Package Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0024 — Identity and Authorization
- ADR-0031 — Performance and Caching
- ADR-0032 — Backup and Disaster Recovery

---

# Implementation Notes

The MVP operates with a single default tenant while preserving tenant identifiers in the public contracts and internal architecture where appropriate.

Business services, repositories, authorization, runtime configuration and future registries are designed to become fully tenant-aware without requiring incompatible contract changes.
