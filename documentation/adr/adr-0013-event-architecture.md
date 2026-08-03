# ADR-0013: Event Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a modular, schema-driven platform consisting of independently evolving subsystems.

Examples include:

- Backend Services
- Frontend
- Chat System
- AI Models
- Model Providers
- Tool Providers
- Resources
- Widgets
- Actions
- Workflows
- Future Plugins
- Future Desktop Clients
- Future Mobile Clients

These subsystems continuously produce information that must be communicated in a consistent and predictable way.

Examples include:

- chat responses
- streaming tokens
- resource updates
- widget invalidation
- hierarchy changes
- workflow progress
- action execution
- notifications
- audit events
- system events

Without a common event architecture, every subsystem would invent its own event format, resulting in inconsistent APIs and duplicated client implementations.

---

# Problem

Different subsystems naturally produce different kinds of events.

Without a common architecture this typically results in:

- inconsistent payloads
- duplicated parsing logic
- incompatible streaming formats
- difficult versioning
- poor observability
- difficult plugin integration

A configurable platform therefore requires one generic event architecture.

---

## Inconsistent Event Formats

Every subsystem invents its own JSON structure.

Clients must implement custom parsers for every endpoint.

---

## Tight Coupling

Frontend components become tightly coupled to backend implementations.

Changes in one subsystem frequently require changes elsewhere.

---

## Difficult Evolution

Adding new event types often requires changing multiple consumers.

---

## Poor Streaming Support

Chat streaming, workflow progress and notifications often use incompatible protocols.

---

## Difficult Plugin Integration

Plugins cannot reliably publish or consume events without stable contracts.

---

# Decision

Kernschmied adopts a **Generic Event Architecture**.

Every runtime event follows a common versioned envelope.

Only the payload differs depending on the event type.

All public event transports shall use the same envelope regardless of protocol.

---

# Architectural Principle

> **Everything that happens is represented as an Event.
>
> Every Event follows the same contract.
>
> Only the payload changes.**

---

# High-Level Architecture

```text
Application

        │

        ▼

Business Event

        │

        ▼

Event Envelope

        │

        ▼

Transport

        │

        ▼

Frontend / Client
```

---

# Core Concepts

The event architecture consists of several independent concepts.

---

## Event Envelope

Every public event is wrapped inside a versioned Event Envelope.

The envelope contains metadata describing the event.

Typical metadata includes:

- schema version
- event identifier
- event type
- timestamp
- sequence number
- request identifier
- correlation identifier
- payload

The payload is event-specific.

---

## Event Types

Events are identified through explicit event types.

Typical examples include:

- chat.started
- chat.token
- chat.message
- chat.completed
- chat.failed

- action.started
- action.completed
- action.failed

- resource.created
- resource.updated
- resource.deleted

- hierarchy.created
- hierarchy.updated
- hierarchy.deleted

- widget.invalidated

- workflow.started
- workflow.completed

- notification.created

Additional event types may be introduced without changing the Event Envelope.

---

## Event Categories

Events generally belong to one of the following categories:

- system
- chat
- action
- resource
- widget
- hierarchy
- workflow
- notification
- audit
- plugin

Categories are descriptive metadata.

---

## Event Payload

The payload contains the event-specific information.

Payloads are independently versioned through their corresponding contracts.

The envelope remains stable.

---

## Event Sequence

Events belonging to the same stream contain an increasing sequence number.

Clients may use the sequence for:

- ordering
- replay detection
- gap detection

---

## Event Correlation

Related events may reference the same:

- request identifier
- conversation identifier
- execution identifier
- workflow identifier

This enables tracing across subsystems.

---

# Event Transport

The Event Architecture is independent of transport technology.

Supported transports may include:

- Server-Sent Events (SSE)
- WebSocket
- REST polling
- Message queues
- Future event brokers

The event contract remains identical.

---

# Server-Sent Events

SSE is the default streaming protocol.

Typical examples include:

- AI token streaming
- workflow progress
- long-running actions
- notifications

The SSE payload always contains a complete Event Envelope.

---

# Event Ordering

Ordering is guaranteed only within a single logical stream.

Examples include:

- one conversation
- one workflow
- one execution

Global ordering is not required.

---

# Event Reliability

Events are divided into two categories.

## Stateful Events

