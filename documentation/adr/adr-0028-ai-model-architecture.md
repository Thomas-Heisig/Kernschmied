# ADR-0028: AI Model Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as an AI-native platform.

Artificial Intelligence is not a single feature but one of the core platform capabilities.

The platform must support multiple AI technologies throughout its lifetime without requiring architectural changes.

Typical examples include:

- local Large Language Models
- cloud AI providers
- reasoning models
- multimodal models
- vision models
- embedding models
- speech recognition
- speech synthesis
- image generation
- translation models
- future AI architectures

Different providers expose different APIs, capabilities and runtime characteristics.

The platform therefore requires a generic AI model architecture.

---

# Problem

Without a dedicated model architecture, AI functionality becomes tightly coupled to individual providers.

Typical problems include:

- provider-specific business logic
- duplicated implementations
- inconsistent capabilities
- difficult provider replacement
- inconsistent error handling
- missing lifecycle management
- poor runtime configurability
- vendor lock-in

As the platform evolves, supporting new providers becomes increasingly difficult.

---

# Decision

Kernschmied adopts a **generic AI Model Architecture**.

Business services never communicate directly with AI providers.

Instead, every request passes through a centralized Model Service that resolves:

- logical models
- physical models
- providers
- capabilities
- runtime configuration

Providers execute requests through standardized provider adapters.

---

# Architectural Principle

> **Business Services request AI capabilities.**
>
> **The Model Service selects logical models.**
>
> **Provider Adapters execute physical models.**
>
> **Registries define what is available.**

---

# High-Level Architecture

```text
Business Service

        │

        ▼

Model Service

        │

        ▼

Model Registry

        │

        ▼

Provider Registry

        │

        ▼

Provider Adapter

        │

        ▼

Physical AI Model
```

---

# Logical Models

Applications always reference logical models.

Examples include:

- default_chat
- coding_assistant
- image_generation
- embeddings
- speech_to_text
- text_to_speech
- reasoning

Logical model identifiers remain stable even if physical models change.

---

# Physical Models

Physical models represent concrete implementations.

Examples include:

- GPT
- Claude
- Gemini
- Qwen
- Mistral
- Llama
- DeepSeek
- Gemma
- Phi

Applications never reference physical models directly.

---

# Provider Architecture

Every provider is implemented through a Provider Adapter.

Typical providers include:

- OpenAI
- Azure OpenAI
- Anthropic
- Google Gemini
- Ollama
- llama.cpp
- MLX
- HuggingFace
- Generic HTTP Providers

Every provider follows the same contract.

---

# Capability Model

Every model declares its supported capabilities.

Typical capabilities include:

- chat
- completion
- reasoning
- streaming
- tool calling
- structured output
- vision
- embeddings
- speech recognition
- speech synthesis
- image generation

Capabilities are declared through manifests and never hard-coded.

---

# Model Registry

Every logical model is represented as a Runtime Registry entry.

Typical metadata includes:

- identifier
- logical model
- provider
- physical model
- capabilities
- deployment profile
- enabled state
- revision

Activation always requires validation.

---

# Model Routing

The Model Service resolves the appropriate model for every request.

Routing may consider:

- logical model
- required capabilities
- deployment profile
- hierarchy context
- runtime configuration
- prompt configuration
- tenant policy

Routing remains deterministic.

---

# Prompt Integration

Prompt resolution is completed before model execution.

The Model Service receives the fully resolved prompt.

Prompt inheritance follows ADR-0008.

---

# Tool Integration

Models may request registered tools.

Tool execution follows ADR-0029.

Models never execute tools directly.

Every tool request is validated before execution.

---

# Streaming

Streaming responses follow the Event Architecture.

Typical events include:

- chat.started
- chat.token
- chat.reasoning
- tool.requested
- tool.completed
- usage
- completed
- failed

Streaming contracts remain provider independent.

---

# Runtime Configuration

Model behaviour is configurable.

Examples include:

- default models
- temperature
- maximum tokens
- timeout
- retry policy
- streaming defaults
- reasoning mode

Configuration is managed through the Runtime Configuration Architecture.

---

# Lifecycle Management

The Model Lifecycle Manager controls:

- initialization
- loading
- unloading
- warm-up
- health monitoring
- shutdown

Provider failures never affect unrelated providers.

---

# Error Handling

Provider-specific errors are translated into generic platform errors.

Typical categories include:

- authentication failure
- timeout
- unavailable provider
- invalid request
- quota exceeded
- model unavailable

Business services never receive provider-specific exceptions.

---

# Security

Models never receive:

- secrets
- internal policies
- registry metadata
- unrestricted database access

All requests are validated before execution.

---

# Monitoring

Operational metrics include:

- request count
- latency
- token usage
- streaming duration
- provider availability
- error rate
- fallback usage

Monitoring integrates with ADR-0030.

---

# Audit

Every model invocation generates immutable audit information.

Typical information includes:

- logical model
- physical model
- provider
- execution time
- token usage
- request identifier
- hierarchy context

Sensitive prompt content may be redacted according to policy.

---

# Versioning

Logical models, providers and manifests evolve independently.

Existing conversations continue using the resolved model version.

New conversations use the active version.

All contracts follow ADR-0005.

---

# API Contracts

Future APIs may include:

- List Models
- Get Model
- Activate Model
- Deactivate Model
- Validate Model
- Test Model
- Provider Status
- Model Capabilities

All contracts are versioned.

---

# Consequences

## Positive

### Provider Independence

Business services remain independent of AI providers.

---

### Runtime Flexibility

Models may be replaced without changing application code.

---

### Consistent Architecture

Every provider follows identical contracts.

---

### Better Observability

Model execution becomes measurable and auditable.

---

### Future Readiness

New AI technologies integrate through registries rather than application changes.

---

## Negative

### Additional Complexity

The Model Service introduces another architectural layer.

---

### Manifest Maintenance

Models and providers require validated manifests.

---

### Operational Monitoring

Multiple providers require continuous monitoring.

---

### Capability Validation

Provider capabilities must be maintained and tested.

---

# Alternatives Considered

## Direct Provider Integration

### Advantages

- Simple implementation
- Fast initial development

### Disadvantages

- Strong provider coupling
- Difficult replacement
- Code duplication

Rejected.

---

## Single Provider Architecture

### Advantages

- Minimal complexity

### Disadvantages

- Vendor lock-in
- No fallback strategy
- Limited flexibility

Rejected.

---

# Related ADRs

- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0009 — Runtime Registry Architecture
- ADR-0012 — Action Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0015 — Chat and Conversation Architecture
- ADR-0019 — Audit and Revision Architecture
- ADR-0022 — Integration Architecture
- ADR-0029 — Tool Execution Architecture
- ADR-0030 — Monitoring and Observability
- ADR-0031 — Performance and Caching

---

# Implementation Notes

The MVP initially supports local and remote AI providers through a common Model Service, Model Registry and Provider Registry. Future releases may introduce intelligent routing, capability negotiation, distributed inference, cost-aware model selection and additional AI modalities without changing the public model contracts.
