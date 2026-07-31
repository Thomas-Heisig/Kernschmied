# Model Registry

The **Model Registry** is the central discovery, validation, and management subsystem for all Artificial Intelligence models available within the Kernschmied backend.

Rather than embedding provider-specific knowledge into application services, the Model Registry maintains a unified catalog of models together with their metadata, capabilities, configuration, and provider associations. Application components interact only with the registry and remain completely independent of individual AI providers.

This architecture allows new models and providers to be added through manifests and configuration without requiring changes to the chat system or frontend.

---

# Goals

The Model Registry is designed to provide:

- Provider-independent model discovery
- Runtime model registration
- Stable model identifiers
- Capability-based model selection
- Manifest-driven configuration
- Version-independent provider integration
- Strong validation
- Future extensibility

---

# Design Principles

## Provider Independence

Application services never communicate directly with AI providers.

Instead:

```text
Chat Service

↓

Model Registry

↓

Provider Backend

↓

AI Model
```

This abstraction keeps business logic independent of provider implementations.

---

## Stable Model Identifiers

Each model is identified by a stable logical identifier.

Example:

```text
assistant-default

↓

Model Registry

↓

qwen2.5-coder:7b

↓

Ollama
```

Clients never depend on provider-specific model names.

---

## Metadata Instead of Logic

The registry stores metadata describing models rather than implementing model-specific behavior.

Typical metadata includes:

- identifier
- display name
- provider
- capabilities
- context length
- default parameters
- availability

Behavior remains the responsibility of provider backends.

---

## Manifest-Driven Registration

Models are registered through versioned manifests.

```text
model.json

↓

Validation

↓

Registry

↓

Available Models
```

This allows models to be added without modifying application code.

---

# High-Level Architecture

```text
Model Manifest

↓

Model Registry

↓

Provider Registry

↓

Provider Backend

↓

Model Execution
```

Each layer has a clearly defined responsibility.

---

# Registry Responsibilities

The Model Registry is responsible for:

- discovering models
- validating manifests
- exposing metadata
- resolving providers
- checking capabilities
- selecting default models
- tracking revisions

It does **not** execute inference itself.

---

# Model Discovery

Models are discovered during application bootstrap.

Typical sequence:

```text
Manifest Discovery

↓

Manifest Validation

↓

Registry Population

↓

Application Ready
```

Only valid models become available.

---

# Model Manifest

Every model is described by a manifest.

Typical information includes:

- identifier
- provider
- model name
- capabilities
- display name
- defaults
- metadata

Manifests are versioned and validated before registration.

---

# Registry Initialization

During bootstrap the registry:

1. discovers manifests
2. validates schemas
3. resolves providers
4. checks duplicates
5. creates immutable registry entries

Initialization must complete successfully before requests are processed.

---

# Registry Entries

Each registry entry represents a logical model.

Typical fields include:

| Field        | Purpose                  |
| ------------ | ------------------------ |
| Identifier   | Stable logical name      |
| Display Name | User-visible name        |
| Provider     | Provider identifier      |
| Model        | Provider model reference |
| Capabilities | Supported features       |
| Metadata     | Optional information     |

The internal structure may evolve independently of the public API.

---

# Capability Management

Capabilities describe what a model can do.

Typical capabilities include:

- chat
- streaming
- tool calling
- reasoning
- vision
- embeddings
- function calling

Capabilities allow services to select compatible models without inspecting provider-specific implementations.

---

# Model Resolution

Application services request models by identifier.

```text
Model ID

↓

Registry

↓

Provider

↓

Resolved Backend
```

Unknown identifiers produce structured errors.

---

# Default Models

The registry may define default models for different purposes.

Examples include:

- default chat model
- coding assistant
- reasoning model
- embedding model
- vision model

Defaults are controlled through runtime configuration rather than source code.

---

# Provider Association

Each registered model references exactly one provider.

Example:

```text
Model

↓

Provider ID

↓

Provider Registry

↓

Backend Instance
```

The provider registry resolves the implementation.

---

# Runtime Availability

Models may become unavailable during runtime.

Examples include:

- provider offline
- configuration disabled
- startup failure
- missing dependencies

