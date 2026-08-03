# ADR-0015: Chat and Conversation Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a long-lived, schema-driven AI platform where conversations are first-class business objects rather than temporary requests.

Unlike traditional chat applications, conversations are embedded into the generic hierarchy and become part of the platform's knowledge structure.

The platform must support:

- long-running conversations
- hierarchical organization
- multiple AI models
- multiple participants
- persistent history
- prompt inheritance
- context resolution
- resources
- actions
- widgets
- workflows
- future collaboration
- future multi-agent conversations

A conversation therefore represents considerably more than a sequence of exchanged messages.

---

# Problem

Many AI applications treat chat as a stateless request/response interaction.

Typical implementations only store:

- prompt
- response

Everything else is reconstructed afterwards.

This approach is insufficient for a configurable platform.

---

## Conversations Become Isolated

Chats are disconnected from projects, workspaces and business objects.

Knowledge cannot be organized naturally.

---

## Context Must Be Rebuilt

Every request must reconstruct:

- prompts
- permissions
- resources
- configuration
- available tools

This increases complexity and inconsistency.

---

## Difficult Collaboration

Traditional chat sessions assume a single user.

Future collaboration and shared conversations become difficult.

---

## Weak Integration

Messages cannot naturally reference:

- resources
- actions
- workflows
- hierarchy nodes

---

## Poor Long-Term Knowledge

Valuable information remains trapped inside message history.

The platform cannot easily promote important knowledge into reusable resources.

---

# Decision

Kernschmied adopts a **Conversation-Centric Architecture**.

Conversations become persistent domain objects integrated into the generic hierarchy.

Messages are immutable historical events belonging to a conversation.

The conversation—not the request—is the primary business object.

---

# Architectural Principle

> **A conversation is a persistent business object.
>
> Messages describe what happened inside the conversation.
>
> Context is resolved around the conversation, not reconstructed from individual requests.**

---

# High-Level Architecture

```text
Hierarchy

        │

        ▼

Conversation

        │

        ▼

Effective Context

        │

        ▼

Messages

        │

        ▼

AI Model

        │

        ▼

Events

```

---

# Core Concepts

The Chat Architecture consists of several independent concepts.

---

## Conversation

A conversation represents a persistent communication context.

Typical metadata includes:

- identifier
- title
- hierarchy node
- participants
- active model
- current status
- revision

A conversation exists independently of individual messages.

---

## Messages

Messages are immutable records belonging to exactly one conversation.

Typical message types include:

- user
- assistant
- system
- tool
- reasoning
- notification

Messages are never modified after creation.

Corrections create new messages.

---

## Conversation Context

Every conversation has an Effective Context.

The Effective Context is resolved from:

- hierarchy
- prompt inheritance
- runtime configuration
- permissions
- available models
- available tools
- resources
- widgets

The frontend never assembles context manually.

---

## Conversation State

A conversation may transition through several states.

Typical examples include:

- created
- active
- waiting
- streaming
- completed
- archived
- deleted

The lifecycle is managed by the backend.

---

## Participants

A conversation may contain multiple participants.

Examples include:

- human users
- AI assistants
- future AI agents
- future external systems

Participants communicate through messages.

---

## Active Model

A conversation may define its active AI model.

Model selection may inherit from:

- system
- tenant
- workspace
- project
- conversation

Conversation-level configuration overrides inherited defaults.

---

## Conversation Metadata

Metadata describes the conversation itself.

Examples include:

- language
- tags
- category
- objectives
- summary
- archived flag

Metadata evolves independently of messages.

---

# Message Architecture

Messages follow versioned contracts.

Each message contains:

- message identifier
- conversation identifier
- sender
- role
- timestamp
- sequence number
- visibility
- content

Additional metadata may be added over time.

---

## Message Ordering

Messages are ordered by sequence number.

Ordering is guaranteed only within a conversation.

Sequence numbers are assigned by the backend.

---

## Streaming

Streaming responses are transported using the Event Architecture.

Streaming produces events such as:

- chat.started
- chat.token
- chat.reasoning
- chat.message
- chat.completed
- chat.failed

The final assistant message becomes a persistent message.

Streaming tokens themselves remain ephemeral.

---

## Conversation Memory

Conversation history is persistent.

The platform may derive higher-level knowledge from conversations.

Examples include:

- summaries
- milestones
- extracted resources
- decisions
- action items

Derived knowledge does not replace original messages.

---

## Context Resolution

Before model execution the backend resolves the Effective Context.

