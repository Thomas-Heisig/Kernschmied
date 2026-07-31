# Backend Overview

The **Kernschmied Backend** is the central execution engine of the platform. It is responsible for processing requests, enforcing security, resolving runtime configuration, managing the application hierarchy, communicating with AI providers, executing tools, and exposing a stable HTTP API to the frontend.

The backend is intentionally designed as a **schema-driven**, **provider-independent**, and **modular** system. Business logic is isolated from infrastructure concerns, allowing new capabilities to be introduced through configuration, manifests, and registries rather than modifications to the application core.

The backend is implemented using **Python 3.12**, **FastAPI**, **Pydantic v2**, **SQLAlchemy Async**, and **Alembic**, following modern asynchronous programming practices.

---

# Goals

The backend architecture is designed to provide:

- Stable public APIs
- Modular services
- Provider independence
- Schema-driven behavior
- Runtime configuration
- Deterministic request processing
- Strong validation
- Secure execution
- Future extensibility

---

# Design Principles

The backend follows several architectural principles.

## Configuration over Hardcoding

Business behavior should be configurable whenever possible.

Examples include:

- prompts
- models
- tools
- hierarchy
- UI schemas
- permissions

Infrastructure remains implemented in code.

---

## Separation of Concerns

Each architectural layer has a clearly defined responsibility.

```text
API

↓

Services

↓

Registries

↓

Repositories

↓

Database / Providers
```

Responsibilities are never duplicated across layers.

---

## Provider Independence

Application services never communicate directly with AI providers.

Instead:

```text
Chat Service

↓

Model Registry

↓

Provider Interface

↓

Ollama / OpenAI / Future Providers
```

This abstraction enables multiple providers without changing business logic.

---

## Schema-Driven Architecture

The backend generates structured schemas describing:

- user interfaces
- forms
- hierarchy nodes
- configuration
- capabilities

The frontend interprets these schemas using trusted components.

---

# Technology Stack

The backend is built using:

| Technology         | Purpose                      |
| ------------------ | ---------------------------- |
| Python 3.12        | Programming language         |
| FastAPI            | HTTP framework               |
| Pydantic v2        | Validation and serialization |
| SQLAlchemy Async   | Database abstraction         |
| SQLite             | Default database             |
| PostgreSQL         | Future production database   |
| Alembic            | Database migrations          |
| Server-Sent Events | Chat streaming               |

---

# High-Level Architecture

```text
                Backend

                    │

        ┌───────────┼───────────┐

        │           │           │

      API       Services    Security

                    │

          Configuration

                    │

      Hierarchy  Registries

                    │

Repositories   Providers

                    │

               Database
```

Each subsystem communicates only through well-defined interfaces.

---

# Backend Responsibilities

The backend is responsible for:

- authentication
- authorization
- configuration management
- hierarchy management
- schema generation
- model management
- tool management
- prompt resolution
- AI communication
- audit logging
- validation
- streaming responses

The frontend is intentionally lightweight and delegates these responsibilities to the backend.

---

# HTTP API Layer

The API layer exposes REST and SSE endpoints.

Typical endpoints include:

| Endpoint         | Purpose               |
| ---------------- | --------------------- |
| `/bootstrap`     | Application bootstrap |
| `/ui/schema`     | UI schema             |
| `/hierarchy`     | Hierarchy data        |
| `/configuration` | Runtime configuration |
| `/models`        | Available models      |
| `/tools`         | Available tools       |
| `/chat/stream`   | Streaming chat        |
| `/health`        | Health information    |

Endpoints validate requests and delegate processing to services.

---

# Application Services

Services coordinate business logic.

Typical services include:

- Chat Service
- Configuration Service
- Hierarchy Service
- Prompt Service
- Bootstrap Service

Services orchestrate repositories, registries, and providers without containing infrastructure-specific code.

---

# Configuration System

Runtime configuration is stored in the database rather than in source code.

Configuration supports:

- inheritance
- validation
- versioning
- runtime updates
- audit logging

The Configuration Resolver computes the effective configuration for each request.

---

# Hierarchy System

The hierarchy represents the logical structure of the application.

Typical node types may include:

- organization
- department
- project
- workspace
- conversation
- user

The backend resolves inheritance and visibility before returning hierarchy information to the frontend.

---

# Prompt Resolution

AI prompts are assembled dynamically from multiple configuration scopes.

```text
System

↓

Hierarchy

↓

Project

↓

User

↓

Request

↓

Final Prompt
```

