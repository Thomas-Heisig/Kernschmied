# Repository Structure

The **Repository Structure** defines the physical organization of the Kernschmied source code. It establishes a consistent layout for backend services, frontend applications, documentation, manifests, tests, and future extensions while preserving clear architectural boundaries.

The repository layout reflects the overall architecture of the platform:

- schema-driven
- manifest-based
- registry-oriented
- provider-independent
- modular
- testable

A well-defined repository structure improves maintainability, onboarding, scalability, and long-term evolution.

---

# Goals

The repository structure is designed to provide:

- Clear separation of concerns
- Predictable project organization
- Scalable module layout
- Independent frontend and backend development
- Consistent naming conventions
- Easy discoverability
- Stable architectural boundaries
- Future extensibility

---

# Design Principles

The repository organization follows several architectural principles.

## Architecture First

The directory layout reflects the system architecture rather than implementation details.

Example:

```text
API

Services

Repositories

Registries

Providers
```

instead of:

```text
Utils

Helpers

Misc

Stuff
```

---

## Feature Isolation

Each architectural concern has a dedicated location.

Examples include:

- configuration
- registries
- hierarchy
- providers
- manifests
- frontend
- documentation

This minimizes coupling between unrelated components.

---

## Stable Public Boundaries

Internal implementation details remain inside their respective modules.

Public interaction occurs through:

- APIs
- services
- registries
- schemas

Filesystem layout is never considered part of the public contract.

---

# Repository Overview

A typical repository layout is shown below.

```text
Kernschmied/

├── backend/
├── frontend/
├── docs/
├── wiki/
├── tests/
├── scripts/
├── examples/
├── .github/
├── LICENSE
├── README.md
└── pyproject.toml
```

Each top-level directory has a dedicated responsibility.

---

# Top-Level Directories

| Directory | Purpose |
|-----------|----------|
| backend | FastAPI application |
| frontend | React application |
| docs | Technical documentation |
| wiki | GitHub Wiki source |
| tests | Automated tests |
| scripts | Development utilities |
| examples | Example configurations |
| .github | CI/CD workflows |

---

# Backend Structure

The backend follows a layered architecture.

```text
backend/

├── app/
├── migrations/
├── manifests/
├── tests/
├── pyproject.toml
└── alembic.ini
```

Business logic resides inside the `app` package.

---

# Backend Application Layout

```text
app/

├── api/
├── core/
├── services/
├── repositories/
├── registries/
├── providers/
├── configuration/
├── hierarchy/
├── models/
├── schemas/
├── storage/
├── dependencies/
├── security/
└── utils/
```

Each package represents an architectural subsystem.

---

# API Layer

The API layer exposes HTTP endpoints.

```text
api/

├── bootstrap.py
├── chat.py
├── configuration.py
├── hierarchy.py
├── models.py
├── tools.py
└── health.py
```

Responsibilities:

- request validation
- response generation
- dependency injection
- HTTP status handling

Business logic belongs elsewhere.

---

# Service Layer

Application services coordinate business operations.

```text
services/

├── chat_service.py
├── configuration_service.py
├── hierarchy_service.py
└── prompt_service.py
```

Services orchestrate repositories, registries, and providers.

---

# Repository Layer

Repositories encapsulate persistence logic.

```text
repositories/

├── configuration_repository.py
├── hierarchy_repository.py
├── chat_repository.py
└── audit_repository.py
```

Repositories are the only components that communicate directly with the database.

---

# Registry Layer

Registries manage runtime metadata.

```text
registries/

├── model_registry.py
├── tool_registry.py
└── provider_registry.py
```

Registries expose stable runtime lookup APIs.

---

# Provider Layer

Providers integrate external AI systems.

```text
providers/

├── ollama/
├── openai/
├── anthropic/
└── llama_cpp/
```

Each provider is isolated behind a common abstraction.

---

# Manifest Storage

Manifest files reside next to their implementations.

Example:

```text
providers/

└── ollama/

    ├── model.json
    └── provider.py
```

Similarly:

```text
tools/

└── calculator/

    ├── tool.json
    └── tool.py
```

This keeps metadata and implementation together while preserving separation of concerns.

---

# Configuration Package

Configuration-related components are grouped together.

```text
configuration/

├── resolver.py
├── schemas.py
├── validators.py
└── service.py
```

This package is responsible for runtime configuration management.

---

# Hierarchy Package

Hierarchy functionality resides in its own module.

```text
hierarchy/

├── nodes.py
├── resolver.py
├── service.py
└── schemas.py
```

