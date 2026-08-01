# Routing

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

## Overview

Routing in Kernschmied is responsible for navigating between application views while remaining consistent with the project's architecture:

> **The router controls navigation, not business logic.**

Business behavior is always implemented by the backend and exposed through APIs and UI Schemas. The frontend router only determines **which page should be displayed**.

---

## Design Goals

The routing system has several objectives:

- Simple and predictable navigation
- Stable URLs
- Support browser history
- Deep linking
- Lazy loading
- Authentication-aware navigation
- Dynamic pages
- Future plugin integration
- Separation from business logic

---

## Architecture

```text
Browser URL

        │

        ▼

Frontend Router

        │

        ▼

Route Definition

        │

        ▼

Page Component

        │

        ▼

API Requests

        │

        ▼

Backend

        │

        ▼

UI Schema

        │

        ▼

Schema Renderer

```

---

## Responsibilities

The router is responsible for:

- matching URLs
- loading pages
- handling navigation
- browser history
- route parameters
- redirects
- lazy loading

The router is **not** responsible for:

- authorization
- business rules
- permissions
- validation
- data persistence

---

## Route Categories

Routes can be grouped into several categories.

```text
Application

├── Public
├── Authenticated
├── Administration
├── Workspace
├── Project
├── Chat
└── Error Pages

```

---

## Example Route Tree

```text
/

├── login
├── dashboard
├── workspaces
│
├── workspace/:workspaceId
│      │
│      ├── project/:projectId
│      │      │
│      │      ├── folder/:folderId
│      │      │
│      │      └── chat/:chatId
│      │
│      └── settings
│
├── admin
│
└── settings

```

---

## Recommended URL Structure

The URL should describe **resources**, not implementation details.

Good examples:

```text
/workspace/123

```

```text
/workspace/123/project/55

```

```text
/chat/84

```

Avoid URLs such as:

```text
/projectEditor?id=55

```

or

```text
/showProject/55

```

Resources are easier to understand and remain stable over time.

---

## Route Parameters

Dynamic routes contain identifiers.

Example:

```text
/project/:projectId

```

Possible URL:

```text
/project/42

```

The frontend extracts the parameter and requests the corresponding data from the backend.

---

## Nested Routing

Nested routes mirror the hierarchy.

Example:

```text
Workspace

└── Project

    └── Folder

        └── Chat

```

Possible URL:

```text
/workspace/1/project/3/folder/7/chat/19

```

Nested routing improves readability and deep linking.

---

## Navigation Flow

```text
User clicks navigation

↓

Router updates URL

↓

Matching Route

↓

Load Component

↓

Load Data

↓

Render UI

```

---

## Browser History

The router integrates with the browser history.

Supported actions include:

- Back
- Forward
- Refresh
- Direct URL access
- Bookmarking

The application should behave consistently regardless of how navigation occurs.

---

## Deep Linking

Every important application state should be reachable through a URL.

Examples:

- specific project
- hierarchy node
- configuration page
- chat
- administration page

Deep links improve collaboration and usability.

---

## Lazy Loading

Pages should be loaded only when required.

```python
Navigate

↓

Import Page

↓

Render

```

Benefits:

- smaller initial bundle
- faster startup
- reduced memory usage

---

## Authentication

Some routes require authentication.

Example:

```text
Anonymous User

↓

Protected Route

↓

Redirect to Login

```

After successful authentication, the user returns to the originally requested page.

---

## Authorization

The frontend may hide routes based on permissions.

However:

**The backend always performs the final authorization check.**

Even if a user manually enters a URL, unauthorized requests must be rejected by the backend.

---

## Error Routes

Typical error pages include:

- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 500 Internal Error

Example flow:

```text
Unknown URL

↓

404 Page

```

---

## Route Metadata

Routes may define metadata such as:

- title
- icon
- breadcrumb
- description
- required permission

Example:

```ts
{
    title: "Models",
    icon: "cpu"
}
```

---

## Breadcrumbs

Navigation hierarchy should be reflected in breadcrumbs.

Example:

```text
Home

>

Workspace

>

Project

>

Chat

```

Breadcrumbs improve orientation within complex hierarchies.

---

## Integration with the Hierarchy

Navigation should integrate naturally with the generic hierarchy.

```text
Hierarchy Node

↓

Selected

↓

Router

↓

URL

↓

Page

```

The hierarchy remains the primary organizational structure of the application.

---

## UI Schema Integration

Routes typically do not contain page definitions.

Instead:

```text
Route

↓

API Request

↓

UI Schema

↓

Schema Renderer

```

This allows backend-controlled pages without changing frontend routing.

---

## Plugin Integration

Future plugins may contribute additional routes.

Example:

```text
Plugin

↓

Manifest

↓

Route Registration

↓

Router

```

Plugins must register routes explicitly.

Unknown routes are ignored.

---

## Navigation Components

Common navigation elements include:

- sidebar
- breadcrumb
- tabs
- tree navigation
- quick search
- recent items

These components should remain independent from the routing implementation.

---

## State Synchronization

Navigation should remain synchronized with:

- browser history
- selected hierarchy node
- breadcrumbs
- page title
- active sidebar item

This ensures a consistent user experience.

---

## Performance Considerations

Routing should:

- lazy-load pages
- prefetch frequently used routes where appropriate
- avoid unnecessary remounts
- preserve local UI state when reasonable

Navigation should feel instantaneous.

---

## Security

Routing must never be treated as a security boundary.

The frontend may:

- hide navigation
- disable links
- redirect users

Only the backend can:

- authorize requests
- enforce permissions
- validate ownership
- protect resources

---

## Testing

Typical routing tests include:

- route matching
- redirects
- nested routes
- parameter parsing
- breadcrumb generation
- history navigation
- lazy loading
- authentication redirects

Tests should verify behavior rather than implementation details.

---

## Future Evolution

The routing architecture is designed to support future capabilities such as:

- plugin-defined routes
- dynamic route registration
- localized URLs
- workspace-specific navigation
- multiple layouts
- route guards
- offline routing support

These extensions should not require breaking changes to existing routes.

---

## Related Documentation

## Architecture (2)

- [[Architecture]]
- [[Request-Lifecycle]]
- [[Hierarchy-Architecture]]

---

## Frontend

- [[Frontend-Overview]]
- [[State-Management]]
- [[Schema-Renderer]]
- [[Generic-Tree]]
- [[API-Client]]

---

## Backend

- [[Hierarchy]]
- [[Contracts]]
- [[Configuration]]

---

## Concepts

- [[Dynamic-UI]]
- [[Runtime-Configuration]]
- [[Plugin-System]]

---

## Summary

Routing in Kernschmied provides a stable, predictable navigation layer while remaining completely independent of business logic.

URLs identify resources, the router selects the appropriate page, and the backend provides the corresponding data and UI Schema. This separation keeps the frontend lightweight, maintainable, and aligned with the platform's schema-driven architecture.

---

Back to [[Home]].
