# Error Handling

The **Error Handling** architecture defines how failures are detected, classified, propagated, logged, and returned throughout the Kernschmied backend.

A consistent error model is essential for a modern, schema-driven application. Every component—from the HTTP API to configuration management, AI providers, tool execution, and database access—must report failures using predictable, structured, and versioned contracts.

Kernschmied intentionally separates **internal exceptions** from **public error responses**. Internal implementation details remain hidden while clients receive stable, machine-readable error information.

---

## Goals

The Error Handling architecture is designed to provide:

- Consistent error reporting
- Structured API responses
- Stable error contracts
- Deterministic behavior
- Secure exception handling
- Comprehensive logging
- Provider-independent failures
- Easy debugging
- Future extensibility

---

## Design Principles

## Fail Fast

Errors should be detected as early as possible.

Typical validation order:

```text
Incoming Request

↓

Authentication

↓

Authorization

↓

Validation

↓

Business Logic

↓

Persistence

```

Invalid requests should never reach deeper application layers.

---

## Internal Exceptions vs Public Errors

The backend distinguishes between internal exceptions and public API responses.

```text
Internal Exception

↓

Exception Handler

↓

Structured Error Response

↓

Client

```

Clients never receive stack traces or implementation details.

---

## Stable Error Contracts

Every public error follows the same contract.

Example:

```json
{
  "code": "validation_error",
  "message": "The request is invalid.",
  "details": {},
  "request_id": "d4af8192"
}
```

Clients should depend on the `code` field rather than parsing human-readable messages.

---

## Error Categories

Errors generally fall into several categories.

| Category       | Examples                       |
| -------------- | ------------------------------ |
| Validation     | Invalid request data           |
| Authentication | Missing credentials            |
| Authorization  | Insufficient permissions       |
| Configuration  | Invalid runtime configuration  |
| Registry       | Unknown model or tool          |
| Provider       | AI provider unavailable        |
| Database       | Persistence failure            |
| Network        | External communication failure |
| Internal       | Unexpected application error   |

Each category maps to appropriate HTTP status codes and structured error codes.

---

## High-Level Architecture

```text
Application Component

↓

Exception

↓

Global Exception Handler

↓

Structured Response

↓

Client

```

All unhandled exceptions eventually pass through the global exception handler.

---

## Validation Errors

Validation occurs at system boundaries.

Examples include:

- missing required fields
- unsupported enum values
- invalid identifiers
- malformed JSON
- schema violations

Validation errors are reported before business logic executes.

---

## Authentication Errors

Authentication errors occur when user identity cannot be established.

Typical situations include:

- missing credentials
- expired session
- invalid token
- unsupported authentication method

Authentication failures do not expose security-sensitive details.

---

## Authorization Errors

Authorization errors occur when an authenticated user lacks permission to perform an action.

Examples include:

- modifying protected configuration
- executing restricted tools
- accessing unauthorized hierarchy nodes

Authorization is enforced entirely on the backend.

---

## Configuration Errors

Configuration failures include:

- invalid configuration values
- missing configuration
- incompatible schema versions
- unresolved inheritance

Configuration errors prevent invalid runtime behavior.

---

## Registry Errors

Registry-related failures include:

- unknown model identifiers
- missing tool definitions
- duplicate registrations
- invalid manifests

Registries validate metadata before runtime use.

---

## Provider Errors

Provider failures originate from AI model backends.

Examples include:

- provider unavailable
- timeout
- unsupported capability
- communication failure
- malformed provider response

Provider-specific details remain internal.

---

## Tool Execution Errors

Tool execution may fail due to:

- invalid parameters
- authorization failure
- execution timeout
- unavailable resources
- internal tool exceptions

Tool failures are reported without exposing implementation internals.

---

## Database Errors

Database failures include:

- connection failures
- transaction errors
- constraint violations
- migration incompatibilities

Repositories translate persistence errors into application-level exceptions.

---

## Network Errors

Communication with external systems may fail.

Examples include:

- timeout
- unreachable endpoint
- DNS failure
- SSL errors
- connection reset

Network errors are handled independently of provider logic.

---

## Internal Errors

Unexpected failures are classified as internal errors.

Typical causes include:

- programming mistakes
- unexpected state
- unhandled exceptions
- infrastructure failures

Internal errors are logged in detail but exposed only through generic public responses.

---

## Exception Hierarchy

Application-specific exceptions should follow a clear hierarchy.

Example:

```text
ApplicationError

├── ValidationError
├── AuthorizationError
├── ConfigurationError
├── RegistryError
├── ProviderError
├── ToolError
├── DatabaseError
└── InternalError

```

