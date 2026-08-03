# ADR-0008: Prompt Architecture and Context Resolution

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a configurable AI platform where the behavior of an assistant is determined by structured configuration rather than hardcoded prompts.

The platform must support:

- multiple deployment profiles
- multiple tenants (future)
- configurable hierarchy structures
- configurable prompt inheritance
- configurable assistant behavior
- multiple AI models
- runtime configuration
- dynamic extensions
- long-term maintainability

Unlike traditional chat applications, the effective prompt is never stored as a single static string.

Instead, it is assembled dynamically from multiple independent prompt sources.

This architecture enables different assistants, projects, workspaces and chats to behave differently without modifying application code.

---

# Problem

Embedding prompt logic directly into application code or storing complete prompts as static templates creates several architectural problems.

## Prompt Duplication

The same instructions become copied into:

- projects
- assistants
- workflows
- templates

This quickly creates inconsistencies.

---

## Difficult Maintenance

Changing one global instruction may require updating dozens of prompts.

---

## Poor Runtime Flexibility

Changing prompt behavior often requires:

- editing files
- restarting services
- redeployment

instead of changing runtime configuration.

---

## Tight Coupling

Prompt behavior becomes coupled to:

- frontend
- backend services
- individual model providers

instead of being resolved through configuration.

---

## No Clear Inheritance

Without explicit inheritance rules it becomes impossible to understand:

- which instructions are active
- where they originate
- which instructions override others

---

## Difficult Debugging

When an AI produces unexpected output it becomes difficult to reconstruct the effective prompt that was actually sent.

---

# Decision

Kernschmied adopts a **hierarchical prompt architecture with deterministic context resolution**.

Prompts are treated as structured configuration objects.

The application dynamically resolves the effective prompt from multiple configuration layers before each model invocation.

The effective prompt is deterministic, reproducible and traceable.

---

# Architectural Principle

> **Prompt behavior is configuration.
>
> Prompt resolution is deterministic.
>
> Model providers receive only the resolved result.**

---

# High-Level Architecture

```text
Platform Prompt

        │

        ▼

Deployment Profile

        │

        ▼

Tenant Prompt (future)

        │

        ▼

Workspace Prompt

        │

        ▼

Project Prompt

        │

        ▼

Assistant Prompt

        │

        ▼

Chat Prompt

        │

        ▼

Task Prompt

        │

        ▼

Runtime Context

        │

        ▼

Effective Prompt

        │

        ▼

Model Provider
```

---

# Prompt Layers

The platform resolves prompts from multiple independent layers.

Typical layers include:

- platform
- deployment profile
- tenant
- workspace
- project
- hierarchy node
- assistant
- chat
- workflow
- task
- runtime context

Each layer contributes only its own responsibility.

---

# Prompt Types

Prompt definitions are categorized.

Typical prompt types include:

- platform
- policy
- assistant
- hierarchy
- workflow
- chat
- task
- formatting
- safety
- tool guidance

Additional prompt types may be introduced through the registry system.

---

# Prompt Resolution

Prompt resolution follows a deterministic order.

Each prompt definition specifies its inheritance mode.

Supported modes include:

- inherit
- extend
- replace
- restrict
- disable

The resolver always produces exactly one effective prompt.

---

# Effective Context

Prompt resolution depends on the current execution context.

The context may include:

- active tenant
- authenticated user
- active hierarchy node
- active project
- active chat
- selected assistant
- enabled tools
- selected model
- runtime configuration
- registry revisions

The context itself is a versioned contract.

---

# Context Resolution

Before every model invocation the backend resolves:

- permissions
- available tools
- effective prompt
- runtime configuration
- active model
- capability set

The frontend never assembles prompts.

---

# Prompt Definitions

Prompt definitions are runtime configuration.

They include metadata such as:

- identifier
- scope
- prompt type
- inheritance mode
- status
- revision
- schema version

Prompt definitions are validated before activation.

---

# Prompt Registry

Prompt definitions participate in the registry architecture.

Registries are responsible for:

- discovery
- validation
- activation
- revision tracking
- lifecycle management

