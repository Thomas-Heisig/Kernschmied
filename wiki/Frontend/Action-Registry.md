# Action Registry

> **Version:** 1.0
> **Status:** Living Document
> **Applies to:** Frontend

---

## Overview

The **Action Registry** is the central mechanism responsible for resolving **UI actions** defined by backend-provided UI Schemas.

Like the Component Registry, it follows a strict registration model.

The Schema Renderer never executes actions directly.

Instead, it delegates action execution to the Action Registry, which resolves the action type to a registered frontend handler.

This keeps rendering independent from interaction logic while maintaining stable contracts between frontend and backend.

---

## Purpose

The Action Registry provides:

- Explicit action registration
- Stable action contracts
- Separation of rendering and behavior
- Runtime safety
- Extensibility
- Consistent execution
- Predictable interaction handling

---

## Architecture

```text
Backend

↓

UI Schema

↓

Schema Renderer

↓

Action Registry

↓

Action Handler

↓

API Client / Navigation / UI

```

---

## Design Philosophy

Traditional applications often embed event handlers directly into components.

```tsx
<Button onClick={saveProject} />

<Button onClick={deleteUser} />

<Button onClick={exportInvoice} />
```

Over time, every page develops its own event handling logic.

Kernschmied intentionally avoids this.

Instead:

```text
Button

↓

Action Type

↓

Action Registry

↓

Registered Handler

↓

Execution

```

The renderer never knows what an action actually does.

---

## Responsibilities

The Action Registry is responsible for:

- registering actions
- resolving action types
- validating action definitions
- preventing duplicate registrations
- providing fallback handlers
- exposing action metadata

The registry is **not** responsible for:

- rendering buttons
- authorization
- backend validation
- business workflows
- persistence

---

## Action Lifecycle

```text
User Click

↓

Component

↓

Schema Renderer

↓

Action Registry

↓

Action Handler

↓

API Client

↓

Backend

↓

Response

↓

UI Update

```

---

## Registration

Every supported action must be explicitly registered during application startup.

Example:

```text
Application Startup

↓

Register Actions

↓

Registry Ready

```

Only registered actions may be executed.

---

## Example Registration

```tsx
registerAction("submit", submitAction);

registerAction("refresh", refreshAction);

registerAction("navigate", navigateAction);

registerAction("dialog", dialogAction);
```

---

## Registry Lookup

```text
"submit"

↓

Action Registry

↓

Submit Handler

↓

Execute

```

Lookup should be deterministic and efficient.

---

## Action Metadata

The registry may expose metadata.

Example:

| Property    | Description               |
| ----------- | ------------------------- |
| type        | Action identifier         |
| category    | Navigation, CRUD, Dialog  |
| description | Documentation             |
| version     | Supported schema versions |

Example:

```json
{
  "type": "submit",
  "category": "form",
  "description": "Submits a form."
}
```

---

## Common Action Types

Typical actions include:

## Form

- submit
- reset
- validate

---

## Navigation

- navigate
- open
- back
- close

---

## Data

- refresh
- reload
- import
- export

---

## CRUD

- create
- update
- duplicate
- delete

---

## Dialog

- dialog
- confirm
- cancel

---

## Clipboard

- copy
- paste

---

## System

- download
- upload
- print

---

## Action Definition

Example:

```json
{
  "type": "submit",
  "label": "Save",
  "endpoint": "/api/projects"
}
```

The schema defines **what** should happen.

The handler defines **how** the frontend performs the action.

---

## Parameters

Actions may receive parameters.

Example:

```json
{
  "type": "navigate",
  "target": "/projects"
}
```

Handlers receive the complete action object.

---

## Handler Responsibilities

Action handlers may:

- call the API Client
- navigate
- open dialogs
- trigger downloads
- update local UI state

Handlers should **not**:

- implement business logic
- authorize requests
- manipulate unrelated application state

---

## Backend Integration

Many actions ultimately invoke backend APIs.

Example:

```text
Action

↓

Handler

↓

API Client

↓

Backend

↓

Result

```

Business decisions remain entirely on the backend.

---

## Navigation Actions

Example:

```json
{
  "type": "navigate",
  "target": "/workspace/12"
}
```

The handler delegates navigation to the routing system.

---

## Dialog Actions

Example:

```json
{
  "type": "dialog",
  "dialog": "delete-confirmation"
}
```

The handler requests the dialog service to display the dialog.

---

## Refresh Actions

```text
Refresh

↓

API Client

↓

Backend

↓

Updated Data

↓

Re-render

```

---

## Unknown Actions

Unknown action types never crash the application.

Instead:

```text
Unknown Action

↓

Fallback Handler

↓

Diagnostic Message

```

The user receives a meaningful message while the application remains functional.

---

## Duplicate Registration

Only one handler may exist for a given action type.

Invalid:

```text
submit

↓

Handler A

↓

Handler B

```

Duplicate registrations are rejected during startup.

---

## Error Handling

Errors during action execution should be isolated.

```text
Action

↓

Error

↓

Notification

↓

Continue Application

```

Failures should not terminate the application.

---

## Security

The Action Registry follows a strict allow-list model.

Only registered actions may execute.

Actions must never:

- execute arbitrary JavaScript
- evaluate expressions
- import unknown modules
- bypass backend authorization
- execute backend logic locally

---

## Accessibility

Actions should remain fully accessible.

Examples include:

- keyboard activation
- focus indicators
- screen reader announcements
- ARIA roles
- disabled state handling

---

## Performance

The registry should:

- cache handler lookups
- minimize allocations
- avoid repeated resolution
- lazy-load optional handlers when appropriate

---

## Plugin Integration

Future plugins may register additional actions.

Example:

```text
Plugin

↓

Action Manifest

↓

Register Action

↓

Registry

```

Plugin actions must follow the same validation rules as built-in actions.

---

## Version Compatibility

Each action handler supports one or more schema versions.

Unsupported versions are rejected before execution.

---

## Testing

Typical tests include:

- registration
- duplicate detection
- lookup
- execution
- fallback handling
- parameter passing
- error handling
- version compatibility

---

## Best Practices

Recommended:

- One responsibility per handler
- Thin handlers
- Delegate API communication to the API Client
- Keep handlers stateless
- Register explicitly
- Use strong TypeScript types

Avoid:

- Business logic inside handlers
- Hidden side effects
- Direct backend calls from components
- Dynamic action evaluation
- Mutable global state

---

## Future Evolution

The Action Registry is designed to support future capabilities such as:

- plugin-defined actions
- action pipelines
- undo/redo support
- optimistic UI updates
- analytics hooks
- audit integration
- feature flags
- localization-aware actions

These additions should preserve the existing public contract.

---

## Related Documentation

## Architecture (2)

- [[Architecture]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[UI-Schema]]

---

## Frontend

- [[API-Client]]
- [[Routing]]
- [[Forms]]
- [[State-Management]]

---

## Backend

- [[Contracts]]
- [[Configuration]]
- [[Security]]

---

## Concepts

- [[Dynamic-UI]]
- [[Runtime-Configuration]]
- [[Plugin-System]]
- [[Schema-Versioning]]

---

## Summary

The Action Registry is the execution counterpart to the Component Registry.

While the Component Registry resolves **what should be rendered**, the Action Registry resolves **what should happen when users interact with the interface**.

Together with the Schema Renderer, API Client, and Component Registry, it forms one of the core architectural pillars of Kernschmied's schema-driven frontend, ensuring that interactions remain explicit, secure, extensible, and independent of business-specific implementations.

---

Back to [[Home]].
