# Schema Renderer

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

# Overview

The **Schema Renderer** is one of the core building blocks of the Kernschmied frontend.

Instead of rendering business-specific React components, the application renders **versioned UI Schemas** received from the backend.

The renderer acts as the bridge between backend-defined user interfaces and the generic React component library.

It is responsible for interpreting schemas, validating them, resolving components, and rendering the final user interface.

---

# Purpose

The Schema Renderer enables the frontend to evolve without requiring business-specific code changes.

Its primary responsibilities are:

- Render UI Schemas
- Validate schema structure
- Resolve components
- Resolve layouts
- Resolve actions
- Handle unsupported schema elements
- Keep rendering deterministic
- Remain independent of business domains

---

# Design Philosophy

Traditional applications often follow this pattern:

```text
Business Object

↓

Business React Component

↓

Business Logic

↓

UI
```

This approach quickly leads to hundreds of custom components.

Kernschmied intentionally replaces this with:

```text
Backend

↓

UI Schema

↓

Schema Renderer

↓

Component Registry

↓

Generic Components

↓

Browser
```

The frontend never knows what a "Project", "Invoice" or "Customer" is.

It only understands schemas.

---

# Renderer Responsibilities

The renderer is responsible for:

- validating schemas
- selecting layouts
- rendering sections
- rendering components
- resolving actions
- rendering nested structures
- displaying placeholders
- handling errors gracefully

The renderer is **not** responsible for:

- business logic
- permissions
- persistence
- workflow execution
- validation authority

---

# Rendering Pipeline

```text
REST API

↓

JSON Schema

↓

Schema Validation

↓

Schema Renderer

↓

Layout Resolution

↓

Component Resolution

↓

Property Mapping

↓

React Components

↓

Rendered UI
```

Every stage validates its input before proceeding.

---

# Rendering Flow

```text
Load Schema

↓

Validate Version

↓

Validate Structure

↓

Resolve Layout

↓

Render Sections

↓

Resolve Components

↓

Attach Actions

↓

Finished Page
```

---

# Schema Validation

Before rendering, every schema is validated.

Validation includes:

- schema version
- required properties
- supported layouts
- component types
- action types
- recursive children

Invalid schemas are rejected before rendering begins.

---

# Version Compatibility

Every schema contains a version.

Example:

```json
{
  "schema_version": 1
}
```

The renderer compares the version with supported versions.

Possible outcomes:

- supported
- deprecated
- unsupported

Unsupported schemas produce a clear diagnostic page.

---

# Layout Resolution

Layouts determine the overall page structure.

Example:

```json
{
    "layout": "two-column"
}
```

The renderer delegates layout creation to the Layout Registry.

```text
Schema

↓

Layout Registry

↓

React Layout Component
```

---

# Section Rendering

Pages are divided into sections.

Example:

```text
General

Permissions

Advanced

Diagnostics
```

Sections improve organization and readability.

Each section is rendered recursively.

---

# Component Resolution

Components are never instantiated directly.

Instead:

```text
Component Type

↓

Component Registry

↓

React Component

↓

Rendering
```

Example:

```text
"text"

↓

TextField
```

---

# Recursive Rendering

Schemas may contain nested structures.

Example:

```text
Tabs

└── Tab

    └── Card

        └── Form

            └── Text Field
```

The renderer supports arbitrary nesting.

---

# Property Mapping

The renderer maps schema properties to React props.

Example:

Schema:

```json
{
    "label": "Name",
    "required": true
}
```

React:

```tsx
<TextField
    label="Name"
    required
/>
```

The mapping layer keeps schemas independent from React implementation details.

---

# Dynamic Rendering

The renderer supports runtime-generated pages.

Examples include:

- administration
- configuration
- plugin settings
- model management
- hierarchy editors

No frontend rebuild is required.

---

# Action Resolution

Buttons and commands are described in the schema.

Example:

```json
{
    "action": "save"
}
```

The renderer resolves the action through the Action Registry.

```text
Schema

↓

Action Registry

↓

Handler

↓

Backend
```

---

# Unknown Components

Unknown component types never crash the application.

Instead, the renderer displays a diagnostic placeholder.

Example:

```text
┌───────────────────────────────┐
│ Unsupported Component         │
│                               │
│ type: ai-super-widget         │
└───────────────────────────────┘
```

This greatly simplifies debugging.

---

# Unknown Layouts

If a layout cannot be resolved:

```text
Unknown Layout

↓

Diagnostic Component

↓

Rendering Continues
```

The remainder of the page remains usable whenever possible.

---

# Error Isolation

Rendering failures should remain local.

Instead of failing the entire page:

```text
Component

↓

Rendering Error

↓

Fallback Component
```

Other components continue rendering.

---

# Performance

The renderer should:

- avoid unnecessary re-renders
- memoize resolved components
- lazy-load large component groups
- minimize allocations
- batch updates where appropriate

Rendering performance should remain predictable even for large schemas.

---

# Component Registry Integration

The renderer communicates with the Component Registry.

```text
Renderer

↓

Component Registry

↓

Registered Component

↓

React Element
```

This makes new component types extensible without modifying the renderer.

---

# Action Registry Integration

Actions follow the same architecture.

```text
Renderer

↓

Action Registry

↓

Action Handler

↓

Backend Request
```

---

# Security

The Schema Renderer must never:

- execute JavaScript
- evaluate expressions
- import arbitrary modules
- instantiate unknown components
- bypass permissions

Schemas describe data—not executable code.

---

# Accessibility

All rendered components should support:

- keyboard navigation
- screen readers
- ARIA attributes
- focus management
- semantic HTML

Accessibility is implemented by the generic components, not by the schemas.

---

# Testing

Typical renderer tests include:

- schema validation
- layout resolution
- recursive rendering
- unsupported components
- unsupported layouts
- property mapping
- action resolution
- error handling

Snapshot tests may be used for stable rendering contracts.

---

# Future Extensions

The renderer is designed to support future capabilities such as:

- virtualized rendering
- lazy section loading
- progressive rendering
- conditional rendering
- localization
- theme-aware rendering
- responsive layout switching
- plugin-provided component packs

These extensions should not require changes to the renderer's public contract.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[UI-Schema]]
- [[UI-Schema-Pipeline]]

---

## Frontend

- [[Component-Registry]]
- [[Action-Registry]]
- [[Forms]]
- [[State-Management]]

---

## Backend

- [[Contracts]]
- [[Configuration]]
- [[Hierarchy]]

---

## Concepts

- [[Dynamic-UI]]
- [[Schema-Versioning]]
- [[Runtime-Configuration]]

---

# Summary

The Schema Renderer is the central rendering engine of the Kernschmied frontend.

By interpreting versioned UI Schemas instead of relying on business-specific React components, it enables a highly flexible, maintainable, and secure architecture.

Together with the Component Registry and Action Registry, it forms the foundation of the platform's schema-driven user interface while ensuring that rendering remains deterministic, extensible, and independent of business domains.

---

Back to [[Home]].