A consistent hierarchy simplifies centralized exception handling.

---

## Global Exception Handler

The global exception handler converts exceptions into public responses.

Responsibilities include:

- mapping exceptions
- assigning HTTP status codes
- generating request identifiers
- logging failures
- producing structured JSON responses

This guarantees consistent client behavior.

---

## Structured Error Response

Every error response follows the same structure.

| Field        | Description                       |
| ------------ | --------------------------------- |
| `code`       | Machine-readable error identifier |
| `message`    | Human-readable description        |
| `details`    | Optional structured metadata      |
| `request_id` | Correlation identifier            |

Additional fields may be introduced through versioned contracts.

---

## HTTP Status Codes

Typical mappings include:

| Status | Meaning                     |
| ------ | --------------------------- |
| 400    | Validation error            |
| 401    | Authentication required     |
| 403    | Authorization denied        |
| 404    | Resource not found          |
| 409    | Conflict                    |
| 422    | Semantic validation failure |
| 500    | Internal server error       |
| 503    | Service unavailable         |

The response body provides more detailed information than the status code alone.

---

## Error Codes

Error codes remain stable across releases.

Examples include:

- `validation_error`
- `authentication_required`
- `permission_denied`
- `configuration_invalid`
- `model_not_found`
- `tool_not_found`
- `provider_unavailable`
- `database_error`
- `internal_error`

Clients should build logic around error codes rather than localized messages.

---

## Request Correlation

Every request receives a unique identifier.

```text
Incoming Request

↓

Request ID

↓

Logging

↓

Error Response

```

The request identifier simplifies diagnostics across distributed logs.

---

## Logging

Errors are logged using structured logging.

Typical log information includes:

- timestamp
- request identifier
- authenticated user
- endpoint
- exception type
- stack trace
- contextual metadata

Logging and public error responses intentionally expose different levels of detail.

---

## Error Propagation

Exceptions should propagate upward until they reach an appropriate handling layer.

```text
Repository

↓

Service

↓

API Layer

↓

Exception Handler

```

Lower layers should not generate HTTP responses directly.

---

## Retry Strategy

Some failures are transient.

Potential retry candidates include:

- temporary provider failures
- network interruptions
- rate limits
- database connection recovery

Retries should be controlled explicitly rather than applied indiscriminately.

---

## Streaming Errors

Errors occurring during Server-Sent Events are transmitted as structured SSE error events.

Example sequence:

```text
start

↓

token

↓

error

↓

complete

```

Clients should terminate stream processing after receiving a terminal error event.

---

## Security

Error handling must never reveal:

- stack traces
- SQL queries
- filesystem paths
- provider credentials
- internal configuration
- source code locations

Sensitive information remains confined to server logs.

---

## Testing

Error handling should be verified through automated tests.

Recommended coverage includes:

- validation failures
- authorization failures
- configuration errors
- registry failures
- provider failures
- database exceptions
- SSE error events
- global exception mapping

Consistent error behavior is part of the public API contract.

---

## Future Extensions

The architecture supports future enhancements including:

- localized error messages
- RFC 9457 Problem Details compatibility
- distributed tracing integration
- automatic diagnostics
- telemetry enrichment
- error analytics dashboards

These capabilities can be added while preserving existing error contracts.

---

## Relationship to Other Backend Components

Error handling spans every backend layer.

```text
HTTP API

↓

Application Services

↓

Repositories

↓

Providers

↓

Exception Handler

↓

Structured Response

```

It provides a unified mechanism for reporting failures throughout the system.

---

## Relationship to Architecture

Error Handling is closely related to:

- [[Request-Lifecycle]]
- [[Contract-Versioning]]
- [[Security-Architecture]]
- [[Configuration-Architecture]]
- [[Registry-Architecture]]

---

## Related Documentation

## Backend

- [[Backend-Overview]]
- [[Validation]]
- [[Configuration]]
- [[Streaming]]
- [[Repositories]]
- [[Provider-System]]

---

## Architecture

- [[Request-Lifecycle]]
- [[Contract-Versioning]]
- [[Security-Architecture]]
- [[Configuration-Architecture]]

---

## APIs

- [[Errors]]
- [[Chat]]
- [[Configuration]]
- [[Bootstrap]]
- [[SSE]]

---

## Summary

The Error Handling architecture provides a consistent and secure mechanism for detecting, classifying, logging, and exposing failures throughout the Kernschmied backend.

By separating internal exceptions from stable public error contracts, enforcing structured responses, maintaining deterministic error codes, centralizing exception handling, and integrating comprehensive logging and request correlation, the backend remains robust, secure, maintainable, and predictable for both users and client applications.

---

Back to [[Home]].
