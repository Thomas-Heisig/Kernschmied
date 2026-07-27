# Dynamic UI

The **Dynamic UI** concept is one of the core architectural principles of Kernschmied. Instead of implementing business-specific screens directly in the frontend, the user interface is generated from schemas delivered by the backend.

This allows new business objects, workflows, hierarchy nodes, and configuration pages to be introduced without changing the frontend application. The frontend provides a fixed set of trusted rendering components, while the backend decides **what** should be displayed.

The Dynamic UI architecture makes Kernschmied highly extensible while preserving strong security boundaries, stable contracts, and predictable behavior.

---

# Goals

The Dynamic UI architecture is designed to provide:

- Schema-driven user interfaces
- Separation of data and presentation
- Backend-controlled rendering
- Stable frontend components
- Runtime extensibility
- Versioned UI contracts
- Secure rendering
- Long-term maintainability

---

# Core Principle

The frontend never decides which business screen should exist.

Instead, the backend provides a UI schema.

```text
Backend

↓

UI Schema

↓

Frontend

↓

Renderer

↓

User Interface
```

The frontend only interprets the schema.

---

# Why Dynamic UI?

Traditional applications often hardcode every page.

```text
CustomerPage.tsx

ProjectPage.tsx

DepartmentPage.tsx

InvoicePage.tsx
```

Adding a new entity usually requires frontend development.

In Kernschmied the frontend instead contains only generic rendering components.

```text
Schema

↓

Renderer

↓

Generic Components
```

Business entities become data rather than code.

---

# Architecture Overview

```text
Database

↓

Configuration

↓

UI Schema Generator

↓

REST API

↓

Frontend

↓

Schema Renderer

↓

Component Registry

↓

Rendered Interface
```

The backend owns the UI definition.

---

# Schema-Driven Rendering

Every visible element is described by a schema.

Typical schema information includes:

- layout
- components
- properties
- actions
- validation
- visibility
- child elements

The renderer interprets the schema at runtime.

---

# Frontend Responsibilities

The frontend is responsible for:

- downloading schemas
- validating schema versions
- resolving components
- rendering layouts
- collecting user input
- invoking backend actions

Business rules remain in the backend.

---

# Backend Responsibilities

The backend is responsible for:

- generating schemas
- enforcing permissions
- resolving configuration
- determining visibility
- validating requests
- exposing stable contracts

The backend decides what users are allowed to see.

---

# Component Registry

Rendering is performed through a fixed Component Registry.

```text
Schema

↓

Component Type

↓

Component Registry

↓

React Component
```

Only registered components can be rendered.

---

# Trusted Components

Every UI component is trusted application code.

Examples include:

- Form
- Table
- Tree
- Tabs
- Panel
- Text
- Button
- Card
- Chat
- Property Grid

Components are compiled into the frontend application.

---

# Unknown Components

Unknown component types are never executed.

Instead:

```text
Unknown Type

↓

Unsupported Component

↓

Safe Placeholder
```

The application continues running safely.

---

# Action Registry

Interactive behavior follows the same pattern.

```text
Schema

↓

Action Identifier

↓

Action Registry

↓

Execution
```

Unknown actions are rejected safely.

---

# Layout System

The schema describes layouts independently of implementation.

Typical layout containers include:

- columns
- rows
- cards
- tabs
- sections
- split views
- dialogs

The renderer constructs the interface dynamically.

---

# Forms

Forms are generated entirely from schema definitions.

Typical field metadata includes:

- label
- identifier
- type
- validation
- default value
- help text
- placeholder

The frontend never hardcodes individual business forms.

---

# Tables

Tables are described declaratively.

Example metadata:

- columns
- sorting
- filtering
- actions
- formatting
- pagination

Rendering remains generic.

---

# Tree Rendering

Hierarchy is rendered using a generic recursive tree.

```text
Hierarchy

↓

Tree Schema

↓

Generic Tree

↓

Visible Navigation
```

The tree renderer has no knowledge of projects, departments, or customers.

---

# Dynamic Navigation

Navigation is generated from hierarchy and schema.

