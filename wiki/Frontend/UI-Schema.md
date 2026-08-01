# UI Schema

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend & Backend

---

## Overview

One of Kernschmied's core architectural principles is that the user interface is **described by data rather than implemented through business-specific React components**.

Instead of hardcoding application screens, the backend provides a **versioned UI Schema** that tells the frontend:

- what should be displayed
- how it should be displayed
- which actions are available
- which permissions are required
- how data should be validated

The frontend is responsible only for **rendering** the schema using generic components.

---

## Design Goals

The UI Schema exists to achieve several goals.

- Eliminate business-specific frontend code
- Support runtime configuration
- Allow new functionality without rebuilding the UI
- Enable generic administration pages
- Keep backend authoritative
- Support versioned contracts
- Provide consistent validation
- Improve long-term maintainability

---

## Philosophy

Traditional applications typically contain code such as:

```tsx
<CustomerForm />
<ProjectSettings />
<OfferEditor />
<EmployeeEditor />
```

Each new business object introduces another custom component.

Kernschmied intentionally avoids this pattern.

Instead, generic renderers are used.

```text
Backend

↓

UI Schema

↓

Schema Renderer

↓

Generic Components

↓

Rendered Application

```

This allows entirely new pages to be introduced through configuration and schemas rather than new frontend implementations.

---

## Rendering Pipeline

```text
REST API

↓

JSON UI Schema

↓

Schema Validation

↓

Schema Renderer

↓

Component Registry

↓

React Components

↓

Browser

```

Each step validates its input before continuing.

---

## Backend Responsibility

The backend determines:

- available pages
- layouts
- forms
- fields
- actions
- permissions
- validation rules
- default values
- visibility
- help text

The backend never sends executable code.

---

## Frontend Responsibility

The frontend is responsible for:

- schema validation
- rendering
- user interaction
- client-side usability
- accessibility
- local UI state

The frontend never invents business logic.

---

## Schema Structure

A UI Schema typically consists of:

```text
Page

├── Metadata
├── Layout
├── Sections
├── Components
├── Actions
└── Validation

```

---

## Example

```json
{
  "schema_version": 1,
  "title": "Project Settings",
  "layout": "two-column",
  "sections": [
    {
      "title": "General",
      "components": [
        {
          "type": "text",
          "name": "project_name",
          "label": "Project Name"
        }
      ]
    }
  ]
}
```

---

## Schema Versioning

Every schema contains a version.

Example:

```json
{
  "schema_version": 1
}
```

The frontend validates compatibility before rendering.

Unknown versions are rejected gracefully.

---

## Metadata

Typical metadata includes:

```text
title
description
icon
permissions
breadcrumbs
help
documentation

```

Example:

```json
{
  "title": "Models",
  "icon": "cpu",
  "description": "Manage available AI models."
}
```

---

## Layouts

Layouts define how content is arranged.

Examples:

- single-column
- two-column
- grid
- tabs
- accordion
- split-view
- wizard

The renderer selects the appropriate generic layout component.

---

## Sections

Pages may contain multiple sections.

```text
General

Models

Permissions

Advanced

Diagnostics

```

Sections improve readability and organization.

---

## Components

Every UI element is represented as a component definition.

Example:

```json
{
  "type": "text",
  "name": "username"
}
```

Component types are resolved through the Component Registry.

---

## Supported Component Types

Typical components include:

- text
- textarea
- password
- number
- checkbox
- switch
- select
- multiselect
- radio
- date
- datetime
- file
- image
- markdown
- table
- tree
- tabs
- card
- property-grid
- list
- button
- alert

Future components can be added without changing existing schemas.

---

## Component Registry

The frontend never renders components directly.

Instead it resolves them through the registry.

```text
"text"

↓

Component Registry

↓

TextField

```

Unknown components produce a visible placeholder rather than crashing the application.

---

## Actions

Actions describe user operations.

Examples:

```json
{
  "id": "save",
  "type": "submit",
  "label": "Save"
}
```

The frontend forwards actions to the backend.

Business logic is never executed locally.

---

## Action Registry

Action types are also resolved through a registry.

Examples:

- submit
- delete
- refresh
- navigate
- dialog
- export
- import

Unknown actions are rejected.

---

## Validation

Validation rules are included in the schema.

Example:

```json
{
  "required": true,
  "minLength": 3,
  "maxLength": 64
}
```

The frontend may perform client-side validation for usability.

The backend always performs authoritative validation.

---

## Conditional Visibility

Schemas can describe visibility rules.

Example:

```text
Show field B

only if

Field A == true

```

This avoids frontend-specific business logic.

---

## Read-Only Fields

Components may be marked as read-only.

Example:

```json
{
  "readonly": true
}
```

Read-only does not imply immutable.

The backend remains authoritative.

---

## Permissions

Visibility and editability may depend on permissions.

Example:

```json
{
  "permission": "models.edit"
}
```

The frontend may hide controls.

The backend always verifies permissions.

---

## Dynamic Data Sources

Selection controls may receive data from:

- static values
- REST endpoints
- hierarchy nodes
- registries
- configuration

Example:

```json
{
  "options_source": "/api/models"
}
```

---

## Error Handling

Invalid schemas never crash the application.

Possible responses:

- unsupported component
- unknown layout
- invalid schema version
- validation failure

The renderer displays diagnostic information when appropriate.

---

## Unknown Components

Unknown component types are rendered as unsupported placeholders.

Example:

```text
┌────────────────────────────┐
│ Unsupported Component      │
│ type: custom-widget        │
└────────────────────────────┘

```

This ensures the application remains usable.

---

## Security

The schema:

- cannot execute JavaScript
- cannot inject React components
- cannot load arbitrary modules
- cannot bypass authorization

Schemas describe data only.

---

## Benefits

The schema-driven architecture provides:

- reusable UI
- consistent rendering
- runtime extensibility
- stable contracts
- reduced maintenance
- easier testing
- improved security

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[UI-Schema-Pipeline]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]

---

## Backend

- [[Contracts]]
- [[Configuration]]
- [[Model-Registry]]
- [[Tool-Registry]]

---

## Concepts

- [[Dynamic-UI]]
- [[Schema-Versioning]]
- [[Runtime-Configuration]]

---

## Summary

The UI Schema is the contract between the backend and the frontend.

The backend defines **what** should be rendered.

The frontend defines **how** it is rendered.

This separation enables Kernschmied to evolve without rewriting the user interface for every new business feature while maintaining secure, stable, and versioned contracts.

---

Back to [[Home]].
