# ADR-0010: Generic Resource Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable platform rather than a fixed business application.

The platform must support an arbitrary number of business objects throughout its lifetime without requiring changes to the application core.

Examples include:

- notes
- documents
- knowledge entries
- contacts
- customers
- suppliers
- products
- tasks
- appointments
- images
- videos
- audio files
- prompts
- templates
- workflows
- datasets
- custom resource types

Future deployments may introduce completely new resource types that are unknown at the time the platform is developed.

The architecture must therefore support business evolution without requiring new source code for every new object type.

---

# Problem

Traditional business applications typically model every object as its own entity.

Examples include:

- Customer
- Product
- Invoice
- Task
- Contact
- Project

Each new object generally requires:

- database tables
- REST endpoints
- validation
- permissions
- frontend pages
- forms
- tests

As the application grows this creates increasing complexity.

---

## Tight Coupling

Business concepts become directly coupled to application code.

Every new object requires modifications across multiple subsystems.

---

## Poor Runtime Extensibility

Creating new business objects often requires:

- backend development
- frontend development
- deployment
- database migrations

instead of runtime configuration.

---

## Code Duplication

Most business objects share common behavior:

- title
- metadata
- permissions
- ownership
- versioning
- lifecycle
- audit logging

Yet each implementation duplicates similar logic.

---

## Difficult Customization

Different deployments often require different business objects.

Supporting customer-specific entities becomes increasingly expensive.

---

## Decision

Kernschmied adopts a **Generic Resource Architecture**.

Business objects are represented as configurable resource types instead of hardcoded application entities.

The platform distinguishes between:

- resource type definitions
- resource instances
- resource schemas
- resource relationships

Only the generic resource infrastructure is implemented in the application core.

Business-specific resource types are introduced through validated runtime configuration.

---

# Architectural Principle

> **The platform understands resources.
>
> Resource types define meaning.
>
> The application core remains generic.**

---

# High-Level Architecture

```text
Resource Type Registry

        │

        ▼

Resource Type Definition

        │

        ▼

Validation Schema

        │

        ▼

Resource Instance

        │

        ▼

Generic Services

        │

        ▼

Widgets / API / AI
```

---

# Core Concepts

The architecture consists of several independent concepts.

## Resource Type

A resource type defines:

- identifier
- display name
- schema
- lifecycle
- permissions
- default actions
- supported widgets
- relationships

Examples include:

- note
- document
- task
- contact
- image
- prompt

New resource types may be added at runtime.

---

## Resource Instance

A resource instance represents actual business data.

Every resource contains common metadata such as:

- identifier
- resource type
- revision
- owner
- timestamps
- classification
- metadata

Business-specific fields are stored inside structured resource data validated against the resource schema.

---

## Resource Schema

Each resource type references a versioned schema.

The schema defines:

- fields
- field types
- required properties
- validation rules
- constraints
- default values

Schemas evolve independently through versioning.

---

## Resource Relationships

Resources may reference other resources.

Examples include:

- parent-child
- attachment
- dependency
- reference
- ownership
- workflow participation

Relationships are generic and are not hardcoded into the application.

---

## Resource Classification

Resources may define a data classification.

Examples include:

- public
- internal
- confidential
- restricted

Classification influences:

- permissions
- retention
- auditing
- export
- AI visibility

---

# Resource Lifecycle

Every resource follows a common lifecycle.

Typical states include:

- draft
- active
- archived
- deleted

Additional lifecycle states may be introduced through configuration.

---

# Generic CRUD

The platform provides generic operations.

Examples include:

- create
- read
- update
- archive
- restore
- delete

Business-specific behavior is implemented through actions and workflows rather than custom CRUD endpoints.

---

# Validation

Every resource is validated before persistence.

Validation includes:

- schema validation
- required fields
- field constraints
- classification rules
- permissions

Validation is performed by the backend.

---

# Versioning

Every resource contains:

