# Generic Tree

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

## Overview

The **Generic Tree** is one of the fundamental UI components of the Kernschmied frontend.

Unlike traditional applications that implement separate tree components for projects, folders, chats, or configuration objects, Kernschmied provides **a single generic tree renderer** capable of displaying any hierarchical data structure.

The Generic Tree is entirely driven by data received from the backend and rendered using the Component Registry.

---

## Design Goals

The Generic Tree has several objectives:

- Display arbitrary hierarchies
- Support unlimited nesting
- Remain independent of business domains
- Be highly reusable
- Integrate with routing
- Support drag & drop
- Support lazy loading
- Provide accessibility
- Scale to large datasets

---

## Design Philosophy

Traditional applications often contain many specialized tree implementations.

```text
Project Tree

Folder Tree

Chat Tree

Settings Tree

Model Tree

Plugin Tree

```

Each implementation duplicates behavior.

Kernschmied replaces all of them with one generic renderer.

```text
Hierarchy Data

↓

Generic Tree

↓

Tree Node Renderer

↓

Browser

```

The frontend does not know whether a node represents a project, chat, model, workspace, or future entity.

---

## Tree Architecture

```text
Backend

↓

Hierarchy API

↓

Hierarchy Contract

↓

Generic Tree

↓

Tree Node

↓

React Components

```

The Generic Tree renders only what the backend describes.

---

## Node Model

Every node follows a common contract.

Example:

```json
{
  "id": "workspace-1",
  "type": "workspace",
  "title": "Main Workspace",
  "children": []
}
```

The renderer relies on the contract rather than business-specific types.

---

## Typical Node Properties

A node may contain:

| Property   | Description                  |
| ---------- | ---------------------------- |
| id         | Unique identifier            |
| parent_id  | Parent node                  |
| type       | Node type                    |
| title      | Display title                |
| subtitle   | Optional secondary text      |
| icon       | Icon identifier              |
| expanded   | Initial expansion state      |
| selectable | Whether selection is allowed |
| draggable  | Drag support                 |
| droppable  | Drop support                 |
| disabled   | Disabled state               |
| children   | Child nodes                  |

Additional metadata may be included without modifying the renderer.

---

## Tree Structure

Example hierarchy:

```text
Workspace

├── Project Alpha
│   ├── Folder A
│   │   ├── Chat 1
│   │   └── Chat 2
│   │
│   └── Folder B
│
└── Project Beta
    └── Chat

```

The renderer supports arbitrary depth.

---

## Recursive Rendering

Rendering is naturally recursive.

```text
Tree

↓

Node

↓

Children

↓

Node

↓

Children

```

There is no predefined nesting limit.

---

## Rendering Pipeline

```text
Hierarchy Data

↓

Validate

↓

Resolve Icons

↓

Resolve Node Renderer

↓

Render Node

↓

Render Children

↓

Finished Tree

```

---

## Tree Node Component

Each node is rendered using the same generic component.

Responsibilities include:

- icon
- label
- expansion
- selection
- actions
- children

Business logic is intentionally excluded.

---

## Selection

The Generic Tree supports single selection.

```text
Click Node

↓

Selected

↓

Selection State Updated

↓

Application Notified

```

Future extensions may include multi-selection.

---

## Expansion

Expansion state determines whether children are visible.

```text
Collapsed

↓

Expand

↓

Render Children

↓

Expanded

```

Expansion state may be restored between sessions.

---

## Lazy Loading

Large hierarchies may load children on demand.

```text
Expand Node

↓

Backend Request

↓

Children Loaded

↓

Render

```

This minimizes initial loading time.

---

## Virtualization

Very large trees may use virtualization.

Benefits include:

- lower memory usage
- improved scrolling
- reduced rendering cost

Virtualization should remain transparent to users.

---

## Drag & Drop

The Generic Tree is designed to support drag-and-drop operations.

Example:

```text
Drag Chat

↓

Move

↓

Drop Into Folder

↓

Backend Validation

↓

Tree Updated

```

The backend remains responsible for validating every move.

---

## Context Menus

Nodes may expose contextual actions.

Examples:

- Rename
- Delete
- Duplicate
- Export
- Properties

Available actions are determined by the backend.

---

## Icons

Icons are determined using node metadata.

Example:

```json
{
  "icon": "folder"
}
```

The frontend resolves the icon using the configured icon library.

Unknown icons fall back to a default representation.

---

## Badges

Nodes may display badges.

Examples:

- unread messages
- warnings
- synchronization status
- running tasks

Badges are purely visual.

---

## Search

The tree supports filtering.

Example:

```text
Search

↓

Matching Nodes

↓

Expand Parents

↓

Highlight Matches

```

Filtering does not modify the underlying hierarchy.

---

## Sorting

Sorting is determined by the backend whenever possible.

Possible strategies:

- alphabetical
- manual order
- creation date
- modification date
- custom order

The frontend should not invent sorting rules.

---

## Accessibility

The Generic Tree should support:

- keyboard navigation
- screen readers
- ARIA tree roles
- focus indicators
- expand/collapse shortcuts

Accessibility is considered a first-class requirement.

---

## Performance Considerations

The tree should:

- minimize re-renders
- memoize node rendering
- lazy-load children
- virtualize large datasets
- preserve expansion state

Performance should remain predictable even with thousands of nodes.

---

## Error Handling

Invalid nodes should not break rendering.

Possible problems include:

- missing IDs
- circular references
- duplicate identifiers
- unknown node types

Invalid nodes should be reported and skipped when possible.

---

## Security

The Generic Tree does not perform authorization.

The backend determines:

- visible nodes
- editable nodes
- draggable nodes
- available actions

The frontend only renders the provided hierarchy.

---

## Future Extensions

The architecture allows future enhancements such as:

- multi-selection
- inline renaming
- favorites
- pinning
- live updates
- collaboration indicators
- node templates
- offline synchronization
- plugin-defined node types

These capabilities can be added without changing the public tree contract.

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Hierarchy-Architecture]]
- [[Request-Lifecycle]]

---

## Frontend

- [[Schema-Renderer]]
- [[State-Management]]
- [[Routing]]
- [[Component-Registry]]

---

## Backend

- [[Hierarchy]]
- [[Configuration]]
- [[Contracts]]

---

## Concepts

- [[Dynamic-UI]]
- [[Runtime-Configuration]]
- [[Plugin-System]]

---

## Summary

The Generic Tree provides a single, reusable mechanism for rendering hierarchical data throughout the Kernschmied platform.

By relying on generic node contracts rather than business-specific implementations, it enables unlimited extensibility, consistent user experience, and long-term maintainability while keeping business logic entirely on the backend.

---

Back to [[Home]].
