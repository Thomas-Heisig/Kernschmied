# ADR-0010: Generic Resource Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable AI platform rather than a fixed business application.

The platform shall support arbitrary business domains throughout its lifetime without requiring architectural changes to the application core.

Everything that represents business information is treated as a **Resource**.

Examples include:

- notes
- documents
- prompts
- templates
- knowledge entries
- contacts
- customers
- suppliers
- projects
- tasks
- calendar events
- workflows
- models
- tools
- assistants
- chats
- messages
- files
- images
- videos
- audio
- web pages
- datasets
- custom business objects

Future installations must be able to introduce completely new resource types that are unknown today.

The application core therefore cannot contain business-specific entities.

---

# Problem

Traditional business applications usually implement every business object separately.

Typical examples are:

- Customer
- Product
- Invoice
- Contact
- Task
- Project

Every new object generally requires:

- new database tables
- new REST endpoints
- new permissions
- new services
- new frontend pages
- new forms
- new tests

This approach does not scale for a configurable platform.

---

## Tight Coupling

Business concepts become tightly coupled to application code.

Adding one new object often requires changes across multiple layers.

---

## Poor Runtime Extensibility

Introducing a new business object often requires:

- backend development
- frontend development
- deployment
- database migration

instead of runtime configuration.

---

## Code Duplication

Most business objects implement similar functionality:

- title
- description
- ownership
- permissions
- metadata
- revisioning
- auditing
- searchability

Yet every implementation duplicates nearly identical logic.

---

## Difficult Customization

Customer-specific business objects become expensive because every deployment requires additional application development.

---

# Decision

Kernschmied adopts a **Generic Resource Architecture**.

The application core understands only generic resources.

Business meaning is provided through configurable resource type definitions.

Every business object consists of three independent concepts:

- Resource Type Definition
- Resource Instance
- Resource Assignment

These concepts evolve independently.

---

# Architectural Principle

> **The platform understands resources.
>
> Resource types define meaning.
>
> Resource instances contain business data.
>
> Resource assignments define context.
>
> The application core remains generic.**

---

# High-Level Architecture

```text
Resource Registry

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

Assignments

        │

        ▼

Hierarchy / Chat / Workflow / Assistant

        │

        ▼

Widgets • Actions • AI • API
```

---

# Core Concepts

The architecture consists of several independent concepts.

---

## Resource Type Definition

A Resource Type defines the meaning of a resource.

Typical properties include:

- identifier
- display name
- schema
- lifecycle
- permissions
- capabilities
- widgets
- actions
- relationships

Examples include:

- note
- document
- image
- prompt
- workflow
- customer
- task

Resource Types are configuration.

They do not contain business data.

---

## Resource Instance

A Resource Instance contains actual business information.

Every resource contains common metadata such as:

- identifier
- resource type
- schema version
- revision
- timestamps
- owner
- classification
- metadata

Business-specific information is stored inside structured resource data.

---

## Resource Assignment

Resources are independent of hierarchy.

Resources are assigned to contexts.

Typical assignment targets include:

- hierarchy nodes
- chats
- assistants
- workflows
- users
- calendar events
- projects

Assignments define visibility and context.

They do not duplicate resource data.

---

# Resource Schema

Every Resource Type references a versioned schema.

The schema defines:

- fields
- field types
- validation
- required properties
- constraints
- default values

Schemas evolve independently.

---

# Resource Schema Evolution

Each Resource Type owns its own schema lifecycle.

Supported concepts include:

- schema versions
- revisions
- deprecated fields
- migration strategies
- compatibility validation

Schema evolution never modifies existing resources implicitly.

---

# Resource Capabilities

Every Resource Type declares its supported capabilities.

Examples include:

- searchable
- editable
- attachable
- embeddable
- ai-readable
- ai-writable
- versioned
- exportable
- importable
- indexable
- commentable
- previewable

Capabilities are declarative metadata.

Application logic must not infer capabilities from resource types.

---

# Resource Providers

Resources may originate from different providers.

Examples include:

- internal database
- filesystem
- object storage
- SharePoint (future)
- Microsoft 365 (future)
- Google Workspace (future)
- Nextcloud (future)

The application communicates only through the Resource Registry.

Provider implementations remain replaceable.

---

# Resource Relationships

Resources may reference other resources.

Examples include:

- parent
- child
- dependency
- attachment
- reference
- ownership
- workflow participation

Relationships are generic.

The application core does not contain business-specific references.

---

# Resource Classification

Resources may define a classification.

Examples include:

- public
- internal
- confidential
- restricted

Classification influences:

- permissions
- retention
- export
- auditing
- AI visibility

---

# Resource Lifecycle

Every resource follows a configurable lifecycle.

Typical states include:

- draft
- active
- archived
- deleted

Additional states may be introduced through configuration.

---

# Generic CRUD

The platform exposes generic operations.

Examples include:

- create
- read
- update
- archive
- restore
- delete

Business-specific behavior is implemented through Actions and Workflows.

---

# Validation

Every resource is validated before persistence.

Validation includes:

- schema validation
- field validation
- permissions
- classification
- lifecycle
- registry validation

Validation always occurs in the backend.

---

# Registry Integration

Resource Types are managed through the Registry Architecture.

The registry is responsible for:

- discovery
- validation
- activation
- revision tracking
- lifecycle management

Only validated resource definitions become active.

---

# Dynamic Extensibility

New Resource Types may be introduced without changing:

- backend services
- frontend components
- REST endpoints
- database schema
- application core

Only configuration changes are required.

---

# Generic User Interface

The frontend never contains business-specific editors.

Examples that must not exist include:

- CustomerEditor
- ProjectEditor
- ProductEditor
- TaskEditor
- DocumentEditor

Instead, generic widgets render resources dynamically.

Rendering is driven by:

- resource schema
- widget definition
- layout definition

The backend defines **what** is rendered.

The frontend defines **how** it is rendered.

---

# Resource Widgets

Resources may be visualized using different widgets.

Examples include:

- form
- properties
- table
- tree
- kanban
- timeline
- gallery
- markdown
- preview
- relationship graph

Widgets are selected through configuration.

Resources never contain presentation logic.

---

# Resource Actions

Resources expose generic actions.

Examples include:

- create
- edit
- duplicate
- archive
- move
- link
- unlink
- export
- summarize
- classify
- translate
- compare

Actions are defined independently of Resource Types.

---

# Resource Events

Resource modifications generate versioned events.

Typical events include:

- resource.created
- resource.updated
- resource.archived
- resource.deleted
- resource.linked
- resource.unlinked
- resource.classified
- resource.moved

Events are transported through the generic event contract.

---

# AI Integration

Resources are first-class citizens for AI.

AI models may:

- search resources
- summarize resources
- classify resources
- reference resources
- compare resources
- generate resources

Access is always validated by the backend.

---

# Search and Indexing

Resources participate in the generic search infrastructure.

Search behavior depends on:

- resource type
- permissions
- metadata
- hierarchy
- classification
- indexing capabilities

The search engine has no knowledge of business-specific entities.

---

# Security

Resources never bypass security.

The backend validates:

- authentication
- authorization
- visibility
- classification
- lifecycle
- revision

The frontend must never assume permissions.

---

# Separation of Responsibilities

The backend is responsible for:

- validation
- persistence
- permissions
- lifecycle
- revisioning
- auditing
- schema enforcement

The frontend is responsible for:

- rendering
- interaction
- editing
- validation feedback

Business rules remain exclusively in the backend.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0007 — Runtime Configuration Architecture
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0009 — Dynamic Registry and Runtime Definitions

The Generic Resource Architecture depends on versioned contracts, runtime registries and schema-driven rendering.

---

# Consequences

## Positive

### Generic Platform

The application core remains independent of business domains.

---

### Runtime Extensibility

New business objects become available through configuration.

---

### Reduced Code Duplication

Common functionality is implemented once.

---

### Stable Contracts

All resources share common contracts.

---

### Better Maintainability

Business evolution occurs through configuration instead of source code modifications.

---

### AI Readiness

Every business object becomes uniformly accessible for AI.

---

### Flexible User Interface

Generic widgets support arbitrary resource types.

---

### Provider Independence

Storage implementations remain replaceable.

---

## Negative

### Higher Initial Complexity

Generic infrastructure requires careful architectural design.

---

### Strong Schema Governance

Poor schemas negatively affect the entire platform.

---

### Migration Requirements

Schema evolution requires migration planning.

---

### Documentation Effort

Resource Types and Schemas must be documented consistently.

---

# Alternatives Considered

## Dedicated Business Entities

### Advantages

- Simple implementation
- Familiar architecture

### Disadvantages

- Tight coupling
- Code duplication
- Poor extensibility
- Frequent deployments

Rejected.

---

## Entity-Attribute-Value (EAV)

### Advantages

- Flexible storage

### Disadvantages

- Weak validation
- Complex querying
- Poor tooling
- Difficult maintenance

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
- Difficult auditing
- Non-deterministic behavior

Rejected.

---

# Compliance

All resource-related implementations shall comply with this ADR.

In particular:

- resource types shall be registry-managed
- resource instances shall be independent of assignments
- assignments shall define context instead of ownership
- resources shall be schema-driven
- schemas shall be versioned
- validation shall occur exclusively in the backend
- business entities shall not be hardcoded into the application core
- resources shall expose declarative capabilities
- widgets shall remain generic
- actions shall remain generic
- providers shall be replaceable
- resource changes shall generate versioned events
- resource evolution shall occur through configuration
- all resource changes shall be auditable
- all public resource contracts shall remain versioned and backward compatible whenever possible