These describe persistent state changes.

Examples:

- resource.created
- hierarchy.updated
- workflow.completed

Stateful events should be reproducible.

---

## Ephemeral Events

These describe temporary runtime information.

Examples:

- typing indicators
- streaming tokens
- progress updates

Ephemeral events do not require persistence.

---

# Event Versioning

Every event contains:

- schema_version
- event_type

Breaking changes require new schema versions.

Payload evolution follows ADR-0005.

---

# Event Registry

Public event types are managed through the Registry Architecture.

The registry provides:

- discovery
- metadata
- version information
- lifecycle
- documentation

Unknown event types are ignored safely.

---

# Event Validation

Every emitted event is validated before publication.

Validation includes:

- envelope structure
- required metadata
- payload schema
- version compatibility

Invalid events are rejected.

---

# Frontend Responsibilities

The frontend is responsible for:

- parsing Event Envelopes
- dispatching events
- updating application state
- refreshing widgets
- displaying notifications

The frontend never generates authoritative business events.

---

# Backend Responsibilities

The backend is responsible for:

- generating events
- assigning identifiers
- sequencing
- validation
- authorization
- persistence (where required)

The backend remains the source of truth.

---

# Event Consumers

Consumers may include:

- frontend applications
- widgets
- workflows
- plugins
- audit services
- monitoring systems

Consumers subscribe to event types rather than implementations.

---

# Event Producers

Typical producers include:

- Chat Service
- Resource Service
- Hierarchy Service
- Action Service
- Workflow Engine
- Registry Service
- Configuration Service

Every producer uses the same Event Envelope.

---

# Dynamic Extensibility

New event types may be introduced through runtime configuration.

Introducing new events shall not require modifications to the Event Architecture.

Clients safely ignore unknown event types unless explicitly supported.

---

# Security

Events never bypass authorization.

Sensitive information is filtered before publication.

Events must never expose:

- secrets
- internal prompts
- credentials
- security tokens
- internal implementation details

Classification policies apply before publication.

---

# Observability

Every event may contain correlation metadata.

This supports:

- tracing
- diagnostics
- performance analysis
- auditing

Observability is built into the architecture.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0010 — Generic Resource Architecture
- ADR-0011 — Generic Widget Architecture
- ADR-0012 — Generic Action Architecture

The Event Architecture provides the communication mechanism connecting these architectural building blocks.

---

# Consequences

## Positive

### Uniform Communication

Every subsystem communicates through the same event structure.

---

### Stable Streaming

Streaming APIs share one common contract.

---

### Reduced Client Complexity

Clients implement one event parser instead of many.

---

### Better Extensibility

New event types require no transport changes.

---

### Improved Observability

Correlation identifiers simplify diagnostics.

---

### Plugin Readiness

Plugins may publish and consume events consistently.

---

### Better Maintainability

The Event Envelope remains stable while payloads evolve independently.

---

## Negative

### Higher Initial Design Effort

A generic event system requires careful planning.

---

### Metadata Overhead

Every event carries standardized metadata.

---

### Strong Contract Governance

Event contracts must remain stable over time.

---

### Documentation Requirements

Every public event type must be documented.

---

# Alternatives Considered

## Custom Events Per Service

### Advantages

- Simple implementation
- Service-specific optimization

### Disadvantages

- Inconsistent contracts
- High client complexity
- Difficult maintenance

Rejected.

---

## Multiple Streaming Formats

Different transports using different payloads.

### Advantages

- Local optimization

### Disadvantages

- Duplicated implementations
- Poor interoperability

Rejected.

---

## Runtime Script-Based Events

Generating arbitrary runtime event structures.

### Advantages

- Maximum flexibility

### Disadvantages

- Unpredictable contracts
- Difficult validation
- Security risks

Rejected.

---

# Compliance

All event-related implementations shall comply with this ADR.

In particular:

- every public event shall use the Event Envelope
- event envelopes shall be versioned
- payloads shall be schema validated
- events shall be registry-managed where applicable
- SSE shall transport Event Envelopes
- unknown event types shall be ignored safely
- producers shall remain independent of consumers
- sensitive information shall never be published
- correlation metadata shall be supported
- event evolution shall remain backward compatible whenever possible
- breaking changes shall require new schema versions
- public event contracts shall remain stable across platform evolution