Prompt generation is deterministic and provider-independent.

---

# Model Management

Available AI models are managed through the Model Registry.

Responsibilities include:

- manifest loading
- validation
- capability reporting
- provider resolution

Services interact with the registry rather than provider implementations.

---

# Tool Management

Tools are managed through the Tool Registry.

Responsibilities include:

- manifest validation
- registration
- permission metadata
- runtime lookup

Tool execution is always mediated by the backend.

---

# Registry Layer

Registries provide stable runtime access to extensible components.

Current registries include:

- Model Registry
- Tool Registry

Future registries may manage plugins, workflows, or notification providers.

---

# Repository Layer

Repositories encapsulate persistence logic.

Responsibilities include:

- querying
- updates
- transactions
- persistence abstraction

Repositories are the only components that interact directly with the database.

---

# Database Layer

The backend currently uses SQLite by default.

Future deployments may use PostgreSQL without requiring architectural changes.

Database responsibilities include:

- configuration storage
- hierarchy
- audit logs
- conversations
- metadata

---

# Dependency Injection

FastAPI's dependency injection system provides shared infrastructure.

Typical injected dependencies include:

- database sessions
- authenticated users
- registries
- configuration resolvers
- request context

This reduces coupling and improves testability.

---

# Validation

Validation occurs at every system boundary.

Examples include:

- HTTP requests
- configuration updates
- manifests
- hierarchy data
- provider responses

Pydantic models define stable contracts for all public APIs.

---

# Streaming

Chat responses are delivered using Server-Sent Events (SSE).

Typical event flow:

```text
Request

↓

Provider

↓

Tokens

↓

SSE Events

↓

Frontend
```

Streaming is independent of the underlying AI provider.

---

# Security

The backend enforces all security decisions.

Responsibilities include:

- authentication
- authorization
- request validation
- permission evaluation
- audit logging

The frontend never bypasses these checks.

---

# Error Handling

Errors are returned using a structured format.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid request.",
  "details": {},
  "request_id": "abc123"
}
```

Internal implementation details remain hidden from clients.

---

# Runtime Configuration

Configuration marked as runtime editable may be modified without restarting the application.

Typical workflow:

```text
Configuration Update

↓

Validation

↓

Database

↓

Revision++

↓

Next Request Uses New Configuration
```

This enables dynamic system behavior while preserving stability.

---

# Caching

The backend uses revision-based caching for runtime data.

Typical cache targets include:

- configuration
- registries
- hierarchy
- UI schemas

Caches are invalidated whenever relevant revisions change.

---

# Extensibility

The backend is designed for controlled extensibility.

Supported extension mechanisms include:

- manifests
- registries
- providers
- configuration
- hierarchy
- schemas

New functionality should integrate through these mechanisms rather than modifying existing services.

---

# Testing

The backend architecture supports comprehensive testing.

Recommended test categories include:

- unit tests
- integration tests
- API tests
- provider tests
- registry tests
- configuration tests

Dependency injection simplifies test isolation.

---

# Performance

The backend is optimized for:

- asynchronous request handling
- non-blocking I/O
- efficient validation
- cached configuration
- fast registry lookups
- streaming responses

These optimizations allow the platform to scale from local development to enterprise deployments.

---

# Relationship to Other Architecture

The backend connects all major architectural subsystems.

```text
HTTP API

↓

Services

↓

Configuration

↓

Hierarchy

↓

Prompt Resolver

↓

Registries

↓

Repositories

↓

Providers

↓

Database
```

It forms the operational core of the Kernschmied platform.

---

# Related Documentation

## Backend

- [[API-Layer]]
- [[Services]]
- [[Dependency-Injection]]
- [[Configuration-Management]]
- [[Hierarchy-Management]]
- [[Prompt-Resolution]]
- [[Provider-System]]
- [[Database]]
- [[Validation]]
- [[Streaming]]

---

## Architecture

- [[Architecture]]
- [[Request-Lifecycle]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Registry-Architecture]]
- [[Security-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Hierarchy]]
- [[Models]]
- [[Tools]]

---

# Summary

The Kernschmied Backend provides the execution core of the platform by combining asynchronous request processing, schema-driven configuration, hierarchical context resolution, provider-independent AI integration, structured validation, and secure runtime management.

Through its layered architecture, stable public contracts, dependency injection, registries, repositories, and runtime configuration system, the backend remains modular, extensible, maintainable, and capable of supporting both local development and enterprise-scale deployments without requiring architectural redesign.

---

Back to [[Home]].
