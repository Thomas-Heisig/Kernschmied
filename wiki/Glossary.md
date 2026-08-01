# Glossary

> **Version:** 1.0  
> **Status:** Living Document

---

## Introduction

This glossary defines the terminology used throughout the Kernschmied project.

The goal is to ensure that every developer, contributor, and future maintainer uses the same vocabulary when discussing the architecture.

---

## A

## Action

A user-initiated operation that is executed by the backend.

Examples:

- Create node
- Delete node
- Send chat message
- Update configuration

Actions are always validated and authorized server-side.

See also:

- [[Action-Registry]]

---

## Action Registry

The frontend registry that maps action identifiers from UI schemas to generic action handlers.

Unknown actions must never be executed automatically.

---

## API

Application Programming Interface.

Kernschmied exposes a REST API and Server-Sent Events (SSE) for communication between frontend and backend.

---

## Audit Log

A persistent record of important system events.

Typical audit entries include:

- configuration changes
- permission changes
- administrative actions
- runtime configuration updates

---

## B

## Backend

The server-side application responsible for:

- business logic
- validation
- authorization
- persistence
- schema generation
- AI integration

The backend is the single source of truth.

---

## Bootstrap

The initialization phase of the application.

Responsibilities include:

- loading configuration
- validating settings
- initializing registries
- preparing services
- exposing runtime information

See:

- [[Bootstrap]]

---

## Business Logic

The configurable rules that define system behavior.

Business logic belongs to the backend and should never be hardcoded into the frontend.

---

## C

## Component

A reusable frontend building block.

Examples:

- FormRenderer
- TreeNode
- PropertyGrid
- ChatView

Components should remain generic.

---

## Component Registry

Maps schema component identifiers to React components.

Unknown components should be rendered as unsupported rather than executed.

---

## Configuration

Settings that influence system behavior.

Kernschmied distinguishes between:

- infrastructure configuration
- runtime configuration

---

## Configuration Revision

A version number representing the current configuration state.

Used for:

- cache invalidation
- synchronization
- change tracking

---

## Contract

A stable interface between different parts of the system.

Examples:

- REST responses
- request schemas
- UI schemas
- manifests

Contracts should remain stable whenever possible.

---

## D

## Database

The persistent storage of Kernschmied.

Default:

- SQLite

Planned:

- PostgreSQL

---

## Dependency Injection

A design pattern used to provide services explicitly instead of relying on global state.

Benefits:

- testability
- modularity
- maintainability

---

## Deployment Profile

A predefined operating mode.

Profiles:

- development
- intranet
- internet

Each profile enforces different security requirements.

---

## E

## Endpoint

A REST API route exposed by FastAPI.

Examples:

```text
GET /bootstrap

GET /hierarchy

POST /chat

```

---

## F

## FastAPI

The backend web framework used by Kernschmied.

Responsible for:

- routing
- validation
- OpenAPI generation
- dependency injection

---

## Frontend

The client-side application.

Responsible for:

- rendering
- interaction
- local state

The frontend never implements business rules.

---

## G

## Generic Component

A reusable component without business-specific knowledge.

Preferred:

- TreeNode
- ListRenderer
- FormRenderer

Avoid:

- CustomerTree
- ProjectTree
- InvoicePage

---

## H

## Hierarchy

A generic tree structure representing configurable entities.

The hierarchy is completely schema-driven.

---

## Hierarchy Node

A single element within the hierarchy.

Each node contains:

- id
- type
- label
- children
- metadata

---

## I

## Infrastructure

Technical components required to operate the system.

Examples:

- database
- middleware
- authentication
- logging

Infrastructure is intentionally separated from business logic.

---

## M

## Manifest

A structured configuration document describing dynamically loadable resources.

Examples:

- model.json
- tool.json

---

## Model

An AI model that can be used by the system.

Models are registered explicitly through the Model Registry.

---

## Model Registry

The backend registry responsible for discovering and validating available AI models.

---

## O

## OpenAPI

Automatically generated API documentation provided by FastAPI.

Accessible via:

```text
/docs

/openapi.json

```

---

## P

## Plugin

An optional extension that adds functionality to Kernschmied.

Plugins must be:

- discovered
- validated
- explicitly enabled

---

## Prompt

Instructions sent to an AI model.

Prompt inheritance allows prompts to be composed from multiple hierarchy levels.

---

## Prompt Inheritance

A mechanism that combines prompts from different hierarchy levels according to configurable rules.

---

## R

## Registry

A controlled list of available components.

Examples:

- Model Registry
- Tool Registry
- Component Registry
- Action Registry

Registries prevent uncontrolled runtime behavior.

---

## Request ID

A unique identifier attached to requests for tracing and diagnostics.

---

## Runtime Configuration

Configuration stored in the database that can influence application behavior while the system is running.

---

## S

## Schema

A structured definition describing data or UI.

Examples:

- Pydantic schemas
- UI schemas
- manifests

Schemas are versioned.

---

## Schema Renderer

The frontend component responsible for rendering UI based entirely on backend-provided schemas.

---

## Security Profile

Defines the minimum security requirements for a deployment environment.

Profiles:

- Development
- Intranet
- Internet

---

## Server-Sent Events (SSE)

A streaming protocol used for chat responses.

Allows incremental message delivery from backend to frontend.

---

## Service

A backend class responsible for a well-defined responsibility.

Examples:

- ConfigService
- ChatService
- HierarchyService

---

## T

## Tool

A callable backend capability.

Examples:

- calculator
- search
- weather
- OCR

Tools must be explicitly registered.

---

## Tool Registry

Responsible for validating and exposing available backend tools.

---

## U

## UI Schema

A backend-generated description of how the frontend should render user interfaces.

Typical elements include:

- forms
- fields
- layouts
- actions
- validation rules

---

## V

## Validation

The process of verifying that data conforms to a defined schema.

Validation occurs at every system boundary.

---

## Versioned Schema

A schema that includes an explicit version identifier.

Breaking changes require a new schema version.

---

## W

## Workspace

A logical environment containing configuration, hierarchy, and associated resources.

The exact implementation depends on the project configuration.

---

## Related Pages

- [[Home]]
- [[Architecture]]
- [[Project-Principles]]
- [[Backend-Overview]]
- [[Frontend-Overview]]
- [[Schema-Renderer]]
- [[Model-Registry]]
- [[Tool-Registry]]

---

Zurück zu [[Home]].
