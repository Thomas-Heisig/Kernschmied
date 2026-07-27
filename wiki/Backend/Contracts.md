# Backend Contracts

The **Backend Contracts** define the stable interfaces between the Kernschmied backend and every external consumer, including the frontend, AI providers, tools, plugins, automation systems, and future third-party integrations.

A contract specifies **what** information is exchanged, **how** it is structured, and **which guarantees** are provided regarding compatibility, validation, and versioning.

One of the primary architectural goals of Kernschmied is that **internal implementation details may change freely while public contracts remain stable**.

---

# Goals

The Backend Contract architecture is designed to provide:

- Stable public interfaces
- Independent frontend and backend evolution
- Strong validation
- Versioned schemas
- Predictable compatibility
- Deterministic serialization
- Extensible APIs
- Long-term maintainability

---

# Design Principles

## Stable Public Interfaces

Public contracts define the supported interface between components.

Application internals—including service implementations, repositories, provider integrations, and storage models—are **never** considered part of the public contract.

```text
Implementation

↓

Public Contract

↓

Consumer
```

Consumers depend only on the contract.

---

## Validation at System Boundaries

Every contract is validated whenever data enters or leaves the backend.

Validation occurs for:

- HTTP requests
- HTTP responses
- SSE events
- configuration updates
- manifests
- provider communication
- tool execution

No unvalidated data should enter the application core.

---

## Provider Independence

Public contracts never expose provider-specific implementations.

Instead of returning provider-specific objects, the backend returns generic models.

```text
Provider

↓

Internal Model

↓

Public Contract

↓

Frontend
```

This keeps clients independent of AI vendors.

---

# Contract Categories

The backend exposes several categories of contracts.

| Contract | Purpose |
|----------|---------|
| REST API | Request and response payloads |
| SSE | Streaming events |
| Bootstrap | Application metadata |
| Configuration | Runtime configuration |
| Hierarchy | Generic hierarchy |
| UI Schema | Schema-driven frontend |
| Models | Model metadata |
| Tools | Tool metadata |
| Errors | Structured error responses |

Each category evolves independently.

---

# High-Level Architecture

```text
Frontend

↓

HTTP / SSE

↓

Backend Contracts

↓

Application Services

↓

Repositories / Providers
```

Contracts isolate consumers from implementation details.

---

# Request Contracts

Request contracts define the structure of incoming data.

Typical characteristics include:

- required fields
- optional fields
- value constraints
- identifiers
- supported schema versions

Requests are validated before processing.

---

# Response Contracts

Response contracts define the data returned to clients.

Responses should be:

- deterministic
- self-describing
- version compatible
- provider independent

Clients should never rely on undocumented fields.

---

# JSON Serialization

REST contracts use JSON.

Example:

```json
{
  "id": "chat-001",
  "status": "ready"
}
```

Serialization follows Pydantic models to ensure consistency.

---

# Streaming Contracts

Streaming responses use Server-Sent Events.

Typical event types include:

```text
start

↓

token

↓

tool_call

↓

tool_result

↓

message

↓

usage

↓

complete
```

Each event follows a documented schema.

---

# Bootstrap Contract

The Bootstrap contract provides application metadata.

Typical information includes:

- application version
- deployment profile
- capabilities
- endpoints
- revisions
- supported schema versions

Bootstrap is usually the first contract consumed by the frontend.

---

# Configuration Contract

Configuration contracts expose runtime configuration through stable schemas.

Configuration contracts include:

- scope
- values
- revision
- schema version

Internal storage details remain hidden.

---

# Hierarchy Contract

Hierarchy contracts expose the generic node structure.

Typical fields include:

- identifier
- parent
- node type
- schema
- metadata

Clients interpret hierarchy generically rather than relying on hardcoded node types.

---

# UI Schema Contract

The UI Schema contract defines the structure of the dynamic frontend.

Typical information includes:

- layouts
- components
- actions
- properties
- children

The frontend maps schema definitions to trusted React components.

---

# Model Contract

Model contracts expose available AI models.

Typical metadata includes:

- identifier
- display name
- capabilities
- provider
- context length

