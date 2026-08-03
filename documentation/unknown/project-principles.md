# Project Principles

> **Version:** 1.0
> **Status:** Living Document
> **Applies to:** Entire Kernschmied Project

---

## Purpose

Kernschmied is designed as a **modular, schema-driven AI platform** that can evolve over many years without requiring architectural redesigns.

The project's primary objective is **long-term maintainability**, **extensibility**, **predictability**, and **security**.

These principles are mandatory for every component of the system.

---

## Core Philosophy

Kernschmied follows one central philosophy:

> **Dynamic business logic, stable contracts, strict security boundaries, and versioned schemas.**

Dynamic behavior is allowed only inside clearly defined boundaries.

Unknown behavior is never executed automatically.

Every extension must be explicitly registered, validated and authorized.

---

## Design Goals

The project aims to achieve:

- Long-term maintainability
- Stable APIs
- Generic architecture
- Minimal coupling
- Maximum configurability
- Predictable runtime behavior
- Strong security
- Clear separation of responsibilities
- Testability
- Future-proof extensibility

---

## Fundamental Principles

## 1. Stable Contracts

Public contracts are more important than internal implementation.

Backend implementations may change.

Frontend implementations may change.

Database structures may evolve.

Public contracts should remain stable whenever possible.

Breaking changes must be versioned.

Examples:

- REST endpoints
- SSE events
- Pydantic schemas
- UI schemas
- plugin manifests

---

## 2. Dynamic Business Logic

Business logic is configurable.

Infrastructure is not.

Examples of dynamic data:

- prompts
- hierarchy
- model assignments
- tool assignments
- UI configuration
- workflows
- permissions
- runtime settings

Examples of static infrastructure:

- authentication
- authorization
- routing
- middleware
- serialization
- schema validation

---

## 3. Schema-Driven UI

The frontend never contains business-specific pages.

The backend describes:

- forms
- layouts
- fields
- actions
- validation
- visibility
- hierarchy

The frontend renders generic components based on schemas.

---

## 4. Generic Components

Frontend components must remain generic.

Examples:

Good:

- TreeNode
- PropertyGrid
- FormRenderer
- ChatView
- ListRenderer

Avoid:

- CustomerTree
- ProjectTree
- OfferNode
- InvoicePanel

Business-specific behavior belongs in schemas.

---

## 5. Registry Pattern

Every dynamically loadable component must be registered.

Examples:

- models
- tools
- node types
- component renderers
- action handlers
- validators

Unknown entries are rejected.

Automatic execution is prohibited.

---

## 6. Explicit Registration

Discovery does not equal permission.

A plugin may exist without being enabled.

A model may exist without being usable.

Every resource must be explicitly approved.

---

## 7. Security by Default

Security is always preferred over convenience.

Unknown requests are rejected.

Unknown schemas are rejected.

Unknown actions are rejected.

Unknown components are displayed as unsupported.

Nothing is executed automatically.

---

## 8. Versioned Schemas

Every externally visible schema must be versioned.

Examples:

- API schemas
- UI schemas
- plugin manifests
- model manifests
- tool manifests

Breaking changes require new versions.

---

## 9. Separation of Concerns

Responsibilities remain separated.

### Backend

Responsible for:

- business logic
- validation
- authorization
- persistence
- configuration
- schema generation

### Frontend

Responsible for:

- rendering
- interaction
- local state
- accessibility

The frontend never decides business rules.

---

## 10. Dependency Injection

Global mutable state should be avoided.

Services are resolved using dependency injection.

Benefits:

- testability
- replacement
- modularity
- isolation

---

## 11. Runtime Configuration

Configuration belongs to the database.

The `.env` file is only used for bootstrap and infrastructure.

Examples stored in `.env`:

- database connection
- bootstrap profile
- secrets
- host
- port

Examples stored in database:

- prompts
- model assignments
- UI configuration
- hierarchy
- plugins
- runtime behavior

---

## 12. Runtime Safety

Changing configuration must never leave the system in an inconsistent state.

Configuration changes require validation.

Some settings may require restart.

Some settings are runtime editable.

Every configuration change is auditable.

---

## 13. Auditability

Configuration changes must be traceable.

Audit logs should contain:

- timestamp
- user
- action
- old value
- new value
- request id

---

## 14. Deterministic Behavior

Identical inputs should produce identical system behavior whenever possible.

Avoid hidden side effects.

Avoid implicit state.

Avoid magic behavior.

---

## 15. Extensibility

The architecture must support future extensions without redesign.

Examples:

- additional AI providers
- new tools
- new hierarchy levels
- additional deployment profiles
- new UI components

Extensions should require configuration rather than source code modifications.

---

## 16. Backend Authority

The backend is the single source of truth.

The frontend may cache data.

The frontend may optimize rendering.

The frontend never authorizes actions.

Every action is validated server-side.

---

## 17. Error Handling

Errors should be structured.

Typical error response:

```json
{
  "code": "validation_error",
  "message": "Invalid hierarchy node.",
  "details": {},
  "request_id": "..."
}
```

Errors should always be actionable.

---

## 18. Testing

Every new feature should include appropriate tests.

Preferred order:

1. unit tests
2. integration tests
3. API tests
4. frontend tests

Critical business logic must never be released without automated tests.

---

## 19. Documentation

Architecture is part of the product.

Every major subsystem should be documented.

Documentation should evolve together with the implementation.

Outdated documentation should be corrected immediately.

---

## 20. Simplicity

Prefer:

- simple solutions
- explicit code
- readable architecture
- maintainable modules

Avoid unnecessary abstraction.

Avoid premature optimization.

Avoid overengineering.

---

## Non-Goals

The following are intentionally outside the initial MVP:

- distributed microservices
- arbitrary remote code execution
- unrestricted plugin loading
- automatic code generation
- self-modifying runtime
- hidden AI decision making

---

## Guiding Principle

Whenever multiple implementation options exist, choose the solution that best preserves:

1. Stability
2. Maintainability
3. Security
4. Predictability
5. Extensibility

Performance optimizations should never compromise these principles.

---

## Summary

Kernschmied is built on a small number of strict architectural rules:

- Stable contracts
- Dynamic business logic
- Generic frontend
- Explicit registration
- Strong validation
- Secure defaults
- Versioned schemas
- Backend authority
- Runtime configurability
- Long-term maintainability

These principles form the foundation for every future decision within the project.

```text


## Verweise
- [[Home]]

Zurück zu [[Home]].

```
