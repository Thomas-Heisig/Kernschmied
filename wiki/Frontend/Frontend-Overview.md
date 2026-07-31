# Frontend Overview

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

# Overview

The Kernschmied frontend is a **schema-driven React application** built around the principle that **business logic belongs exclusively to the backend**.

Unlike traditional business applications that implement dedicated React pages for every business object, Kernschmied renders nearly the entire user interface dynamically from backend-provided schemas.

The frontend therefore acts as a **generic rendering engine**, responsible for presenting data, handling user interaction, and communicating with the backend through stable, versioned contracts.

---

# Goals

The frontend architecture has several primary objectives:

- Generic rather than business-specific
- Schema-driven
- Maintainable
- Highly modular
- Extensible
- Secure
- Accessible
- Testable
- Performant
- Predictable

---

# Design Philosophy

The frontend follows one simple rule:

> **Render what the backend describes.**

Instead of creating components such as

- CustomerEditor
- InvoiceForm
- ProjectSettings
- UserManagement

the frontend renders generic components based on a UI Schema.

```text
Backend

↓

UI Schema

↓

Schema Renderer

↓

Component Registry

↓

React Components

↓

Browser
```

This dramatically reduces duplicated frontend code while allowing the backend to evolve independently.

---

# Technology Stack

The frontend is built using modern technologies.

| Technology         | Purpose                        |
| ------------------ | ------------------------------ |
| React              | Component framework            |
| TypeScript         | Static typing                  |
| Vite               | Development server and bundler |
| Tailwind CSS       | Styling                        |
| Fetch API          | HTTP communication             |
| Server-Sent Events | AI response streaming          |

---

# High-Level Architecture

```text
Browser

↓

React Application

↓

Routing

↓

Page

↓

Schema Renderer

↓

Component Registry

↓

Generic Components

↓

REST API / SSE

↓

FastAPI Backend
```

---

# Responsibilities

The frontend is responsible for:

- rendering user interfaces
- navigation
- user interaction
- local UI state
- accessibility
- responsive layouts
- API communication
- streaming responses
- displaying validation errors

The frontend is **not** responsible for:

- business logic
- authorization
- persistence
- workflow execution
- permissions
- model management

---

# Architectural Principles

The frontend follows these principles:

- Generic components
- Stable contracts
- Schema-driven rendering
- Explicit registration
- Composition over inheritance
- Backend authority
- Runtime validation
- Progressive enhancement

---

# Frontend Layers

```text
Application

├── App Shell
├── Routing
├── Pages
├── Schema Renderer
├── Component Registry
├── Generic Components
├── API Client
└── Shared Utilities
```

Each layer has clearly defined responsibilities.

---

# Application Shell

The App Shell provides the permanent structure of the application.

Typical responsibilities include:

- header
- navigation
- sidebar
- workspace layout
- notification area
- dialogs
- loading indicators

Business pages are rendered inside the shell.

---

# Routing

Routing controls navigation throughout the application.

Responsibilities include:

- URL matching
- browser history
- deep linking
- lazy loading
- redirects

Routing never contains business logic.

See:

- [[Routing]]

---

# Schema Renderer

The Schema Renderer converts backend-provided UI Schemas into React components.

Responsibilities:

- validate schemas
- resolve layouts
- resolve components
- resolve actions
- render recursively

See:

- [[Schema-Renderer]]

---

# Component Registry

Every renderable component is registered centrally.

Example:

```text
"text"

↓

TextField
```

This enables new component types without modifying the renderer.

See:

- [[Component-Registry]]

---

# Action Registry

User actions are also registered centrally.

Examples:

- submit
- refresh
- navigate
- delete
- export

Actions are forwarded to the backend whenever business logic is required.

See:

- [[Action-Registry]]

---

# Generic Components

Instead of domain-specific components, Kernschmied provides reusable building blocks.

Examples include:

- TextField
- Select
- Checkbox
- Table
- Tree
- Tabs
- Card
- PropertyGrid
- MarkdownViewer
- Button
- Dialog

These components know nothing about the application's business domain.

---

# Generic Tree

Hierarchical data is rendered through a single Generic Tree component.

The tree supports:

- unlimited nesting
- lazy loading
- drag & drop
- selection
- context menus
- keyboard navigation

See:

- [[Generic-Tree]]

---

# Forms

Forms are generated dynamically from schemas.

The backend defines:

- fields
- validation
- layout
- actions

The frontend simply renders them.

See:

- [[Forms]]

---

# State Management

State is intentionally simple.

Categories include:

- Local UI State
- Shared Application State
- Server State
- Streaming State

The backend remains the authoritative source for all business data.

See:

- [[State-Management]]

---

# API Client

The API Client provides a single abstraction for backend communication.

Responsibilities:

- HTTP requests
- authentication
- error handling
- request IDs
- response validation

Components never communicate directly with the backend.

See:

- [[API-Client]]

---

# Streaming

AI responses are streamed using Server-Sent Events.

Typical flow:

```text
User Request

↓

Backend

↓

SSE Stream

↓

Incremental Rendering
```

Streaming remains provider-independent.

See:

- [[Streaming]]

---

# Styling

The frontend uses Tailwind CSS.

Goals include:

- consistency
- responsiveness
- maintainability
- accessibility
- minimal custom CSS

Business-specific styling should be avoided.

---

# Error Handling

Errors are handled at multiple levels.

Examples:

- network errors
- schema validation errors
- unsupported components
- unsupported layouts
- authentication failures

Errors should remain localized whenever possible.

---

# Accessibility

Accessibility is a first-class architectural requirement.

The frontend should support:

- keyboard navigation
- screen readers
- semantic HTML
- ARIA attributes
- focus management
- sufficient color contrast

Accessibility is implemented within the generic component library.

---

# Performance

The frontend is designed for predictable performance.

Techniques include:

- lazy loading
- memoization
- code splitting
- virtualization
- incremental rendering
- efficient state updates

Optimization should never compromise readability.

---

# Security

The frontend follows a zero-trust approach.

It must never:

- execute arbitrary code
- evaluate schemas
- bypass authorization
- trust client-side validation
- expose secrets

All security decisions remain on the backend.

---

# Testing

Frontend testing includes:

- component tests
- hook tests
- rendering tests
- accessibility tests
- integration tests
- end-to-end tests

Testing focuses on observable behavior rather than implementation details.

---

# Future Evolution

The architecture supports future capabilities such as:

- plugin-provided components
- dynamic layouts
- theme switching
- localization
- offline support
- collaborative editing
- desktop integration
- mobile adaptations

These extensions should not require breaking existing contracts.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[System-Context]]
- [[Request-Lifecycle]]

---

## Frontend

- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Generic-Tree]]
- [[Routing]]
- [[State-Management]]
- [[Streaming]]
- [[API-Client]]
- [[Forms]]
- [[UI-Schema]]

---

## Backend

- [[Backend-Overview]]
- [[Contracts]]
- [[Hierarchy]]
- [[Configuration]]

---

## Concepts

- [[Dynamic-UI]]
- [[Runtime-Configuration]]
- [[Plugin-System]]
- [[Schema-Versioning]]

---

# Summary

The Kernschmied frontend is not a traditional business application—it is a **generic user interface platform**.

By combining React, TypeScript, schema-driven rendering, generic components, and stable backend contracts, the frontend remains highly maintainable, extensible, and independent of business-specific implementations.

This architecture allows entirely new functionality to be introduced through backend configuration and schemas while preserving a consistent user experience and minimizing frontend complexity.

---

Back to [[Home]].
