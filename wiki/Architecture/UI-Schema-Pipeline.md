# UI Schema Pipeline

The **UI Schema Pipeline** defines how user interface definitions are created, validated, transported, cached, interpreted, and rendered within the Kernschmied platform.

Unlike traditional web applications where user interfaces are tightly coupled to frontend code, Kernschmied uses a **schema-driven architecture**. The backend describes *what* should be rendered, while the frontend decides *how* to render it using a fixed set of trusted components.

This separation enables dynamic interfaces without allowing arbitrary code execution or uncontrolled frontend behavior.

The UI Schema Pipeline is one of the central architectural concepts of Kernschmied and connects the backend configuration system with the React frontend.

---

# Goals

The UI Schema Pipeline is designed to provide:

- Schema-driven user interfaces
- Stable frontend contracts
- Dynamic backend-controlled layouts
- Strong validation
- Component safety
- Versioned schemas
- Runtime extensibility
- Provider independence

---

# Design Principles

The pipeline follows several architectural principles.

## Backend Defines Intent

The backend describes the desired interface.

Example:

```text
Display

↓

Tree

↓

Toolbar

↓

Chat View
```

The backend never sends executable UI code.

---

## Frontend Owns Rendering

The frontend maps schema definitions to trusted React components.

```text
Schema

↓

Component Registry

↓

React Component

↓

Rendered UI
```

Rendering always remains under frontend control.

---

## Stable Contracts

The communication between backend and frontend uses versioned UI schemas.

This guarantees:

- predictable rendering
- backward compatibility
- independent frontend evolution

---

# High-Level Pipeline

The complete UI Schema Pipeline is shown below.

```text
Configuration

↓

Schema Builder

↓

Validation

↓

UI Schema

↓

API

↓

Frontend

↓

Schema Renderer

↓

Component Registry

↓

React Components
```

Each stage has a clearly defined responsibility.

---

# Schema Sources

UI schemas may be generated from multiple sources.

Typical sources include:

- system configuration
- hierarchy configuration
- feature definitions
- deployment profile
- application capabilities
- user permissions

These sources are merged before schema generation.

---

# Schema Generation

The backend generates a complete UI schema.

Typical responsibilities include:

- layout definition
- navigation
- available actions
- supported components
- feature visibility
- metadata

The frontend never assembles schemas on its own.

---

# Schema Validation

Every generated schema is validated before being returned.

Validation includes:

- schema version
- required fields
- component types
- action types
- layout consistency
- identifier uniqueness

Invalid schemas are rejected before reaching the client.

---

# UI Schema Contract

The schema represents a stable API contract.

Example:

```json
{
  "version": 1,
  "components": []
}
```

The schema contract evolves independently of frontend implementation details.

---

# API Transport

The validated schema is delivered through the UI Schema API.

```text
Frontend

↓

GET /ui/schema

↓

Backend

↓

Validated Schema
```

The schema is transported as JSON.

---

# Bootstrap Relationship

Bootstrap provides metadata that allows clients to determine whether the UI schema should be refreshed.

Typical information includes:

- UI schema version
- configuration revision
- capabilities

Clients reload schemas only when necessary.

---

# Client Loading

During startup the frontend loads:

```text
Bootstrap

↓

Capabilities

↓

UI Schema

↓

Hierarchy

↓

Application Ready
```

This creates a deterministic startup sequence.

---

# Schema Parsing

After download the frontend parses the schema into TypeScript models.

```text
JSON

↓

Parser

↓

Type Definitions

↓

Renderer
```

Invalid schemas are rejected immediately.

---

# Schema Renderer

The Schema Renderer is responsible for interpreting the schema.

```text
UI Schema

↓

Schema Renderer

↓

Component Resolution

↓

React Tree
```

The renderer never performs business logic.

---

# Component Registry

The renderer resolves component types through the Component Registry.

Example:

```text
chat

↓

Component Registry

↓

GenericChatView
```

Unknown component types are handled safely.

---

# Action Registry

Interactive actions are resolved through the Action Registry.

```text
refresh

↓

Action Registry

↓

Handler
```

The backend defines available actions, while the frontend provides trusted implementations.

---

# Recursive Rendering

Many schemas contain nested layouts.

Example:

```text
Layout

├── Toolbar

├── Sidebar

└── Content

    ├── Tree

    └── Chat
```

The renderer recursively renders child components.

---

# Generic Components

The frontend uses generic components whenever possible.

Examples include:

- Generic Tree
- Generic Forms
- Generic Chat
- Generic Toolbar
- Generic Layout

Business-specific React components are intentionally avoided.

---

# Unknown Components

Unknown component types never execute arbitrary code.

Instead:

```text
Unknown Component

↓

UnsupportedSchema

↓

Visible Placeholder
```

The application remains stable even when the backend evolves.

---

# Unknown Actions

Unknown actions are rejected safely.

```text
Unknown Action

↓

Ignore

↓

Warning

↓

Continue Rendering
```

This prevents undefined runtime behavior.

---

# Permission Filtering

The backend determines which components and actions are available.

The frontend only renders what has already been authorized.

Permission enforcement always remains server-side.

---

# Dynamic Forms

Forms are generated from schemas.

Example:

```text
Field Definitions

↓

Form Renderer

↓

Input Components
```

The frontend never hardcodes configuration forms.

---

# Dynamic Navigation

Navigation may also be schema-driven.

Typical elements include:

- pages
- tabs
- menus
- toolbars
- dialogs

Navigation remains declarative.

---

# Schema Caching

Downloaded schemas may be cached.

Typical cache key:

```text
UI Schema Version

+

Configuration Revision
```

Caches are invalidated whenever either value changes.

---

# Runtime Updates

If runtime-editable configuration changes affect the UI:

```text
Configuration Updated

↓

Revision++

↓

Schema Reload

↓

UI Refresh
```

No frontend rebuild is required.

---

# Versioning

The UI schema has its own version.

Example:

```text
Application

Version 0.5

↓

UI Schema

Version 2
```

Schema evolution is independent of application releases.

---

# Validation on the Frontend

The frontend performs defensive validation.

Typical checks include:

- supported schema version
- required properties
- component identifiers
- layout integrity

Malformed schemas are rejected before rendering.

---

# Error Handling

Rendering failures are isolated.

```text
Invalid Schema

↓

Error Component

↓

Remaining UI Continues
```

A single invalid section should not prevent unrelated parts of the application from functioning.

---

# Performance

The pipeline is optimized for:

- incremental rendering
- lazy component loading
- registry lookup
- recursive rendering
- minimal allocations

Schemas are interpreted rather than compiled.

---

# Security

Several architectural boundaries protect the pipeline.

The backend never sends executable JavaScript.

The frontend never evaluates arbitrary code.

Only trusted components registered within the Component Registry may be rendered.

Likewise, only registered actions may be executed.

---

# Future Extensions

The architecture supports future capabilities including:

- theme schemas
- responsive layouts
- localization
- reusable schema fragments
- workflow editors
- dashboard builders
- plugin-defined schemas
- visual schema designers

These features can be introduced without changing the fundamental pipeline.

---

# Relationship to Other Architecture

The UI Schema Pipeline integrates multiple architectural subsystems.

```text
Configuration

↓

Hierarchy

↓

Schema Builder

↓

UI Schema

↓

API

↓

Schema Renderer

↓

Component Registry

↓

React UI
```

It therefore connects backend configuration with frontend rendering through stable contracts.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Registry-Architecture]]
- [[Manifest-System]]
- [[Request-Lifecycle]]

---

## Frontend

- [[UI-Schema]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Forms]]
- [[Generic-Tree]]
- [[API-Client]]

---

## APIs

- [[Bootstrap]]
- [[UI-Schema]]
- [[Configuration]]

---

## ADRs

- [[ADR-0002-Bootstrap]]
- [[ADR-0004-Schema-Driven-Frontend]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]

---

# Summary

The UI Schema Pipeline provides the complete end-to-end process for transforming backend-defined interface descriptions into secure, dynamic, and fully rendered React user interfaces.

By combining versioned UI schemas, deterministic schema generation, strict validation, stable API contracts, recursive schema rendering, trusted component and action registries, and backend-controlled authorization, Kernschmied achieves a flexible schema-driven frontend architecture that remains secure, extensible, maintainable, and independent of individual business domains.

---

Back to [[Home]].