Provider-specific APIs remain hidden.

---

# Tool Contract

Tool contracts describe executable tools.

Typical information includes:

- identifier
- description
- permissions
- input schema
- output schema

Execution details remain internal.

---

# Error Contract

Every error follows the same structure.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid request.",
  "details": {},
  "request_id": "91d8f5a2"
}
```

Clients should process errors using the documented fields rather than HTTP status codes alone.

---

# Versioning

Every contract category has its own version.

```text
Application

↓

Bootstrap v2

↓

UI Schema v3

↓

API v1

↓

SSE v2
```

Independent versioning allows individual contracts to evolve without forcing unrelated changes.

---

# Backward Compatibility

Contracts evolve using additive changes whenever possible.

Preferred evolution strategies include:

- adding optional fields
- introducing new event types
- extending metadata

Existing fields should not change semantics.

---

# Breaking Changes

Breaking changes require explicit version updates.

Examples include:

- removing required fields
- changing data types
- modifying event semantics
- altering identifier formats

Clients can determine compatibility using version metadata.

---

# Optional Fields

Optional properties allow gradual evolution.

Example:

```json
{
  "id": "chat-001",
  "title": "Architecture Discussion"
}
```

Older clients ignore unknown optional fields.

---

# Unknown Fields

Consumers should ignore unknown fields unless explicitly documented otherwise.

This approach supports forward compatibility between different application versions.

---

# Contract Validation

Contracts are validated using Pydantic.

Validation includes:

- required properties
- supported values
- enumerations
- nested objects
- schema versions

Validation occurs automatically at API boundaries.

---

# Internal Models vs Public Contracts

Internal application models are not public contracts.

```text
Database Model

↓

Domain Model

↓

API Model

↓

JSON
```

Changes to internal models do not necessarily affect public APIs.

---

# Dependency Injection

Application services receive validated contract models through dependency injection.

Endpoints should never manipulate raw request payloads directly.

---

# Security

Contracts never expose:

- database schemas
- provider internals
- filesystem paths
- implementation classes
- confidential configuration

Only documented information is returned.

---

# Testing

Contract stability should be verified through automated testing.

Recommended tests include:

- serialization tests
- validation tests
- backward compatibility tests
- API integration tests
- SSE event validation

Stable contracts are critical for frontend compatibility.

---

# Documentation

Every public contract should be documented.

Documentation should include:

- purpose
- fields
- required properties
- optional properties
- examples
- version information

Documentation evolves together with the contract.

---

# Future Extensions

The contract architecture supports future additions including:

- plugin contracts
- workflow contracts
- automation contracts
- notification contracts
- localization contracts
- reporting contracts

New contracts should follow the same architectural principles.

---

# Relationship to Other Backend Components

Backend contracts connect every external interface to the application core.

```text
Client

↓

Contracts

↓

Application Services

↓

Repositories

↓

Providers
```

Contracts provide the stable boundary between consumers and implementation.

---

# Relationship to Architecture

Backend Contracts are closely related to:

- [[Contract-Versioning]]
- [[Request-Lifecycle]]
- [[Registry-Architecture]]
- [[Configuration-Architecture]]
- [[Security-Architecture]]

---

# Related Documentation

## Backend

- [[Backend-Overview]]
- [[Validation]]
- [[Streaming]]
- [[Provider-System]]
- [[API-Layer]]

---

## Architecture

- [[Contract-Versioning]]
- [[Request-Lifecycle]]
- [[Configuration-Architecture]]
- [[Registry-Architecture]]

---

## APIs

- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Hierarchy]]
- [[Models]]
- [[Tools]]
- [[Errors]]
- [[SSE]]
- [[UI-Schema]]

---

# Summary

The Backend Contracts define the stable, versioned interfaces that separate external consumers from the internal implementation of the Kernschmied backend.

By combining strict validation, provider-independent models, deterministic serialization, structured error handling, independent contract versioning, and comprehensive documentation, the contract architecture enables the backend, frontend, AI providers, and future integrations to evolve independently while preserving compatibility, security, and long-term maintainability.

---

Back to [[Home]].
