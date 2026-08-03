# Hierarchy Management

The **Hierarchy Management** subsystem is responsible for representing, storing, validating, and resolving the generic hierarchy used throughout the Kernschmied backend.

Unlike traditional applications that hardcode concepts such as projects, folders, workspaces, or organizations into the data model, Kernschmied uses a **schema-driven hierarchy** composed of generic nodes. Every hierarchy node is interpreted through metadata and schemas rather than fixed application logic.

This approach enables the platform to evolve without changing the backend whenever new business structures, organizational models, or custom node types are introduced.

---

## Goals

The Hierarchy Management subsystem is designed to provide:

- Generic hierarchical structures
- Schema-driven node behavior
- Runtime extensibility
- Deterministic inheritance
- Stable APIs
- Efficient tree traversal
- Secure authorization boundaries
- Future-proof architecture

---

## Design Principles

## Generic Instead of Specialized

The backend does not implement dedicated entity types such as:

- Project
- Workspace
- Department
- Customer
- Folder

Instead, everything is represented as a generic hierarchy node.

```text
Hierarchy Node

↓

Schema

↓

Runtime Behavior

```

Business meaning is determined by configuration rather than source code.

---

## Data Defines Structure

The hierarchy is defined entirely by persistent data.

Typical node information includes:

- identifier
- parent identifier
- schema identifier
- node type
- metadata
- display information

The backend interprets these values dynamically.

---

## Stable Contracts

The frontend communicates exclusively through generic hierarchy contracts.

A hierarchy response should not expose implementation-specific classes or database structures.

---

## Separation of Structure and Behavior

Hierarchy stores relationships.

Application services determine behavior.

```text
Hierarchy

↓

Resolvers

↓

Services

↓

Application Logic

```

This separation keeps the hierarchy reusable across multiple subsystems.

---

## High-Level Architecture

```text
Database

↓

Hierarchy Repository

↓

Hierarchy Service

↓

Hierarchy Resolver

↓

Application Services

↓

Frontend

```

Each layer has a clearly defined responsibility.

---

## Hierarchy Node

A hierarchy node represents a single element within the tree.

Typical properties include:

- unique identifier
- parent identifier
- schema identifier
- node type
- display name
- metadata

Additional attributes may be introduced through versioned schemas.

---

## Parent-Child Relationships

Nodes form a tree using parent references.

Example:

```text
Organization

├── Department A
│   ├── Project Alpha
│   └── Project Beta
│
└── Department B
    └── Workspace

```

Each node has at most one parent but may contain multiple children.

---

## Root Node

Every hierarchy begins with a root node.

Example:

```text
Root

↓

Organization

↓

Departments

↓

Projects

↓

Chats

```

The root provides a deterministic entry point for traversal.

---

## Schema-Driven Nodes

Each node references a schema.

Example:

```text
Node

↓

Schema

↓

Renderer

↓

Behavior

```

Schemas define presentation, actions, validation rules, and configuration inheritance.

---

## Node Types

Node types classify the general purpose of a node.

Examples include:

- system
- organization
- workspace
- project
- user
- chat

Applications should treat node types as metadata rather than hardcoded business entities.

---

## Metadata

Nodes may contain additional metadata.

Typical examples include:

- icons
- colors
- ordering
- tags
- descriptions
- feature flags

Metadata remains schema-dependent.

---

## Hierarchy Repository

The repository manages persistence.

Responsibilities include:

- loading nodes
- storing nodes
- updating relationships
- deleting nodes
- querying descendants

Repositories isolate persistence from business logic.

---

## Hierarchy Service

The Hierarchy Service coordinates runtime operations.

Responsibilities include:

- validation
- tree construction
- lookup operations
- traversal
- authorization integration

Business logic never communicates directly with the repository.

---

## Hierarchy Resolver

The Hierarchy Resolver computes relationships required by other subsystems.

Typical responsibilities include:

- ancestor lookup
- descendant lookup
- inheritance path generation
- configuration scope resolution
- prompt inheritance

The resolver produces deterministic traversal results.

---

## Traversal

Hierarchy traversal may proceed upward or downward.

Example:

```text
Root

↓

Organization

↓

Project

↓

Chat

```

or

```text
Chat

↑

Project

↑

Organization

↑

Root

```

Traversal direction depends on the requesting subsystem.

---

## Configuration Inheritance

