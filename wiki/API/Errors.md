# Error Handling API

The Kernschmied platform uses a **single, consistent error contract** across all REST endpoints and streaming interfaces.

Rather than exposing framework-specific exceptions or provider-specific error messages, every failure is translated into a structured, machine-readable response that is stable across platform versions.

This enables clients to implement reliable error handling without depending on internal implementation details.

---

# Goals

The Error API is designed to provide:

- Stable error contracts
- Machine-readable error codes
- Human-readable messages
- Request tracing
- Structured validation details
- Provider independence
- Secure error reporting
- Consistent frontend behavior

---

# Design Principles

The error system follows several core principles.

## Stable Contracts

Applications should react to **error codes**, not text messages.

Messages may change over time.

Codes remain stable.

---

## Structured Responses

Every REST error follows the same JSON structure.

---

## Provider Independence

Internal exceptions from:

- FastAPI
- SQLAlchemy
- Ollama
- OpenAI
- Anthropic
- Python

are never exposed directly.

---

## Secure by Default

Internal implementation details must never leak to clients.

Examples include:

- stack traces
- SQL statements
- filesystem paths
- API keys
- environment variables

---

# Error Response Format

Every REST error follows the same structure.

```json
{
  "code": "validation_error",
  "message": "The request is invalid.",
  "details": {},
  "request_id": "4c6fd38b"
}
```

---

# Fields

| Field      | Description                        |
| ---------- | ---------------------------------- |
| code       | Stable machine-readable identifier |
| message    | Human-readable description         |
| details    | Optional structured information    |
| request_id | Unique request identifier          |

---

# Error Code

The `code` field is intended for application logic.

Example:

```json
{
  "code": "validation_error"
}
```

Frontend applications should never parse the message text.

---

# Message

The message explains the error for humans.

Example:

```json
{
  "message": "Hierarchy node was not found."
}
```

Messages may be localized in future versions.

---

# Details

Additional information may be supplied.

Example:

```json
{
  "details": {
    "field": "model_id"
  }
}
```

The structure depends on the error type.

---

# Request ID

Every request receives a unique identifier.

Example:

```json
{
  "request_id": "d9235b70"
}
```

This identifier simplifies diagnostics and support.

---

# HTTP Status Codes

Kernschmied follows standard HTTP semantics.

| Status | Meaning               |
| ------ | --------------------- |
| 400    | Bad Request           |
| 401    | Unauthorized          |
| 403    | Forbidden             |
| 404    | Not Found             |
| 409    | Conflict              |
| 422    | Validation Error      |
| 429    | Too Many Requests     |
| 500    | Internal Server Error |
| 503    | Service Unavailable   |

---

# Common Error Codes

Typical platform error codes include:

| Code                    | Description                     |
| ----------------------- | ------------------------------- |
| validation_error        | Invalid request                 |
| authentication_required | Authentication missing          |
| authorization_failed    | Permission denied               |
| resource_not_found      | Requested object does not exist |
| configuration_error     | Invalid configuration           |
| model_not_found         | Unknown model                   |
| tool_not_found          | Unknown tool                    |
| provider_timeout        | Provider timeout                |
| provider_unavailable    | Provider offline                |
| internal_error          | Unexpected server error         |

These codes are stable public contracts.

---

# Validation Errors

Validation failures return structured information.

Example:

```json
{
  "code": "validation_error",
  "message": "Validation failed.",
  "details": {
    "field": "temperature",
    "reason": "Value must be between 0 and 2."
  },
  "request_id": "2fd7d935"
}
```

---

# Authentication Errors

Example:

```json
{
  "code": "authentication_required",
  "message": "Authentication is required.",
  "details": {},
  "request_id": "34a7120d"
}
```

HTTP status:

```text
401 Unauthorized
```

---

# Authorization Errors

Example:

```json
{
  "code": "authorization_failed",
  "message": "Permission denied.",
  "details": {},
  "request_id": "5d2e847c"
}
```

HTTP status:

```text
403 Forbidden
```

---

# Not Found Errors

Example:

```json
{
  "code": "resource_not_found",
  "message": "Hierarchy node not found.",
  "details": {
    "id": "project-42"
  },
  "request_id": "9f871bd4"
}
```

---

# Provider Errors

Provider-specific failures are normalized.

Example:

```json
{
  "code": "provider_timeout",
  "message": "The selected model did not respond in time.",
  "details": {},
  "request_id": "b15c9217"
}
```

Clients never receive provider-specific exception names.

---

# Configuration Errors

Example:

```json
{
  "code": "configuration_error",
  "message": "Configuration is invalid.",
  "details": {
    "key": "default_model"
  },
  "request_id": "a7b42d19"
}
```

---

# Internal Errors

Unexpected failures are converted into a generic response.

Example:

```json
{
  "code": "internal_error",
  "message": "An unexpected error occurred.",
  "details": {},
  "request_id": "8ef92db4"
}
```

Implementation details are intentionally omitted.

---

# Streaming Errors

Streaming endpoints use Server-Sent Events (SSE).

Failures are transmitted as structured events.

Example:

```text
event:error

data:
{
    "code":"provider_timeout",
    "message":"Generation timed out."
}
```

After an error event the stream terminates.

---

# Validation Pipeline

```text
Incoming Request

↓

Pydantic Validation

↓

Business Validation

↓

Authorization

↓

Execution

↓

Structured Response
```

Errors can occur at every stage.

---

# Exception Translation

Internal exceptions are translated before leaving the backend.

```text
Python Exception

↓

Platform Exception

↓

REST Error

↓

JSON Response
```

This keeps the public API independent from implementation details.

---

# Logging

Errors are logged internally with additional diagnostic information.

Typical log entries include:

- timestamp
- request id
- user
- endpoint
- exception type
- stack trace
- provider information

Only safe information is returned to clients.

---

# Audit Logging

Administrative failures may also generate audit events.

Examples include:

- permission failures
- configuration updates
- authentication failures
- administrative operations

---

# Security Considerations

Error responses must never reveal:

- passwords
- API keys
- SQL statements
- filesystem paths
- internal class names
- stack traces
- provider credentials

Security always takes precedence over diagnostic detail.

---

# Client Recommendations

Clients should:

- use the `code` field for logic
- display the `message` to users
- include the `request_id` in bug reports
- ignore unknown fields
- gracefully handle unknown error codes

---

# Versioning

The error contract is part of the public API.

New fields may be added without breaking compatibility.

Existing fields retain their semantics.

---

# Performance Considerations

Error generation should remain lightweight.

The platform avoids:

- expensive exception formatting
- unnecessary serialization
- repeated validation
- large payloads

---

# Related APIs

- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Streaming]]

---

# Related Documentation

- [[REST-API]]
- [[Architecture]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0013-Error-Handling-and-Logging]]

---

# Summary

The Kernschmied Error API provides a consistent, secure, and provider-independent error contract for both REST and streaming interfaces.

By exposing stable error codes, structured validation details, and request identifiers while hiding internal implementation details, the platform enables robust client applications, simplifies diagnostics, and supports long-term API compatibility across all deployment profiles and provider implementations.

---

Back to [[Home]].
