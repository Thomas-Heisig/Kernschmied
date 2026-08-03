# ADR-0023: Hierarchy and Modeling

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable platform rather than a collection of isolated business modules.

Traditional applications usually define fixed object hierarchies such as:

- Customers
- Projects
- Tasks
- Documents
- Conversations

These structures are embedded directly into the application code and database schema.

Kernschmied instead must allow organizations to model their own structures without changing application code.

Examples include:

- Companies
- Departments
- Workspaces
- Projects
- Construction Sites
- Knowledge Areas
- Documentation
- AI Assistants
- Customers
- Teams
- Chats
- Resources

The hierarchy therefore becomes a core architectural concept instead of a business-specific implementation.

---

# Problem

Hardcoded business models create several long-term problems.

Typical examples include:

- fixed database structures
- business-specific React components
- specialized REST endpoints
- duplicated permissions
- difficult customization
- expensive migrations
- limited extensibility

Adding a new business concept often requires:

- database migrations
- backend changes
- frontend changes
- API changes
- additional tests

The platform therefore requires a generic modeling approach.

---

# Decision

Kernschmied adopts a **Generic Hierarchy and Modeling Architecture**.

Business concepts are represented through configurable hierarchy nodes instead of specialized application objects.

The hierarchy describes business organization.

The application provides the behavior.

---

# Architectural Principle

> **The hierarchy defines structure.**
>
> **Registries define capabilities.**
>
> **Configuration defines behavior.**
>
> **Business concepts emerge from modeling rather than hardcoded classes.**

---

# High-Level Architecture

```text
Tenant

        │

        ▼

Hierarchy

        │

 ┌──────┼─────────────┐
 │      │             │
 ▼      ▼             ▼

Workspace Project   Knowledge

        │

        ▼

Chat

        │

        ▼

Resources
```

---

# Generic Hierarchy Nodes

Every object within the hierarchy is represented by a generic node.

Nodes share the same structural properties.

Examples include:

- identifier
- parent
- position
- metadata
- capabilities
- revision
- status

Behavior is determined by configuration rather than by node classes.

---

# Node Types

A node always references a node type definition.

Examples include:

- workspace
- project
- department
- customer
- construction_site
- documentation
- assistant
- chat
- archive

Node types are runtime definitions.

They are not hardcoded application classes.

---

# Definition versus Instance

The architecture distinguishes between:

## Definition

A reusable description.

Examples:

- node type
- widget type
- action definition
- resource type

Definitions are managed through runtime registries.

---

## Instance

A concrete object created from a definition.

Examples:

- Workspace "Development"
- Project "Kernschmied"
- Chat "Architecture"
- Customer "Example Ltd."

Instances contain business data.

Definitions describe behavior.

---

# Modeling

Organizations create their own business models by combining node types.

Example:

```text
Workspace

↓

Projects

↓

Construction Sites

↓

Documents
```

Another installation may use:

```text
Company

↓

Departments

↓

Knowledge

↓

Chats
```

The application remains unchanged.

---

# Parent-Child Rules

Node type definitions specify:

- allowed parent types
- allowed child types
- maximum depth
- minimum depth
- ordering rules

These rules are validated by the backend.

---

# Hierarchy Operations

The hierarchy supports generic operations.

Examples include:

- create
- rename
- move
- reorder
- archive
- restore
- delete

Operations remain identical regardless of node type.

---

# Context Resolution

Every request executes within an effective hierarchy context.

Typical context includes:

- tenant
- hierarchy path
- active node
- active workspace
- active project
- active chat

Business services use the effective context rather than reconstructing hierarchy information.

---

# Capability Assignment

Capabilities are assigned through configuration.

Examples include:

- available widgets
- available actions
- available tools
- available resources
- prompts
- workflows

Capabilities are inherited through the hierarchy unless explicitly overridden.

---

# Inheritance

Configuration may inherit from parent nodes.

Possible strategies include:

- inherit
- extend
- replace
- disable

Inheritance behavior is defined per configuration type.

---

# Resources

Hierarchy nodes may own resources.

