# Hierarchy Architecture

The **Hierarchy Architecture** defines the organizational structure of the Kernschmied platform and the mechanisms by which configuration, prompts, permissions, and business context are inherited across different organizational levels.

Unlike traditional applications that model projects, departments, customers, or users as independent entities, Kernschmied represents all organizational elements as **generic hierarchy nodes**.

This approach provides maximum flexibility while maintaining stable APIs, deterministic inheritance, and a schema-driven user interface.

---

# Goals

The Hierarchy Architecture is designed to provide:

- Generic organizational structures
- Schema-driven node rendering
- Configuration inheritance
- Prompt inheritance
- Extensible node types
- Stable APIs
- Fine-grained authorization
- Future-proof data modeling

---

# Architectural Principles

The hierarchy subsystem follows several core principles.

## Generic Instead of Specialized

The backend does not contain entity types such as:

- Project
- Customer
- Department
- Workspace
- Team

Instead, all organizational entities are represented by generic hierarchy nodes with associated schemas.

---

## Schema-Driven Representation

The meaning of a node is determined by its schema.

For example:

```text
Node

↓

Schema

↓

Rendered View

↓

Available Actions
```

The backend remains independent of frontend presentation.

---

## Hierarchical Inheritance

Each node inherits context from its ancestors.

Inherited elements include:

- configuration
- prompts
- permissions
- metadata
- defaults

Overrides are applied deterministically.

---

# High-Level Architecture

```text
                     Hierarchy

                          │

                 Root (System)

                          │

            ┌─────────────┴─────────────┐

            │                           │

        Organization               Shared Area

            │

      Department

            │

        Project

            │

       Conversation

            │

          Request
```

The number and meaning of intermediate levels are configurable.

---

# Generic Node Model

Every hierarchy node shares the same core structure.

Typical attributes include:

- unique identifier
- parent identifier
- schema identifier
- display name
- configuration
- metadata
- ordering information
- timestamps

Business semantics are defined externally through schemas.

---

# Node Identity

Each node has a globally unique identifier.

Example:

```text
node_7c41d8
```

Identifiers remain stable even if:

- the name changes
- the schema changes
- the parent changes

This allows reliable references throughout the platform.

---

# Parent-Child Relationships

Nodes form a directed tree.

```text
Root

├── Organization

│   ├── Team A

│   └── Team B

└── Shared
```

Every node has exactly one parent except the root node.

---

# Root Node

The root node represents the global application context.

Typical responsibilities:

- system defaults
- global prompts
- root configuration
- inherited permissions

There is exactly one root node.

---

# Node Schemas

A node's schema determines:

- available fields
- UI layout
- validation
- icons
- actions
- editable properties

The hierarchy engine itself remains schema-independent.

---

# Hierarchy Levels

Although generic, many installations use logical levels such as:

```text
System

↓

Organization

↓

Department

↓

Project

↓

Conversation

↓

Request
```

These are conventions rather than hardcoded entity types.

---

# Configuration Inheritance

Configuration is resolved along the hierarchy.

```text
Root

↓

Department

↓

Project

↓

Conversation

↓

Resolved Configuration
```

Child nodes override inherited values where permitted.

---

# Prompt Inheritance

Prompt inheritance follows the same traversal.

```text
Global Prompt

↓

Department Prompt

↓

Project Prompt

↓

Conversation Prompt

↓

Resolved Prompt
```

The resulting prompt is deterministic and reproducible.

---

# Permission Inheritance

Authorization policies may also be inherited.

Example:

```text
Organization

↓

Department

↓

Project

↓

User Access
```

More specific rules override inherited defaults where applicable.

---

# Metadata

Hierarchy nodes may contain arbitrary metadata.

Examples:

- customer number
- project code
- department color
- business identifiers

Metadata is validated by the node schema.

---

# UI Representation

The frontend renders hierarchy nodes using the Generic Tree.

```text
Hierarchy API

↓

Generic Tree

↓

Schema Renderer

↓

Node View
```

No frontend component is tied to a specific business entity.

---

# Node Creation

