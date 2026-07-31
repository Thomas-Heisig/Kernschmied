# UI Schema API

The UI Schema API provides the schema-driven foundation of the Kernschmied frontend.

Instead of hardcoding user interfaces for individual business objects, the backend delivers declarative UI schemas that describe how data should be rendered, edited, validated, and interacted with.

The frontend interprets these schemas using a fixed set of generic components and actions, allowing new business objects to be introduced without modifying frontend source code.

The UI Schema API is a cornerstone of the platform's schema-driven architecture.

---

# Goals

The UI Schema API is designed to provide:

- Schema-driven user interfaces
- Stable frontend contracts
- Backend-controlled UI configuration
- Generic rendering
- Dynamic forms
- Versioned schemas
- Component independence
- Future extensibility

---

# Endpoint

## List UI Schemas

```http
GET /api/v1/ui/schema
```

Returns all available UI schemas.

---

## Future Endpoints

Possible future additions include:

```http
GET /api/v1/ui/schema/{schema_id}

POST /api/v1/ui/schema/validate

GET /api/v1/ui/schema/components

GET /api/v1/ui/schema/actions

GET /api/v1/ui/schema/revisions
```

---

# Architecture

```text
REST API

        │

        ▼

UI Schema Service

        │

        ▼

Schema Registry

        │

        ▼

Database / Configuration

        │

        ▼

Frontend Schema Renderer
```

The backend defines **what** should be rendered.

The frontend decides **how** known schema elements are rendered.

---

# Why a Schema-Driven UI?

Traditional applications tightly couple backend models to frontend components.

Example:

```text
Project

↓

ProjectPage

↓

ProjectEditor
```

This approach requires frontend development whenever new business objects are introduced.

Kernschmied instead follows:

```text
Node

↓

Schema

↓

Schema Renderer

↓

Generic Components
```

The frontend becomes data-driven rather than business-object-driven.

---

# Example Response

```json
[
  {
    "id": "project",
    "title": "Project",
    "component": "detail_view",
    "fields": [
      {
        "name": "name",
        "label": "Project Name",
        "component": "text"
      },
      {
        "name": "description",
        "label": "Description",
        "component": "textarea"
      }
    ]
  }
]
```

The exact schema format is versioned independently.

---

# Schema Structure

A UI schema typically contains:

- identifier
- title
- layout information
- fields
- actions
- validation rules
- metadata

Future versions may introduce additional properties.

---

# Schema Identifier

Each schema has a stable identifier.

Example:

```json
{
  "id": "project"
}
```

Hierarchy nodes reference this identifier.

The frontend resolves it through the Schema Renderer.

---

# Layout

Schemas describe the logical layout.

Examples include:

- detail view
- form
- list
- tabs
- sections
- cards

The layout remains declarative.

The frontend controls the visual implementation.

---

# Fields

Fields describe editable or read-only values.

Example:

```json
{
  "name": "email",
  "label": "Email",
  "component": "text"
}
```

Fields never directly reference React components.

---

# Components

The `component` field references a generic frontend component.

Examples:

- text
- textarea
- checkbox
- select
- date
- number
- markdown
- image
- tree
- chat

The frontend resolves these identifiers through the Component Registry.

Unknown component types are displayed using an unsupported component view.

---

# Component Registry

The frontend maintains a fixed registry.

```text
Schema

↓

Component Registry

↓

Known Component

↓

Render
```

The backend cannot introduce arbitrary executable frontend code.

This guarantees predictable rendering and security.

---

# Actions

Schemas may define available user actions.

Example:

```json
{
  "id": "save",
  "type": "submit"
}
```

Actions are resolved through the frontend Action Registry.

---

# Action Registry

Like components, actions are fixed frontend implementations.

Examples include:

- save
- cancel
- delete
- refresh
- open_chat
- create_child
- duplicate

Unknown actions are ignored or displayed as unsupported.