Examples include:

- notes
- documents
- images
- files
- datasets

Resource ownership is independent of node type.

---

# Widgets

Widgets are assigned to hierarchy nodes.

Examples include:

- chat widget
- resource list
- documentation viewer
- calendar
- dashboard

Widgets are selected dynamically.

---

# Actions

Actions are assigned through configuration.

Examples include:

- create child
- rename
- archive
- generate report
- upload document

The hierarchy determines available actions.

---

# Prompt Integration

Prompt inheritance follows the hierarchy.

Possible prompt levels include:

- tenant
- workspace
- project
- chat

Effective prompts are calculated by the Prompt Service.

---

# Security

Permissions are evaluated within the hierarchy.

Examples include:

- subtree permissions
- inherited permissions
- explicit permissions

The frontend never determines access rights.

---

# Runtime Configuration

Hierarchy behavior is runtime configurable.

Examples include:

- node types
- icons
- ordering
- inheritance
- capabilities

Changing hierarchy definitions requires no code changes.

---

# Registry Integration

Hierarchy definitions are stored in runtime registries.

Examples include:

- node type definitions
- hierarchy templates
- hierarchy validators

The hierarchy engine consumes registry definitions.

---

# Search Integration

Hierarchy provides search scope.

Examples include:

- current node
- subtree
- workspace
- tenant

Search providers respect hierarchy boundaries.

---

# Event Integration

Hierarchy operations generate platform events.

Examples include:

- hierarchy.created
- hierarchy.updated
- hierarchy.moved
- hierarchy.deleted
- hierarchy.archived

Other services react to these events.

---

# Audit Integration

Administrative hierarchy changes generate:

- audit entries
- revision updates
- cache invalidation

Every structural modification is traceable.

---

# Performance

The architecture supports future optimizations including:

- cached hierarchy paths
- materialized paths
- nested sets
- closure tables

The optimization strategy remains an implementation detail.

---

# Consequences

## Positive

### Generic Business Modeling

Organizations model their own structures.

---

### Reduced Code Duplication

Business concepts reuse the same infrastructure.

---

### Stable Contracts

Public APIs remain independent of business terminology.

---

### Runtime Flexibility

Hierarchy evolution requires no code changes.

---

### Better Maintainability

Generic services replace specialized implementations.

---

### Future-Proof Architecture

New business concepts become configuration rather than software development tasks.

---

## Negative

### Higher Initial Complexity

Generic modeling requires careful architectural design.

---

### More Metadata

Definitions require additional configuration.

---

### Validation Complexity

Hierarchy rules must be validated consistently.

---

### Learning Curve

Administrators must understand hierarchy modeling concepts.

---

# Alternatives Considered

## Hardcoded Business Objects

Advantages

- Simple implementation
- Easy understanding

Disadvantages

- Poor extensibility
- Frequent code changes
- Tight coupling

Rejected.

---

## Independent Object Trees

Advantages

- Local optimization

Disadvantages

- Duplicate logic
- Inconsistent behavior
- Difficult maintenance

Rejected.

---

## Dynamic Database Tables

Advantages

- Flexible schemas

Disadvantages

- Difficult validation
- Poor tooling
- Complex migrations

Rejected.

---

## Fixed Enterprise Data Model

Advantages

- Predictable structure

Disadvantages

- Limited adaptability
- Business assumptions embedded in software

Rejected.

---

# Related ADRs

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0007 — Generic Hierarchy and Context Architecture
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0010 — Generic Resource Architecture
- ADR-0011 — Widget Architecture
- ADR-0012 — Action Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0015 — Chat and Conversation Architecture
- ADR-0016 — Knowledge Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0020 — Multi-Tenant Architecture
- ADR-0021 — Search Architecture
- ADR-0023a — Storage Architecture
- ADR-0024 — Identity and Authorization

---

# Implementation Notes

The MVP provides a generic hierarchy supporting workspaces, projects and chats.

Future node types are introduced through runtime registries and configuration.

The hierarchy engine, contracts and APIs remain unchanged as the business model evolves.
