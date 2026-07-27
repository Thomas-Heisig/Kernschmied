# Chat System

The **Chat System** is the central runtime component of the Kernschmied backend. It coordinates user conversations, resolves runtime context, constructs AI prompts, communicates with model providers, executes authorized tools, and streams responses back to connected clients.

The Chat System is intentionally designed to be **provider-independent**, **schema-driven**, and **configuration-aware**. It does not depend on any individual Large Language Model (LLM) implementation. Instead, it delegates provider-specific behavior to the Model Registry and provider abstraction layer.

The backend remains the authoritative execution environment for every chat request. The frontend is responsible only for collecting user input and rendering streamed responses.

---

# Goals

The Chat System is designed to provide:

- Provider-independent AI communication
- Deterministic request processing
- Streaming responses
- Hierarchical prompt resolution
- Runtime configuration
- Authorized tool execution
- Conversation management
- Structured error handling
- Future extensibility

---

# Design Principles

## Provider Independence

The Chat Service never communicates directly with a specific AI provider.

Instead:

```text
Chat Service

↓

Model Registry

↓

Provider Interface

↓

Ollama / OpenAI-Compatible / Future Providers
```

This abstraction allows providers to be added or replaced without changing business logic.

---

## Context Before Generation

Before generating a response, the backend resolves all required context.

Typical context includes:

- runtime configuration
- hierarchy
- prompts
- selected model
- enabled tools
- conversation state

The provider receives a fully prepared request.

---

## Streaming First

The Chat System is optimized for incremental response generation.

Instead of waiting for complete model output, tokens are streamed immediately to the client using Server-Sent Events (SSE).

---

# High-Level Architecture

```text
Browser

↓

Chat API

↓

Chat Service

↓

Configuration Resolver

↓

Hierarchy Resolver

↓

Prompt Resolver

↓

Model Registry

↓

Provider

↓

Streaming Response
```

Each subsystem performs a clearly defined responsibility.

---

# Chat Lifecycle

A typical chat request follows this sequence.

```text
Request

↓

Validation

↓

Authorization

↓

Configuration Resolution

↓

Prompt Resolution

↓

Model Resolution

↓

Provider Invocation

↓

Streaming

↓

Completion
```

The sequence is deterministic and repeatable.

---

# Chat Request

A chat request contains all information required for generation.

Typical fields include:

- message
- conversation identifier
- hierarchy node
- selected model
- enabled tools
- request metadata

The request is validated before processing begins.

---

# Request Validation

Validation includes:

- required fields
- supported model identifier
- valid hierarchy node
- authorized tools
- schema compatibility

Invalid requests are rejected before reaching the provider.

---

# Conversation Context

The Chat Service maintains conversation state.

Typical conversation data includes:

- previous messages
- system context
- hierarchy
- selected model
- tool history

Conversation handling remains independent of the frontend.

---

# Hierarchy Resolution

If a request references a hierarchy node, the backend resolves inherited context.

Examples include:

- organization
- department
- project
- workspace
- conversation

Hierarchy determines inherited configuration and prompt fragments.

---

# Configuration Resolution

Runtime configuration is resolved before generation.

Typical configuration includes:

- generation parameters
- provider options
- enabled features
- prompt settings
- safety policies

Configuration is resolved using the Configuration Resolver.

---

# Prompt Resolution

The Prompt Resolver assembles the final prompt.

Typical sources include:

```text
System

↓

Organization

↓

Project

↓

Conversation

↓

User

↓

Request
```

The resulting prompt is deterministic and provider-independent.

---

# Model Resolution

The requested model is resolved through the Model Registry.

```text
Model Identifier

↓

Model Registry

↓

Provider Metadata

↓

Provider Backend
```

Services never instantiate provider implementations directly.

---

# Provider Invocation

After prompt resolution, the provider generates the response.

Typical provider responsibilities include:

- request translation
- provider communication
- token streaming
- usage reporting
- provider-specific error handling

The Chat Service remains unaware of provider-specific APIs.

---

# Tool Execution

If the model requests a tool, execution follows a controlled workflow.

```text
Model

↓

Tool Call

↓

Tool Registry

↓

Authorization

↓

Tool Execution

↓

Tool Result

↓

Model
```

