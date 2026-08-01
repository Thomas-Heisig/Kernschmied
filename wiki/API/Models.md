# Models API

The Models API provides a provider-independent view of all language models available to the Kernschmied platform.

Rather than exposing provider-specific APIs or SDKs, the Models API presents a unified catalog of validated models that can be used by chat sessions, tools, administration interfaces, and future plugins.

The API is backed by the **Model Registry**, which discovers, validates, and manages models from one or more providers.

---

## Goals

The Models API is designed to provide:

- Provider-independent model discovery
- Stable REST contracts
- Runtime model availability
- Capability reporting
- Model metadata
- Health information
- Administrative visibility
- Future extensibility

---

## Endpoints

## List Models

```http
GET /api/v1/models
```

Returns all available models.

---

## Get Model

```http
GET /api/v1/models/{model_id}
```

Returns metadata for a single model.

---

## Future Endpoints

Potential future additions include:

```http
POST /api/v1/models/refresh

GET /api/v1/models/providers

GET /api/v1/models/capabilities

GET /api/v1/models/default

POST /api/v1/models/validate
```

---

## Architecture

```text
REST API

        │

        ▼

Model Registry

        │

        ▼

Provider Registry

        │

        ▼

Model Backend

        │

        ▼

LLM Provider

```

The REST API never communicates directly with provider implementations.

---

## Registry-Based Design

The Models API is backed by the **Model Registry**.

The registry is responsible for:

- model discovery
- manifest validation
- provider resolution
- capability reporting
- availability tracking
- health monitoring

Business services consume the registry instead of provider-specific APIs.

---

## Model Manifest

Each model is defined by a validated manifest.

Example:

```text
model.json

```

Typical manifest fields include:

- id
- provider
- model
- display_name
- description
- capabilities
- context_length
- default_parameters
- visibility

The manifest is validated before registration.

---

## Example Response

```json
[
  {
    "id": "qwen2.5-coder:7b",
    "display_name": "Qwen 2.5 7B",
    "provider": "ollama",
    "capabilities": ["chat", "streaming", "tool_calling"],
    "context_length": 32768,
    "available": true
  }
]
```

The exact schema may evolve through versioned contracts.

---

## Model Fields

| Field          | Description               |
| -------------- | ------------------------- |
| id             | Stable model identifier   |
| display_name   | Human-readable name       |
| provider       | Provider identifier       |
| capabilities   | Supported features        |
| context_length | Maximum supported context |
| available      | Runtime availability      |

Additional metadata may be added without breaking compatibility.

---

## Model Identifier

Every model has a unique identifier.

Example:

```text
qwen2.5-coder:7b

```

The identifier is used throughout the platform:

- Chat API
- Configuration
- Hierarchy defaults
- Administration
- Plugins

Identifiers remain stable whenever possible.

---

## Display Name

The display name is intended for user interfaces.

Example:

```text
Qwen 2.5 7B

```

Unlike the identifier, display names may change without affecting compatibility.

---

## Provider

Each model belongs to exactly one provider.

Examples:

- ollama
- llama_cpp
- openai
- anthropic
- gemini
- azure_openai

Clients should treat provider information as descriptive rather than executable.

---

## Capabilities

Models advertise supported capabilities.

Typical capabilities include:

- chat
- streaming
- tool_calling
- reasoning
- vision
- embeddings
- structured_output

Clients may adapt their behavior based on supported capabilities.

---

## Context Length

The context length describes the maximum supported token window.

Example:

```json
{
  "context_length": 32768
}
```

Applications should not exceed this limit.

---

## Availability

Availability indicates whether the model can currently be used.

Example:

```json
{
  "available": true
}
```

Possible states include:

- available
- unavailable
- loading
- degraded (future)

---

## Model Discovery

During startup the Model Registry discovers available models.

```text
Application Startup

↓

Provider Registry

↓

Provider Discovery

↓

Manifest Validation

↓

Model Registry

↓

Models API

```

Only validated models become visible.

---

## Model Selection

The Models API is informational.

Actual model selection occurs during chat execution.

Typical flow:

```text
Chat Request

↓

Requested Model

↓

Model Registry

↓

Provider Resolution

↓

Generation

```

---

## Default Model

The default model is determined through configuration.

```text
Configuration

↓

Model Registry

↓

Default Model

```

The Models API reports available models, not configuration decisions.

---

## Runtime Refresh

Future versions may support refreshing the registry without restarting the application.

Example:

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

---

## Health Information

Future versions may expose provider health.

Typical information:

- online
- offline
- loading
- degraded
- maintenance

Health reporting remains provider-independent.

---

## Authentication

Reading model metadata generally requires authentication depending on the deployment profile.

Administrative operations always require elevated permissions.

---

## Authorization

Typical permissions include:

- models.read
- models.refresh
- models.manage

The backend always performs authorization checks.

---

## Validation

The registry validates:

- manifest schema
- provider existence
- unique identifiers
- capability definitions
- required metadata

Invalid models are rejected before registration.

---

## Error Responses

Errors follow the standard platform contract.

Example:

```json
{
  "code": "model_not_found",
  "message": "The requested model does not exist.",
  "details": {
    "model_id": "unknown-model"
  },
  "request_id": "62e41a9f"
}
```

---

## Versioning

The Models API follows the REST API version.

```text
/api/v1/models

```

The registry version is published separately through the Bootstrap API.

Clients may invalidate cached model information whenever the model registry revision changes.

---

## Performance Considerations

The Models API is optimized through:

- registry caching
- immutable snapshots
- revision tracking
- provider abstraction
- asynchronous provider initialization

Model discovery should not occur for every request.

---

## Security Considerations

The Models API never exposes:

- provider credentials
- API keys
- authentication tokens
- internal network addresses
- provider implementation details

Only safe metadata is returned.

---

## Frontend Integration

The frontend typically retrieves available models during application startup.

Typical workflow:

```text
Bootstrap

↓

GET /models

↓

Model Selector

↓

Chat View

↓

User Selection

```

The frontend should rely on model identifiers rather than provider-specific information.

---

## Relationship to the Chat API

The Models API is responsible for **discovery**.

The Chat API is responsible for **execution**.

```text
Models API

↓

Available Models

↓

User Selection

↓

Chat API

↓

Generation

```

This separation keeps both APIs focused and simplifies long-term evolution.

---

## Related APIs

```http
GET /api/v1/bootstrap

GET /api/v1/config

POST /api/v1/chat/stream

GET /api/v1/tools
```

---

## Related Documentation

- [[Architecture]]
- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Model-Registry]]
- [[Provider-Registry]]
- [[ADR-0003-Registries]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

## Summary

The Models API provides a stable, provider-independent catalog of all language models available within Kernschmied.

By exposing validated model metadata, capabilities, availability, and registry information through a unified REST interface, the platform decouples frontend clients and business services from individual LLM providers while supporting runtime discovery, configuration-driven model selection, and future expansion to new AI backends.

---

Back to [[Home]].
