# Architecture

> **Version:** 1.0
> **Status:** Living Document
> **Applies to:** Entire Kernschmied Platform

---

## Overview

Kernschmied is a **schema-driven, modular AI platform** built around one central architectural idea:

> **Dynamic business logic, stable contracts, strict security boundaries, and versioned schemas.**

Unlike traditional business applications, the project separates **infrastructure**, **business logic**, **configuration**, and **presentation** into clearly defined layers.

The architecture is designed to support continuous evolution without requiring fundamental redesigns.

---

## Architectural Goals

The architecture aims to provide:

- Long-term maintainability
- Stable public interfaces
- Generic UI rendering
- Secure defaults
- Runtime configurability
- Testability
- Extensibility
- Clear separation of responsibilities

---

## High-Level Architecture

```text
                                ┌──────────────────────────────┐
                                │          Frontend            │
                                │ React · TypeScript · Vite    │
                                │ Generic Components           │
                                │ Schema Renderer              │
                                └──────────────┬───────────────┘
                                               │
                                 REST API / SSE│
                                               │
                                ┌──────────────▼───────────────┐
                                │          FastAPI API         │
                                │ Controllers / Routers        │
                                │ Request Validation           │
                                └──────────────┬───────────────┘
                                               │
                                ┌──────────────▼───────────────┐
                                │        Application Layer     │
                                │ Services                     │
                                │ Authorization                │
                                │ Business Rules               │
                                └──────────────┬───────────────┘
                                               │
                ┌──────────────────────────────┼──────────────────────────────┐
                │                              │                              │
      ┌─────────▼─────────┐        ┌──────────▼──────────┐        ┌──────────▼──────────┐
      │ Config Service     │        │ Model Registry      │        │ Tool Registry       │
      │ Hierarchy Service  │        │ Provider Resolver   │        │ Tool Execution      │
      └─────────┬─────────┘        └──────────┬──────────┘        └──────────┬──────────┘
                │                              │                              │
                └──────────────┬───────────────┴──────────────┬───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Persistence Layer   │
                    │ SQLAlchemy Async    │
                    │ SQLite / PostgreSQL │
                    └─────────────────────┘

```

---

## Layered Architecture

Kernschmied follows a layered architecture.

## 1. Presentation Layer

Responsible for:

- User interface
- Rendering
- User interaction
- Local state
- Accessibility

Technology:

- React
- TypeScript
- Tailwind CSS

The frontend **does not implement business logic**.

---

## 2. API Layer

Responsible for:

- REST endpoints
- Streaming endpoints (SSE)
- Request validation
- Response serialization
- Error formatting

Technology:

- FastAPI
- Pydantic

---

## 3. Application Layer

Contains the business logic.

Responsibilities include:

- authorization
- orchestration
- workflow execution
- hierarchy processing
- configuration
- registry coordination

---

## 4. Domain Services

Encapsulate reusable business functionality.

Examples:

- ChatService
- ConfigService
- HierarchyService
- BootstrapService
- ModelService

Each service has a single responsibility.

---

## 5. Infrastructure Layer

Responsible for technical concerns:

- database
- logging
- authentication
- middleware
- configuration loading
- caching

Infrastructure is intentionally separated from business logic.

---

## Backend Architecture

The backend follows a service-oriented structure.

Typical modules:

```text
app/

api/
services/
models/
schemas/
repositories/
registries/
providers/
config/
database/
core/

```

Each module has clearly defined responsibilities.

---

## Frontend Architecture

The frontend is completely schema-driven.

```text
Frontend

↓

Schema Renderer

↓

Component Registry

↓

Generic Components

↓

Rendered UI

```

The backend defines **what** should be rendered.

The frontend decides **how** to render it.

---

## Schema-Driven UI

Instead of hardcoded pages, the backend sends UI schemas describing:

- forms
- fields
- layouts
- validation
- visibility
- actions

The frontend renders these schemas using generic components.

Advantages:

- reusable UI
- minimal duplication
- configurable interfaces
- extensibility

---

## Generic Components

The frontend should only contain generic components.

Examples:

✔ TreeNode

✔ FormRenderer

✔ ListRenderer

✔ PropertyGrid

Avoid:

✘ CustomerNode

