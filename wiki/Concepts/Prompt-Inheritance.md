# Prompt Inheritance

The **Prompt Inheritance** concept defines how Kernschmied builds the final prompt that is sent to an AI model by combining prompt fragments from multiple hierarchical levels.

Instead of storing one large static system prompt for every conversation, Kernschmied assembles prompts dynamically from reusable configuration layers. This enables organizations, projects, users, and individual requests to contribute contextual instructions while preserving a deterministic and predictable resolution process.

Prompt Inheritance is one of the key architectural concepts behind Kernschmied's schema-driven and configuration-driven design.

---

# Goals

The Prompt Inheritance architecture is designed to provide:

- Reusable prompt definitions
- Hierarchical context composition
- Runtime configurability
- Deterministic prompt generation
- Separation of responsibilities
- Provider independence
- Stable behavior
- Future extensibility

---

# Core Principle

Instead of creating prompts manually for every conversation, the backend assembles them from multiple inheritance levels.

```text
System Prompt

↓

Organization Prompt

↓

Workspace Prompt

↓

Project Prompt

↓

Conversation Prompt

↓

Request Prompt

↓

Final Prompt
```

Every layer contributes additional context.

---

# Why Prompt Inheritance?

Without inheritance, every conversation would require its own complete prompt.

```text
Conversation A

↓

Complete Prompt

Conversation B

↓

Complete Prompt

Conversation C

↓

Complete Prompt
```

This approach leads to:

- duplicated instructions
- inconsistent behavior
- difficult maintenance
- error-prone updates

Prompt inheritance removes duplication by reusing shared instructions.

---

# Design Principles

## Composition Instead of Duplication

Prompt fragments are composed together.

```text
Reusable Fragments

↓

Prompt Resolver

↓

Final Prompt
```

Individual layers only define what they need to contribute.

---

## Deterministic Resolution

Given identical configuration and hierarchy, prompt resolution always produces the same result.

The backend never generates prompts using random ordering or undefined merge behavior.

---

## Provider Independence

Prompt construction is completely independent of the AI provider.

```text
Prompt Resolver

↓

Final Prompt

↓

Provider Backend
```

The provider receives an already resolved prompt.

---

## Configuration Driven

Prompt fragments are stored as runtime configuration rather than hardcoded application logic.

Administrators can update prompts without modifying source code or restarting the application.

---

# Prompt Hierarchy

A typical inheritance chain may look like this:

```text
System

↓

Organization

↓

Department

↓

Project

↓

Conversation

↓

Request
```

Additional hierarchy levels may be introduced through configuration.

---

# System Prompt

The system level defines global platform behavior.

Typical examples include:

- assistant personality
- response language
- formatting guidelines
- safety rules
- general instructions

Every conversation inherits the system prompt.

---

# Organization Prompt

Organizations may define shared instructions.

Examples include:

- company terminology
- writing style
- branding
- legal requirements
- compliance rules

These instructions apply to all descendant nodes.

---

# Workspace Prompt

A workspace may define context shared by related projects.

Examples include:

- documentation standards
- engineering guidelines
- department-specific terminology

Workspaces help avoid repetition across multiple projects.

---

# Project Prompt

Projects contribute project-specific context.

Examples include:

- coding conventions
- architectural principles
- project goals
- preferred technologies
- domain vocabulary

Project prompts affect only the corresponding project hierarchy.

---

# Conversation Prompt

Individual conversations may define temporary context.

Examples include:

- current task
- discussion topic
- temporary assumptions
- session-specific instructions

Conversation prompts are isolated from other conversations.

---

# Request Prompt

The request level has the highest priority.

Typical examples include:

- explicit user instructions
- temporary generation settings
- one-time formatting requests

Request prompts exist only for a single request.

---

# Prompt Resolution

The Prompt Resolver combines all applicable prompt fragments.

```text
Hierarchy

↓

Configuration Resolver

↓

Prompt Resolver

↓

Resolved Prompt
```

The resulting prompt is immutable during model execution.

---

# Prompt Composition

Each inheritance level contributes only its own instructions.

Example:

```text
System
  You are an engineering assistant.

↓

Project
  Use Python 3.12.

↓

Request
  Explain dependency injection.

↓

Final Prompt
```

The resolver combines the fragments in a deterministic order.

---

# Ordering

Prompt ordering is well-defined.

Lower-level prompts extend higher-level prompts rather than replacing them unless explicitly configured.

Example order:

```text
Global

↓

Organizational

↓

Project

↓

Conversation

↓

Request
```

Ordering never depends on database retrieval order.

---

# Merge Strategy

Different prompt sections may use different merge strategies.

Typical strategies include:

| Strategy         | Description                              |
| ---------------- | ---------------------------------------- |
| Append           | Add instructions after inherited content |
| Replace          | Replace inherited section                |
| Disable          | Remove inherited contribution            |
| Structured Merge | Merge structured prompt metadata         |

The merge strategy is defined by configuration.

---

# Runtime Configuration

Prompt fragments are stored as runtime configuration.

Benefits include:

- immediate updates
- revision tracking
- audit logging
- validation
- centralized management

No application restart is required for runtime-editable prompt changes.

---

# Hierarchy Integration

Prompt inheritance follows the same hierarchy used for configuration.

```text
Hierarchy

↓

Prompt Resolver

↓

Final Prompt
```

Hierarchy changes automatically influence inherited prompts.

---

# Configuration Revisions

Prompt updates increment the configuration revision.

```text
Prompt Updated

↓

Configuration Revision++

↓

Cache Invalidated

↓

Next Request Uses New Prompt
```

The resolver always uses the latest valid configuration.

---

# Provider Interaction

Providers never assemble prompts.

Instead:

```text
Prompt Resolver

↓

Resolved Prompt

↓

Provider
```

Every provider receives identical prompt content regardless of implementation.

---

# Chat Integration

When a chat request arrives:

```text
Chat Request

↓

Resolve Hierarchy

↓

Resolve Configuration

↓

Resolve Prompt

↓

Model Execution
```

Prompt construction always precedes inference.

---

# Prompt Validation

Prompt configuration is validated before activation.

Validation includes:

- schema compatibility
- required fields
- supported merge strategies
- configuration integrity

Invalid prompt configuration is rejected.

---

# Security

Prompt inheritance follows backend security policies.

Only authorized users may modify prompt configuration.

Prompt fragments cannot:

- execute code
- bypass authorization
- modify application logic
- access protected runtime state

Prompt text remains data rather than executable behavior.

---

# Performance

Prompt resolution is optimized through:

- immutable prompt snapshots
- revision-aware caching
- efficient hierarchy traversal
- deterministic merge algorithms

Prompt construction remains inexpensive enough to occur for every request.

---

# Benefits

Prompt Inheritance provides several architectural advantages.

## Consistency

Shared instructions are applied uniformly across related conversations.

---

## Reusability

Prompt fragments can be reused across multiple hierarchy levels.

---

## Maintainability

Common instructions are updated once instead of being duplicated.

---

## Scalability

Large organizations can manage prompt behavior centrally while allowing local customization.

---

## Provider Independence

Prompt construction remains independent of AI model implementations.

---

# Future Extensions

The architecture supports future capabilities including:

- conditional prompt fragments
- localization-aware prompts
- tenant-specific prompt layers
- reusable prompt templates
- prompt diagnostics
- prompt version history
- policy-driven prompt composition

These enhancements can be introduced without changing the fundamental inheritance model.

---

# Relationship to Other Concepts

Prompt Inheritance is closely related to:

- [[Configuration]]
- [[Hierarchy]]
- [[Runtime Configuration]]
- [[Configuration Revisions]]
- [[Dynamic-UI]]

---

# Related Documentation

## Concepts

- [[Configuration]]
- [[Hierarchy]]
- [[Configuration Revisions]]
- [[Runtime Configuration]]
- [[Versioning]]

---

## Architecture

- [[Prompt-Inheritance]]
- [[Configuration-Architecture]]
- [[Hierarchy-Architecture]]
- [[Request-Lifecycle]]

---

## Backend

- [[Chat]]
- [[Configuration]]
- [[Hierarchy]]
- [[Model-Registry]]

---

## APIs

- [[Chat]]
- [[Configuration]]
- [[Hierarchy]]

---

# Summary

Prompt Inheritance enables Kernschmied to construct AI prompts dynamically by combining reusable prompt fragments from multiple hierarchical configuration levels instead of relying on duplicated, conversation-specific prompts.

Through deterministic resolution, configuration-driven composition, revision-aware caching, provider-independent prompt generation, and seamless integration with the hierarchy and configuration systems, Prompt Inheritance delivers consistent AI behavior while remaining flexible enough to support organizations, projects, conversations, and future extensions without increasing maintenance complexity.

---

Back to [[Home]].