Availability status is exposed separately from registration metadata.

---

# Validation

Every manifest is validated before registration.

Validation includes:

- schema version
- required properties
- unique identifiers
- supported capabilities
- provider existence
- configuration consistency

Invalid manifests are rejected during bootstrap.

---

# Duplicate Detection

Logical model identifiers must be unique.

Invalid example:

```text
assistant-default

assistant-default
```

Duplicate registrations prevent successful startup.

---

# Revision Tracking

The registry maintains a revision number.

```text
Revision 15

↓

Registry Updated

↓

Revision 16
```

Clients can use revision information to invalidate cached metadata.

---

# Registry API

The backend exposes registry information through stable REST endpoints.

Typical operations include:

- list models
- retrieve metadata
- query capabilities
- retrieve revisions

Execution remains separate from discovery.

---

# Interaction with Chat

The Chat Service relies on the registry for model selection.

```text
Chat Request

↓

Model Registry

↓

Provider

↓

Inference
```

The Chat Service never instantiates provider implementations directly.

---

# Interaction with Configuration

Runtime configuration determines:

- default models
- enabled models
- visibility
- generation defaults

Configuration and registry remain separate but closely integrated.

---

# Interaction with Bootstrap

During startup:

```text
Bootstrap

↓

Manifest Discovery

↓

Model Registry

↓

Application Ready
```

Registry initialization is part of the deterministic bootstrap process.

---

# Interaction with Providers

The registry stores metadata.

Providers perform inference.

```text
Registry

↓

Provider Backend

↓

AI Response
```

This separation allows providers to evolve independently.

---

# Error Handling

Typical registry errors include:

- unknown model
- invalid manifest
- duplicate identifier
- unsupported capability
- provider missing

Errors are returned using the standard backend error contract.

---

# Security

The registry enforces several safety guarantees.

It never:

- executes arbitrary code
- loads untrusted Python modules
- trusts invalid manifests
- exposes provider credentials

Only validated metadata becomes visible to application services.

---

# Performance

The registry is optimized for:

- immutable lookup structures
- constant-time identifier resolution
- cached metadata
- revision-aware invalidation
- lightweight provider resolution

Lookup operations should remain inexpensive even with large model catalogs.

---

# Testing

The Model Registry should be verified through automated tests.

Recommended coverage includes:

- manifest validation
- duplicate detection
- capability resolution
- provider resolution
- default model selection
- revision tracking
- API serialization

Testing ensures deterministic registry behavior.

---

# Future Extensions

The architecture supports future capabilities including:

- hot-reloadable model catalogs
- remote model registries
- tenant-specific model visibility
- model health monitoring
- cost and latency metadata
- automatic capability discovery
- model recommendation policies

These enhancements can be introduced without changing existing service interfaces.

---

# Relationship to Other Backend Components

The Model Registry coordinates model discovery across the backend.

```text
Bootstrap

↓

Model Registry

↓

Provider Registry

↓

Chat Service

↓

AI Providers
```

It acts as the authoritative source of model metadata.

---

# Relationship to Architecture

The Model Registry integrates closely with:

- [[Registry-Architecture]]
- [[Manifest-System]]
- [[Configuration-Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Request-Lifecycle]]

---

# Related Documentation

## Backend

- [[Backend-Overview]]
- [[Chat]]
- [[Provider-System]]
- [[Configuration]]
- [[Bootstrap]]

---

## Architecture

- [[Registry-Architecture]]
- [[Manifest-System]]
- [[Configuration-Architecture]]
- [[Bootstrap-Lifecycle]]
- [[Request-Lifecycle]]

---

## APIs

- [[Models]]
- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]

---

# Summary

The Model Registry provides the authoritative catalog of AI models available to the Kernschmied backend by separating provider-specific implementations from stable, provider-independent model metadata.

Through manifest-driven registration, capability-based discovery, runtime validation, revision tracking, deterministic lookup, and seamless integration with configuration, bootstrap, and provider registries, the Model Registry enables the platform to support multiple AI providers and future model types while preserving stable contracts, extensibility, and long-term maintainability.

---

Back to [[Home]].