The backend cannot inject executable JavaScript.

---

# Validation

Schemas may include validation rules.

Examples:

- required
- minimum length
- maximum length
- regex
- numeric range

Validation occurs:

1. in the frontend for user feedback
2. in the backend for security

Backend validation is always authoritative.

---

# Forms

Schemas drive dynamic forms.

Typical workflow:

```text
Schema

↓

Form Builder

↓

Generic Components

↓

User Input

↓

REST API
```

No form is hardcoded for a specific business object.

---

# Read-Only Fields

Schemas may define read-only values.

Example:

```json
{
  "name": "created_at",
  "readonly": true
}
```

The frontend prevents editing.

The backend still validates incoming requests.

---

# Conditional Visibility

Future schema versions may support conditional rendering.

Examples:

```text
Show field when

status == "advanced"
```

The schema remains declarative.

Business rules continue to reside in the backend.

---

# Schema Versioning

Each schema contract is versioned independently.

Example:

```json
{
  "schema_version": 1
}
```

Version information is also exposed through the Bootstrap API.

---

# Unknown Schemas

The frontend must never fail because of an unknown schema.

Instead it renders an **Unsupported Schema** view.

Example:

```text
Unknown Schema

↓

Unsupported Schema Component

↓

Inform User
```

This preserves forward compatibility.

---

# Unknown Components

If a schema references an unknown component:

```text
Unknown Component

↓

Unsupported Component

↓

Continue Rendering
```

The remainder of the page continues to function normally.

---

# Unknown Actions

Unknown actions are handled similarly.

The frontend:

- logs the issue
- ignores unsupported actions
- keeps remaining actions functional

---

# Authentication

Reading UI schemas depends on the deployment profile.

Normally authenticated users may retrieve UI schemas.

Administrative schema management requires elevated permissions.

---

# Authorization

Typical permissions include:

- ui_schema.read
- ui_schema.manage

The backend determines which schemas are visible.

---

# Error Responses

Errors follow the standard platform contract.

Example:

```json
{
  "code": "resource_not_found",
  "message": "UI schema not found.",
  "details": {
    "schema": "project"
  },
  "request_id": "8d4c6a12"
}
```

---

# Performance Considerations

The UI Schema API is optimized through:

- immutable schemas
- client caching
- revision tracking
- lazy loading
- schema reuse

Schemas change infrequently and are ideal cache candidates.

---

# Security Considerations

UI schemas never contain:

- executable code
- JavaScript
- authentication secrets
- SQL
- backend implementation details

Only declarative metadata is transferred.

Every user action is still validated by the backend.

---

# Frontend Integration

Typical startup sequence:

```text
Bootstrap

↓

GET /ui/schema

↓

Schema Renderer

↓

Component Registry

↓

Action Registry

↓

Application Ready
```

Subsequent hierarchy navigation reuses cached schemas whenever possible.

---

# Relationship to the Hierarchy API

Hierarchy nodes reference UI schemas.

```text
Hierarchy Node

↓

Schema ID

↓

UI Schema API

↓

Schema Renderer
```

The hierarchy defines **what** is selected.

The UI schema defines **how** it is presented.

---

# Related APIs

```http
GET /api/v1/bootstrap

GET /api/v1/hierarchy

GET /api/v1/config

POST /api/v1/chat/stream
```

---

# Related Documentation

- [[Architecture]]
- [[Bootstrap]]
- [[Hierarchy]]
- [[Configuration]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Frontend-Overview]]
- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0012-Frontend-Architecture-and-Schema-Driven-UI]]

---

# Summary

The UI Schema API provides the declarative foundation for Kernschmied's schema-driven frontend.

By delivering versioned UI definitions instead of hardcoded views, the platform enables generic rendering, dynamic forms, flexible layouts, and backend-controlled user interfaces while maintaining a fixed frontend component and action registry for security, consistency, and long-term maintainability.

---

Back to [[Home]].