Hierarchy logic remains independent of UI rendering.

---

# Storage Package

Database access is isolated.

```text
storage/

├── database.py
├── session.py
├── migrations.py
└── models.py
```

The storage package abstracts the underlying database implementation.

---

# Security Package

Security-related components are grouped together.

```text
security/

├── authentication.py
├── authorization.py
├── permissions.py
└── policies.py
```

This keeps security concerns centralized.

---

# Frontend Structure

The frontend follows a feature-oriented layout.

```text
frontend/

├── src/
├── public/
├── tests/
├── package.json
└── vite.config.ts
```

---

# Frontend Source Layout

```text
src/

├── api/
├── app/
├── components/
├── features/
├── hooks/
├── pages/
├── schemas/
├── stores/
├── styles/
├── types/
└── utils/
```

The frontend mirrors the architectural concepts of the backend.

---

# Component Organization

Reusable components reside under:

```text
components/

├── schema/
├── tree/
├── forms/
├── layout/
└── common/
```

Business-specific components should be avoided.

---

# Schema Components

Schema-driven rendering components are grouped together.

```text
components/schema/

├── SchemaRenderer.tsx
├── ComponentRegistry.ts
├── ActionRegistry.ts
└── UnsupportedSchema.tsx
```

These form the basis of the dynamic UI.

---

# API Client

All backend communication is centralized.

```text
api/

├── client.ts
├── bootstrap.ts
├── chat.ts
├── configuration.ts
└── hierarchy.ts
```

Components never perform raw HTTP requests.

---

# Documentation

Documentation is stored separately from implementation.

```text
docs/

├── architecture/
├── api/
├── frontend/
└── adr/
```

The GitHub Wiki resides in its own dedicated directory.

---

# Wiki Structure

```text
wiki/

├── Architecture/
├── API/
├── Frontend/
├── ADR/
├── Home.md
├── _Sidebar.md
└── _Footer.md
```

The wiki mirrors the logical architecture of the project.

---

# Tests

Tests are organized by architectural layer.

```text
tests/

├── unit/
├── integration/
├── api/
├── frontend/
└── fixtures/
```

Tests should follow the same module boundaries as production code.

---

# Scripts

Development utilities are isolated.

```text
scripts/

├── start_backend.ps1
├── start_frontend.ps1
├── build.ps1
└── lint.ps1
```

Scripts should never contain application logic.

---

# Naming Conventions

Recommended naming conventions:

| Item | Convention |
|------|------------|
| Python modules | `snake_case.py` |
| React components | `PascalCase.tsx` |
| TypeScript utilities | `camelCase.ts` |
| Markdown files | `Title-Case.md` |
| Directories | `lowercase` |

Consistency improves discoverability.

---

# Dependency Direction

Dependencies always point toward lower architectural layers.

```text
API

↓

Services

↓

Repositories

↓

Database
```

The reverse direction is prohibited.

---

# Module Independence

Modules communicate through stable interfaces.

Example:

```text
Chat Service

↓

Model Registry

↓

Provider
```

Internal implementation details remain encapsulated.

---

# Scalability

The repository layout supports future growth.

New architectural modules can be introduced without restructuring existing packages.

Examples:

- plugins
- workflows
- notifications
- localization
- reporting

---

# Best Practices

Recommended guidelines:

- Keep modules focused.
- Avoid circular dependencies.
- Group by architecture, not by file type.
- Keep manifests next to implementations.
- Centralize API communication.
- Separate documentation from source code.
- Mirror backend concepts in the frontend where appropriate.

---

# Relationship to Other Architecture

The Repository Structure reflects the overall architecture of the platform.

```text
Repository

↓

Architecture

↓

Modules

↓

Implementation
```

It therefore complements:

- [[C4-Container]]
- [[Registry-Architecture]]
- [[Manifest-System]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[C4-Container]]
- [[Registry-Architecture]]
- [[Manifest-System]]
- [[Configuration-Architecture]]
- [[Security-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Configuration]]
- [[Hierarchy]]
- [[Models]]
- [[Tools]]

---

## ADRs

- [[ADR-0003-Registries]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

The Repository Structure organizes the Kernschmied codebase according to architectural responsibilities rather than implementation convenience.

By separating the backend, frontend, documentation, manifests, registries, services, repositories, and supporting infrastructure into clearly defined modules, the repository remains scalable, maintainable, and aligned with the platform's schema-driven, manifest-based, and provider-independent architecture. This structure enables efficient development, predictable navigation, and long-term evolution without sacrificing modularity or architectural clarity.

---

Back to [[Home]].
