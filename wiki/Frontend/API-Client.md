# API Client

> **Version:** 1.0  
> **Status:** Living Document  
> **Applies to:** Frontend

---

# Overview

The **API Client** is the single entry point for all communication between the Kernschmied frontend and backend.

No React component should communicate with the backend directly.

Instead, every request is routed through the API Client, which provides a consistent interface for:

- HTTP requests
- Authentication
- Error handling
- Response validation
- Streaming support
- Request cancellation
- Logging
- Future middleware

The API Client acts as the transport layer between the user interface and the backend services.

---

# Design Goals

The API Client is designed to provide:

- A single communication layer
- Strong typing
- Stable contracts
- Centralized error handling
- Request cancellation
- Consistent authentication
- Automatic serialization
- Easy testing
- Future extensibility

---

# Architecture

```text
React Component

        │

        ▼

Custom Hook

        │

        ▼

API Client

        │

        ▼

HTTP Request

        │

        ▼

FastAPI Backend

        │

        ▼

JSON / SSE Response

        │

        ▼

API Client

        │

        ▼

Hook

        │

        ▼

React Component
```

---

# Responsibilities

The API Client is responsible for:

- building requests
- sending requests
- parsing responses
- handling errors
- attaching authentication
- validating contracts
- supporting request cancellation
- exposing a typed API

The API Client is **not** responsible for:

- business logic
- permission decisions
- caching business rules
- rendering
- application state

---

# Design Principles

The API Client follows several architectural principles.

- Single entry point
- Backend authority
- Explicit contracts
- Strong typing
- Immutable request objects
- Predictable behavior
- Centralized configuration
- No hidden side effects

---

# Request Lifecycle

```text
Component

↓

Hook

↓

API Client

↓

Serialize Request

↓

HTTP

↓

Backend

↓

Deserialize Response

↓

Return Result
```

---

# HTTP Methods

The API Client supports the standard HTTP methods.

| Method | Purpose |
|----------|---------|
| GET | Read data |
| POST | Create resources |
| PUT | Replace resources |
| PATCH | Partial updates |
| DELETE | Remove resources |

---

# Example

Instead of:

```tsx
fetch("/api/models")
```

Components should use:

```tsx
api.get("/models")
```

or

```tsx
api.post("/chat", request)
```

The implementation details remain hidden.

---

# Base URL

The API Client manages the backend base URL centrally.

Example:

```text
/api
```

Changing the API prefix requires only one configuration change.

---

# Serialization

Requests are serialized automatically.

```text
TypeScript Object

↓

JSON

↓

HTTP Body
```

---

# Deserialization

Responses are converted into typed objects.

```text
JSON

↓

Validation

↓

Typed Object
```

---

# Type Safety

All public API methods should use TypeScript types.

Example:

```tsx
const hierarchy =
    await api.get<HierarchyTree>("/hierarchy");
```

Strong typing improves maintainability and IDE support.

---

# Error Handling

The backend returns structured errors.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid request.",
  "details": {},
  "request_id": "..."
}
```

The API Client converts these into typed frontend errors.

---

# Error Categories

Typical categories include:

- Validation
- Authentication
- Authorization
- Network
- Timeout
- Server
- Unknown

Each category should produce a consistent user experience.

---

# Request IDs

Every backend response may contain a request identifier.

Example:

```text
request_id

↓

Frontend

↓

Logs

↓

Support
```

Request IDs simplify troubleshooting.

---

# Authentication

Authentication headers are attached automatically.

Possible mechanisms include:

- Session cookies
- Bearer tokens
- Future SSO integration

Individual components never construct authentication headers manually.

---

# Authorization

Authorization is always performed by the backend.

The API Client only transports credentials.

---

# Request Cancellation

Long-running requests should be cancellable.

Example:

```text
User

↓

Cancel

↓

AbortController

↓

Request Aborted
```

This is especially important for AI generation.

---

# Streaming Support

Streaming requests use Server-Sent Events.

```text
API Client

↓

SSE Connection

↓

Events

↓

Streaming Hook

↓

UI
```

Streaming remains independent from standard REST requests.

---

# Response Validation

The API Client validates response structures whenever practical.

Invalid responses are rejected before reaching the UI.

This prevents undefined behavior caused by malformed data.

---

# Retry Strategy

The API Client may automatically retry transient failures.

Suitable examples:

- temporary network interruption
- gateway timeout
- service unavailable

Requests that modify data should never be retried automatically unless explicitly designed to be idempotent.

---

# Timeouts

Requests should use reasonable timeout values.

Timeouts prevent the application from waiting indefinitely for unavailable services.

---

# Configuration

Typical configuration includes:

- API base URL
- timeout
- retry policy
- authentication mode
- logging level

Configuration is centralized.

---

# Logging

The API Client may log:

- request duration
- endpoint
- status code
- request ID
- retry attempts

Sensitive information must never be logged.

---

# Hooks Integration

Components typically communicate through custom hooks.

```text
Component

↓

useHierarchy()

↓

API Client

↓

Backend
```

Hooks encapsulate data loading while the API Client focuses on transport.

---

# Security

The API Client must never:

- store secrets
- bypass authentication
- bypass authorization
- disable TLS validation
- expose internal errors

All security-sensitive decisions remain on the backend.

---

# Testing

Typical tests include:

- successful requests
- failed requests
- timeout handling
- cancellation
- authentication
- response validation
- retry behavior

Tests should mock backend responses rather than real servers.

---

# Future Evolution

The API Client is designed to support future capabilities such as:

- HTTP caching
- offline mode
- request batching
- GraphQL adapters
- WebSocket transport
- metrics collection
- distributed tracing

These additions should not require changes to application components.

---

# Best Practices

Recommended:

- One API Client
- Strong typing
- Centralized configuration
- Explicit request models
- Structured errors
- Abortable requests
- Thin transport layer

Avoid:

- Direct fetch calls inside components
- Duplicate HTTP code
- Hidden retries
- Business logic inside the client
- Global mutable request state

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Request-Lifecycle]]
- [[Contracts]]

---

## Frontend

- [[Frontend-Overview]]
- [[State-Management]]
- [[Streaming]]
- [[Routing]]
- [[Forms]]

---

## Backend

- [[Backend-Overview]]
- [[Error-Handling]]
- [[Configuration]]

---

## Concepts

- [[Runtime-Configuration]]
- [[Schema-Versioning]]
- [[Dynamic-UI]]

---

# Summary

The API Client provides the single, consistent communication layer between the Kernschmied frontend and backend.

By centralizing request handling, authentication, serialization, validation, and error processing, it keeps React components simple while ensuring reliable, secure, and maintainable communication with the platform.

Together with the Schema Renderer, State Management, and Streaming infrastructure, it forms one of the core building blocks of the Kernschmied frontend architecture.

---

Back to [[Home]].