The core application never loads prompt definitions directly from arbitrary locations.

---

# Runtime Modification

Administrators may:

- create prompt definitions
- modify prompt definitions
- activate prompt revisions
- archive prompt definitions

Changes become effective through configuration rather than deployment.

---

# Prompt Versioning

Prompt definitions are versioned independently.

Each definition contains:

- schema_version
- revision
- status

Historical revisions remain available for auditing.

---

# Prompt Auditing

Every prompt change is auditable.

Audit information includes:

- author
- timestamp
- revision
- activation
- previous revision

The effective prompt itself may optionally be stored for debugging purposes depending on deployment profile and data classification.

---

# Security

Prompt definitions are configuration, not executable code.

The following principles apply:

- prompts never contain executable Python code
- prompts never execute JavaScript
- prompts never bypass authorization
- prompts never expose secrets
- prompts are validated before activation

Dynamic prompt configuration never implies arbitrary code execution.

---

# Separation of Responsibilities

The backend is responsible for:

- prompt storage
- inheritance
- validation
- context resolution
- effective prompt generation

The frontend is responsible only for:

- editing prompt definitions
- displaying prompt metadata
- visualizing inheritance
- presenting validation errors

---

# Dynamic Extensibility

New prompt types may be introduced through the registry architecture.

New prompt definitions must not require:

- backend source modifications
- frontend business components
- deployment

Only validated definitions may become active.

---

# Relationship to Other ADRs

This decision complements:

- ADR-0001 — Schema-Driven User Interface
- ADR-0002 — Bootstrap Configuration and Runtime Initialization
- ADR-0003 — Registry-Based Extension Architecture
- ADR-0005 — Versioned Contracts and Schema Evolution
- ADR-0006 — API Contracts and Versioning
- ADR-0007 — Runtime Configuration Architecture

Prompt resolution relies on the registry system, runtime configuration and versioned contracts.

---

# Consequences

## Positive

### Deterministic Prompt Resolution

Every model invocation is reproducible.

---

### Runtime Flexibility

Prompt behavior can evolve without redeployment.

---

### Reduced Duplication

Instructions are maintained once and inherited where appropriate.

---

### Improved Maintainability

Prompt logic is centralized instead of scattered across the application.

---

### Better Auditability

Every prompt revision is traceable.

---

### Registry Integration

Prompt types evolve consistently with the rest of the platform.

---

### Provider Independence

Model providers receive resolved prompts without knowledge of inheritance.

---

## Negative

### Higher Initial Complexity

Prompt resolution requires a dedicated resolver.

---

### More Metadata

Prompt definitions require lifecycle and revision information.

---

### Additional Validation

Prompt activation requires schema validation.

---

### Increased Documentation Requirements

Inheritance rules must be clearly documented to remain understandable.

---

# Alternatives Considered

## Static Prompt Files

### Advantages

- Simple implementation
- Easy debugging

### Disadvantages

- No runtime flexibility
- High duplication
- Requires redeployment

Rejected.

---

## Hardcoded Prompts

### Advantages

- Fast implementation
- Minimal infrastructure

### Disadvantages

- No configurability
- Poor maintainability
- High coupling

Rejected.

---

## Prompt Construction in the Frontend

### Advantages

- Immediate UI customization

### Disadvantages

- Security risks
- Inconsistent behavior
- Duplicate logic
- Impossible to guarantee deterministic execution

Rejected.

---

## Runtime Code Generation

Generating prompts through dynamically executed scripts.

### Advantages

- Maximum flexibility

### Disadvantages

- Security risks
- Non-deterministic behavior
- Difficult validation
- Difficult auditing

Rejected.

---

# Compliance

All prompt-related implementations shall comply with this ADR.

In particular:

- prompt definitions shall be versioned
- prompt resolution shall be deterministic
- prompt inheritance shall be explicit
- prompt execution shall occur only after backend context resolution
- prompt configuration shall never execute arbitrary code
- prompt lifecycle shall be managed through registries
- prompt changes shall be auditable
- effective prompts shall be reproducible