# Component Registry

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

## Overview

The **Component Registry** is the central mechanism that maps **UI Schema component types** to concrete React components.

It enables Kernschmied's schema-driven frontend by ensuring that the Schema Renderer never imports or instantiates business-specific components directly.

Instead, every renderable component must be explicitly registered.

---

## Design Goals

The Component Registry has several objectives:

- Explicit component registration
- Stable rendering contracts
- Schema-driven rendering
- Easy extensibility
- Runtime safety
- Predictable behavior
- Testability
- Separation of concerns

---

## Architecture

```text
Backend

↓

UI Schema

↓

Schema Renderer

↓

Component Registry

↓

React Component

↓

Rendered UI

```

The Schema Renderer never knows which React component it will receive.

It only knows the requested component type.

---

## Why a Registry?

Without a registry, rendering often looks like this:

```tsx
if (type === "text") {
  return <TextField />;
}

if (type === "checkbox") {
  return <Checkbox />;
}

if (type === "table") {
  return <Table />;
}
```

Over time this becomes difficult to maintain.

Instead, Kernschmied performs a lookup.

```text
"text"

↓

Registry Lookup

↓

TextField

```

This approach is easier to extend and test.

---

## Responsibilities

The Component Registry is responsible for:

- registering components
- resolving components
- validating component types
- preventing duplicate registrations
- providing fallback components
- exposing metadata

The registry is **not** responsible for:

- rendering
- validation
- business logic
- permissions
- layout management

---

## Registration

Components are registered explicitly during application startup.

Example:

```text
Application Startup

↓

Register Components

↓

Registry Ready

↓

Application Starts

```

Unknown components cannot be rendered.

---

## Example Registration

```tsx
registerComponent("text", TextField);

registerComponent("checkbox", CheckboxField);

registerComponent("table", TableView);
```

Every registration associates a schema type with a React component.

---

## Registry Lookup

Rendering follows a simple process.

```text
"text"

↓

Component Registry

↓

TextField

↓

Render

```

If no component exists, the fallback component is used.

---

## Component Metadata

The registry may expose metadata such as:

| Property    | Description            |
| ----------- | ---------------------- |
| type        | Component identifier   |
| name        | Human-readable name    |
| category    | UI category            |
| version     | Supported version      |
| description | Optional documentation |

Example:

```json
{
  "type": "text",
  "name": "Text Field",
  "category": "Input"
}
```

---

## Supported Components

Typical component categories include:

## Input Components

- text
- textarea
- password
- email
- url
- number
- checkbox
- switch
- select
- multiselect
- radio
- slider

---

## Data Components

- table
- list
- property-grid
- tree
- markdown
- json-view

---

## Layout Components

- card
- section
- tabs
- accordion
- split-view
- container

---

## Feedback Components

- alert
- badge
- progress
- spinner
- notification

---

## Action Components

- button
- toolbar
- menu
- context-menu

---

## Version Compatibility

Every registered component supports one or more schema versions.

Example:

```text
Schema Version

↓

Registry

↓

Compatible Component

```

If compatibility cannot be guaranteed, rendering is rejected gracefully.

---

## Unknown Components

Unknown component types never crash the application.

Instead, a placeholder is displayed.

Example:

```text
┌─────────────────────────────┐
│ Unsupported Component       │
│                             │
│ type: custom-widget         │
└─────────────────────────────┘

```

This simplifies debugging and prevents complete rendering failures.

---

## Duplicate Registration

Each component type must be unique.

Invalid:

```text
"text"

↓

TextField

↓

AnotherTextField

```

The registry rejects duplicate registrations during startup.

---

## Lazy Loading

Large or rarely used components may be loaded on demand.

```text
Schema

↓

Registry

↓

Dynamic Import

↓

Render

```

Lazy loading reduces the initial bundle size.

---

## Component Isolation

Every component should be self-contained.

A component should not assume:

- application state
- backend behavior
- business rules
- routing details

Components receive only the properties defined by the schema.

---

## Interaction with the Schema Renderer

The renderer delegates all component resolution to the registry.

```text
Schema Renderer

↓

Component Registry

↓

Resolved Component

↓

React Element

```

This keeps the renderer small and focused.

---

## Interaction with the Action Registry

Components may expose actions.

Example:

```text
Button

↓

Action Registry

↓

Action Handler

↓

Backend

```

Component rendering and action execution remain separate concerns.

---

## Accessibility

Every registered component should provide:

- semantic HTML
- keyboard navigation
- ARIA support
- focus management
- screen reader compatibility

Accessibility is the responsibility of the component implementation.

---

## Performance

The registry should:

- cache lookups
- avoid repeated resolution
- support lazy imports
- minimize bundle size
- avoid unnecessary object creation

Registry lookup should be effectively constant time.

---

## Security

The Component Registry follows a strict allow-list model.

Only registered components can be rendered.

The registry must never:

- execute arbitrary code
- dynamically evaluate JavaScript
- import unknown modules
- load components from untrusted sources

All component types must be explicitly registered by the application.

---

## Testing

Typical registry tests include:

- successful registration
- duplicate registration
- lookup
- unknown component fallback
- lazy loading
- metadata retrieval
- version compatibility

---

## Future Extensions

Possible future capabilities include:

- plugin-provided components
- feature flags
- theme-specific implementations
- localization-aware components
- mobile-specific renderers
- renderer capabilities
- component deprecation support

These extensions should preserve the registry's public contract.

---

## Best Practices

Recommended:

- One responsibility per component
- Stateless components whenever possible
- Generic naming
- Explicit registration
- Stable props
- Strong TypeScript typing
- Accessibility by default

Avoid:

- Business-specific components
- Hidden dependencies
- Runtime registration side effects
- Circular dependencies
- Global mutable state

---

## Related Documentation

## Architecture (2)

- [[Architecture]]
- [[Schema-Renderer]]
- [[UI-Schema]]

---

## Frontend

- [[Action-Registry]]
- [[Forms]]
- [[Generic-Tree]]
- [[State-Management]]
- [[Routing]]

---

## Backend

- [[Contracts]]
- [[Configuration]]

---

## Concepts

- [[Dynamic-UI]]
- [[Schema-Versioning]]
- [[Plugin-System]]

---

## Summary

The Component Registry is the central lookup mechanism that connects backend-defined UI Schemas with generic React components.

By requiring explicit registration, providing safe fallback behavior, and separating component resolution from rendering, it forms one of the key architectural pillars of Kernschmied's schema-driven frontend.

Together with the Schema Renderer and Action Registry, it enables a flexible, maintainable, and secure user interface that can evolve without introducing business-specific frontend code.

---

Back to [[Home]].
