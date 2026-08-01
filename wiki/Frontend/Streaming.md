# Streaming

> **Version:** 1.0
> **Status:** Living Document
> **Applies to:** Frontend

---

## Overview

Kernschmied uses **Server-Sent Events (SSE)** as the primary streaming protocol between the frontend and the backend.

Streaming allows AI responses to appear incrementally while they are generated, providing immediate feedback to the user instead of waiting for the complete response.

The frontend treats streaming as a generic transport mechanism. It is independent of any specific AI model or provider.

---

## Why Server-Sent Events?

Several technologies were evaluated.

| Technology                   | Advantages                                          | Disadvantages                                           |
| ---------------------------- | --------------------------------------------------- | ------------------------------------------------------- |
| Polling                      | Simple                                              | High latency, unnecessary traffic                       |
| Long Polling                 | Better than polling                                 | More complex                                            |
| WebSockets                   | Bidirectional                                       | Higher complexity, unnecessary for current requirements |
| **Server-Sent Events (SSE)** | Simple, HTTP-native, automatic reconnection support | One-way communication                                   |

For the current architecture, SSE provides the best balance between simplicity, performance, and maintainability.

---

## Architecture

```text
+-----------+
| React UI  |
+-----------+
      │
      │ POST /chat
      ▼
+----------------+
| FastAPI API    |
+----------------+
      │
      ▼
+----------------+
| Chat Service   |
+----------------+
      │
      ▼
+----------------+
| AI Provider    |
+----------------+
      │
      │ Token Stream
      ▼
+----------------+
| SSE Endpoint   |
+----------------+
      │
      │ text/event-stream
      ▼
+----------------+
| React Client   |
+----------------+

```

---

## Streaming Lifecycle

```text
User sends message

↓

Backend validates request

↓

Conversation starts

↓

Model generates tokens

↓

Backend emits SSE events

↓

Frontend receives events

↓

UI updates continuously

↓

Completion event

↓

Connection closes

```

---

## HTTP Endpoint

Typical endpoint:

```text
POST /api/chat/stream

```

The endpoint returns

```text
Content-Type:
text/event-stream

```

---

## Event Flow

A complete conversation consists of multiple events.

```text
start

↓

metadata

↓

token

↓

token

↓

token

↓

usage

↓

complete

```

Errors interrupt the stream and are reported as dedicated events.

---

## Typical Event Types

## Start

Signals that streaming has begun.

```json
{
  "type": "start"
}
```

---

## Metadata

Contains information about the conversation.

Example:

```json
{
  "type": "metadata",
  "conversation_id": "...",
  "model": "llama3"
}
```

---

## Token

Represents one streamed text fragment.

```json
{
  "type": "token",
  "text": "Hello"
}
```

The frontend appends the token to the current assistant message.

---

## Usage

Provides statistics after generation.

Example:

```json
{
  "type": "usage",
  "prompt_tokens": 124,
  "completion_tokens": 582
}
```

---

## Complete

Marks the end of the response.

```json
{
  "type": "complete"
}
```

The frontend finalizes the message and closes the stream.

---

## Error

Errors are sent as structured events.

Example:

```json
{
  "type": "error",
  "code": "model_not_found",
  "message": "Requested model is unavailable."
}
```

---

## Event Format

Each SSE event follows the standard format.

```text
event: token
data: {"text":"Hello"}


```

Multiple events are separated by a blank line.

---

## Frontend Responsibilities

The frontend is responsible for:

- opening the stream
- decoding events
- updating the UI
- buffering tokens
- handling reconnects
- displaying errors
- cancelling requests

The frontend never generates response content.

---

## State Management

Typical streaming state:

```text
Idle

↓

Connecting

↓

Streaming

↓

Completed

↓

Idle

```

If an error occurs:

```text
Streaming

↓

Error

↓

Idle

```

---

## Token Rendering

Incoming tokens are appended incrementally.

```text
Received:

Hel

↓

Hello

↓

Hello World

↓

Hello World!

```

Rendering should be efficient to avoid unnecessary React re-renders.

---

## Cancellation

Users may cancel generation.

Flow:

```text
User presses Stop

↓

AbortController

↓

HTTP request cancelled

↓

Backend stops generation

↓

Resources released

```

Cancellation should be immediate.

---

## Error Handling

Possible errors include:

- connection lost
- timeout
- provider unavailable
- invalid request
- authentication failure
- authorization failure
- malformed stream

Errors should always be presented in a user-friendly way.

---

## Reconnection

If supported by the endpoint, the frontend may reconnect after temporary network failures.

However:

- duplicate events must be ignored
- completed conversations must not restart
- message ordering must remain deterministic

---

## Performance Considerations

The frontend should:

- batch UI updates when appropriate
- avoid unnecessary renders
- reuse message components
- release closed streams promptly
- clean up event listeners

Streaming should remain responsive even during long responses.

---

## Security

Streaming endpoints follow the same security model as all REST endpoints.

The backend validates:

- authentication
- authorization
- request schema
- conversation ownership
- model permissions
- tool permissions

The frontend must never assume that a stream is authorized simply because it could be opened.

---

## Future Extensions

The streaming protocol is designed to support additional event types, including:

- reasoning updates
- progress notifications
- tool invocation
- tool results
- citations
- source references
- image generation progress
- audio streaming
- multimodal responses

Unknown event types should be ignored gracefully or displayed using a generic fallback.

---

## Related Documentation

## Architecture (2)

- [[Architecture]]
- [[Request-Lifecycle]]
- [[Contracts]]

---

## Frontend

- [[API-Client]]
- [[State-Management]]
- [[Chat]]

---

## Backend

- [[Chat]]
- [[Error-Handling]]
- [[Model-Registry]]

---

## Concepts

- [[Runtime-Configuration]]
- [[Dynamic-UI]]

---

## Summary

Streaming is a fundamental part of the Kernschmied user experience.

By using Server-Sent Events, the platform delivers AI responses incrementally while keeping the implementation simple, standards-based, and independent of any specific model provider.

The frontend focuses exclusively on rendering streamed events, while the backend remains responsible for orchestration, authorization, and response generation.

---

Back to [[Home]].
