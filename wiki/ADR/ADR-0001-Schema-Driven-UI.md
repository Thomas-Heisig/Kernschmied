# ADR-0001: Adopt a Schema-Driven User Interface

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is intended to become a highly configurable platform rather than a fixed business application.

The platform must support:

- Different deployment environments
- Configurable hierarchies
- Configurable tools
- Configurable AI models
- Configurable workflows
- Future plugins
- Runtime configuration
- Long-term maintainability

A traditional React application would typically contain dedicated pages and components for each business object:

- CustomerPage
- ProjectEditor
- InvoiceForm
- UserManagement
- SettingsPage

While this approach is simple for small systems, it scales poorly as the number of configurable objects grows.

It also tightly couples the frontend to backend implementation details, requiring coordinated releases whenever business functionality changes.

The architecture therefore requires a solution that allows backend-driven evolution without constant frontend development.

---

# Problem

Traditional frontend architectures have several disadvantages for a configurable platform.

## Business Logic Leaks into the Frontend

Business rules often become embedded in React components.

This creates duplicated logic between frontend and backend.

---

## Tight Coupling

Frontend releases become necessary whenever:

- new object types are introduced
- forms change
- workflows change
- layouts change

---

## Poor Extensibility

Every new business feature typically requires:

- new pages
- new components
- new routes
- new validation
- new tests

---

## High Maintenance Cost

As the application grows:

- duplicated code increases
- inconsistencies appear
- frontend complexity rises
- testing effort grows significantly

---

## Difficult Plugin Support

Plugins become difficult because they must integrate into many different frontend areas instead of providing declarative metadata.

---

# Decision

Kernschmied adopts a **Schema-Driven User Interface Architecture**.

The backend becomes the authoritative source for describing user interfaces.

The frontend renders generic components based exclusively on versioned UI Schemas.

Business-specific React components are intentionally avoided.

---

# Architectural Principle

The guiding principle is:

> **The backend defines what should be rendered.  
> The frontend defines how it is rendered.**

---

# High-Level Architecture

```text
Backend

↓

Business Objects

↓

UI Schema

↓

REST API

↓

Frontend

↓

Schema Renderer

↓

Component Registry

↓

React Components
```

---

# Core Concepts

The architecture consists of several cooperating building blocks.

## UI Schema

The backend exposes versioned UI Schemas.

Schemas describe:

- layouts
- sections
- fields
- tables
- trees
- actions
- validation
- metadata

---

## Schema Renderer

The Schema Renderer interprets schemas and converts them into React elements.

The renderer contains no business knowledge.

---

## Component Registry

Every supported component type is registered explicitly.

Example:

```text
"text"

↓

TextField
```

Unknown component types never execute arbitrary code.

---

## Action Registry

User interactions are resolved through the Action Registry.

Instead of embedding business logic inside components:

```text
Button

↓

Action Type

↓

Registered Handler

↓

API Client

↓

Backend
```

---

## Backend Authority

The backend remains responsible for:

- permissions
- validation
- business logic
- persistence
- workflows
- configuration

The frontend is responsible only for presentation and interaction.

---

# Example

Instead of creating:

```text
ProjectEditor.tsx

CustomerEditor.tsx

InvoiceEditor.tsx
```

The backend may expose:

```json
{
  "layout": "single-column",
  "fields": [
    {
      "type": "text",
      "name": "name"
    }
  ]
}
```

The frontend renders the schema without requiring new React pages.

---

# Consequences

## Positive

### Backend-Driven Evolution

Most UI changes no longer require frontend code changes.

---

### Reduced Frontend Complexity

The frontend contains fewer business-specific components.

---

### Better Reusability

Generic components are reused across the entire platform.

---

### Stable Contracts

Communication occurs through versioned schemas instead of implementation details.

---

### Easier Testing

Generic renderers and registries are easier to test than hundreds of specialized pages.

---

### Improved Maintainability

Bug fixes in generic components automatically benefit every screen.

---

### Plugin Readiness

Plugins can provide metadata and schemas rather than React pages.

---

## Negative

### Higher Initial Complexity

Building a generic rendering engine requires more upfront work than creating individual pages.

---

### Schema Design Becomes Critical

Poor schema design can make future evolution difficult.

Versioning and validation therefore become architectural requirements.

---

### Generic Components Require Careful Design

Each generic component must be flexible enough to support many use cases without becoming overly complex.

---

### More Backend Responsibility

The backend must generate complete, valid schemas.

This increases backend responsibilities but centralizes business knowledge.

---

# Alternatives Considered

## Traditional React Pages

### Advantages

- Familiar development model
- Fast for small projects
- Simple debugging

### Disadvantages

- High coupling
- Poor scalability
- Difficult runtime customization
- Extensive duplication

Rejected.

---

## Low-Code UI Framework

Examples include commercial low-code platforms.

### Advantages

- Rapid UI creation
- Visual editors

### Disadvantages

- Vendor lock-in
- Limited flexibility
- Difficult integration
- Poor long-term control

Rejected.

---

## Runtime JavaScript Evaluation

Allowing backend-provided JavaScript to construct user interfaces.

### Advantages

- Maximum flexibility

### Disadvantages

- Severe security risks
- Difficult debugging
- No type safety
- No deterministic behavior

Explicitly rejected.

---

# Security Considerations

The schema-driven architecture follows a strict allow-list model.

The frontend never:

- executes arbitrary JavaScript
- evaluates expressions
- imports unknown modules
- trusts client-side validation
- authorizes requests

Only explicitly registered components and actions may be resolved.

Unknown schema elements are displayed as unsupported instead of being executed.

---

# Performance Considerations

The architecture supports efficient rendering through:

- registry lookups
- lazy loading
- memoization
- virtualization
- incremental rendering
- code splitting

Schema interpretation introduces minimal overhead compared to network latency and rendering costs.

---

# Operational Impact

This decision affects nearly every frontend subsystem, including:

- Routing
- Forms
- Component Registry
- Action Registry
- Generic Tree
- API Client
- Streaming
- State Management

The backend also becomes responsible for generating valid UI Schemas.

---

# Risks

Potential risks include:

- Overly generic components
- Schema version drift
- Poor schema documentation
- Excessive schema complexity
- Weak validation

These risks are mitigated through:

- Versioned schemas
- Runtime validation
- Explicit registries
- Strong TypeScript typing
- Comprehensive testing

---

# Implementation Notes

The implementation should follow these principles:

- Stable schema contracts
- Explicit component registration
- Explicit action registration
- Backend authority
- Runtime schema validation
- Graceful fallback for unsupported schema elements
- Dependency injection
- Comprehensive automated testing

---

# Related Decisions

- [[ADR-0002-Backend-Authority]]
- [[ADR-0003-Registry-Based-Extension]]
- [[ADR-0004-Versioned-Contracts]]
- [[ADR-0005-Deny-by-Default-Security]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[UI-Schema]]
- [[Schema-Renderer]]

## Frontend

- [[Frontend-Overview]]
- [[Component-Registry]]
- [[Action-Registry]]
- [[Forms]]

## Backend

- [[Backend-Overview]]
- [[Contracts]]

---

# Decision Summary

Kernschmied adopts a **schema-driven user interface architecture** in which the backend describes user interfaces through versioned schemas and the frontend renders them using generic components and explicit registries.

This decision establishes one of the fundamental architectural principles of the platform, enabling runtime configurability, extensibility, maintainability, and secure long-term evolution while avoiding business-specific frontend implementations.

---

Back to [[Home]].
