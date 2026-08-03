# ADR-0012: Frontend Architecture and Schema-Driven UI

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

## Context

Kernschmied is intended to become a highly configurable AI platform rather than a traditional web application with fixed pages and hardcoded workflows.

The frontend must be able to display new functionality introduced by backend configuration without requiring React source code modifications for every business feature.

Examples include:

- new hierarchy node types
- additional forms
- new actions
- future plugins
- administrator-defined workflows
- new configuration pages
- provider management
- future enterprise modules

The frontend therefore acts primarily as a rendering engine driven by schemas rather than hardcoded business components.

---

## Problem

Traditional React applications often contain business-specific components such as:

- ProjectTree
- CustomerPage
- InvoiceEditor
- AIModelSettings
- UserAdministration

Each new feature requires:

- new routes
- new components
- duplicated state
- duplicated validation
- repeated API integration

As the platform grows this becomes increasingly difficult to maintain.

---

## Decision

Kernschmied adopts a **Schema-Driven Frontend Architecture**.

The backend describes what should be rendered.

The frontend provides generic rendering capabilities.

Business behavior remains backend-driven.

---

## Architectural Principle

> The backend defines intent.
>
> The frontend renders intent.

---

## High-Level Architecture

```text
Backend

        │

UI Schema

        │

        ▼

Schema Renderer

        │

        ▼

Component Registry

        │

        ▼

React Components

```

---

## Design Goals

The frontend architecture should provide:

- schema-driven rendering
- reusable components
- minimal business logic
- stable APIs
- plugin readiness
- extensibility
- predictable rendering
- accessibility

---

## Technology Stack

The frontend is based on:

| Technology         | Purpose     |
| ------------------ | ----------- |
| React              | UI          |
| TypeScript         | Type safety |
| Vite               | Build       |
| Tailwind CSS       | Styling     |
| Fetch API          | HTTP        |
| Server-Sent Events | Streaming   |

---

## Application Shell

The application shell is responsible for:

- startup
- routing
- bootstrap loading
- layout
- providers
- global error boundaries

Business functionality resides in feature modules.

---

## Bootstrap

During startup the frontend loads:

```text
GET /api/v1/bootstrap

```

The bootstrap response provides:

- application information
- supported versions
- enabled features
- endpoints
- security profile
- configuration revision

The bootstrap defines the capabilities available during the current session.

---

## Schema Renderer

The Schema Renderer is the central rendering engine.

Responsibilities include:

- interpreting UI schemas
- selecting components
- validating schema types
- rendering recursively
- displaying unsupported schemas safely

Business rules are intentionally excluded.

---

## Component Registry

The Component Registry maps schema types to React components.

Example:

```text
form

↓

FormRenderer

```

```text
tree

↓

GenericTree

```

```text
chat

↓

GenericChatView

```

Unknown components are never instantiated dynamically.

---

## Why a Registry?

A registry provides:

- compile-time safety
- explicit registrations
- discoverability
- stable rendering
- security

The frontend never evaluates arbitrary JavaScript received from the backend.

---

## Unknown Components

Unknown schema types are handled gracefully.

Example:

```text
Unknown Schema

↓

UnsupportedSchema Component

```

The application continues operating.

Unexpected schemas never crash the interface.

---

## Action Registry

Actions are handled through a dedicated registry.

Examples include:

- navigate
- submit
- refresh
- delete
- open dialog
- execute tool
- download

Actions are identifiers rather than executable JavaScript.

---

## Why Action Identifiers?

The backend communicates:

```json
{
  "action": "refresh"
}
```

The frontend resolves:

```text
refresh

↓

Registered Action

↓

Execution

```

No executable code is transferred.

---

## Generic Tree

Hierarchy rendering uses a recursive Generic Tree component.

The tree is independent of business node types.

Example node types:

- project
- folder
- user
- assistant
- workspace
- repository

Future node types require no new tree implementation.

---

## Dynamic Forms

Forms are generated from backend schemas.

Field definitions include:

- type
- label
- validation
- default values
- layout
- visibility

Form validation remains consistent between frontend and backend.

---

## API Client

All HTTP communication passes through a single API client.

Responsibilities include:

- authentication
- request IDs
- version handling
- retries
- error mapping
- SSE support

Business components never call Fetch directly.

---

## State Management

State is intentionally localized.

Typical state includes:

- bootstrap
- hierarchy
- configuration
- active chat
- streaming
- dialogs

Global state is reserved for cross-cutting concerns.

---

## Streaming

Chat responses use Server-Sent Events.

Supported event types include:

- start
- token
- message
- reasoning
- tool_call
- tool_result
- usage
- complete
- heartbeat
- error

Unknown events are ignored safely.

---

## Routing

Routing is intentionally lightweight.

Routes primarily represent application shells.

Business navigation is driven through schemas.

Future pages should be introduced through backend configuration rather than hardcoded routes whenever practical.

---

## Error Handling

Frontend errors are categorized as:

- network
- validation
- schema
- rendering
- streaming
- unexpected

Errors are presented consistently.

---

## Accessibility

The frontend follows accessibility best practices.

Examples include:

- semantic HTML
- keyboard navigation
- focus management
- screen reader compatibility
- sufficient contrast

Accessibility remains part of every reusable component.

---

## Security Considerations

The frontend never:

- executes arbitrary JavaScript
- evaluates schemas as code
- bypasses backend authorization
- trusts client-side permissions

Unknown schema types are rendered using safe fallback components.

Authorization is always enforced by the backend.

---

## Performance Considerations

Performance techniques include:

- lazy rendering
- immutable state
- component reuse
- registry lookup caching
- streaming updates
- recursive rendering only where necessary

The architecture minimizes unnecessary React re-renders.

---

## Plugin Readiness

Future plugins may contribute:

- schemas
- actions
- components
- icons

Plugins register through controlled registries.

Dynamic runtime code loading is never implicitly trusted.

---

## Operational Impact

The frontend architecture enables:

- rapid feature development
- simplified maintenance
- backend-driven customization
- reusable UI
- enterprise scalability

Administrators can evolve business workflows through configuration rather than frontend rewrites.

---

## Consequences

## Positive

- Minimal business-specific React code
- High reusability
- Predictable rendering
- Easier testing
- Future plugin support
- Stable contracts

## Negative

- More sophisticated renderer
- Registry maintenance
- Schema design complexity

---

## Alternatives Considered

## Business-Specific React Components

Rejected because each new feature requires frontend development.

---

## Dynamic JavaScript Execution

Rejected because executing backend-provided code is incompatible with the platform's security principles.

---

## Server-Rendered HTML

Rejected because rich interactive AI interfaces benefit from a modern client-side application.

---

## Multiple Independent Frontend Modules

Rejected because duplicated infrastructure increases maintenance.

---

## Risks

Potential risks include:

- poorly designed schemas
- excessively generic components
- rendering complexity
- schema evolution

Mitigation strategies include:

- schema validation
- versioned contracts
- component registry
- automated frontend testing
- graceful fallbacks

---

## Implementation Notes

The implementation should provide:

- Schema Renderer
- Component Registry
- Action Registry
- Generic Tree
- Generic Forms
- API Client
- Bootstrap Loader
- Streaming Support
- Error Boundaries
- UnsupportedSchema component

Business logic should remain inside backend services whenever possible.

---

## Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]

---

## Related Documentation

## Frontend

- [[Frontend-Overview]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Generic-Tree]]
- [[Forms]]
- [[State-Management]]
- [[Routing]]
- [[API-Client]]
- [[Streaming]]

---

## Architecture

- [[Architecture]]
- [[UI-Schema]]
- [[Bootstrap]]

---

## Backend

- [[REST-API]]
- [[Configuration]]
- [[Hierarchy]]

---

## Decision Summary

Kernschmied adopts a **Schema-Driven Frontend Architecture** in which the backend describes application structure through versioned schemas while the frontend provides a stable rendering engine composed of a Schema Renderer, Component Registry, Action Registry, Generic Tree, Generic Forms, and centralized API Client.

This approach minimizes business-specific React code, prevents execution of untrusted code, enables future plugin integration, and allows the platform to evolve through backend configuration while preserving a secure, maintainable, and extensible user interface.

---

Back to [[Home]].
