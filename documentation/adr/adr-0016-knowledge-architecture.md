# ADR-0016: Knowledge Architecture

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is intended to become a long-lived AI platform whose value increases over time through accumulated knowledge.

Unlike traditional chat applications, knowledge is not limited to conversation history.

The platform must support:

- persistent knowledge
- reusable knowledge
- structured knowledge
- unstructured knowledge
- manually created knowledge
- AI-generated knowledge
- imported knowledge
- future external knowledge sources
- future Retrieval-Augmented Generation (RAG)
- future semantic search

Knowledge must become an independent architectural concept rather than a by-product of conversations.

---

# Problem

Many AI systems treat knowledge as raw documents or previous chat messages.

Typical implementations simply search text without understanding the architectural relationship between conversations, resources and reusable knowledge.

This approach creates several problems.

---

## Knowledge Becomes Fragmented

Important information is scattered across:

- conversations
- documents
- notes
- prompts
- configuration
- external systems

No unified knowledge architecture exists.

---

## Chat History Is Not Knowledge

Conversation history contains:

- temporary discussions
- corrections
- incomplete ideas
- outdated decisions

Not every message represents reusable knowledge.

---

## Difficult Reuse

Knowledge stored only inside chats cannot easily be reused by:

- other conversations
- workflows
- tools
- future AI agents

---

## Weak Governance

Knowledge often lacks:

- ownership
- lifecycle
- classification
- revision history
- approval workflows

---

## Poor Extensibility

Supporting future knowledge sources frequently requires architectural changes.

---

# Decision

Kernschmied adopts a **Knowledge Architecture** that separates conversations, resources and knowledge into independent concepts.

Knowledge becomes a first-class business object.

Conversations generate knowledge.

Resources may contain knowledge.

Knowledge itself remains independently managed.

---

# Architectural Principle

> **Conversations create information.
>
> Resources organize information.
>
> Knowledge represents validated and reusable information.**

---

# High-Level Architecture

```text
Conversation

        │

        ▼

Messages

        │

        ▼

Resources

        │

        ▼

Knowledge

        │

        ▼

Search / AI / Workflows
```

---

# Core Concepts

The Knowledge Architecture consists of several independent concepts.

---

## Knowledge Object

Knowledge is represented as a versioned business object.

Typical metadata includes:

- identifier
- title
- description
- knowledge type
- classification
- revision
- status
- owner

Knowledge objects are independent from conversations.

---

## Knowledge Sources

Knowledge may originate from many sources.

Examples include:

- conversations
- notes
- documents
- imported files
- workflows
- tools
- external systems
- future connectors

The architecture is source-independent.

---

## Knowledge Types

Examples include:

- article
- note
- decision
- guideline
- procedure
- FAQ
- specification
- reference
- lesson learned
- future custom types

Knowledge types are registry-driven.

---

## Structured and Unstructured Knowledge

The platform supports both:

### Structured Knowledge

Examples:

- configuration
- specifications
- metadata
- decision records

---

### Unstructured Knowledge

Examples:

- documents
- notes
- markdown
- OCR
- transcripts

Both are handled through the same architecture.

---

## Knowledge Lifecycle

Knowledge follows an explicit lifecycle.

Typical states include:

- draft
- reviewed
- approved
- active
- deprecated
- archived

Lifecycle policies are configurable.

---

## Knowledge Classification

Knowledge may be classified.

Examples include:

- public
- internal
- confidential
- restricted

Classification determines visibility and handling.

---

## Knowledge Ownership

Every knowledge object has ownership.

Ownership supports:

- accountability
- review
- auditing
- maintenance

Ownership may belong to:

- user
- team
- tenant
- system

---

## Knowledge Revision

Knowledge objects are versioned.

Every modification creates a new revision.

Previous revisions remain traceable.

Revision management follows ADR-0005.

---

## Knowledge Relationships

Knowledge objects may reference:

- conversations
- resources
- hierarchy nodes
- workflows
- actions
- prompts
- widgets

Relationships are metadata.

Knowledge remains independent.

---

# Knowledge Extraction

Knowledge may be created manually or automatically.

Automatic extraction may occur after:

- conversations
- workflow completion
- document import
- tool execution

Extracted knowledge always requires validation according to platform policy.