- schema_version
- revision

Resource schemas evolve independently from resource instances.

Breaking schema changes require migration strategies.

---

# Registry Integration

Resource types are managed through the Registry Architecture.

Registries are responsible for:

- discovery
- validation
- activation
- lifecycle
- revision tracking

Only active resource types become available.

---

# Dynamic Extensibility

New resource types may be introduced without modifying:

- backend services
- frontend components
- REST endpoints
- database structure

Only validated resource definitions may become active.

---

# Generic User Interface

The frontend never contains dedicated business pages such as:

- CustomerEditor
- ProductEditor
- TaskEditor

Instead it renders generic widgets using:

- resource schemas
- widget definitions
- layout definitions

The backend defines what should be presented.

The frontend defines how it is rendered.

---

# AI Integration

Resources are first-class citizens for AI interactions.

AI models may:

- search resources
- summarize resources
- classify resources
- reference resources
- generate new resources

Access is always controlled by permissions and classification.

---

# Search and Indexing

Resources participate in the generic search infrastructure.

Search behavior may depend on:

- resource type
- metadata
- hierarchy
- permissions
- classification

The search engine does not require knowledge of business-specific resource types.

---

# Security

Resource access is always validated by the backend.

Validation includes:

- authentication
- authorization
- visibility
- classification
- lifecycle state

The frontend must never assume access rights.

---

# Separation of Responsibilities

The backend is responsible for:

- resource validation
- persistence
- permissions
- lifecycle
- versioning
- auditing

The frontend is responsible for:

- rendering
- editing
- interaction
- validation feedback

Business rules remain exclusively in the backend.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0007 — Runtime Configuration Architecture
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0009 — Dynamic Registry and Runtime Definitions

The Generic Resource Architecture relies on versioned contracts, runtime registries and schema-driven rendering.

---

# Consequences

## Positive

### Generic Business Platform

The application core remains independent of business domains.

---

### Runtime Extensibility

New resource types become available without source code modifications.

---

### Reduced Code Duplication

Common functionality is implemented once.

---

### Consistent Validation

All resources follow the same validation model.

---

### Better Maintainability

Business evolution occurs through configuration instead of application changes.

---

### AI Readiness

Resources become uniformly accessible for AI-assisted workflows.

---

### Stable Contracts

Resource contracts evolve independently through versioning.

---

## Negative

### Higher Initial Complexity

Generic resource services require more upfront design.

---

### Strong Schema Governance

Poor schema definitions may negatively affect usability.

---

### Migration Complexity

Schema evolution requires migration planning for existing resources.

---

### Documentation Requirements

Resource types and schemas must be documented consistently.

---

# Alternatives Considered

## Dedicated Business Entities

### Advantages

- Simple implementation
- Familiar architecture

### Disadvantages

- High duplication
- Tight coupling
- Poor extensibility
- Frequent deployments

Rejected.

---

## Entity-Attribute-Value (EAV)

### Advantages

- High flexibility

### Disadvantages

- Difficult validation
- Poor performance
- Complex querying
- Difficult tooling

Rejected.

---

## Arbitrary JSON Documents

### Advantages

- Maximum flexibility

### Disadvantages

- No contracts
- Weak validation
- Poor interoperability
- Difficult evolution

Rejected.

---

## Runtime Code Generation

Generating business entities through executable scripts.

### Advantages

- Extremely flexible

### Disadvantages

- Security risks
- Difficult testing
- Difficult maintenance
- Non-deterministic behavior

Rejected.

---

# Compliance

All resource-related implementations shall comply with this ADR.

In particular:

- resources shall be generic
- resource types shall be registry-managed
- schemas shall be versioned
- validation shall occur in the backend
- business entities shall not be hardcoded into the application core
- resource evolution shall occur through configuration
- permissions shall always be enforced server-side
- resource changes shall be auditable
- resource contracts shall remain versioned and backward compatible whenever possible