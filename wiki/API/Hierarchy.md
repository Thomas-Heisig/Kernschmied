# Hierarchy API

The Hierarchy API provides access to the generic hierarchical structure used throughout the Kernschmied platform.

Unlike traditional applications that hardcode concepts such as projects, folders, workspaces, or departments, Kernschmied stores all hierarchical structures as generic nodes with schema-driven behavior.

The Hierarchy API allows clients to:

- Browse hierarchy trees
- Retrieve node metadata
- Resolve inheritance
- Create and modify nodes
- Manage permissions
- Drive the schema-based user interface

The hierarchy is a fundamental building block of the platform and is used by nearly every subsystem.

---

# Goals

The Hierarchy API is designed to provide:

- Generic hierarchical data
- Schema-driven navigation
- Stable REST contracts
- Context resolution
- Configuration inheritance
- Prompt inheritance
- Permission boundaries
- Future extensibility

---

# Endpoints

## List Hierarchy

```http
GET /api/v1/hierarchy
```

Returns the root hierarchy or a filtered subtree.

---

## Get Node

```http
GET /api/v1/hierarchy/{node_id}
```

Returns a single hierarchy node.

---

## Create Node

```http
POST /api/v1/hierarchy
```

Creates a new hierarchy node.

---

## Update Node

```http
PUT /api/v1/hierarchy/{node_id}
```

Updates an existing node.

---

## Delete Node

```http
DELETE /api/v1/hierarchy/{node_id}
```

Deletes a hierarchy node if permitted.

---

## Future Endpoints

Future API extensions may include:

```http
GET /api/v1/hierarchy/{node_id}/children

GET /api/v1/hierarchy/{node_id}/effective-config

GET /api/v1/hierarchy/{node_id}/effective-prompt

POST /api/v1/hierarchy/{node_id}/move

POST /api/v1/hierarchy/{node_id}/copy

POST /api/v1/hierarchy/search
```

---

# Architecture

```text
REST API

        │

        ▼

Hierarchy Service

        │

        ▼

Configuration Resolver

        │

        ▼

Database
```

The Hierarchy Service is the single authoritative component responsible for hierarchy management.

---

# Generic Node Model

Every node follows the same generic contract.

Example:

```json
{
  "id": "project-17",
  "parent_id": "workspace-2",
  "type": "project",
  "name": "AI Migration",
  "schema": "project",
  "metadata": {}
}
```

No node type receives special treatment inside the backend.

---

# Node Fields

| Field | Description |
|--------|-------------|
| id | Unique node identifier |
| parent_id | Parent node identifier |
| type | Generic node type |
| name | Display name |
| schema | UI schema identifier |
| metadata | Optional custom metadata |

Additional fields may be introduced without breaking compatibility.

---

# Root Nodes

Every hierarchy begins with one or more root nodes.

Example:

```text
Workspace

├── Projects

├── Users

├── Teams

└── Archive
```

The root structure is defined by configuration rather than source code.

---

# Example Response

```json
[
  {
    "id": "root",
    "type": "workspace",
    "name": "Workspace",
    "children": [
      {
        "id": "project-1",
        "type": "project",
        "name": "Documentation"
      }
    ]
  }
]
```

The exact representation may evolve while maintaining version compatibility.

---

# Node Types

Node types are configuration-driven.

Examples include:

- workspace
- project
- folder
- team
- department
- customer
- chat
- user

Applications may introduce additional types without backend modifications.

---

# Schema Association

Every node references a UI schema.

Example:

```json
{
  "schema": "project"
}
```

The frontend uses the schema identifier to select the appropriate view through the Schema Renderer.

---

# Parent-Child Relationships

Every node belongs to exactly one parent except root nodes.

```text
Workspace

↓

Project

↓

Chat

↓

Conversation
```

Cycles are not permitted.

---

# Tree Traversal

Clients may recursively traverse the hierarchy.

```text
Root

↓

Children

↓

Grandchildren

↓

Leaf Nodes
```

The Generic Tree component renders the hierarchy independently of node types.

---

# Configuration Inheritance

Hierarchy nodes define configuration scopes.

Effective configuration is resolved by traversing the hierarchy from the root to the selected node.

```text
System

↓

Workspace

↓

Project

↓

Chat

↓

Effective Configuration
```

The Hierarchy API exposes structure only.

Configuration resolution is handled by the Configuration Resolver.

---

# Prompt Inheritance

Prompts inherit through the hierarchy using deterministic merge strategies.

Example:

```text
Global Prompt

↓

Workspace Prompt

↓

Project Prompt

↓

Chat Prompt

↓

Effective Prompt
```

The Chat Service always receives the fully resolved prompt.

---

# Authorization

Every node is protected by backend authorization.

Typical operations include:

- read
- create
- update
- delete
- move

Permissions are verified before every operation.

---

# Node Creation

Example request:

```json
{
  "parent_id": "workspace-1",
  "type": "project",
  "name": "Research",
  "schema": "project"
}
```

The backend validates:

- parent existence
- permissions
- schema validity
- node type
- naming rules

---

# Node Update

Example request:

```json
{
  "name": "Research 2027"
}
```

Only mutable fields may be modified.

Immutable identifiers remain unchanged.

---

# Node Deletion

Deletion is subject to validation.

Checks may include:

- child nodes
- active chats
- references
- permissions

Deletion rules are implemented by the Hierarchy Service.

---

# Moving Nodes

Future versions may support moving nodes.

Typical workflow:

```text
Read Node

↓

Validate Destination

↓

Permission Check

↓

Update Parent

↓

Recalculate Inheritance
```

---

# Validation

Hierarchy validation includes:

- unique identifiers
- valid parent references
- schema existence
- node type validation
- cycle detection
- maximum depth (optional)

Invalid hierarchies are rejected.

---

# Error Responses

Errors follow the standard platform contract.

Example:

```json
{
  "code": "resource_not_found",
  "message": "Hierarchy node not found.",
  "details": {
    "id": "project-42"
  },
  "request_id": "ef82b091"
}
```

---

# Versioning

The Hierarchy API follows the REST API version.

```text
/api/v1/hierarchy
```

The hierarchy contract also exposes its version through the Bootstrap API.

---

# Performance Considerations

The Hierarchy API is optimized through:

- recursive loading
- immutable snapshots
- caching
- revision tracking
- efficient tree traversal

Large hierarchies should avoid repeated full-tree reloads.

---

# Security Considerations

Hierarchy data never bypasses authorization.

The API does not expose:

- hidden nodes
- unauthorized metadata
- internal database identifiers
- implementation-specific information

The backend remains the single source of truth.

---

# Frontend Integration

The frontend loads the hierarchy during startup.

Typical workflow:

```text
Bootstrap

↓

GET /hierarchy

↓

Generic Tree

↓

Schema Renderer

↓

User Interaction
```

The frontend does not hardcode node types.

---

# Related APIs

```http
GET /api/v1/bootstrap

GET /api/v1/ui/schema

GET /api/v1/config

POST /api/v1/chat/stream
```

---

# Related Documentation

- [[Architecture]]
- [[Bootstrap]]
- [[Configuration]]
- [[UI-Schema]]
- [[Schema-Renderer]]
- [[Generic-Tree]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]

---

# Summary

The Hierarchy API provides the generic, schema-driven structure that organizes all resources within Kernschmied.

By representing every entity as a configurable hierarchy node, the platform enables deterministic configuration and prompt inheritance, flexible UI rendering, and consistent authorization without embedding domain-specific concepts into the backend.

This approach creates a scalable foundation that supports evolving business structures while maintaining stable API contracts and long-term architectural flexibility.

---

Back to [[Home]].