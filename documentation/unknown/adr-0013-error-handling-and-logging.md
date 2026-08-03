# ADR-0013: Error Handling and Logging

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

## Context

Kernschmied consists of multiple independently evolving subsystems:

- REST API
- Server-Sent Events
- Model Providers
- Tool Providers
- Configuration Services
- Hierarchy Services
- Frontend
- Future Plugins

Failures may occur at every architectural layer.

Examples include:

- validation failures
- configuration errors
- provider timeouts
- tool failures
- network interruptions
- authentication failures
- database errors
- unexpected exceptions

Without a unified error architecture every subsystem would expose different error formats, making diagnostics, monitoring and client implementations unnecessarily complex.

---

## Problem

Traditional applications often return inconsistent errors.

Typical examples include:

- plain text responses
- HTML error pages
- uncaught exceptions
- provider-specific error objects
- missing request identifiers
- inconsistent HTTP status codes

These inconsistencies increase development effort and complicate monitoring.

---

## Decision

Kernschmied adopts a **structured error architecture**.

Every error returned to clients follows a common contract.

Unexpected exceptions are converted into structured application errors.

Logging is centralized and correlated using request identifiers.

---

## Architectural Principle

> Every failure should be observable.
>
> Every error should be understandable.
>
> Every request should be traceable.

---

## High-Level Architecture

```text
Request

        │

        ▼

Business Service

        │

        ▼

ApplicationError

        │

        ▼

Exception Handler

        │

        ▼

Structured Error Response

        │

        ▼

Client

```

---

## Design Goals

The error architecture should provide:

- predictable responses
- centralized handling
- correlation
- structured logging
- provider independence
- safe diagnostics
- user-friendly messages

---

## Error Categories

Errors are grouped into architectural categories.

Typical categories include:

- Validation
- Authentication
- Authorization
- Configuration
- Database
- Tool
- Model Provider
- Streaming
- Network
- Internal

---

## Structured Error Response

Every API endpoint returns the same structure.

Example:

```json
{
  "code": "validation_error",
  "message": "The request is invalid.",
  "details": {},
  "request_id": "6f3b7e1c"
}
```

---

## Error Fields

Every structured error contains:

| Field      | Purpose                            |
| ---------- | ---------------------------------- |
| code       | Stable machine-readable identifier |
| message    | Human-readable description         |
| details    | Additional structured information  |
| request_id | Correlation identifier             |

---

## Error Codes

Error codes remain stable across releases.

Examples:

```text
validation_error

configuration_error

tool_execution_failed

provider_timeout

permission_denied

resource_not_found

internal_error

```

Clients should rely on error codes rather than localized messages.

---

## HTTP Status Codes

Errors use standard HTTP status codes.

| Status | Meaning             |
| ------ | ------------------- |
| 400    | Bad Request         |
| 401    | Unauthorized        |
| 403    | Forbidden           |
| 404    | Not Found           |
| 409    | Conflict            |
| 422    | Validation Error    |
| 429    | Too Many Requests   |
| 500    | Internal Error      |
| 503    | Service Unavailable |

---

## Exception Hierarchy

Application exceptions derive from a common base type.

Typical hierarchy:

```text
ApplicationError

│

├── ValidationError

├── AuthenticationError

├── AuthorizationError

├── ConfigurationError

├── ToolError

├── ProviderError

├── DatabaseError

└── InternalError

```

Specialized services may define additional subclasses while preserving the common response contract.

---

## Validation Errors

Validation occurs before business logic executes.

Typical validation failures include:

- missing fields
- invalid types
- unsupported enum values
- malformed JSON
- schema violations

Validation errors return structured details describing invalid fields.

---

## Provider Errors

Model providers may fail because of:

- unavailable models
- network failures
- authentication problems
- unsupported capabilities
- malformed responses

Provider-specific exceptions are translated into platform-wide error codes.

---

## Tool Errors

Tools may fail because of:

- invalid input
- missing permissions
- unavailable resources
- execution failures
- external system errors

Tool-specific implementation details are not exposed to clients unless explicitly required.

---

## Database Errors

Database exceptions are converted into application errors.

Internal SQL details are never returned to clients.

Sensitive information remains inside server logs.

---

## Streaming Errors

Server-Sent Events use dedicated error events.

Example:

```text
event: error

data:
{
    "code":"provider_timeout",
    "message":"Generation timed out."
}

```

Streaming clients should terminate gracefully after receiving terminal error events.

---

## Request IDs

Every incoming request receives a unique request identifier.

```text
Incoming Request

↓

request_id

↓

Logs

↓

Error Response

↓

Support

```

