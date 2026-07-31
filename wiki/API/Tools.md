# Tools API

The Tools API provides a provider-independent view of all tools available within the Kernschmied platform.

Tools extend the capabilities of language models by enabling controlled interaction with external systems such as calculators, databases, file systems, web services, or custom business logic.

Rather than exposing implementation details, the Tools API presents validated tool metadata managed by the **Tool Registry**. Models never access tools directly—they request tool execution through the backend, which performs validation, authorization, and execution.

---

# Goals

The Tools API is designed to provide:

- Provider-independent tool discovery
- Stable REST contracts
- Runtime tool availability
- Capability reporting
- Administrative visibility
- Secure execution
- Schema-driven integration
- Future extensibility

---

# Endpoints

## List Tools

```http
GET /api/v1/tools
```

Returns all available tools.

---

## Get Tool

```http
GET /api/v1/tools/{tool_id}
```

Returns metadata for a single tool.

---

## Future Endpoints

Potential future additions include:

```http
POST /api/v1/tools/refresh

GET /api/v1/tools/categories

GET /api/v1/tools/capabilities

GET /api/v1/tools/permissions

POST /api/v1/tools/validate
```

---

# Architecture

```text
REST API

        │

        ▼

Tool Registry

        │

        ▼

Tool Factory Registry

        │

        ▼

Tool Implementation

        │

        ▼

External Resource
```

Business services never communicate directly with tool implementations.

---

# Registry-Based Design

The Tool Registry is responsible for:

- tool discovery
- manifest validation
- registration
- capability reporting
- runtime availability
- health monitoring

Every executable tool must be registered before it can be used.

---

# Tool Manifest

Each tool is described by a validated manifest.

Example:

```text
tool.json
```

Typical manifest fields include:

- id
- name
- description
- category
- version
- permissions
- input_schema
- output_schema
- capabilities
- visibility

The manifest is validated before the tool becomes available.

---

# Example Response

```json
[
  {
    "id": "calculator",
    "name": "Calculator",
    "description": "Evaluates mathematical expressions.",
    "category": "utility",
    "capabilities": ["expression_evaluation"],
    "available": true
  }
]
```

The response intentionally contains metadata only.

---

# Tool Fields

| Field        | Description            |
| ------------ | ---------------------- |
| id           | Stable tool identifier |
| name         | Human-readable name    |
| description  | Functional description |
| category     | Tool category          |
| capabilities | Supported operations   |
| available    | Runtime availability   |

Future versions may add additional metadata without breaking compatibility.

---

# Tool Identifier

Each tool has a globally unique identifier.

Example:

```text
calculator
```

The identifier is used throughout the platform:

- Chat API
- Tool Registry
- Configuration
- Permissions
- Audit Log

Identifiers should remain stable.

---

# Categories

Tools may be grouped into logical categories.

Examples include:

- utility
- filesystem
- search
- communication
- document
- administration
- integration

Categories are informational and may evolve over time.

---

# Capabilities

Tools advertise their supported capabilities.

Examples include:

- expression_evaluation
- file_read
- file_write
- web_search
- email
- image_processing
- document_generation

Capability information assists administration interfaces and future automation.

---

# Availability

Availability indicates whether the tool can currently be executed.

Example:

```json
{
  "available": true
}
```

Typical runtime states include:

- available
- unavailable
- disabled
- degraded (future)

Unavailable tools are omitted from execution but may remain visible for administration.

---

# Tool Discovery

During startup the Tool Registry discovers available tools.

```text
Application Startup

↓

Tool Discovery

↓

Manifest Validation

↓

Registry

↓

Tools API
```

Only validated tools are registered.

---

# Tool Execution

The Tools API is informational.

Actual execution occurs through the Chat API.

Typical execution flow:

```text
Model

↓

tool_call

↓

Tool Registry

↓

Permission Check

↓

Validation

↓

Execution

↓

tool_result
```

Frontend applications never invoke tool implementations directly.

---

# Tool Factory Registry

Tool implementations are instantiated through the Tool Factory Registry.

Responsibilities include:

- dependency injection
- lifecycle management
- validation
- instance creation

This keeps execution independent from registration.

---

# Permissions

Every tool defines the permissions required for execution.

Examples include:

- filesystem.read
- filesystem.write
- calculator.execute
- web.search
- configuration.read

Permission checks are always performed server-side.

---

# Validation

Tool execution includes multiple validation stages.

```text
Tool Request

↓

Schema Validation

↓

Permission Validation

↓

Configuration Validation

↓

Execution
```

Invalid tool requests never reach tool implementations.

---

# Input and Output Schemas

Every tool exposes structured contracts.

Input schemas validate incoming arguments.

Output schemas define the structure of returned data.

This enables:

- frontend validation
- documentation
- tooling
- future automation

---

# Runtime Refresh

Future versions may allow refreshing the registry without restarting the application.

Typical workflow:

```text
Administrator

↓

Refresh Registry

↓

Validate

↓

Update Registry

↓

Revision++
```

The Bootstrap API exposes the registry revision for cache invalidation.

---

# Health Information

Future versions may expose tool health information.

Examples:

- available
- disabled
- degraded
- maintenance

Health reporting remains independent from implementation details.

---

# Authentication

Reading tool metadata depends on the active deployment profile.

Administrative operations always require authentication.

---

# Authorization

Typical permissions include:

- tools.read
- tools.manage
- tools.refresh

Tool execution permissions are evaluated independently.

The backend always remains the authoritative decision maker.

---

# Error Responses

Errors follow the standard platform contract.

Example:

```json
{
  "code": "tool_not_found",
  "message": "The requested tool does not exist.",
  "details": {
    "tool_id": "unknown-tool"
  },
  "request_id": "7fa92d4c"
}
```

---

# Versioning

The Tools API follows the REST API version.

```text
/api/v1/tools
```

The Tool Registry version is published through the Bootstrap API.

Clients should invalidate cached tool information whenever the registry revision changes.

---

# Performance Considerations

The Tools API is optimized through:

- registry caching
- immutable snapshots
- revision tracking
- asynchronous initialization
- manifest validation during startup

Tool discovery should not occur during normal request processing.

---

# Security Considerations

The Tools API never exposes:

- implementation classes
- filesystem locations
- credentials
- secret configuration
- internal execution details

Tool execution always remains under backend control.

Models cannot execute arbitrary code or bypass permission checks.

---

# Frontend Integration

The frontend retrieves available tools during initialization.

Typical workflow:

```text
Bootstrap

↓

GET /tools

↓

Tool Selection

↓

Chat View

↓

Tool Execution via Chat API
```

The frontend displays tool metadata only.

Execution requests are always routed through the Chat API.

---

# Relationship to the Chat API

The Tools API provides **discovery**.

The Chat API provides **execution**.

```text
Tools API

↓

Available Tools

↓

Chat Request

↓

Tool Registry

↓

Execution
```

This separation keeps both APIs focused and simplifies long-term maintenance.

---

# Related APIs

```http
GET /api/v1/bootstrap

GET /api/v1/models

GET /api/v1/config

POST /api/v1/chat/stream
```

---

# Related Documentation

- [[Architecture]]
- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Model-Registry]]
- [[Tool-Registry]]
- [[ADR-0003-Registries]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

The Tools API provides a stable, provider-independent catalog of all tools available within the Kernschmied platform.

By exposing validated tool metadata, capabilities, availability, and registry information through a unified REST interface while delegating execution to the Chat API and Tool Registry, the platform ensures secure, extensible, and maintainable tool integration without coupling clients or business services to individual implementations.

---

Back to [[Home]].
