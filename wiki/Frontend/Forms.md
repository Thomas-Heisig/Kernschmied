# Forms

> **Version:** 1.0
> **Status:** Living Document
> **Applies to:** Frontend

---

## Overview

Forms are one of the primary interaction mechanisms in Kernschmied.

Unlike traditional applications where each business entity has its own handcrafted form, Kernschmied generates forms dynamically from **versioned UI Schemas** provided by the backend.

This approach keeps the frontend generic while allowing the backend to define:

- fields
- layouts
- validation rules
- permissions
- actions
- conditional visibility
- help texts

The frontend is responsible only for rendering and user interaction.

---

## Design Goals

The Forms subsystem has several objectives:

- Generic rendering
- Runtime configurability
- Schema-driven validation
- Accessibility
- Responsive layouts
- Consistent appearance
- Reusable components
- Backend authority
- Stable contracts

---

## Architecture

```text
Backend

↓

UI Schema

↓

Schema Renderer

↓

Form Renderer

↓

Component Registry

↓

Input Components

↓

Browser

```

The backend describes **what** should be rendered.

The frontend decides **how** to render it.

---

## Responsibilities

## Backend

The backend defines:

- fields
- field types
- labels
- validation rules
- permissions
- actions
- default values
- help texts
- grouping
- layout

---

## Frontend

The frontend is responsible for:

- rendering fields
- collecting user input
- client-side usability validation
- displaying validation errors
- keyboard navigation
- accessibility
- submitting data

---

## Form Lifecycle

```text
Load Schema

↓

Render Form

↓

User Input

↓

Local Validation

↓

Submit

↓

Backend Validation

↓

Success / Error

```

The backend always performs the final validation.

---

## Form Structure

A typical form consists of:

```text
Form

├── Metadata
├── Sections
├── Fields
├── Actions
└── Validation

```

---

## Example Schema

```json
{
  "title": "Create Project",
  "layout": "single-column",
  "fields": [
    {
      "type": "text",
      "name": "name",
      "label": "Project Name",
      "required": true
    }
  ],
  "actions": [
    {
      "type": "submit",
      "label": "Create"
    }
  ]
}
```

---

## Field Types

Common field types include:

| Type        | Description      |
| ----------- | ---------------- |
| text        | Single-line text |
| textarea    | Multi-line text  |
| password    | Password input   |
| email       | Email address    |
| url         | URL              |
| number      | Numeric input    |
| checkbox    | Boolean          |
| switch      | Toggle           |
| select      | Dropdown         |
| multiselect | Multiple values  |
| radio       | Radio buttons    |
| date        | Date             |
| datetime    | Date & time      |
| time        | Time             |
| color       | Color picker     |
| file        | File upload      |
| image       | Image upload     |
| markdown    | Markdown editor  |
| json        | JSON editor      |

New field types can be introduced through the Component Registry.

---

## Sections

Large forms are divided into sections.

Example:

```text
General

Permissions

Advanced

Diagnostics

```

Sections improve readability and usability.

---

## Layouts

Forms support multiple layouts.

Examples:

- single-column
- two-column
- grid
- tabs
- accordion
- wizard

Layouts are resolved through the Layout Registry.

---

## Labels

Every field should have a descriptive label.

Example:

```text
Project Name

```

Labels improve accessibility and usability.

---

## Help Text

Fields may provide additional explanations.

Example:

```text
The project name must be unique within the workspace.

```

Help text should explain _why_, not merely repeat the label.

---

## Placeholders

Placeholders provide examples rather than instructions.

Good example:

```text
Example Project

```

Poor example:

```text
Enter project name here

```

---

## Default Values

The backend may define default values.

Example:

```json
{
  "default": "Untitled Project"
}
```

Defaults improve usability but never replace validation.

---

## Validation

Validation rules are included in the schema.

Example:

```json
{
  "required": true,
  "minLength": 3,
  "maxLength": 100
}
```

The frontend performs lightweight validation to improve the user experience.

The backend always performs authoritative validation.

---

## Validation Lifecycle

```text
User Input

↓

Client Validation

↓

Submit

↓

Server Validation

↓

Response

```

---

## Required Fields

Required fields are explicitly marked.

Example:

```json
{
  "required": true
}
```

The visual representation should clearly communicate mandatory input.

---

## Conditional Visibility

Fields may depend on other values.

Example:

```text
Advanced Settings

↓

Visible only if

Expert Mode = Enabled

```

Visibility rules are defined in the schema.

---

## Read-Only Fields

Some fields are informational only.

Example:

```json
{
  "readonly": true
}
```

Read-only fields remain visible but cannot be edited.

---

## Disabled Fields

Disabled fields are temporarily unavailable.

Example:

```json
{
  "disabled": true
}
```

Unlike read-only fields, disabled controls are excluded from interaction.

---

## Dynamic Data Sources

Selection controls may retrieve options dynamically.

Example:

```json
{
  "options_source": "/api/models"
}
```

The API Client retrieves the data.

---

## File Uploads

File inputs should support:

- drag & drop
- progress indication
- size validation
- type validation
- cancellation

Upload authorization remains the responsibility of the backend.

---

## Actions

Forms expose actions through the Action Registry.

Typical actions include:

- Submit
- Save
- Cancel
- Delete
- Reset
- Refresh
- Duplicate

Actions remain independent from business logic.

---

## Error Handling

Validation errors should appear close to the affected field.

Example:

```text
Project Name

"This field is required."

```

Global errors should only be used for form-wide failures.

---

## Accessibility

Forms should support:

- keyboard navigation
- screen readers
- semantic labels
- ARIA attributes
- error announcements
- focus management

Accessibility is implemented by generic form components.

---

## Responsive Design

Forms should adapt automatically.

Typical layouts:

```text
Desktop

Two Columns

↓

Tablet

Single Column

↓

Mobile

Stacked Layout

```

No schema changes are required.

---

## Performance

The form system should:

- avoid unnecessary re-renders
- validate incrementally
- lazy-load heavy controls
- memoize static schemas
- minimize DOM updates

Large forms should remain responsive.

---

## Security

The frontend must never trust:

- hidden fields
- disabled fields
- read-only fields
- client validation

The backend validates every submitted value.

---

## Anti-Patterns

Avoid:

- business-specific forms
- duplicated validation logic
- custom field implementations without registry registration
- direct backend calls from field components
- mutable form state

---

## Testing

Typical tests include:

- schema rendering
- validation
- field visibility
- action execution
- accessibility
- responsive layouts
- submission flow
- error handling

---

## Future Evolution

The form architecture supports future capabilities such as:

- autosave
- collaborative editing
- offline editing
- nested forms
- reusable field groups
- plugin-defined field types
- localization
- theme-aware rendering

These enhancements should not require changes to existing schemas.

---

## Related Documentation

## Architecture (2)

- [[Architecture]]
- [[UI-Schema]]
- [[Schema-Renderer]]

---

## Frontend (2)

- [[Component-Registry]]
- [[Action-Registry]]
- [[State-Management]]
- [[API-Client]]

---

## Backend (2)

- [[Contracts]]
- [[Configuration]]
- [[Hierarchy]]

---

## Concepts

- [[Dynamic-UI]]
- [[Runtime-Configuration]]
- [[Schema-Versioning]]

---

## Summary

The Forms subsystem enables Kernschmied to provide powerful, configurable, and consistent user interfaces without creating business-specific React components.

By combining schema-driven rendering, reusable components, centralized validation, and backend authority, forms remain maintainable, extensible, and secure while supporting future requirements without architectural changes.

---

Back to [[Home]].