The request identifier allows administrators to correlate logs, monitoring events and user reports.

---

## Logging Architecture

Logging follows a layered approach.

```text
Application

↓

Structured Logger

↓

Log Sink

↓

Storage

↓

Monitoring

```

Each layer adds context without changing log semantics.

---

## Log Levels

The platform uses consistent log levels.

| Level    | Purpose                 |
| -------- | ----------------------- |
| DEBUG    | Development diagnostics |
| INFO     | Normal operation        |
| WARNING  | Recoverable problems    |
| ERROR    | Failed operations       |
| CRITICAL | Severe system failures  |

Log levels should be used consistently across all modules.

---

## Structured Logging

Logs should contain structured fields whenever possible.

Typical fields include:

- timestamp
- request_id
- user_id
- component
- operation
- duration
- outcome

Structured logging simplifies automated analysis.

---

## Audit Logging

Audit logging is distinct from operational logging.

Audit records include:

- configuration changes
- authentication events
- permission changes
- administrative actions
- tool execution

Audit records are immutable.

---

## Frontend Error Handling

The frontend categorizes failures into:

- network errors
- validation errors
- streaming errors
- schema errors
- rendering errors
- unexpected failures

The user interface presents meaningful messages while preserving technical details for diagnostics.

---

## Error Presentation

User-facing messages should be:

- understandable
- actionable
- localized where appropriate
- independent from internal implementation

Internal exception details should not be displayed to end users.

---

## Retry Strategy

Only transient failures should be retried.

Typical retry candidates:

- temporary network failures
- provider timeouts
- transient database connection failures

Validation errors and authorization failures must never be retried automatically.

---

## Security Considerations

Error handling must never expose:

- stack traces
- SQL queries
- filesystem paths
- internal secrets
- authentication tokens

Unexpected exceptions are logged internally but sanitized before returning to clients.

---

## Performance Considerations

Logging should remain efficient.

Strategies include:

- asynchronous logging where appropriate
- structured log serialization
- configurable log levels
- minimal allocation during high-frequency operations

Diagnostic quality should not significantly reduce application throughput.

---

## Operational Impact

The logging architecture enables:

- centralized monitoring
- request tracing
- incident investigation
- operational dashboards
- alerting
- compliance auditing

Operations teams can investigate failures using request identifiers without reproducing user sessions.

---

## Consequences

## Positive

- Consistent error contracts
- Easier debugging
- Better monitoring
- Simplified client implementation
- Strong operational visibility
- Improved security

## Negative

- Additional infrastructure
- Exception mapping effort
- Structured logging overhead

---

## Alternatives Considered

## Returning Raw Exceptions

Rejected because implementation details would leak to clients.

---

## Provider-Specific Errors

Rejected because clients would need provider-specific handling.

---

## Plain Text Error Messages

Rejected because machine-readable error handling becomes impossible.

---

## Logging Only to Console

Rejected because enterprise deployments require centralized monitoring.

---

## Risks

Potential risks include:

- excessive logging
- missing request identifiers
- inconsistent error codes
- accidental disclosure of sensitive information

Mitigation includes:

- centralized exception handling
- structured logging
- security reviews
- automated testing
- standardized error contracts

---

## Implementation Notes

The implementation should provide:

- `ApplicationError`
- specialized exception hierarchy
- global exception handlers
- structured error responses
- request identifier middleware
- structured logging
- audit logging
- provider exception translation
- frontend error presentation

All components should participate in the same logging and error-handling architecture.

---

## Related Decisions

- [[ADR-0004-Security-Profiles]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0009-Authentication-and-Authorization]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

## Related Documentation

## Architecture

- [[Architecture]]
- [[Logging]]
- [[Monitoring]]

---

## Backend

- [[REST-API]]
- [[Streaming]]
- [[Configuration]]
- [[Tool-Registry]]
- [[Model-Registry]]

---

## Frontend

- [[API-Client]]
- [[Streaming]]
- [[State-Management]]

---

## Concepts

- [[Application-Errors]]
- [[Structured-Logging]]
- [[Audit-Log]]
- [[Request-IDs]]

---

## Decision Summary

Kernschmied adopts a **centralized error handling and structured logging architecture** in which every failure is translated into a consistent application-wide error contract.

Errors are categorized using stable machine-readable codes, correlated through unique request identifiers, logged using structured logging, and presented to clients without exposing sensitive implementation details.

This architecture provides predictable client behavior, improved diagnostics, operational transparency, and a secure foundation for monitoring, troubleshooting, and future enterprise deployments.

---

Back to [[Home]].