```text
Hierarchy

↓

Schema

↓

Navigation Tree
```

Changing the hierarchy automatically changes navigation.

---

# Dynamic Views

A hierarchy node references a schema.

```text
Hierarchy Node

↓

Schema Identifier

↓

UI Schema

↓

Rendered View
```

The frontend renders the appropriate interface without requiring specialized pages.

---

# Schema Versioning

Every schema has an explicit version.

```text
Schema v1

↓

Schema Renderer

↓

Compatible Components
```

Versioning allows UI evolution while preserving compatibility.

---

# Validation

Schemas are validated before rendering.

Validation includes:

- supported schema version
- component existence
- property validation
- action validation
- structural consistency

Invalid schemas are rejected.

---

# Runtime Configuration

Configuration influences generated schemas.

Examples include:

- enabled features
- visible actions
- deployment profile
- permissions
- hierarchy context

The frontend receives only the resulting schema.

---

# Authorization

Visibility is determined by the backend.

Example:

```text
Authorization

↓

Schema Generation

↓

Visible Components
```

Hidden components are never sent to unauthorized users.

---

# Error Handling

Rendering failures are isolated.

```text
Schema

↓

Unknown Component

↓

Placeholder

↓

Application Continues
```

The entire application does not fail because of one unsupported component.

---

# Performance

Dynamic UI is optimized through:

- schema caching
- immutable schemas
- revision-based invalidation
- lazy rendering
- efficient component lookup

Rendering remains comparable to traditional React applications.

---

# Security

The Dynamic UI architecture enforces several important security guarantees.

The frontend:

- never executes arbitrary JavaScript
- never evaluates schemas as code
- never loads unknown React components
- never bypasses backend authorization

Schemas describe interfaces but cannot execute logic.

---

# Benefits

The architecture provides significant advantages.

## Extensibility

New business objects can often be introduced without frontend changes.

---

## Consistency

All screens follow the same rendering pipeline.

---

## Maintainability

Frontend developers maintain rendering components rather than business pages.

---

## Security

Only trusted components are executed.

---

## Flexibility

Business logic evolves through schemas and configuration.

---

# Example Rendering Flow

```text
Hierarchy Node Selected

↓

Backend Resolves Configuration

↓

Backend Generates UI Schema

↓

Frontend Downloads Schema

↓

Schema Renderer

↓

Component Registry

↓

Rendered View
```

Every step is deterministic.

---

# Future Extensions

The Dynamic UI architecture supports future enhancements including:

- plugin-provided schemas
- customizable layouts
- responsive schema variants
- localization metadata
- accessibility metadata
- workflow-driven interfaces
- tenant-specific UI definitions

These features can be introduced while preserving the existing rendering model.

---

# Relationship to Other Concepts

Dynamic UI is closely related to:

- [[Schema-Driven Architecture]]
- [[Configuration]]
- [[Hierarchy]]
- [[Runtime Configuration]]
- [[Configuration Revisions]]

---

# Related Documentation

## Concepts

- [[Schema-Driven Architecture]]
- [[Hierarchy]]
- [[Configuration]]
- [[Versioning]]
- [[Caching]]

---

## Architecture

- [[UI-Schema-Pipeline]]
- [[Hierarchy-Architecture]]
- [[Configuration-Architecture]]

---

## Backend

- [[Hierarchy]]
- [[Configuration]]
- [[Model-Registry]]
- [[Tool-Registry]]

---

## Frontend

- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Forms]]
- [[Generic-Tree]]
- [[Routing]]
- [[UI-Schema]]

---

# Summary

The Dynamic UI architecture enables Kernschmied to generate complete user interfaces from backend-provided schemas instead of relying on hardcoded business pages. The backend determines what should be displayed, while the frontend renders trusted components through fixed component and action registries.

By combining schema-driven rendering, backend-controlled authorization, stable versioned contracts, runtime configuration, generic layouts, and secure component resolution, the Dynamic UI concept provides a highly extensible, maintainable, and secure foundation for building enterprise applications that can evolve without continuous frontend redevelopment.

---

Back to [[Home]].