Only registered and authorized tools may execute.

---

# Streaming Responses

Responses are streamed using Server-Sent Events.

Typical event sequence:

```text
start

↓

token

↓

token

↓

tool_call

↓

tool_result

↓

message

↓

usage

↓

complete
```

Streaming allows clients to render responses incrementally.

---

# Supported Event Types

Typical SSE events include:

| Event | Purpose |
|--------|----------|
| `start` | Stream initialized |
| `token` | Incremental model output |
| `reasoning` | Optional reasoning information |
| `tool_call` | Tool invocation |
| `tool_result` | Tool execution result |
| `message` | Final assistant message |
| `usage` | Token usage information |
| `complete` | Stream finished |
| `error` | Structured error |
| `heartbeat` | Keep-alive event |

Additional event types may be introduced through versioned contracts.

---

# Token Streaming

Streaming begins as soon as the provider produces output.

```text
Provider

↓

Token

↓

SSE Event

↓

Frontend
```

The frontend never polls for chat completion.

---

# Usage Reporting

Providers may return usage metadata.

Typical information includes:

- prompt tokens
- completion tokens
- total tokens

Usage reporting is provider-independent.

---

# Conversation Persistence

Conversation storage is separated from generation.

Possible persisted information includes:

- messages
- timestamps
- selected model
- hierarchy references
- metadata

Persistence policies remain configurable.

---

# Error Handling

Errors are translated into structured API responses.

Example:

```json
{
  "code": "provider_error",
  "message": "Model provider unavailable.",
  "details": {},
  "request_id": "7d83bc12"
}
```

Internal provider details remain hidden.

---

# Cancellation

Clients may cancel active streaming requests.

Typical sequence:

```text
Client Disconnect

↓

Stream Cancelled

↓

Provider Stopped

↓

Resources Released
```

Cancellation prevents unnecessary computation.

---

# Security

The Chat System enforces several security boundaries.

Every request is:

- authenticated
- authorized
- validated
- configuration-aware
- provider-isolated

The frontend cannot bypass backend validation.

---

# Performance

The Chat System is optimized for:

- asynchronous processing
- incremental streaming
- provider abstraction
- cached configuration
- efficient prompt construction
- minimal latency

Performance optimizations never compromise deterministic behavior.

---

# Extensibility

The Chat System supports future extensions including:

- multimodal models
- image generation
- audio processing
- document analysis
- workflow execution
- multiple simultaneous providers
- collaborative conversations

These capabilities integrate through registries and stable contracts rather than modifications to the Chat Service itself.

---

# Relationship to Other Backend Components

The Chat System coordinates multiple backend subsystems.

```text
Chat API

↓

Chat Service

↓

Configuration Resolver

↓

Hierarchy Resolver

↓

Prompt Resolver

↓

Model Registry

↓

Provider

↓

Streaming
```

It serves as the orchestration layer for conversational AI.

---

# Relationship to Architecture

The Chat System depends on several architectural concepts.

- [[Prompt-Inheritance]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Registry-Architecture]]
- [[Request-Lifecycle]]
- [[Security-Architecture]]

---

# Related Documentation

## Backend

- [[Backend-Overview]]
- [[Prompt-Resolution]]
- [[Provider-System]]
- [[Streaming]]
- [[Configuration-Management]]
- [[Hierarchy-Management]]

---

## Architecture

- [[Request-Lifecycle]]
- [[Prompt-Inheritance]]
- [[Registry-Architecture]]
- [[Configuration-Architecture]]
- [[Security-Architecture]]

---

## APIs

- [[Chat]]
- [[SSE]]
- [[Models]]
- [[Tools]]

---

# Summary

The Chat System is the orchestration layer that transforms validated user requests into streamed AI responses by combining runtime configuration, hierarchical context, prompt inheritance, provider-independent model resolution, authorized tool execution, and Server-Sent Events.

Through its layered architecture, deterministic processing pipeline, registry-based provider abstraction, and structured streaming protocol, the Chat System enables Kernschmied to support multiple AI providers and future capabilities while maintaining stable public contracts, strong security, and a consistent user experience.

---

Back to [[Home]].
