# ADR-0015: LLM Provider Architecture

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as an AI platform that must support multiple Large Language Model (LLM) providers throughout its lifetime.

The platform should never become coupled to a single provider such as:

- Ollama
- llama.cpp
- OpenAI
- Anthropic
- Google Gemini
- Azure OpenAI
- Future providers

Different providers expose different:

- APIs
- authentication mechanisms
- streaming protocols
- model metadata
- capabilities
- pricing models
- configuration formats

Business services should remain completely independent from these differences.

---

# Problem

Directly integrating provider-specific SDKs into business logic leads to:

- duplicated code
- vendor lock-in
- inconsistent streaming
- incompatible tool calling
- difficult testing
- fragile upgrades

Adding a new provider should not require changes throughout the application.

---

# Decision

Kernschmied adopts a **provider abstraction architecture**.

Every LLM implementation must implement a common provider contract.

Business services communicate only with the abstraction layer.

Concrete providers are discovered and managed through the **Model Registry**.

---

# Architectural Principle

> Models are interchangeable.
>
> Providers implement capabilities.
>
> Business services consume contracts.

---

# High-Level Architecture

```text
Chat Service

        │

        ▼

Model Registry

        │

        ▼

Provider Registry

        │

        ▼

Provider Backend

        │

        ▼

External Model
```

---

# Goals

The architecture should provide:

- provider independence
- capability discovery
- unified streaming
- consistent metadata
- structured errors
- runtime discovery
- future extensibility

---

# Provider Abstraction

Every provider implements a common interface.

Typical responsibilities include:

- model discovery
- generation
- streaming
- capability reporting
- validation
- health checks

Business services never call provider SDKs directly.

---

# BaseModelBackend

All providers derive from a common abstraction.

Typical responsibilities include:

- chat completion
- streaming
- embeddings (future)
- model metadata
- provider information
- validation

The abstraction defines stable contracts for the rest of the platform.

---

# Provider Registry

The Provider Registry manages available provider implementations.

Responsibilities include:

- provider discovery
- registration
- lookup
- lifecycle management
- health reporting

Providers are registered during application startup.

---

# Model Registry

The Model Registry exposes available models independently from provider implementation details.

Responsibilities include:

- model discovery
- metadata
- default model selection
- capability lookup
- runtime availability
- filtering

Business services request models through the registry.

---

# Model Manifest

Each model is described through a declarative manifest.

Example:

```text
model.json
```

Typical fields include:

- id
- provider
- model
- display name
- capabilities
- context length
- default parameters
- visibility

The manifest is validated before registration.

---

# Why Manifests?

Model manifests allow:

- runtime discovery
- administration
- documentation
- capability reporting
- frontend integration

without loading provider-specific code.

---

# Supported Providers

The architecture is designed for providers such as:

## Ollama

Local inference server.

Typical advantages:

- offline execution
- privacy
- simple deployment

---

## llama.cpp

Direct execution of GGUF models.

Advantages:

- lightweight
- embedded deployment
- CPU support
- local inference

---

## OpenAI

Cloud-hosted models.

Advantages:

- broad model selection
- mature APIs
- enterprise ecosystem

---

## Anthropic

Cloud-hosted Claude models.

Designed through the same provider interface.

---

## Google Gemini

Supported through a dedicated provider implementation.

Business services remain unchanged.

---

## Azure OpenAI

Enterprise deployment of OpenAI-compatible models.

Implemented through the same abstraction layer.

---

## Generic HTTP Provider

Future providers exposing compatible APIs may be integrated through a generic HTTP backend.

---

# Capability Model

Providers expose supported capabilities.

Examples include:

- chat
- streaming
- tool calling
- vision
- embeddings
- reasoning
- structured output

Capabilities are queried through the Model Registry.

---

# Model Selection

Business services request a model by identifier.

Example:

```text
Chat Request

↓

Model Registry

↓

Resolve Model

↓

Resolve Provider

↓

Execute
```

Business services never instantiate providers.

---

# Streaming

Streaming is normalized across providers.

Internal event types include:

- start
- token
- message
- reasoning
- tool_call
- tool_result
- usage
- complete
- error

Provider-specific protocols are translated into the common event model.

---

# Tool Calling

Different providers implement tool calling differently.

The provider abstraction converts provider-specific requests into a common platform contract.

Business services receive a uniform tool call structure.

---

# Configuration

Provider configuration is stored through the Configuration Management system.

Typical configuration includes:

- endpoint
- authentication
- timeout
- retry policy
- model defaults

Configuration remains provider-independent wherever possible.

---

# Provider Health

Each provider may expose health information.

Typical values include:

- available
- unavailable
- degraded
- loading

The registry exposes provider health to administration interfaces.

---

# Error Handling

Provider-specific exceptions are translated into structured platform errors.

Examples include:

- timeout
- authentication failure
- model unavailable
- invalid request
- quota exceeded

Clients never receive provider-specific exception types.

---

# Security Considerations

Providers never bypass platform security.

The architecture enforces:

- centralized authorization
- validated configuration
- structured logging
- request auditing
- secure secret handling

API keys should never be stored inside manifests.

---

# Performance Considerations

Performance techniques include:

- provider caching
- connection reuse
- asynchronous requests
- streaming
- registry lookup caching

Provider abstraction should introduce minimal overhead.

---

# Operational Impact

The architecture enables:

- provider replacement
- model migration
- local/cloud hybrid deployments
- runtime administration
- monitoring
- future provider additions

Operations teams may introduce new providers without modifying business services.

---

# Future Capabilities

The architecture is intentionally extensible.

Future capabilities may include:

- embeddings
- speech generation
- speech recognition
- image generation
- multimodal reasoning
- document understanding
- agent execution

The provider abstraction should evolve without breaking existing integrations.

---

# Consequences

## Positive

- Provider independence
- Simplified testing
- Stable contracts
- Runtime discovery
- Extensible architecture
- Unified streaming
- Consistent capabilities

## Negative

- Additional abstraction
- Registry maintenance
- Manifest management
- Capability translation effort

---

# Alternatives Considered

## Direct Provider Integration

Rejected because business services become tightly coupled to provider SDKs.

---

## Provider-Specific APIs

Rejected because every provider would require separate business logic.

---

## Single Provider Architecture

Rejected because long-term flexibility is a primary design goal.

---

## Runtime Code Loading

Rejected because providers should be explicitly registered and validated.

---

# Risks

Potential risks include:

- inconsistent provider capabilities
- provider API changes
- incompatible streaming behavior
- capability mismatches

Mitigation strategies include:

- common contracts
- capability reporting
- registry validation
- automated integration testing
- provider abstraction

---

# Implementation Notes

The implementation should provide:

- `BaseModelBackend`
- Provider Registry
- Model Registry
- `model.json` manifests
- capability discovery
- provider health checks
- structured streaming
- provider-independent configuration
- dependency injection

Business services should never depend directly on provider SDKs.

---

# Related Decisions

- [[ADR-0002-Bootstrap]]
- [[ADR-0003-Registries]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0013-Error-Handling-and-Logging]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Model-Architecture]]
- [[Registry-Architecture]]

---

## Backend

- [[Model-Registry]]
- [[Provider-Registry]]
- [[REST-API]]
- [[Streaming]]
- [[Configuration]]

---

## Concepts

- [[Model-Manifests]]
- [[Capabilities]]
- [[Provider-Abstraction]]
- [[Runtime-Configuration]]

---

# Decision Summary

Kernschmied adopts a **provider-independent LLM architecture** in which every model backend implements the common `BaseModelBackend` contract and is registered through the Provider Registry and Model Registry.

Models are described using validated `model.json` manifests, provider-specific behavior is translated into common platform contracts, and streaming, tool calling, capability reporting, configuration, and error handling are normalized across all supported providers.

This architecture enables seamless integration of local and cloud-based models, minimizes vendor lock-in, supports future multimodal capabilities, and provides a stable foundation for long-term platform evolution.

---

Back to [[Home]].
