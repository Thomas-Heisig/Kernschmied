# State Management

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

# Overview

Kernschmied intentionally follows a **minimal, predictable, and explicit state management architecture**.

Rather than introducing a large global state framework from the beginning, the frontend relies primarily on the capabilities already provided by React.

The goal is to keep application state:

- easy to understand
- easy to debug
- easy to test
- easy to replace
- independent from business logic

Business rules always remain on the backend.

---

# Design Principles

The state architecture follows several principles.

- Keep state local whenever possible.
- Lift state only when necessary.
- Never duplicate authoritative data.
- The backend is always the source of truth.
- Derived state should not be stored.
- Prefer composition over global stores.
- State must remain serializable.
- Avoid hidden side effects.

---

# Types of State

The frontend distinguishes several categories of state.

```text
Frontend State

├── Local UI State
├── Shared Application State
├── Server State
├── Session State
└── Temporary State
```

Each category has different responsibilities.

---

# Local UI State

Local state belongs to a single component.

Examples include:

- dialog visibility
- expanded tree nodes
- active tab
- form input
- selected row
- search text
- sorting
- pagination

Typical implementation:

```tsx
const [open, setOpen] = useState(false);
```

Local state should remain inside the component whenever possible.

---

# Shared Application State

Some state must be shared between multiple components.

Examples:

- selected workspace
- selected project
- selected hierarchy node
- current user
- application settings
- theme
- language

This state should be exposed through React Context or dedicated providers.

---

# Server State

Server state originates from the backend.

Examples:

- hierarchy
- UI schemas
- configuration
- chat history
- available models
- available tools

Server state is never considered authoritative on the client.

Whenever inconsistencies occur, the backend wins.

---

# Session State

Session state exists only while the application is running.

Examples:

- current chat
- current stream
- open editors
- unsaved changes
- navigation history

It is recreated after a browser refresh unless explicitly persisted.

---

# Temporary State

Temporary state has a very short lifetime.

Examples:

- drag & drop targets
- hover information
- resize operations
- animations
- loading indicators

Temporary state should never become part of global application state.

---

# State Ownership

Every piece of state has exactly one owner.

```text
Component

↓

owns

↓

State

↓

passes via props

↓

Children
```

Duplicating ownership should be avoided.

---

# State Flow

State flows in one direction.

```text
Backend

↓

API Client

↓

React Providers

↓

Components

↓

User Interaction

↓

API Request

↓

Backend
```

The frontend never bypasses the backend.

---

# React Context

React Context is used for application-wide state that is relatively stable.

Typical contexts include:

- Authentication
- Theme
- Notifications
- Configuration
- Current Workspace

Context should not become a replacement for proper component composition.

---

# Custom Hooks

Business-independent logic is encapsulated in custom hooks.

Examples:

```text
useHierarchy()

useAppSchema()

useStreaming()

useCurrentProject()

useNotifications()
```

Hooks improve reuse while keeping components focused on rendering.

---

# API Integration

State originating from REST endpoints is loaded through dedicated hooks.

Example flow:

```text
Component

↓

Hook

↓

API Client

↓

Backend

↓

Hook

↓

Component
```

The API client remains the only layer responsible for HTTP communication.

---

# Streaming State

Streaming requires additional transient state.

Typical lifecycle:

```text
Idle

↓

Connecting

↓

Streaming

↓

Completed
```

Additional information may include:

- received tokens
- generation progress
- cancellation state
- usage statistics

Streaming state is isolated from the rest of the application.

---

# Forms

Forms maintain temporary local state until submitted.

```text
Backend

↓

Form Schema

↓

User Input

↓

Validation

↓

Submit

↓

Backend Validation
```

The backend always performs authoritative validation.

---

# Derived State

Derived values should not be stored.

Instead:

```text
Data

↓

Calculation

↓

Rendered Output
```

Example:

Instead of storing

```
filteredProjects
```

store

```
projects
filterText
```

and calculate the filtered list when rendering.

---

# Immutable Updates

State should always be updated immutably.

Preferred:

```tsx
setItems(items => [...items, newItem]);
```

Avoid mutating existing objects.

---

# Asynchronous State

Async operations generally follow this lifecycle:

```text
Idle

↓

Loading

↓

Success

↓

Idle
```

or

```text
Idle

↓

Loading

↓

Error
```

Each asynchronous operation should expose:

- loading
- error
- data

---

# Error State

Errors should remain local to the feature that produced them.

Example:

```text
Hierarchy Error

↓

Hierarchy Component
```

rather than

```text
Global Error Store
```

unless the error affects the entire application.

---

# Persistence

Only selected state should be persisted locally.

Suitable examples:

- theme
- sidebar width
- language
- recently opened items

Unsuitable examples:

- authentication permissions
- model configuration
- hierarchy data

Persistent data must never replace backend state.

---

# Performance Considerations

Good practices include:

- keep state small
- memoize expensive calculations
- split providers by responsibility
- avoid unnecessary re-renders
- avoid deeply nested contexts
- use lazy loading where appropriate

Performance optimizations should not reduce readability.

---

# Anti-Patterns

Avoid the following:

- giant global stores
- duplicated server state
- storing derived data
- mutable state
- business logic inside components
- hidden side effects
- circular dependencies
- unnecessary context providers

---

# Testing

State management should be tested independently from rendering.

Typical tests include:

- hook behavior
- provider initialization
- loading state
- error state
- update logic
- streaming lifecycle

UI tests should verify observable behavior rather than implementation details.

---

# Future Evolution

The current architecture intentionally avoids introducing a large state management library.

If future complexity requires it, an additional state solution may be introduced without changing the overall architecture.

Possible candidates include:

- Redux Toolkit
- Zustand
- Jotai
- TanStack Store

Any future solution must preserve:

- unidirectional data flow
- backend authority
- explicit state ownership
- predictable updates

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Frontend-Overview]]
- [[Request-Lifecycle]]

---

## Frontend

- [[API-Client]]
- [[Streaming]]
- [[Forms]]
- [[Schema-Renderer]]

---

## Backend

- [[Configuration]]
- [[Hierarchy]]
- [[Contracts]]

---

## Concepts

- [[Runtime-Configuration]]
- [[Dynamic-UI]]
- [[UI-Schema]]

---

# Summary

Kernschmied's frontend state management emphasizes simplicity, predictability, and clear ownership.

Local UI state remains close to the components that use it, shared application state is managed through dedicated providers, and all business data ultimately originates from the backend.

This approach minimizes complexity while keeping the frontend maintainable, testable, and aligned with the project's schema-driven architecture.

---

Back to [[Home]].