---

# Knowledge Retrieval

Knowledge retrieval is independent of storage.

Future retrieval methods may include:

- keyword search
- semantic search
- vector search
- hybrid search
- metadata filtering

The architecture remains unchanged.

---

# Retrieval-Augmented Generation (RAG)

Future RAG capabilities consume Knowledge Objects rather than arbitrary files.

RAG becomes a consumer of the Knowledge Architecture.

Knowledge remains authoritative.

---

# Search

Search indexes are implementation details.

The Knowledge Architecture defines:

- knowledge objects
- metadata
- revisions
- permissions

Search technologies may evolve independently.

---

# Knowledge Context

Knowledge contributes to the Effective Context.

Relevant knowledge is selected based on:

- hierarchy
- permissions
- classification
- conversation
- user
- active workflow

The frontend never assembles knowledge context.

---

# Dynamic Extensibility

New knowledge types may be introduced through the Registry Architecture.

No architectural changes are required.

---

# AI Responsibilities

AI models may:

- summarize knowledge
- classify knowledge
- suggest relationships
- propose updates

AI models never become the authoritative source.

Final decisions remain under platform governance.

---

# Frontend Responsibilities

The frontend may:

- display knowledge
- search knowledge
- edit knowledge
- organize knowledge

The frontend never determines knowledge validity.

---

# Backend Responsibilities

The backend is responsible for:

- validation
- persistence
- revision management
- authorization
- indexing
- relationship management
- lifecycle management

---

# Security

Knowledge is subject to authorization.

Users may only access knowledge they are permitted to view.

Knowledge must never expose:

- secrets
- credentials
- private prompts
- protected system information

Classification policies apply before retrieval.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0008 — Prompt Architecture and Context Resolution
- ADR-0010 — Generic Resource Architecture
- ADR-0013 — Event Architecture
- ADR-0014 — Runtime Configuration Architecture
- ADR-0015 — Chat and Conversation Architecture

The Knowledge Architecture defines how reusable information is represented independently of conversations and resources.

---

# Consequences

## Positive

### Persistent Knowledge

Knowledge becomes a reusable platform asset.

---

### Better AI Context

Relevant knowledge can be supplied consistently to AI models.

---

### Clear Separation

Conversations, resources and knowledge remain independent.

---

### Extensibility

Future search and RAG technologies require no architectural redesign.

---

### Governance

Knowledge follows explicit lifecycle and revision policies.

---

### Better Collaboration

Knowledge can be reused across projects and conversations.

---

### Future Readiness

The architecture supports future semantic technologies.

---

## Negative

### Higher Initial Complexity

Knowledge requires dedicated infrastructure.

---

### Governance Overhead

Knowledge must be reviewed and maintained.

---

### Additional Storage

Persistent knowledge increases storage requirements.

---

### Relationship Management

Knowledge relationships require additional metadata.

---

# Alternatives Considered

## Chat History as Knowledge

### Advantages

- Simple implementation
- No extraction required

### Disadvantages

- Poor quality
- Difficult reuse
- Weak governance

Rejected.

---

## Documents Only

### Advantages

- Familiar approach

### Disadvantages

- No structured relationships
- Weak lifecycle management

Rejected.

---

## External Knowledge Only

### Advantages

- Reduced implementation effort

### Disadvantages

- Dependency on external systems
- Limited integration
- Weak governance

Rejected.

---

## AI Memory Only

Allowing the AI model to retain knowledge internally.

### Advantages

- Simple user experience

### Disadvantages

- Non-deterministic
- Poor auditability
- No versioning
- No governance

Rejected.

---

# Compliance

All knowledge-related implementations shall comply with this ADR.

In particular:

- knowledge shall be represented as independent business objects
- knowledge shall be versioned
- knowledge shall support explicit lifecycle management
- knowledge shall support classification
- authorization shall be enforced server-side
- conversations shall not be treated as knowledge
- resources and knowledge shall remain separate concepts
- search shall remain implementation-independent
- future RAG shall consume Knowledge Objects
- unknown future knowledge types shall be registry-managed
- knowledge contracts shall remain backward compatible whenever possible
- breaking changes shall require new schema versions
- knowledge shall remain independent of any specific AI model or search technology