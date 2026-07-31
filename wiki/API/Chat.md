# Chat API

The Chat API is the central interface between frontend clients and the AI execution pipeline.

It is responsible for:

- Receiving user messages
- Resolving hierarchy context
- Resolving effective configuration
- Selecting models
- Executing tools
- Streaming responses
- Returning structured events

The Chat API is intentionally provider-independent. Clients never communicate directly with Ollama, OpenAI, llama.cpp, or any other model provider.

---

# Goals

The Chat API is designed to provide:

- Stable contracts
- Streaming responses
- Provider independence
- Tool execution
- Configuration inheritance
- Structured events
- Error resilience
- Future extensibility

---

# Endpoints

## Streaming Chat

```http
POST /api/v1/chat/stream
```

Primary endpoint used by the frontend.

Returns:

```text
Content-Type: text/event-stream
```

---

## Future Endpoints

Possible future additions:

```http
POST /api/v1/chat

GET /api/v1/chat/{id}

GET /api/v1/chat/{id}/messages

DELETE /api/v1/chat/{id}
```

---

# Request Lifecycle

```text
Frontend

↓

POST /chat/stream

↓

Authentication

↓

Authorization

↓

Hierarchy Resolution

↓

Configuration Resolution

↓

Model Resolution

↓

Tool Resolution

↓

Generation

↓

SSE Stream
```

---

# Request Body

Example:

```json
{
  "message": "Explain dependency injection.",
  "conversation_id": "chat-42",
  "hierarchy_node_id": "project-15",
  "model_id": "qwen2.5-coder:7b",
  "tool_ids": ["calculator", "filesystem"],
  "metadata": {
    "language": "en"
  }
}
```

---

# Request Fields

| Field             | Required | Description        |
| ----------------- | -------- | ------------------ |
| message           | ✔        | User prompt        |
| conversation_id   | Optional | Existing chat      |
| hierarchy_node_id | Optional | Context node       |
| model_id          | Optional | Requested model    |
| tool_ids          | Optional | Allowed tools      |
| metadata          | Optional | Additional context |

---

# Message

Contains the user's input.

Example:

```json
{
  "message": "Write a REST API."
}
```

The message must be validated before execution.

---

# Conversation ID

If supplied, the request belongs to an existing chat.

Otherwise a new conversation may be created.

Example:

```json
{
  "conversation_id": "chat-4711"
}
```

---

# Hierarchy Node

Determines configuration inheritance.

Example:

```json
{
  "hierarchy_node_id": "project-7"
}
```

The hierarchy resolver determines:

- prompts
- tools
- model defaults
- permissions

---

# Model ID

Explicitly requests a model.

Example:

```json
{
  "model_id": "qwen2.5-coder:7b"
}
```

If omitted, the default model is resolved through the Configuration Resolver.

---

# Tool IDs

Limits available tools.

Example:

```json
{
  "tool_ids": ["calculator", "web_search"]
}
```

Requested tools are filtered against:

- permissions
- configuration
- deployment profile

---

# Metadata

Metadata contains additional request information.

Typical examples:

```json
{
  "language": "en",
  "temperature": 0.3
}
```

Metadata must never override protected configuration.

---

# Server-Sent Events

The response is streamed.

```text
Content-Type:

text/event-stream
```

Clients process events incrementally.

---

# Event Sequence

Typical execution:

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

token

↓

usage

↓

complete
```

---

# Event Types

Supported events:

| Event       | Purpose               |
| ----------- | --------------------- |
| start       | Generation started    |
| token       | Token stream          |
| message     | Complete message      |
| reasoning   | Reasoning information |
| tool_call   | Tool invocation       |
| tool_result | Tool result           |
| usage       | Token statistics      |
| heartbeat   | Keep connection alive |
| complete    | Finished              |
| error       | Failure               |

---

# Start Event

Example:

```text
event:start

data:
{
    "conversation_id":"chat-42"
}
```

---

# Token Event

Example:

```text
event:token

data:
{
    "content":"Hello"
}
```

Multiple token events may be emitted.

---

# Message Event

Represents the final generated message.

Example:

```text
event:message
```

This event is optional if token streaming is sufficient.

---

# Reasoning Event

Some providers expose reasoning information.

Example:

```text
event:reasoning
```

Clients should display reasoning only when explicitly enabled.

---

# Tool Call Event

Example:

```text
event:tool_call

data:
{
    "tool":"calculator"
}
```

This informs the frontend that a tool is being executed.

---

# Tool Result Event

Example:

```text
event:tool_result

data:
{
    "success":true
}
```

---

# Usage Event

Example:

```text
event:usage

data:
{
    "prompt_tokens":120,
    "completion_tokens":84
}
```

---

# Complete Event

Final event.

Example:

```text
event:complete
```

No additional events follow.

---

# Error Event

Example:

```text
event:error

data:
{
    "code":"provider_timeout",
    "message":"Generation timed out."
}
```

Clients should terminate the stream gracefully.

---

# Heartbeat

Long-running generations may emit heartbeat events.

Example:

```text
event:heartbeat
```

This prevents idle network timeouts.

---

# Authentication

Authentication depends upon the deployment profile.

Development:

Optional.

Intranet:

Required.

Internet:

Required.

---

# Authorization

Authorization verifies:

- chat access
- hierarchy access
- model permissions
- tool permissions

Unauthorized requests are rejected before generation begins.

---

# Configuration Resolution

Before generation starts:

```text
Hierarchy

↓

Configuration Resolver

↓

Effective Configuration

↓

Chat Service
```

The model receives only the effective configuration.

---

# Model Resolution

The Model Registry resolves:

- requested model
- default model
- provider
- capabilities

Business services never instantiate providers directly.

---

# Tool Execution

Tool calls follow the centralized Tool Architecture.

Execution pipeline:

```text
Model

↓

Tool Registry

↓

Permission Check

↓

Validation

↓

Execution

↓

Result
```

---

# Error Responses

Non-streaming failures return standard API errors.

Example:

```json
{
  "code": "validation_error",
  "message": "Invalid request.",
  "details": {},
  "request_id": "..."
}
```

Streaming failures use SSE error events.

---

# Validation

Requests are validated using Pydantic.

Validation includes:

- required fields
- supported models
- hierarchy identifiers
- permissions
- message length

Invalid requests never reach providers.

---

# Performance Considerations

The Chat API supports:

- asynchronous execution
- streaming
- provider abstraction
- incremental rendering
- connection reuse

Long-running responses do not block the server.

---

# Security Considerations

The Chat API never:

- executes arbitrary code
- trusts client permissions
- exposes provider secrets
- bypasses authorization
- exposes internal exceptions

All provider interactions remain backend controlled.

---

# Related Endpoints

```http
GET /api/v1/bootstrap

GET /api/v1/models

GET /api/v1/tools

GET /api/v1/hierarchy

GET /api/v1/config
```

---

# Related Documentation

- [[Architecture]]
- [[Streaming]]
- [[Bootstrap]]
- [[Configuration]]
- [[Hierarchy]]
- [[Model-Registry]]
- [[Tool-Registry]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

The Chat API is the primary interaction endpoint of Kernschmied.

It provides a provider-independent, streaming-based interface that combines hierarchy resolution, configuration inheritance, model selection, tool execution, and structured Server-Sent Events into a single, stable contract.

This design allows frontend clients to communicate with the platform without knowledge of the underlying AI providers while ensuring consistent security, extensibility, and long-term compatibility.

---

Back to [[Home]].