Configuration inheritance relies on hierarchy traversal.

```text
Root

↓

Organization

↓

Project

↓

Conversation

↓

Resolved Configuration

```

Each level may contribute additional configuration.

---

## Prompt Inheritance

Prompt inheritance follows the same hierarchy.

Example:

```text
System Prompt

↓

Organization Prompt

↓

Project Prompt

↓

Conversation Prompt

↓

Final Prompt

```

The hierarchy therefore influences AI behavior without requiring provider-specific logic.

---

## Authorization

Hierarchy also defines authorization boundaries.

Examples include:

- accessible nodes
- inherited permissions
- administrative scopes
- isolated workspaces

Authorization is enforced entirely on the backend.

---

## API Representation

Hierarchy data is exposed through stable REST contracts.

Typical information includes:

- node identifier
- parent identifier
- schema
- metadata
- children

Clients should interpret the hierarchy generically.

---

## Validation

Hierarchy updates are validated before persistence.

Validation includes:

- unique identifiers
- parent existence
- cycle detection
- schema validity
- relationship integrity

Invalid tree structures are rejected.

---

## Cycle Prevention

The hierarchy always represents a tree.

The following structure is invalid:

```text
A

↓

B

↓

C

↓

A

```

Cycle detection is performed before updates are committed.

---

## Performance

Hierarchy operations are optimized through:

- indexed lookups
- efficient parent resolution
- revision-aware caching
- immutable traversal results

Frequently accessed hierarchy information may be cached.

---

## Revision Tracking

Hierarchy modifications increment a hierarchy revision.

```text
Revision 8

↓

Hierarchy Updated

↓

Revision 9

```

Clients use revision metadata to determine when cached hierarchy information must be refreshed.

---

## Integration with UI Schema

The hierarchy determines what the frontend renders.

```text
Hierarchy

↓

UI Schema

↓

Schema Renderer

↓

User Interface

```

The frontend does not require knowledge of individual business entities.

---

## Integration with Chat

Chat requests reference hierarchy nodes.

The backend resolves:

- inherited prompts
- configuration
- permissions
- available tools

before communicating with AI providers.

---

## Security

Hierarchy integrity is protected through:

- authentication
- authorization
- validation
- cycle prevention
- audit logging

Clients cannot modify hierarchy relationships directly without passing backend validation.

---

## Testing

Hierarchy functionality should be verified through automated tests.

Recommended coverage includes:

- tree construction
- ancestor resolution
- descendant traversal
- cycle detection
- inheritance resolution
- authorization integration
- API serialization

Testing ensures deterministic hierarchy behavior across application updates.

---

## Future Extensions

The hierarchy architecture supports future capabilities including:

- multiple hierarchy roots
- virtual nodes
- filtered views
- cross-tree references
- tenant isolation
- hierarchical policies
- dynamic navigation trees

These features can be introduced without changing existing public contracts.

---

## Relationship to Other Backend Components

Hierarchy Management supports numerous backend subsystems.

```text
Hierarchy

↓

Configuration Resolver

↓

Prompt Resolver

↓

Authorization

↓

Chat Service

↓

Frontend

```

It provides the structural backbone for runtime behavior throughout the platform.

---

## Relationship to Architecture

Hierarchy Management integrates closely with:

- [[Hierarchy-Architecture]]
- [[Configuration-Architecture]]
- [[Prompt-Inheritance]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

## Related Documentation

## Backend

- [[Backend-Overview]]
- [[Configuration]]
- [[Chat]]
- [[Validation]]
- [[Repositories]]

---

## Architecture

- [[Hierarchy-Architecture]]
- [[Configuration-Architecture]]
- [[Prompt-Inheritance]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

## APIs

- [[Hierarchy]]
- [[Configuration]]
- [[Bootstrap]]
- [[Chat]]
- [[UI-Schema]]

---

## Summary

The Hierarchy Management subsystem provides the generic structural foundation of the Kernschmied backend by representing all organizational elements as schema-driven hierarchy nodes rather than hardcoded business entities.

Through deterministic traversal, configuration and prompt inheritance, backend-enforced authorization, revision tracking, validation, and stable API contracts, the hierarchy enables the platform to support evolving organizational structures, dynamic user interfaces, and extensible application behavior while preserving architectural consistency and long-term maintainability.

---

Back to [[Home]].