The Effective Context includes:

- hierarchy path
- inherited prompts
- runtime configuration
- permissions
- registry revisions
- available resources
- available actions
- available widgets

The model never receives unrestricted platform data.

---

## Prompt Resolution

Prompt resolution follows ADR-0008.

Conversation prompts participate in prompt inheritance.

Resolved prompts become part of the Effective Context.

---

## Resources

Conversations may reference resources.

Examples include:

- notes
- documents
- tasks
- files
- future resource types

Resources remain independent business objects.

---

## Widgets

Widgets may visualize conversation data.

Examples include:

- chat history
- participants
- referenced resources
- generated tasks

Widgets never own conversation state.

---

## Actions

Actions may be executed within a conversation.

Examples include:

- create resource
- update resource
- execute workflow
- call tool

Actions follow ADR-0012.

---

## Tool Calls

AI models may request tool execution.

Tool execution follows registered Action contracts.

Tool execution results become conversation events and optionally persistent messages.

---

## Hierarchy Integration

Every conversation belongs to exactly one hierarchy node.

Typical examples:

```text
Workspace

    │

    ▼

Project

    │

    ▼

Conversation
```

Additional hierarchy structures may exist in the future.

---

## Conversation Lifecycle

Typical lifecycle:

```text
Created

    │

    ▼

Active

    │

    ▼

Streaming

    │

    ▼

Completed

    │

    ▼

Archived
```

Deletion is a controlled administrative operation.

---

## Revision Handling

Conversation metadata carries revisions.

Messages remain immutable.

Editing metadata increases the conversation revision.

Adding messages does not modify previous messages.

---

## Authorization

Authorization is evaluated by the backend.

Permissions determine:

- who may read
- who may write
- who may archive
- who may delete
- who may invite participants

The frontend only reflects permissions.

---

## Security

Conversations may contain confidential information.

Security policies determine:

- visibility
- retention
- export
- sharing
- auditing

Sensitive information must never be leaked across conversation boundaries.

---

## Dynamic Extensibility

Future extensions may introduce:

- new participant types
- new message types
- new metadata
- new conversation capabilities

The Conversation Architecture remains unchanged.

---

## Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0010 — Generic Resource Architecture
- ADR-0011 — Generic Widget Architecture
- ADR-0012 — Generic Action Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture

The Chat and Conversation Architecture defines how AI interactions become persistent business objects inside the platform.

---

# Consequences

## Positive

### Persistent Conversations

Conversations become durable business objects.

---

### Stable Context Resolution

Context is resolved consistently before every model invocation.

---

### Better Knowledge Management

Knowledge can evolve from conversations into reusable resources.

---

### Extensibility

New participant and message types require no architectural changes.

---

### Better Collaboration

The architecture naturally supports future multi-user and multi-agent conversations.

---

### Consistent Integration

Resources, widgets, actions and workflows integrate directly with conversations.

---

### Improved Maintainability

Conversation logic remains centralized.

---

## Negative

### Higher Initial Complexity

Persistent conversations require additional infrastructure.

---

### Storage Requirements

Long-lived conversations increase storage needs.

---

### Context Resolution Overhead

Effective Context generation requires additional processing.

---

### Lifecycle Management

Conversation lifecycle requires dedicated management.

---

# Alternatives Considered

## Stateless Request/Response

### Advantages

- Simple implementation
- Low storage requirements

### Disadvantages

- Weak context
- Poor persistence
- Difficult collaboration

Rejected.

---

## Session-Based Chat

### Advantages

- Familiar architecture
- Lightweight

### Disadvantages

- Weak hierarchy integration
- Difficult long-term knowledge management

Rejected.

---

## Conversation Embedded Inside Projects

### Advantages

- Simpler data model

### Disadvantages

- Conversations cannot evolve independently
- Poor extensibility

Rejected.

---

# Compliance

All conversation-related implementations shall comply with this ADR.

In particular:

- conversations shall be persistent business objects
- conversations shall belong to the hierarchy
- messages shall be immutable
- sequence numbers shall be assigned by the backend
- Effective Context shall be resolved server-side
- streaming shall use the Event Architecture
- prompts shall follow ADR-0008
- actions shall follow ADR-0012
- resources shall remain independent objects
- widgets shall not own conversation state
- authorization shall be enforced by the backend
- conversation metadata shall be versioned
- unknown future capabilities shall be ignored safely
- conversation contracts shall remain backward compatible whenever possible
- breaking changes shall require new schema versions

```

```
