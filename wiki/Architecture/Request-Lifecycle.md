# Request Lifecycle

The **Request Lifecycle** describes how a request flows through the Kernschmied platform, from the moment it is received until a response is returned to the client.

Understanding this lifecycle is essential because Kernschmied is intentionally built as a layered, schema-driven, and provider-independent platform. Every request follows the same architectural pipeline regardless of whether it targets configuration, hierarchy, model discovery, or AI chat generation.

The Request Lifecycle ensures that every request is:

- validated
- authenticated
- authorized
- resolved
- executed
- audited
- returned using stable contracts

---

# Goals

The Request Lifecycle is designed to provide:

- Deterministic request processing
- Clear separation of concerns
- Centralized validation
- Consistent authorization
- Stable API contracts
- Provider independence
- Structured error handling
- Complete auditability

---

# High-Level Overview

Every incoming request passes through the same major processing stages.

```text
Client

↓

HTTP Request

↓

Middleware

↓

Authentication

↓

Authorization

↓

API Endpoint

↓

Application Service

↓

Configuration Resolution

↓

Business Logic

↓

Repositories / Registries / Providers

↓

Response

↓

Client
```

Each stage has a clearly defined responsibility.

---

# Request Categories

The lifecycle applies to all request types, including:

- Bootstrap
- Configuration
- Hierarchy
- Model Registry
- Tool Registry
- Chat Streaming
- Health Checks

Although internal execution differs, the overall architecture remains consistent.

---

# HTTP Layer

Every request begins with an HTTP request to the FastAPI application.

Typical protocols include:

- REST
- Server-Sent Events (SSE)

Example:

```text
Browser

↓

HTTPS

↓

FastAPI
```

---

# Middleware Processing

Before a request reaches an API endpoint, it passes through middleware.

Typical middleware responsibilities include:

- request ID generation
- logging
- CORS
- HTTPS enforcement
- compression
- security headers
- exception handling

Middleware remains independent of business logic.

---

# Request Identification

Every request receives a unique identifier.

Example:

```text
request_id

↓

2ab8b53d
```

The identifier is included in:

- logs
- audit entries
- error responses

This enables end-to-end traceability.

---

# Authentication

Authentication verifies the identity of the caller.

Possible authentication mechanisms include:

- Development identity
- Session authentication
- OAuth2
- OpenID Connect
- LDAP
- Active Directory

Unauthenticated requests are rejected before business logic executes.

---

# Authorization

After authentication, authorization determines whether the request is permitted.

Authorization evaluates:

- user permissions
- resource ownership
- hierarchy visibility
- deployment policies

Authorization is always enforced server-side.

---

# Dependency Injection

FastAPI resolves required dependencies before entering the endpoint.

Typical dependencies include:

- database session
- configuration resolver
- registries
- authenticated user
- request context

Services never construct these dependencies manually.

---

# API Endpoint

API endpoints provide the public interface of the platform.

Responsibilities include:

- request validation
- dependency resolution
- response conversion
- status code selection

Endpoints contain minimal business logic.

---

# Request Validation

Incoming data is validated using Pydantic models.

Validation includes:

- required fields
- data types
- value ranges
- schema compatibility
- identifiers

Invalid requests return structured validation errors.

---

# Application Services

After validation, the endpoint delegates processing to an application service.

```text
API

↓

Chat Service
```

or

```text
API

↓

Configuration Service
```

Services coordinate the remaining processing pipeline.

---

# Configuration Resolution

Many services require runtime configuration.

The Configuration Resolver builds the effective configuration.

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

Resolved Configuration
```

Configuration resolution is deterministic.

---

# Hierarchy Resolution

Requests associated with hierarchy nodes trigger hierarchy resolution.

The resolver determines:

- active node
- inherited configuration
- prompt context
- visibility rules

This step is skipped for requests that do not use hierarchy data.

---

# Prompt Resolution

Chat requests additionally invoke the Prompt Resolver.

```text
Hierarchy

↓

