# ADR-0011: Hierarchy and Prompt Inheritance

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decision Makers:** Kernschmied Architecture Team
- **Supersedes:** None
- **Superseded by:** None

---

# Context

Kernschmied is designed as a generic AI platform rather than a single-purpose chat application.

Users organize their work into hierarchical structures such as:

- Organizations
- Departments
- Teams
- Projects
- Folders
- Chats

Future installations may introduce completely different node types without requiring backend or frontend changes.

The hierarchy therefore becomes one of the core architectural concepts of the entire platform.

It is responsible for:

- logical organization
- configuration inheritance
- prompt inheritance
- tool inheritance
- model defaults
- security boundaries
- navigation
- context resolution

---

# Problem

Traditional AI applications frequently duplicate configuration at every level.

Examples include:

- copying prompts into every chat
- manually enabling tools
- assigning models repeatedly
- duplicating system instructions

This results in:

- inconsistent behavior
- configuration drift
- difficult maintenance
- increased administrative effort

The platform requires a deterministic inheritance mechanism.

---

# Decision

Kernschmied adopts a **generic hierarchical configuration model**.

Every node may contribute configuration.

The effective runtime configuration is calculated by combining inherited configuration from parent nodes with local overrides.

The hierarchy itself contains no business-specific logic.

---

# Architectural Principle

> Configuration flows downward through the hierarchy.
>
> Nodes inherit defaults unless they explicitly override them.

---

# High-Level Architecture

```text
System

        │

        ▼

Organization

        │

        ▼

Project

        │

        ▼

Folder

        │

        ▼

Chat
```

Each level may define additional configuration.

---

# Goals

The hierarchy architecture should provide:

- generic node types
- unlimited hierarchy depth
- prompt inheritance
- tool inheritance
- model inheritance
- configuration inheritance
- deterministic resolution
- future extensibility

---

# Generic Nodes

Hierarchy nodes are generic.

Examples include:

- organization
- department
- workspace
- project
- folder
- user
- assistant
- chat

Additional node types may be introduced without modifying the hierarchy engine.

---

# Node Structure

Every node contains common metadata.

Typical properties include:

- identifier
- parent identifier
- node type
- title
- description
- metadata
- configuration reference
- permissions

Business-specific data belongs outside the hierarchy itself.

---

# Hierarchy Service

The **Hierarchy Service** manages the tree structure.

Responsibilities include:

- loading nodes
- validating parent-child relationships
- resolving ancestry
- calculating inheritance chains
- preventing invalid structures
- exposing navigation APIs

Business services never traverse the hierarchy directly.

---

# Hierarchy Traversal

Typical traversal:

```text
Chat

↓

Folder

↓

Project

↓

Organization

↓

System
```

The resolver collects configuration beginning at the root.

---

# Configuration Inheritance

Every node may contribute configuration.

Example:

```text
System

↓

Default Model

↓

Project

↓

Project Prompt

↓

Chat

↓

Temperature Override
```

The resulting configuration combines all applicable values.

---

# Prompt Inheritance

Prompt inheritance follows the same hierarchical model.

Example:

```text
System Prompt

↓

Organization Prompt

↓

Project Prompt

↓

Chat Prompt
```

The effective prompt is produced by the Configuration Resolver.

---

# Prompt Composition

Prompt inheritance is deterministic.

Example:

```text
System

↓

Company Policies

↓

Project Instructions

↓

Chat Instructions

↓

Current User Message
```

The resulting prompt is assembled before model execution.

---

# Tool Inheritance

Nodes may enable or disable tools.

Example:

```text
System

Calculator

Filesystem

↓

Project

Web Search

↓

Chat

Image Generation
```

The effective tool set is resolved automatically.

---

# Model Inheritance

Nodes may define default models.

Example:

```text
System

Default Model

↓

Project

Coding Model

↓

Chat

Reasoning Model
```

Lower levels override inherited defaults where appropriate.

---

# Configuration Resolution

The effective configuration is calculated by combining:

- inherited values
- local values
- merge strategies
- request overrides

The resulting configuration is immutable during request processing.

---

# Merge Strategies

Hierarchy inheritance supports multiple merge strategies.

---

## Replace

The local value replaces the inherited value.

---

## Extend

Collections are extended.

---

## Deep Merge

Nested configuration objects are recursively merged.

These strategies are defined by the Configuration Management architecture.

---

# Effective Configuration

Business services receive only the effective configuration.

Example:

```text
Hierarchy

↓

Resolver

↓

Merge

↓

Validation

↓

Effective Configuration
```

The service never knows where a value originated.

---

# Effective Prompt

Prompt generation follows the same principle.

```text
Hierarchy

↓

Prompt Fragments

↓

Merge

↓

Template Processing

↓

Effective Prompt
```

Models receive only the final prompt.

---

# Hierarchy Navigation

The hierarchy supports navigation operations such as:

- children
- parent
- ancestors
- descendants
- siblings
- root

Traversal remains independent from business logic.

---

# Dynamic Node Types

Node types are configuration-driven.

Examples:

```text
workspace

department

campaign

knowledge_base

assistant

repository
```

Unknown node types are displayed generically by the frontend.

---

# Frontend Integration

The frontend renders hierarchy nodes using the Generic Tree component.

Rendering is based on:

- node type
- UI schema
- metadata
- registered components

No node-specific React components are required.

---

# Prompt Templates

Prompt inheritance may reference reusable templates.

Example:

```text
Corporate Prompt

↓

Coding Prompt

↓

Chat Prompt

↓

Request Prompt
```

Templates remain versioned configuration rather than hardcoded strings.

---

# Security Considerations

Hierarchy boundaries influence authorization.

Permissions may depend upon:

- node ownership
- workspace
- project
- department
- inherited policies

Hierarchy traversal never bypasses authorization checks.

---

# Performance Considerations

Hierarchy resolution is optimized through:

- caching
- immutable snapshots
- ancestry caching
- revision-based invalidation

Traversal should remain inexpensive even for deep trees.

---

# Operational Impact

The hierarchy architecture enables:

- enterprise organization
- reusable configuration
- centralized prompt management
- project templates
- workspace defaults
- scalable administration

Administrators modify shared behavior at higher hierarchy levels.

---

# Consequences

## Positive

- Minimal duplication
- Centralized configuration
- Deterministic inheritance
- Generic architecture
- Extensible node model
- Consistent prompts

## Negative

- More complex resolver
- Inheritance debugging
- Additional caching requirements

---

# Alternatives Considered

## Flat Configuration

Every chat stores all configuration.

Rejected because it duplicates data and increases maintenance.

---

## Prompt Duplication

Copy prompts into every project.

Rejected because updates become inconsistent.

---

## Hardcoded Node Types

Rejected because future deployments require arbitrary hierarchy structures.

---

## Recursive Runtime Resolution Without Caching

Rejected because deep hierarchies would degrade performance.

---

# Risks

Potential risks include:

- circular parent references
- inheritance conflicts
- excessive hierarchy depth
- unexpected overrides
- stale caches

Mitigation includes:

- hierarchy validation
- cycle detection
- deterministic merge rules
- revision tracking
- automated tests

---

# Implementation Notes

The implementation should provide:

- Hierarchy Service
- generic hierarchy nodes
- ancestry resolver
- prompt resolver
- configuration resolver
- merge strategies
- hierarchy validation
- cache invalidation
- immutable effective configuration

Business services should never manually traverse hierarchy relationships.

---

# Related Decisions

- [[ADR-0001-Schema-Driven-UI]]
- [[ADR-0002-Bootstrap]]
- [[ADR-0007-Database-and-Storage-Architecture]]
- [[ADR-0010-Configuration-Management]]
- [[ADR-0012-Frontend-Architecture-and-Schema-Driven-UI]]

---

# Related Documentation

## Architecture

- [[Architecture]]
- [[Hierarchy]]
- [[Configuration-Architecture]]

---

## Backend

- [[Hierarchy-Service]]
- [[Configuration]]
- [[Prompt-Resolver]]
- [[REST-API]]

---

## Frontend

- [[Generic-Tree]]
- [[Schema-Renderer]]
- [[UI-Schema]]

---

## Concepts

- [[Prompt-Inheritance]]
- [[Configuration-Resolver]]
- [[Hierarchy-Nodes]]
- [[Runtime-Configuration]]

---

# Decision Summary

Kernschmied adopts a **generic hierarchy architecture** in which every node may contribute configuration, prompts, tools, models, permissions, and metadata through deterministic inheritance.

The **Hierarchy Service** is responsible for resolving ancestry, while the **Configuration Resolver** calculates the immutable effective configuration and prompt presented to business services and language models.

By separating hierarchy management from business logic and supporting arbitrary node types, the platform remains extensible, schema-driven, and suitable for future enterprise deployments without requiring architectural changes.

---

Back to [[Home]].