✘ OfferTree

✘ InvoiceEditor

Business-specific behavior belongs in schemas.

---

## Registries

Kernschmied uses registries for all dynamic resources.

Current registries include:

- Model Registry
- Tool Registry
- Component Registry
- Action Registry

Future registries may include:

- Validator Registry
- Storage Registry
- Notification Registry

Registries guarantee controlled discovery.

---

## Bootstrap Process

Application startup follows a defined sequence.

```text
Application Start

↓

Load Environment

↓

Initialize Logging

↓

Load Configuration

↓

Validate Configuration

↓

Initialize Database

↓

Initialize Registries

↓

Initialize Services

↓

Expose API

```

The bootstrap process ensures that the application never starts in an inconsistent state.

---

## Configuration Model

Configuration is divided into two categories.

## Infrastructure Configuration

Stored in:

```text
.env

```

Examples:

- database
- host
- ports
- secrets
- deployment profile

---

## Runtime Configuration

Stored in:

- database

Examples:

- hierarchy
- prompts
- UI configuration
- model assignments
- tool assignments

---

## Hierarchy

The hierarchy is a generic tree.

Example:

```text
Workspace

└── Project

    └── Folder

        └── Chat

```

Future node types can be introduced without modifying the frontend.

---

## AI Model Integration

Models are managed through the Model Registry.

Responsibilities:

- discovery
- validation
- loading
- provider abstraction

The frontend does not know implementation details.

---

## Tool Integration

Tools are managed through the Tool Registry.

Every tool:

- has a manifest
- is validated
- is registered
- must be authorized before execution

Unknown tools are rejected.

---

## Security Model

Security follows a **deny-by-default** strategy.

Unknown:

- components
- actions
- schemas
- tools
- manifests

must never be executed automatically.

---

## Deployment Profiles

The architecture supports multiple deployment environments.

## Development

- simplified authentication
- verbose logging
- local development

---

## Intranet

- authenticated users
- audit logging
- stricter validation

---

## Internet

- HTTPS
- secure sessions
- CSRF protection
- rate limiting
- hardened defaults

---

## Contracts

Public contracts are treated as stable interfaces.

Examples:

- REST APIs
- SSE messages
- UI schemas
- manifests

Breaking changes require versioning.

---

## Error Handling

Errors follow a structured format.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid hierarchy node.",
  "details": {},
  "request_id": "..."
}
```

Every request should be traceable using a request ID.

---

## Design Patterns

The project primarily uses:

- Layered Architecture
- Dependency Injection
- Registry Pattern
- Repository Pattern
- Service Pattern
- Manifest Pattern
- Schema-Driven UI
- Composition over Inheritance

---

## Architectural Principles

Every subsystem should follow these rules:

- Single Responsibility
- Explicit Registration
- Stable Contracts
- Generic Components
- Backend Authority
- Runtime Validation
- Secure Defaults
- Versioned Schemas

---

## Non-Goals

The initial MVP intentionally excludes:

- Distributed microservices
- Automatic plugin execution
- Arbitrary Python code loading
- Remote code execution
- Full RAG infrastructure
- Docker-only deployment

These capabilities may be added later without changing the core architecture.

---

## Related Documentation

## Start Here

- [[Home]]
- [[Getting-Started]]
- [[Project-Principles]]

---

## Backend

- [[Backend-Overview]]
- [[Bootstrap]]
- [[Configuration]]
- [[Contracts]]
- [[Hierarchy]]
- [[Security]]

---

## Frontend

- [[Frontend-Overview]]
- [[Schema-Renderer]]
- [[Component-Registry]]
- [[Action-Registry]]

---

## Concepts

- [[Dynamic-UI]]
- [[Plugin-System]]
- [[Runtime-Configuration]]
- [[Configuration-Revisions]]
- [[Schema-Versioning]]

---

## ADRs

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]

---

## Summary

Kernschmied is designed as a **long-lived, extensible platform** rather than a single application.

By combining:

- stable contracts,
- schema-driven rendering,
- generic components,
- registries,
- runtime configuration,
- dependency injection,
- and strict security boundaries,

the platform can evolve for many years while remaining maintainable, predictable, and secure.

---

Zurück zu [[Home]].