Prompt Fragments

↓

Merge

↓

Final Prompt
```

The resulting prompt is provider-independent.

---

# Registry Lookup

Application services use registries to locate runtime components.

Examples:

```text
Model ID

↓

Model Registry

↓

Provider
```

```text
Tool ID

↓

Tool Registry

↓

Tool
```

Services never access manifests directly.

---

# Repository Access

Persistence is performed exclusively through repositories.

```text
Service

↓

Repository

↓

Database
```

Repositories encapsulate all database operations.

---

# Provider Invocation

Chat requests eventually invoke a model provider.

```text
Prompt

↓

Provider

↓

Model

↓

Response
```

The provider abstraction hides implementation-specific details.

---

# Tool Execution

If tools are enabled, the request may invoke one or more tools.

Typical flow:

```text
Model

↓

Tool Call

↓

Tool Registry

↓

Tool Execution

↓

Tool Result

↓

Model
```

Only authorized tools may execute.

---

# Response Construction

After business logic completes, the service returns a structured result.

The endpoint converts this into the public API contract.

Example:

```text
Business Result

↓

API Response

↓

JSON
```

---

# Streaming Requests

Streaming requests use Server-Sent Events instead of a single JSON response.

Lifecycle:

```text
Client

↓

Chat Endpoint

↓

Provider

↓

SSE Events

↓

Client
```

Streaming remains active until completion or error.

---

# Error Handling

Errors are translated into structured responses.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid request.",
  "details": {},
  "request_id": "2ab8b53d"
}
```

The request identifier allows correlation with server logs.

---

# Audit Logging

Sensitive operations generate audit events.

Typical audit information includes:

- user
- timestamp
- action
- resource
- request ID

Audit logging occurs independently of normal application logging.

---

# Response Delivery

The completed response is returned to the client.

Possible response types:

- JSON
- SSE stream
- HTTP error

The response always follows the documented public contract.

---

# Lifecycle Diagram

```text
Client

↓

Middleware

↓

Authentication

↓

Authorization

↓

Validation

↓

Endpoint

↓

Application Service

↓

Configuration Resolver

↓

Hierarchy Resolver

↓

Prompt Resolver

↓

Registry

↓

Repository / Provider

↓

Response

↓

Client
```

This sequence is representative of a typical chat request.

---

# Caching

Several stages may use caching.

Examples:

- configuration
- hierarchy
- registries
- prompt fragments

Caches are invalidated using revision numbers.

---

# Failure Handling

Failures terminate processing immediately.

```text
Validation Error

↓

Structured Error

↓

Client
```

Subsequent stages are not executed.

---

# Security Considerations

Every request is processed within strict security boundaries.

Security checks include:

- authentication
- authorization
- configuration validation
- hierarchy visibility
- provider permissions
- tool permissions

The frontend never bypasses these checks.

---

# Performance Considerations

The lifecycle is optimized for:

- minimal allocations
- dependency reuse
- cached configuration
- fast registry lookup
- asynchronous database access
- asynchronous provider communication

These optimizations keep request latency low while preserving deterministic behavior.

---

# Relationship to Other Architecture

The Request Lifecycle integrates nearly every architectural subsystem.

```text
HTTP Request

↓

Security

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

HTTP Response
```

It serves as the operational backbone of the platform.

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[C4-Container]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Prompt-Inheritance]]
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
- [[Errors]]

---

## Frontend

- [[API-Client]]
- [[Streaming]]
- [[State-Management]]

---

## ADRs

- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0011-Hierarchy-and-Prompt-Inheritance]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

The Request Lifecycle defines the complete processing pipeline for every request handled by the Kernschmied platform.

By combining middleware, authentication, authorization, dependency injection, configuration resolution, hierarchy traversal, prompt composition, registry lookups, repository access, provider abstraction, and structured response generation into a deterministic sequence, Kernschmied achieves a consistent, secure, maintainable, and extensible execution model that applies uniformly across all APIs and runtime services.

---

Back to [[Home]].
