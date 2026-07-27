# Server-Sent Events (SSE)

Server-Sent Events (SSE) are the primary streaming protocol used by Kernschmied to deliver AI responses from the backend to frontend clients.

Instead of waiting for an entire response to be generated before returning it, the backend streams structured events as soon as they become available. This enables responsive user interfaces, real-time tool execution updates, and provider-independent streaming behavior.

The SSE protocol is a core part of the platform and is used by the Chat API regardless of the underlying LLM provider.

---

# Goals

The SSE implementation is designed to provide:

- Real-time token streaming
- Provider-independent event contracts
- Low-latency responses
- Structured tool execution events
- Incremental UI updates
- Connection health monitoring
- Stable public contracts
- Future extensibility

---

# Why Server-Sent Events?

Compared to traditional request/response communication, SSE provides:

- Immediate feedback
- Lower perceived latency
- Continuous response generation
- Simpler implementation than WebSockets
- Native browser support
- Efficient one-way communication

The frontend receives events as they occur without polling.

---

# Endpoint

Streaming responses are returned from the Chat API.

```http
POST /api/v1/chat/stream
```

Response:

```http
Content-Type: text/event-stream
```

---

# High-Level Architecture

```text
Frontend

        │

        ▼

Chat API

        │

        ▼

Chat Service

        │

        ▼

Model Provider

        │

        ▼

SSE Event Stream
```

Provider-specific streaming protocols are translated into the unified SSE contract.

---

# Event Format

Each event follows the standard SSE format.

```text
event: token

data:
{
    "content":"Hello"
}
```

Events are separated by an empty line.

---

# Event Lifecycle

Typical generation flow:

```text
Client Request

↓

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

Errors terminate the stream immediately.

---

# Supported Events

The platform defines the following standard events.

| Event | Purpose |
|--------|----------|
| start | Generation started |
| token | Incremental text |
| message | Complete assistant message |
| reasoning | Optional reasoning information |
| tool_call | Tool execution begins |
| tool_result | Tool execution completed |
| usage | Token usage statistics |
| heartbeat | Keep-alive event |
| complete | Stream finished |
| error | Stream terminated بسبب error |

---

# Start Event

The first event emitted after successful request validation.

Example:

```text
event:start

data:
{
    "conversation_id":"chat-42",
    "message_id":"assistant-15"
}
```

The frontend prepares the UI for streaming.

---

# Token Event

The most frequently emitted event.

Example:

```text
event:token

data:
{
    "content":"Dependency"
}
```

Multiple token events together form the assistant response.

---

# Message Event

Some providers generate a complete message after streaming.

Example:

```text
event:message

data:
{
    "content":"Dependency injection separates object creation from usage."
}
```

The event is optional.

---

# Reasoning Event

Certain reasoning-capable models expose intermediate reasoning.

Example:

```text
event:reasoning

data:
{
    "content":"Analyzing architecture..."
}
```

Reasoning visibility is controlled by backend configuration.

Clients should not assume this event is always present.

---

# Tool Call Event

Indicates that the model requested a tool.

Example:

```text
event:tool_call

data:
{
    "tool":"calculator",
    "call_id":"tool-17",
    "arguments":{
        "expression":"12*7"
    }
}
```

The frontend may visualize tool execution progress.

---

# Tool Result Event

Represents the completion of a tool execution.

Example:

```text
event:tool_result

data:
{
    "tool":"calculator",
    "success":true,
    "result":"84"
}
```

This event allows users to understand how external tools contributed to the response.

---

# Usage Event

Provides token statistics after generation.

Example:

```text
event:usage

data:
{
    "prompt_tokens":325,
    "completion_tokens":168,
    "total_tokens":493
}
```

Not all providers expose identical usage information.

The backend normalizes available statistics whenever possible.

---

# Heartbeat Event

Long-running requests may periodically emit heartbeat events.

Example:

```text
event:heartbeat

data:{}
```

Heartbeats prevent idle proxies, browsers, and load balancers from closing the connection.

---

# Complete Event

Marks successful completion of the stream.

Example:

```text
event:complete

data:{}
```

No additional events are sent afterwards.

---

# Error Event

Errors occurring after streaming has started are transmitted as SSE events.

Example:

```text
event:error

data:
{
    "code":"provider_timeout",
    "message":"The selected model did not respond."
}
```

After an error event the stream closes.

---

# Stream Lifecycle

```text
Request

↓

Validation

↓

Authorization

↓

Configuration Resolution

↓

Model Resolution

↓

Generation

↓

Streaming Events

↓

Completion
```

All validation occurs before the first streaming event.

---

# Connection Handling

Each client receives an independent stream.

```text
Client A

↓

Stream A


Client B

↓

Stream B
```

Streams do not share state.

---

# Provider Independence

Different providers expose different streaming mechanisms.

Examples include:

- HTTP chunked responses
- JSON streams
- event streams
- proprietary protocols

The Chat Service converts provider output into the common SSE event model.

Frontend applications never depend on provider-specific behavior.

---

# Tool Integration

Tool execution is integrated into the streaming pipeline.

```text
Model

↓

tool_call

↓

Tool Registry

↓

Execution

↓

tool_result

↓

Continue Generation
```

This provides complete transparency for users and simplifies debugging.

---

# Error Handling

Streaming errors differ from REST errors.

REST errors occur before streaming begins.

Streaming errors occur after headers have already been sent.

Therefore:

- REST endpoints return JSON
- Streaming endpoints emit `error` events

This distinction allows consistent client behavior.

---

# Client Responsibilities

Clients should:

- process events incrementally
- preserve event order
- gracefully ignore unknown events
- terminate after `complete`
- terminate after `error`
- reconnect only when appropriate

Future platform versions may introduce additional event types.

---

# Versioning

The SSE event contract is versioned independently.

Its version is published through the Bootstrap API.

Unknown event fields should be ignored by clients to preserve forward compatibility.

---

# Performance Considerations

Streaming minimizes perceived latency by:

- sending tokens immediately
- avoiding large response buffers
- reducing frontend waiting time
- enabling incremental rendering

Asynchronous processing ensures multiple concurrent streams can execute efficiently.

---

# Security Considerations

SSE streams never expose:

- provider credentials
- API keys
- internal exceptions
- stack traces
- implementation details

Authorization is completed before streaming starts.

Tool execution always remains server-side.

---

# Relationship to Other APIs

The SSE protocol complements the REST APIs.

```text
Bootstrap

↓

Models

↓

Hierarchy

↓

Configuration

↓

Chat API

↓

SSE Stream
```

REST endpoints initialize the application.

SSE delivers live AI responses.

---

# Related Documentation

- [[Architecture]]
- [[Bootstrap]]
- [[Chat]]
- [[Configuration]]
- [[Streaming]]
- [[Model-Registry]]
- [[Tool-Registry]]
- [[ADR-0005-Versioned-Contracts]]
- [[ADR-0008-Tool-Architecture]]
- [[ADR-0015-LLM-Provider-Architecture]]

---

# Summary

Server-Sent Events provide the standardized streaming protocol for all AI interactions within Kernschmied.

By translating provider-specific streaming mechanisms into a unified sequence of structured events—including token generation, reasoning, tool execution, usage statistics, heartbeats, completion, and errors—the platform delivers responsive user experiences while maintaining provider independence, stable contracts, and long-term architectural flexibility.

---

Back to [[Home]].