Typical lifecycle:

```text
Create Request

↓

Schema Validation

↓

Parent Validation

↓

Persistence

↓

Revision Update
```

Invalid nodes are rejected before persistence.

---

# Node Update

Updates follow the same validation pipeline.

Modified elements may include:

- name
- schema
- metadata
- configuration
- ordering

Hierarchy integrity is preserved.

---

# Node Deletion

Deletion policies are implementation dependent.

Possible strategies:

- reject when children exist
- recursive deletion
- logical deletion
- archival

The chosen strategy should remain deterministic.

---

# Ordering

Sibling nodes may define an explicit ordering.

Ordering affects:

- tree rendering
- navigation
- UI presentation

Ordering has no effect on inheritance semantics.

---

# Hierarchy Traversal

Traversal occurs in two primary directions.

## Downward Traversal

Used for:

- tree rendering
- recursive operations
- search

---

## Upward Traversal

Used for:

- configuration resolution
- prompt inheritance
- permission evaluation

Both traversals are deterministic.

---

# Validation

Hierarchy operations validate:

- parent existence
- schema compatibility
- cycles
- required fields
- unique identifiers

Invalid structures are rejected.

---

# Cyclic Dependency Prevention

The hierarchy must remain a tree.

Example of an invalid structure:

```text
A

↓

B

↓

C

↓

A
```

Cycles are detected during updates.

---

# Configuration Resolution

The Configuration Resolver walks the hierarchy upward.

```text
Current Node

↓

Parent

↓

Grandparent

↓

Root

↓

Resolved Configuration
```

Each level contributes configuration according to merge rules.

---

# Prompt Resolution

Prompt resolution uses the same traversal.

Prompt fragments are merged in hierarchical order.

This guarantees consistent conversational context.

---

# API Integration

Hierarchy nodes are exposed through dedicated REST endpoints.

Typical operations include:

- list
- retrieve
- create
- update
- delete

The API contract remains independent of specific node types.

---

# Revision Tracking

Hierarchy changes increment the hierarchy revision.

```text
Hierarchy Updated

↓

Revision++

↓

Frontend Reload
```

Clients reload cached trees only when revisions change.

---

# Caching

Frequently cached elements include:

- tree structure
- schema metadata
- resolved configuration

Caches are invalidated using hierarchy revisions.

---

# Security

Hierarchy operations require authorization.

Typical checks include:

- node visibility
- creation rights
- update permissions
- deletion permissions

Authorization is always evaluated server-side.

---

# Performance Considerations

The hierarchy is optimized for:

- fast traversal
- deterministic inheritance
- efficient caching
- incremental updates

Recursive queries should remain inexpensive for typical organizational sizes.

---

# Future Extensions

The hierarchy architecture allows future support for:

- multiple roots
- virtual nodes
- filtered views
- cross-links
- soft references
- tenant isolation
- workspace overlays

These additions can be implemented without changing the core node model.

---

# Relationship to Other Architecture

The hierarchy subsystem interacts with several architectural components.

```text
Hierarchy

↓

Configuration Resolver

↓

Prompt Resolver

↓

Schema Renderer

↓

Generic Tree
```

It therefore forms the structural backbone of the platform.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Configuration-Architecture]]
- [[Prompt-Inheritance]]
- [[UI-Schema-Pipeline]]
- [[Request-Lifecycle]]

---

## APIs

- [[Hierarchy]]
- [[Configuration]]
- [[Bootstrap]]
- [[UI-Schema]]

---

## Frontend

- [[Generic-Tree]]
- [[Schema-Renderer]]
- [[Frontend-Overview]]

---

## ADRs

- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0001-Schema-Driven-UI]]

---

# Summary

The Hierarchy Architecture provides a generic, schema-driven organizational model that replaces fixed business entities with flexible hierarchy nodes.

By combining deterministic inheritance, schema-based rendering, centralized configuration resolution, prompt composition, and server-side authorization, the hierarchy becomes the structural foundation of the Kernschmied platform while remaining extensible, maintainable, and independent of specific business domains.

---

Back to [[Home]].
